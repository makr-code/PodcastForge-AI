#!/usr/bin/env python3
"""
Threading und Queue System für PodcastForge GUI
Best-Practice Implementation mit Observer Pattern
"""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from queue import Queue, Empty
from typing import Callable, Optional, Any, Dict
from enum import Enum
import threading
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Task-Prioritäten"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Task-Status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskResult:
    """Ergebnis eines Tasks"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[Exception] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ITaskObserver(ABC):
    """Observer Interface für Task-Events"""
    
    @abstractmethod
    def on_task_started(self, task_id: str, metadata: Dict):
        """Called when task starts"""
        pass
    
    @abstractmethod
    def on_task_progress(self, task_id: str, progress: float, message: str):
        """Called during task execution"""
        pass
    
    @abstractmethod
    def on_task_completed(self, task_id: str, result: Any):
        """Called when task completes successfully"""
        pass
    
    @abstractmethod
    def on_task_failed(self, task_id: str, error: Exception):
        """Called when task fails"""
        pass


class ThreadManager:
    """
    Thread-Pool Manager mit Queue-basiertem Event-System
    
    Features:
    - ThreadPoolExecutor für Worker-Threads
    - Priority Queue für Tasks
    - Observer Pattern für Events
    - Automatisches Cleanup
    
    Best Practices:
    - Max 4 Worker-Threads (CPU-bound)
    - Thread-safe Queue-Operations
    - Graceful Shutdown
    """
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PodcastForge")
        self.task_queue: Queue[tuple[TaskPriority, Callable]] = Queue()
        self.result_queue: Queue[TaskResult] = Queue()
        self.observers: list[ITaskObserver] = []
        self.active_tasks: Dict[str, Future] = {}
        self._shutdown = False
        self._lock = threading.Lock()
        
        logger.info(f"ThreadManager initialized with {max_workers} workers")
    
    def add_observer(self, observer: ITaskObserver):
        """Registriere Observer für Task-Events"""
        with self._lock:
            if observer not in self.observers:
                self.observers.append(observer)
                logger.debug(f"Observer registered: {observer.__class__.__name__}")
    
    def remove_observer(self, observer: ITaskObserver):
        """Entferne Observer"""
        with self._lock:
            if observer in self.observers:
                self.observers.remove(observer)
                logger.debug(f"Observer removed: {observer.__class__.__name__}")
    
    def _notify_started(self, task_id: str, metadata: Dict):
        """Benachrichtige Observer über Task-Start"""
        with self._lock:
            for observer in self.observers:
                try:
                    observer.on_task_started(task_id, metadata)
                except Exception as e:
                    logger.error(f"Observer error in on_task_started: {e}")
    
    def _notify_progress(self, task_id: str, progress: float, message: str):
        """Benachrichtige Observer über Fortschritt"""
        with self._lock:
            for observer in self.observers:
                try:
                    observer.on_task_progress(task_id, progress, message)
                except Exception as e:
                    logger.error(f"Observer error in on_task_progress: {e}")
    
    def _notify_completed(self, task_id: str, result: Any):
        """Benachrichtige Observer über Erfolg"""
        with self._lock:
            for observer in self.observers:
                try:
                    observer.on_task_completed(task_id, result)
                except Exception as e:
                    logger.error(f"Observer error in on_task_completed: {e}")
    
    def _notify_failed(self, task_id: str, error: Exception):
        """Benachrichtige Observer über Fehler"""
        with self._lock:
            for observer in self.observers:
                try:
                    observer.on_task_failed(task_id, error)
                except Exception as e:
                    logger.error(f"Observer error in on_task_failed: {e}")
    
    def submit_task(self, 
                    task_fn: Callable,
                    task_id: str,
                    priority: TaskPriority = TaskPriority.NORMAL,
                    metadata: Optional[Dict] = None,
                    callback: Optional[Callable[[TaskResult], None]] = None) -> str:
        """
        Submit Task für Ausführung
        
        Args:
            task_fn: Task-Funktion (muss task_id, progress_callback akzeptieren)
            task_id: Eindeutige Task-ID
            priority: Task-Priorität
            metadata: Zusätzliche Metadaten
            callback: Optional callback für Ergebnis
            
        Returns:
            Task-ID
        """
        if self._shutdown:
            raise RuntimeError("ThreadManager is shutting down")
        
        metadata = metadata or {}
        
        def wrapped_task():
            """Wrapper für Task mit Error-Handling und Notifications"""
            try:
                # Start notification
                self._notify_started(task_id, metadata)
                
                # Progress callback
                def progress_callback(progress: float, message: str):
                    self._notify_progress(task_id, progress, message)
                
                # Execute task
                result = task_fn(task_id=task_id, progress_callback=progress_callback)
                
                # Success
                task_result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    result=result,
                    metadata=metadata
                )
                self._notify_completed(task_id, result)
                
            except Exception as e:
                logger.error(f"Task {task_id} failed: {e}", exc_info=True)
                task_result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=e,
                    metadata=metadata
                )
                self._notify_failed(task_id, e)
            
            # Put result in queue
            self.result_queue.put(task_result)
            
            # Callback
            if callback:
                try:
                    callback(task_result)
                except Exception as e:
                    logger.error(f"Callback error for task {task_id}: {e}")
            
            # Cleanup
            with self._lock:
                self.active_tasks.pop(task_id, None)
        
        # Submit to executor
        future = self.executor.submit(wrapped_task)
        
        with self._lock:
            self.active_tasks[task_id] = future
        
        logger.info(f"Task submitted: {task_id} (priority={priority.name})")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Versuche Task zu canceln
        
        Returns:
            True wenn erfolgreich gecancelt
        """
        with self._lock:
            future = self.active_tasks.get(task_id)
            if future:
                cancelled = future.cancel()
                if cancelled:
                    self.active_tasks.pop(task_id)
                    logger.info(f"Task cancelled: {task_id}")
                return cancelled
        return False
    
    def get_result(self, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """
        Hole nächstes Ergebnis aus Queue (non-blocking)
        
        Args:
            timeout: Timeout in Sekunden (None = non-blocking)
            
        Returns:
            TaskResult oder None
        """
        try:
            return self.result_queue.get(block=timeout is not None, timeout=timeout)
        except Empty:
            return None
    
    def get_active_tasks(self) -> list[str]:
        """Hole Liste aktiver Task-IDs"""
        with self._lock:
            return list(self.active_tasks.keys())
    
    def shutdown(self, wait: bool = True):
        """
        Fahre Thread-Pool herunter
        
        Args:
            wait: Warte auf laufende Tasks
        """
        self._shutdown = True
        logger.info("ThreadManager shutting down...")
        
        # Cancel pending tasks
        with self._lock:
            for task_id, future in list(self.active_tasks.items()):
                future.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=wait)
        logger.info("ThreadManager shutdown complete")


class UITaskObserver(ITaskObserver):
    """
    Observer für UI-Updates (tkinter-safe)
    
    Verwendet after() für Thread-safe UI-Updates
    """
    
    def __init__(self, root_widget):
        """
        Args:
            root_widget: tkinter Root-Widget (muss after() haben)
        """
        self.root = root_widget
        self._callbacks = {
            'started': [],
            'progress': [],
            'completed': [],
            'failed': []
        }
    
    def on_started(self, callback: Callable[[str, Dict], None]):
        """Registriere Callback für Task-Start"""
        self._callbacks['started'].append(callback)
    
    def on_progress(self, callback: Callable[[str, float, str], None]):
        """Registriere Callback für Progress"""
        self._callbacks['progress'].append(callback)
    
    def on_completed(self, callback: Callable[[str, Any], None]):
        """Registriere Callback für Completion"""
        self._callbacks['completed'].append(callback)
    
    def on_failed(self, callback: Callable[[str, Exception], None]):
        """Registriere Callback für Fehler"""
        self._callbacks['failed'].append(callback)
    
    def on_task_started(self, task_id: str, metadata: Dict):
        """Thread-safe UI-Update"""
        def update():
            for callback in self._callbacks['started']:
                try:
                    callback(task_id, metadata)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        self.root.after(0, update)
    
    def on_task_progress(self, task_id: str, progress: float, message: str):
        """Thread-safe UI-Update"""
        def update():
            for callback in self._callbacks['progress']:
                try:
                    callback(task_id, progress, message)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        self.root.after(0, update)
    
    def on_task_completed(self, task_id: str, result: Any):
        """Thread-safe UI-Update"""
        def update():
            for callback in self._callbacks['completed']:
                try:
                    callback(task_id, result)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        self.root.after(0, update)
    
    def on_task_failed(self, task_id: str, error: Exception):
        """Thread-safe UI-Update"""
        def update():
            for callback in self._callbacks['failed']:
                try:
                    callback(task_id, error)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        self.root.after(0, update)


# Singleton ThreadManager für Anwendung
_thread_manager: Optional[ThreadManager] = None


def get_thread_manager(max_workers: int = 4) -> ThreadManager:
    """
    Hole Singleton ThreadManager
    
    Args:
        max_workers: Anzahl Worker-Threads
        
    Returns:
        ThreadManager instance
    """
    global _thread_manager
    if _thread_manager is None:
        _thread_manager = ThreadManager(max_workers=max_workers)
    return _thread_manager


def shutdown_thread_manager():
    """Fahre globalen ThreadManager herunter"""
    global _thread_manager
    if _thread_manager:
        _thread_manager.shutdown()
        _thread_manager = None
