import os
import logging
from logging.handlers import RotatingFileHandler

# Debug Configuration
DEBUG_CONFIG = {
    'ENABLED': True,
    'LOG_LEVEL': 'DEBUG',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'LOG_FILE': 'app.log',
    'LOG_FORMAT': '%(asctime)s [%(levelname)s] - %(message)s',
    'LOG_TO_CONSOLE': True,
    'LOG_TO_FILE': True,
    
    # Feature specific debug flags
    'DEBUG_FILE_UPLOADS': True,
    'DEBUG_QUERIES': True,
    'DEBUG_SESSION': True,
    'DEBUG_GEMINI': True,
    
    # Performance monitoring
    'TRACK_PERFORMANCE': True,
    'TRACK_MEMORY_USAGE': True,
    
    # Data validation
    'VALIDATE_CSV_DATA': True,
    'MAX_CSV_SIZE': 16 * 1024 * 1024,  # 16MB
    
    # API Debug
    'LOG_API_REQUESTS': True,
    'LOG_API_RESPONSES': True,
    
    # Frontend Debug
    'ENABLE_FRONTEND_CONSOLE': True,
    'LOG_FRONTEND_EVENTS': True,
    
    # Security
    'LOG_SECURITY_EVENTS': True,
    'TRACK_SESSION_ACTIVITY': True,

    # Log rotation
    'LOG_MAX_SIZE': 10 * 1024 * 1024,  # 10MB
    'LOG_BACKUP_COUNT': 5,  # Keep 5 backup files
}

# Environment-specific settings
if os.getenv('FLASK_ENV') == 'development':
    DEBUG_CONFIG.update({
        'LOG_LEVEL': 'DEBUG',
        'LOG_TO_CONSOLE': True,
    })
elif os.getenv('FLASK_ENV') == 'production':
    DEBUG_CONFIG.update({
        'LOG_LEVEL': 'INFO',
        'LOG_TO_CONSOLE': False,
        'ENABLE_FRONTEND_CONSOLE': False,
    })

def setup_logging():
    """Setup logging with rotation"""
    log_formatter = logging.Formatter(DEBUG_CONFIG['LOG_FORMAT'])
    
    # File Handler with rotation
    if DEBUG_CONFIG['LOG_TO_FILE']:
        file_handler = RotatingFileHandler(
            DEBUG_CONFIG['LOG_FILE'],
            maxBytes=DEBUG_CONFIG['LOG_MAX_SIZE'],
            backupCount=DEBUG_CONFIG['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(getattr(logging, DEBUG_CONFIG['LOG_LEVEL']))
    else:
        file_handler = logging.NullHandler()
    
    # Console Handler
    if DEBUG_CONFIG['LOG_TO_CONSOLE']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(getattr(logging, DEBUG_CONFIG['LOG_LEVEL']))
    else:
        console_handler = logging.NullHandler()
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, DEBUG_CONFIG['LOG_LEVEL']))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add new handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_debug_config():
    """Get the current debug configuration"""
    return DEBUG_CONFIG

def set_debug_option(key, value):
    """Update a specific debug configuration option"""
    if key in DEBUG_CONFIG:
        DEBUG_CONFIG[key] = value
        return True
    return False

def is_debug_enabled(feature):
    """Check if debugging is enabled for a specific feature"""
    return DEBUG_CONFIG.get(f'DEBUG_{feature.upper()}', False)

# Performance monitoring utilities
def start_performance_tracking():
    if not DEBUG_CONFIG['TRACK_PERFORMANCE']:
        return None
    import time
    return time.time()

def end_performance_tracking(start_time):
    if not start_time:
        return None
    import time
    return time.time() - start_time