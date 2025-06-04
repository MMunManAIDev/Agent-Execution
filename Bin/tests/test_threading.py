"""
Tests voor threading utilities
"""

import pytest
import time
from agent_executive.utils import threaded, run_in_thread, ThreadSafeCounter, ThreadPool
from agent_executive.utils import ThreadingError

def test_threaded_decorator():
    """Test threaded decorator"""
    results = []
    
    @threaded
    def test_func():
        time.sleep(0.1)
        results.append(True)
    
    thread = test_func()
    assert not results  # Should not have result yet
    thread.join()
    assert results == [True]  # Should have result after join

def test_thread_safe_counter():
    """Test thread-safe counter"""
    counter = ThreadSafeCounter()
    assert counter.value == 0
    
    assert counter.increment() == 1
    assert counter.increment() == 2
    assert counter.decrement() == 1
    assert counter.value == 1

def test_run_in_thread():
    """Test run_in_thread functie"""
    def slow_func():
        time.sleep(0.1)
        return "done"
    
    # Test successful execution
    assert run_in_thread(slow_func) == "done"
    
    # Test timeout
    with pytest.raises(ThreadingError):
        run_in_thread(slow_func, timeout=0.01)

def test_thread_pool():
    """Test thread pool"""
    pool = ThreadPool(max_workers=2)
    
    def task(x):
        time.sleep(0.1)
        return x * 2
    
    # Submit tasks
    pool.submit("task1", task, 1)
    pool.submit("task2", task, 2)
    
    # Get results
    assert pool.get_result("task1") == 2
    assert pool.get_result("task2") == 4
    
    # Test non-existent task
    with pytest.raises(ThreadingError):
        pool.get_result("task3")