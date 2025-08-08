import time
import functools
import psutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def profile_performance(func):
    """Decorator to profile function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            logger.debug(
                f"Performance Profile - {func.__name__}:\n"
                f"  Execution Time: {execution_time:.2f}s\n"
                f"  Memory Usage: {memory_used:.2f}MB\n"
                f"  Timestamp: {datetime.now().isoformat()}"
            )

    return wrapper

def track_memory():
    """Get current memory usage"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        'rss': memory_info.rss / 1024 / 1024,  # MB
        'vms': memory_info.vms / 1024 / 1024,  # MB
        'percent': process.memory_percent()
    }

def track_cpu():
    """Get current CPU usage"""
    return {
        'process': psutil.Process().cpu_percent(),
        'system': psutil.cpu_percent()
    }

class PerformanceMonitor:
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.checkpoints = []

    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.start_memory = track_memory()
        self.checkpoints = []
        return self

    def checkpoint(self, label):
        """Record a checkpoint"""
        self.checkpoints.append({
            'label': label,
            'time': time.time() - self.start_time,
            'memory': track_memory(),
            'cpu': track_cpu()
        })

    def end(self):
        """End monitoring and get report"""
        if not self.start_time:
            return None

        total_time = time.time() - self.start_time
        end_memory = track_memory()
        memory_diff = end_memory['rss'] - self.start_memory['rss']

        report = {
            'total_time': total_time,
            'memory_change': memory_diff,
            'checkpoints': self.checkpoints,
            'summary': f"Total time: {total_time:.2f}s, Memory change: {memory_diff:.2f}MB"
        }

        # Log the report
        logger.debug(f"Performance Report:\n{report['summary']}")
        for cp in self.checkpoints:
            logger.debug(f"  {cp['label']}: {cp['time']:.2f}s, Memory: {cp['memory']['rss']:.2f}MB")

        return report