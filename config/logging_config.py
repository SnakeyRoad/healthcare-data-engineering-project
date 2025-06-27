"""
Healthcare Data Engineering Project - Logging Configuration
Cross-platform logging setup for Windows and Linux environments
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
import structlog
from typing import Optional

def setup_logging(
    log_level: str = None,
    log_file: str = None,
    enable_structured_logging: bool = True
) -> None:
    """
    Setup comprehensive logging for the healthcare data engineering project
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Custom log file path
        enable_structured_logging: Enable structured logging with structlog
    """
    
    # Get configuration from environment
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Default log file with timestamp
    if log_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = logs_dir / f"healthcare_etl_{timestamp}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
        ]
    )
    
    # Configure structured logging if enabled
    if enable_structured_logging:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")

def create_specialized_loggers():
    """Create specialized loggers for different components"""
    # Note: Specialized loggers are not currently used in the ETL pipeline
    # This function is kept for future extensibility but doesn't create empty log files
    pass

class PerformanceLogger:
    """Context manager for performance logging"""
    
    def __init__(self, operation_name: str, logger_name: str = 'performance'):
        self.operation_name = operation_name
        self.logger = logging.getLogger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"START - {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"COMPLETED - {self.operation_name} - Duration: {duration:.2f}s")
        else:
            self.logger.error(f"FAILED - {self.operation_name} - Duration: {duration:.2f}s - Error: {exc_val}")

class DataQualityLogger:
    """Specialized logger for data quality metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger('data_quality')
    
    def log_missing_values(self, table_name: str, column: str, missing_count: int, total_count: int):
        """Log missing value statistics"""
        percentage = (missing_count / total_count) * 100 if total_count > 0 else 0
        self.logger.info(f"MISSING_VALUES - {table_name}.{column}: {missing_count}/{total_count} ({percentage:.2f}%)")
    
    def log_data_validation(self, table_name: str, validation_rule: str, passed: bool, details: str = ""):
        """Log data validation results"""
        status = "PASS" if passed else "FAIL"
        message = f"VALIDATION - {table_name} - {validation_rule}: {status}"
        if details:
            message += f" - {details}"
        
        if passed:
            self.logger.info(message)
        else:
            self.logger.warning(message)
    
    def log_quality_score(self, table_name: str, score: float, metrics: dict = None):
        """Log overall quality score for a dataset"""
        self.logger.info(f"QUALITY_SCORE - {table_name}: {score:.2f}%")
        if metrics:
            for metric, value in metrics.items():
                self.logger.info(f"QUALITY_METRIC - {table_name}.{metric}: {value}")

class SecurityLogger:
    """Specialized logger for security events"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_database_access(self, user: str, operation: str, table: str, success: bool):
        """Log database access attempts"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"DB_ACCESS - User: {user} - Operation: {operation} - Table: {table} - Status: {status}")
    
    def log_authentication(self, user: str, success: bool, details: str = ""):
        """Log authentication attempts"""
        status = "SUCCESS" if success else "FAILED"
        message = f"AUTH - User: {user} - Status: {status}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def log_data_access(self, user: str, patient_ids: list, purpose: str):
        """Log patient data access for GDPR compliance"""
        patient_count = len(patient_ids) if patient_ids else 0
        self.logger.info(f"DATA_ACCESS - User: {user} - Patients: {patient_count} - Purpose: {purpose}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)

def log_system_info():
    """Log system information for debugging"""
    import platform
    import sys
    
    logger = get_logger('system')
    
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Log environment variables (excluding sensitive ones)
    sensitive_vars = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']
    env_vars = {
        k: v for k, v in os.environ.items() 
        if not any(sensitive in k.upper() for sensitive in sensitive_vars)
    }
    
    for var, value in env_vars.items():
        if var.startswith(('POSTGRES_', 'APP_', 'LOG_')):
            logger.info(f"Environment: {var}={value}")

# Global logger instances
performance_logger = PerformanceLogger
data_quality_logger = DataQualityLogger()
security_logger = SecurityLogger()

# Convenience functions
def log_performance(operation_name: str):
    """Decorator for automatic performance logging"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceLogger(f"{func.__name__} - {operation_name}"):
                return func(*args, **kwargs)
        return wrapper
    return decorator

def log_database_operation(operation: str):
    """Decorator for database operation logging"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger('database')
            try:
                logger.info(f"Starting database operation: {operation}")
                result = func(*args, **kwargs)
                logger.info(f"Database operation completed: {operation}")
                return result
            except Exception as e:
                logger.error(f"Database operation failed: {operation} - Error: {e}")
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # Test logging configuration
    setup_logging()
    
    # Test different loggers
    logger = get_logger(__name__)
    logger.info("Testing main logger")
    
    data_quality_logger.log_quality_score("test_table", 95.5, {"completeness": 0.98, "validity": 0.93})
    security_logger.log_database_access("test_user", "SELECT", "patients", True)
    
    with PerformanceLogger("test_operation"):
        import time
        time.sleep(1)  # Simulate work
    
    log_system_info()
    
    print("Logging test completed. Check logs/ directory for output files.")
