"""
Unit tests for error_handler module.

Tests custom exceptions, retry decorators, and error handling utilities.
"""

import pytest
import time
from unittest.mock import Mock, patch
from utils.error_handler import (
    SSVBookGeneratorError,
    ValidationError,
    APIError,
    FileProcessingError,
    retry_on_error,
    handle_api_errors,
    safe_execute
)


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_base_exception(self):
        """Test base SSVBookGeneratorError."""
        error = SSVBookGeneratorError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_validation_error(self):
        """Test ValidationError exception."""
        error = ValidationError("Invalid data")
        assert str(error) == "Invalid data"
        assert isinstance(error, SSVBookGeneratorError)
    
    def test_api_error(self):
        """Test APIError exception."""
        error = APIError("API failed")
        assert str(error) == "API failed"
        assert isinstance(error, SSVBookGeneratorError)
    
    def test_file_processing_error(self):
        """Test FileProcessingError exception."""
        error = FileProcessingError("File not found")
        assert str(error) == "File not found"
        assert isinstance(error, SSVBookGeneratorError)


class TestRetryDecorator:
    """Test retry_on_error decorator."""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt."""
        @retry_on_error(max_attempts=3)
        def successful_function():
            return "success"
        
        result = successful_function()
        assert result == "success"
    
    def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        call_count = {'count': 0}
        
        @retry_on_error(max_attempts=3, delay=0.1)
        def flaky_function():
            call_count['count'] += 1
            if call_count['count'] < 3:
                raise APIError("Temporary failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert call_count['count'] == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test that exception is raised after max attempts."""
        @retry_on_error(max_attempts=3, delay=0.1)
        def always_fails():
            raise APIError("Permanent failure")
        
        with pytest.raises(APIError, match="Permanent failure"):
            always_fails()
    
    def test_retry_with_different_exceptions(self):
        """Test retry only retries specified exceptions."""
        call_count = {'count': 0}
        
        @retry_on_error(max_attempts=3, delay=0.1, exceptions=(APIError,))
        def mixed_errors():
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise APIError("API error")
            elif call_count['count'] == 2:
                raise ValidationError("Validation error")  # Should not retry
            return "success"
        
        with pytest.raises(ValidationError):
            mixed_errors()
        assert call_count['count'] == 2


class TestHandleAPIErrorsDecorator:
    """Test handle_api_errors decorator."""
    
    def test_handle_api_errors_success(self):
        """Test successful execution with decorator."""
        @handle_api_errors
        def successful_api_call():
            return {"data": "success"}
        
        result = successful_api_call()
        assert result == {"data": "success"}
    
    def test_handle_api_errors_catches_exception(self):
        """Test that decorator catches and wraps exceptions."""
        @handle_api_errors
        def failing_api_call():
            raise ValueError("Something went wrong")
        
        with pytest.raises(APIError):
            failing_api_call()
    
    def test_handle_api_errors_preserves_api_error(self):
        """Test that APIError is not double-wrapped."""
        @handle_api_errors
        def api_error_function():
            raise APIError("Original API error")
        
        with pytest.raises(APIError, match="Original API error"):
            api_error_function()


class TestSafeExecute:
    """Test safe_execute context manager."""
    
    def test_safe_execute_success(self):
        """Test successful execution in context manager."""
        with safe_execute("test operation"):
            result = "success"
        assert result == "success"
    
    def test_safe_execute_handles_exception(self):
        """Test exception handling in context manager."""
        with pytest.raises(FileProcessingError):
            with safe_execute("file operation", FileProcessingError):
                raise ValueError("File error")
    
    def test_safe_execute_custom_error_class(self):
        """Test context manager with custom error class."""
        with pytest.raises(ValidationError):
            with safe_execute("validation", ValidationError):
                raise Exception("Validation failed")
    
    def test_safe_execute_message_in_error(self):
        """Test that operation message is included in error."""
        with pytest.raises(FileProcessingError, match="reading file"):
            with safe_execute("reading file", FileProcessingError):
                raise IOError("File not found")


class TestIntegration:
    """Integration tests for error handling."""
    
    def test_combined_decorators(self):
        """Test using multiple decorators together."""
        call_count = {'count': 0}
        
        @handle_api_errors
        @retry_on_error(max_attempts=3, delay=0.1)
        def combined_function():
            call_count['count'] += 1
            if call_count['count'] < 2:
                raise APIError("Temporary error")
            return "success"
        
        result = combined_function()
        assert result == "success"
        assert call_count['count'] == 2
    
    def test_nested_error_handling(self):
        """Test nested error handling scenarios."""
        @handle_api_errors
        def outer_function():
            @retry_on_error(max_attempts=2, delay=0.1)
            def inner_function():
                raise ValidationError("Inner error")
            
            return inner_function()
        
        with pytest.raises(APIError):
            outer_function()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
