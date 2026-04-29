"""
后台处理线程 - 避免阻塞GUI（支持每图选择模型）
"""

import threading
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Callable, Dict, Any, Optional
from queue import Queue

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.workflow import TextRemovalWorkflow
from core.nanobanana_adapter import ProcessingResult
from gui.file_list import FileListItem


class ProcessWorker(threading.Thread):
    """处理工作线程 - 支持每图选择模型"""

    def __init__(self,
                 file_items: List[FileListItem],
                 output_dir: str,
                 config: Dict[str, Any],
                 progress_callback: Callable[[str, str, int, str], None],
                 finished_callback: Callable[[], None],
                 reference_items: Optional[List[FileListItem]] = None):
        """
        初始化工作线程

        Args:
            file_items: 待处理文件项列表（包含模型信息）
            output_dir: 输出目录
            config: 配置字典 (api_key, prompt, output_quality, output_format, provider)
            progress_callback: 进度回调 (file_path, status, progress, message)
            finished_callback: 完成回调
            reference_items: 参考图列表（多参考图模式）
        """
        super().__init__(daemon=True)
        self.file_items = file_items
        self.output_dir = Path(output_dir)
        self.config = config
        self.progress_callback = progress_callback
        self.finished_callback = finished_callback

        # 收集参考图路径
        self.reference_paths = [item.file_path for item in (reference_items or [])]

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 默认不暂停

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 存储处理结果用于生成JSON报告
        self.results = []

    def run(self):
        """执行处理"""
        try:
            api_key = self.config.get('api_key')
            provider = self.config.get('provider', 'gemini')

            # 调试信息：显示 API Key 前几位
            if api_key:
                masked_key = api_key[:8] + '...' if len(api_key) > 8 else api_key[:4] + '...'
                print(f"[调试] 使用服务商: {provider}, API Key: {masked_key} (长度: {len(api_key)})")
            else:
                print(f"[调试] 服务商: {provider}, API Key 为空!")

            # 显示实际使用的 prompt
            gui_prompt = self.config.get('prompt', '')
            print(f"[调试] GUI Prompt: {gui_prompt[:80]}..." if len(gui_prompt) > 80 else f"[调试] GUI Prompt: {gui_prompt}")

            # 如果没有文件，直接返回
            if not self.file_items:
                print("[警告] 没有待处理的文件")
                return

            total_items = len(self.file_items)

            for idx, item in enumerate(self.file_items):
                file_path = item.file_path
                model = item.model

                # 检查停止信号
                if self._stop_event.is_set():
                    self.progress_callback(file_path, "已取消", 0, "用户取消")
                    # 记录取消的结果
                    result_info = {
                        'url': file_path,
                        'filename': item.filename,
                        'output_path': None,
                        'success': False,
                        'message': '用户取消',
                        'model': model,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results.append(result_info)
                    # 记录剩余未处理的图片
                    for remaining_item in self.file_items[idx+1:]:
                        result_info = {
                            'url': remaining_item.file_path,
                            'filename': remaining_item.filename,
                            'output_path': None,
                            'success': False,
                            'message': '用户取消',
                            'model': remaining_item.model,
                            'timestamp': datetime.now().isoformat()
                        }
                        self.results.append(result_info)
                    break

                # 等待暂停恢复
                self._pause_event.wait()

                # 更新状态为处理中
                self.progress_callback(file_path, "处理中", 0, f"初始化... [使用 {self._get_model_display_name(model)}]")

                try:
                    # 创建工作流（每次创建新的以使用不同的模型）
                    workflow = TextRemovalWorkflow(
                        api_key=api_key,
                        provider=provider,
                        model=model
                    )

                    # 构建输出文件名
                    filename = Path(file_path).stem or f"image_{idx+1}"
                    output_path = self.output_dir / f"{filename}_clean.jpg"

                    # 始终使用 GUI 中用户输入的 prompt
                    prompt = self.config.get('prompt')
                    print(f"[调试] [{idx+1}/{total_items}] 使用 Prompt: {prompt[:80]}")

                    # 处理单张图片
                    result = workflow.process(
                        image_input=file_path,
                        output_path=str(output_path),
                        prompt=prompt,
                        reference_images=self.reference_paths if self.reference_paths else None,
                        progress_callback=lambda msg, pct: self._on_progress(
                            file_path, msg, pct, idx, total_items
                        )
                    )

                    # 记录结果
                    result_info = {
                        'url': file_path,
                        'filename': filename,
                        'output_path': str(output_path) if result.success else None,
                        'success': result.success,
                        'message': result.message if not result.success else '处理成功',
                        'model': model,
                        'reference_images': self.reference_paths if self.reference_paths else [],
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results.append(result_info)

                    # 更新最终状态
                    if result.success:
                        self.progress_callback(
                            file_path,
                            "完成",
                            100,
                            f"处理成功 [{self._get_model_display_name(model)}]"
                        )
                    else:
                        self.progress_callback(
                            file_path,
                            "失败",
                            0,
                            result.message
                        )

                except Exception as e:
                    error_msg = str(e)
                    # 记录异常结果
                    result_info = {
                        'url': file_path,
                        'filename': item.filename,
                        'output_path': None,
                        'success': False,
                        'message': error_msg,
                        'model': model,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results.append(result_info)
                    self.progress_callback(file_path, "失败", 0, error_msg)

                # 处理间隔
                if idx < total_items - 1:
                    time.sleep(1)

        finally:
            # 生成JSON报告
            self._generate_report()
            self.finished_callback()

    def _get_model_display_name(self, model: str) -> str:
        """获取模型显示名称"""
        model_names = {
            "gemini-2.5-flash-image": "Nano Banana",
            "gemini-3.1-flash-image-preview": "BananaPro 2",
            "gemini-3-pro-image-preview": "BananaPro Pro",
            "gpt-image-2": "OpenAI GPT Image"
        }
        return model_names.get(model, model)

    def _on_progress(self, file_path: str, message: str, progress: int, current_idx: int, total: int):
        """进度回调"""
        overall_progress = int((current_idx * 100 + progress) / total)
        self.progress_callback(file_path, "处理中", overall_progress, message)

    def stop(self):
        """停止处理"""
        self._stop_event.set()
        self._pause_event.set()  # 如果处于暂停状态，唤醒线程

    def _generate_report(self):
        """生成JSON处理报告"""
        import time
        try:
            total = len(self.results)
            success_count = sum(1 for r in self.results if r['success'])
            failed_count = total - success_count

            # 统计各模型使用情况
            model_stats = {}
            for r in self.results:
                model = r.get('model', 'unknown')
                if model not in model_stats:
                    model_stats[model] = {'total': 0, 'success': 0}
                model_stats[model]['total'] += 1
                if r['success']:
                    model_stats[model]['success'] += 1

            report = {
                'report_info': {
                    'generated_at': datetime.now().isoformat(),
                    'total_images': total,
                    'success_count': success_count,
                    'failed_count': failed_count,
                    'output_dir': str(self.output_dir)
                },
                'model_statistics': model_stats,
                'results': self.results
            }

            # 保存JSON报告 - 添加重试机制处理文件锁定
            report_path = self.output_dir / 'report.json'
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    with open(report_path, 'w', encoding='utf-8') as f:
                        json.dump(report, f, ensure_ascii=False, indent=2)
                    print(f"[报告] 已生成处理报告: {report_path}")
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"[警告] 报告文件被锁定，重试中... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                    else:
                        print(f"[错误] 报告文件被锁定，无法写入: {e}")
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"[警告] 生成报告失败，重试中... ({attempt + 1}/{max_retries}): {e}")
                        time.sleep(1)
                    else:
                        print(f"[错误] 生成报告失败: {e}")
        except Exception as e:
            print(f"[警告] 生成报告时发生错误: {e}")

    def pause(self):
        """暂停处理"""
        self._pause_event.clear()

    def resume(self):
        """恢复处理"""
        self._pause_event.set()

    def is_paused(self) -> bool:
        """是否暂停"""
        return not self._pause_event.is_set()


class LogQueue:
    """日志队列 - 用于线程安全的日志传递"""

    def __init__(self):
        self.queue = Queue()
        self._lock = threading.Lock()

    def put(self, message: str):
        """添加日志"""
        with self._lock:
            self.queue.put(message)

    def get(self) -> str:
        """获取日志"""
        with self._lock:
            if not self.queue.empty():
                return self.queue.get()
            return ""

    def empty(self) -> bool:
        """是否为空"""
        with self._lock:
            return self.queue.empty()

    def clear(self):
        """清空队列"""
        with self._lock:
            while not self.queue.empty():
                self.queue.get()
