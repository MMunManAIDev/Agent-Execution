"""
Threading Utilities Module

Bevat utilities voor thread management en asynchrone operaties.
"""

import threading
import queue
import logging
import time
import functools
from typing import Callable, Any, Optional, TypeVar, Dict
from concurrent.futures import ThreadPoolExecutor

# Direct importeren van constants
from .constants import (
    ThreadingError,
    THREAD_POOL_SIZE,
    THREAD_TIMEOUT
)

# Type variables voor generics
T = TypeVar('T')
R = TypeVar('R')

logger = logging.getLogger(__name__)

class ThreadSafeCounter:
    """Thread-safe counter voor het bijhouden van asynchrone operaties"""
    
    def __init__(self, initial: int = 0):
        self._value = initial
        self._lock = threading.Lock()
        
    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value
            
    def decrement(self) -> int:
        with self._lock:
            self._value = max(0, self._value - 1)
            return self._value
            
    @property
    def value(self) -> int:
        with self._lock:
            return self._value

# Deze functies moeten buiten de ThreadSafeCounter class staan
def threaded(func: Callable[..., T]) -> Callable[..., threading.Thread]:
    """
    Decorator die een functie in een aparte thread uitvoert.
    
    Args:
        func: De functie om in een thread uit te voeren
        
    Returns:
        Wrapper functie die een Thread object teruggeeft
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(
            target=func,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        return thread
    return wrapper

def run_in_thread(
    func: Callable[..., T],
    *args,
    timeout: Optional[float] = None,
    **kwargs
) -> Optional[T]:
    """
    Voer een functie uit in een aparte thread met timeout.
    
    Args:
        func: Functie om uit te voeren
        *args: Positional arguments voor de functie
        timeout: Maximum wachttijd in seconden
        **kwargs: Keyword arguments voor de functie
    """
    result_queue = queue.Queue()
    
    def worker():
        try:
            result = func(*args, **kwargs)
            result_queue.put(('success', result))
        except Exception as e:
            result_queue.put(('error', e))
    
    thread = threading.Thread(target=worker)
    thread.daemon = True
    thread.start()
    
    try:
        status, result = result_queue.get(timeout=timeout or THREAD_TIMEOUT)
        if status == 'error':
            raise ThreadingError(f"Thread execution failed: {str(result)}")
        return result
    except queue.Empty:
        raise ThreadingError(f"Thread execution timed out after {timeout} seconds")

class ThreadPool:
    """Thread pool voor parallelle taak uitvoering"""
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize thread pool.
        
        Args:
            max_workers: Maximum aantal worker threads
        """
        self.max_workers = max_workers or THREAD_POOL_SIZE
        self._pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self._tasks: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
    def submit(self, task_id: str, func: Callable[..., T], *args, **kwargs) -> None:
        """
        Submit een taak aan de thread pool.
        
        Args:
            task_id: Unieke identifier voor de taak
            func: Functie om uit te voeren
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        with self._lock:
            if task_id in self._tasks:
                raise ThreadingError(f"Task {task_id} already exists")
                
            future = self._pool.submit(func, *args, **kwargs)
            self._tasks[task_id] = future
            
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[T]:
        """
        Krijg het resultaat van een taak.
        
        Args:
            task_id: De taak identifier
            timeout: Maximum wachttijd
            
        Returns:
            Taak resultaat of None bij timeout
            
        Raises:
            ThreadingError: Als de taak niet bestaat of faalt
        """
        with self._lock:
            future = self._tasks.get(task_id)
            if not future:
                raise ThreadingError(f"Task {task_id} not found")
                
        try:
            result = future.result(timeout=timeout or THREAD_TIMEOUT)
            return result
        except Exception as e:
            raise ThreadingError(f"Task {task_id} failed: {str(e)}")
        finally:
            with self._lock:
                self._tasks.pop(task_id, None)
                
    def cancel(self, task_id: str) -> bool:
        """
        Cancel een lopende taak.
        
        Args:
            task_id: De taak identifier
            
        Returns:
            True als de taak gecanceld is
        """
        with self._lock:
            future = self._tasks.get(task_id)
            if future and not future.done():
                cancelled = future.cancel()
                if cancelled:
                    self._tasks.pop(task_id, None)
                return cancelled
        return False
        
    def shutdown(self, wait: bool = True) -> None:
        """
        Sluit de thread pool.
        
        Args:
            wait: Wacht tot alle taken klaar zijn
        """
        self._pool.shutdown(wait=wait)

class AsyncOperation:
    """Class voor het beheren van asynchrone operaties met callbacks"""
    
    def __init__(self, func: Callable[..., T], callback: Optional[Callable[[T], None]] = None):
        """
        Initialize async operation.
        
        Args:
            func: Functie om uit te voeren
            callback: Optional callback voor het resultaat
        """
        self.func = func
        self.callback = callback
        self._thread: Optional[threading.Thread] = None
        self._cancelled = threading.Event()
        self._completed = threading.Event()
        
    def start(self, *args, **kwargs) -> None:
        """Start de asynchrone operatie"""
        if self._thread and self._thread.is_alive():
            raise ThreadingError("Operation already running")
            
        self._cancelled.clear()
        self._completed.clear()
        
        def worker():
            try:
                if not self._cancelled.is_set():
                    result = self.func(*args, **kwargs)
                    if self.callback and not self._cancelled.is_set():
                        self.callback(result)
            except Exception as e:
                logger.error(f"Async operation failed: {str(e)}")
            finally:
                self._completed.set()
        
        self._thread = threading.Thread(target=worker)
        self._thread.daemon = True
        self._thread.start()
        
    def cancel(self) -> None:
        """Cancel de operatie"""
        self._cancelled.set()
        
    def is_cancelled(self) -> bool:
        """Check of de operatie gecanceld is"""
        return self._cancelled.is_set()
        
    def is_completed(self) -> bool:
        """Check of de operatie voltooid is"""
        return self._completed.is_set()
        
    def wait(self, timeout: Optional[float] = None) -> bool:
        """
        Wacht tot de operatie voltooid is.
        
        Args:
            timeout: Maximum wachttijd
            
        Returns:
            True als de operatie voltooid is
        """
        return self._completed.wait(timeout=timeout)

def periodic_task(interval: float) -> Callable[[Callable[..., None]], Callable[..., threading.Thread]]:
    """
    Decorator voor het periodiek uitvoeren van een taak.
    
    Args:
        interval: Tijd tussen uitvoeringen in seconden
        
    Example:
        @periodic_task(5.0)
        def check_status():
            print("Checking status...")
            
        thread = check_status()  # Start periodic execution
        thread.join()            # Wacht op voltooiing
    """
    def decorator(func: Callable[..., None]) -> Callable[..., threading.Thread]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> threading.Thread:
            stop_event = threading.Event()
            
            def periodic_worker():
                while not stop_event.is_set():
                    try:
                        func(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"Periodic task failed: {str(e)}")
                    
                    # Wacht voor het volgende interval of tot stoppen
                    stop_event.wait(interval)
            
            thread = threading.Thread(target=periodic_worker)
            thread.daemon = True
            thread.start()
            
            # Bewaar stop_event voor later gebruik
            thread.stop_event = stop_event
            return thread
            
        return wrapper
    return decorator