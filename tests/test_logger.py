"""
Unit tests for logger module.

Tests logging setup, formatters, and function call decorators.
"""

import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from io import StringIO
from utils.logger import (
    setup_logger,
    log_function_call,
    ColoredFormatter,
    JSONFormatter
)


class TestSetupLogger:
    """Test logger setup functionality."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
    
    def test_setup_logger_custom_level(self):
        """Test logger with custom level."""
        logger = setup_logger("test_debug", level=logging.DEBUG)
        assert logger.level == logging.DEBUG
    
    def test_setup_logger_with_file(self, tmp_path):
        """Test logger with file output."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_file", log_file=str(log_file))
        
        logger.info("Test message")
        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content
    
    def test_setup_logger_multiple_instances(self):
        """Test creating multiple logger instances."""
        logger1 = setup_logger("logger1")
        logger2 = setup_logger("logger2")
        
        assert logger1.name != logger2.name
        assert logger1 is not logger2


class TestColoredFormatter:
    """Test ColoredFormatter class."""
    
    def test_colored_formatter_creation(self):
        """Test ColoredFormatter can be created."""
        formatter = ColoredFormatter()
        assert isinstance(formatter, logging.Formatter)
    
    def test_colored_formatter_format_info(self):
        """Test formatting INFO level message."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test INFO message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        assert "Test INFO message" in formatted
    
    def test_colored_formatter_format_error(self):
        """Test formatting ERROR level message."""
        formatter = ColoredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test ERROR message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        assert "Test ERROR message" in formatted


class TestJSONFormatter:
    """Test JSONFormatter class."""
    
    def test_json_formatter_creation(self):
        """Test JSONFormatter can be created."""
        formatter = JSONFormatter()
        assert isinstance(formatter, logging.Formatter)
    
    def test_json_formatter_format(self):
        """Test formatting message as JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        formatted = formatter.format(record)
        
        # Parse as JSON
        log_data = json.loads(formatted)
        assert log_data["message"] == "Test message"
        assert log_data["level"] == "INFO"
        assert "timestamp" in log_data
    
    def test_json_formatter_with_exception(self):
        """Test formatting message with exception."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()
            
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="test.py",
                lineno=1,
                msg="Error occurred",
                args=(),
                exc_info=exc_info
            )
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert "exception" in log_data
            assert "ValueError" in log_data["exception"]


class TestLogFunctionCallDecorator:
    """Test log_function_call decorator."""
    
    def test_log_function_call_basic(self, caplog):
        """Test basic function call logging."""
        @log_function_call()
        def test_function():
            return "result"
        
        with caplog.at_level(logging.INFO):
            result = test_function()
        
        assert result == "result"
        assert "test_function" in caplog.text
    
    def test_log_function_call_with_args(self, caplog):
        """Test logging function with arguments."""
        @log_function_call()
        def test_function(arg1, arg2):
            return arg1 + arg2
        
        with caplog.at_level(logging.INFO):
            result = test_function(1, 2)
        
        assert result == 3
        assert "test_function" in caplog.text
    
    def test_log_function_call_with_exception(self, caplog):
        """Test logging when function raises exception."""
        @log_function_call()
        def failing_function():
            raise ValueError("Test error")
        
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()
        
        assert "failing_function" in caplog.text
        assert "Test error" in caplog.text
    
    def test_log_function_call_timing(self, caplog):
        """Test that execution time is logged."""
        import time
        
        @log_function_call()
        def slow_function():
            time.sleep(0.1)
            return "done"
        
        with caplog.at_level(logging.INFO):
            result = slow_function()
        
        assert result == "done"
        assert "slow_function" in caplog.text
        # Should log execution time
        assert any("completed" in record.message.lower() or "executed" in record.message.lower() 
                  for record in caplog.records)


class TestIntegration:
    """Integration tests for logging."""
    
    def test_logger_with_multiple_handlers(self, tmp_path):
        """Test logger with console and file handlers."""
        log_file = tmp_path / "integration.log"
        logger = setup_logger("integration_test", log_file=str(log_file))
        
        logger.info("Integration test message")
        logger.error("Integration error message")
        
        # Check file content
        content = log_file.read_text()
        assert "Integration test message" in content
        assert "Integration error message" in content
    
    def test_decorated_function_logging(self, tmp_path, caplog):
        """Test logging decorated function to file."""
        log_file = tmp_path / "decorated.log"
        logger = setup_logger("decorated_test", log_file=str(log_file))
        
        @log_function_call()
        def decorated_function(x, y):
            return x * y
        
        with caplog.at_level(logging.INFO):
            result = decorated_function(3, 4)
        
        assert result == 12
        assert "decorated_function" in caplog.text
    
    def test_logger_hierarchy(self):
        """Test logger hierarchy and inheritance."""
        parent_logger = setup_logger("parent")
        child_logger = setup_logger("parent.child")
        
        assert child_logger.name.startswith(parent_logger.name)
        assert child_logger.parent == parent_logger or child_logger.name.startswith(parent_logger.name + ".")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
