"""
Input Validation

Validates user inputs for security and correctness.
"""

import re
from typing import Tuple, List, Optional


class ValidationError(Exception):
    """Validation error exception"""
    pass


class InputValidator:
    """
    Input validator for security and correctness

    Features:
    - Prompt validation
    - Path validation
    - Command injection prevention
    - Length limits

    Example:
        >>> validator = InputValidator()
        >>> is_valid, error = validator.validate_prompt("Hello world")
        >>> if not is_valid:
        >>>     print(f"Invalid: {error}")
    """

    # Security patterns to block
    DANGEROUS_PATTERNS = [
        r'rm\s+-rf',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__',
        r'subprocess\.',
        r'os\.system',
        r';\s*rm\s+',
        r'\|\s*sh',
        r'&&\s*rm\s+',
    ]

    # Maximum prompt length
    MAX_PROMPT_LENGTH = 50000

    # Maximum task count
    MAX_TASK_COUNT = 50

    def __init__(self):
        """Initialize validator"""
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]

    def validate_prompt(self, prompt: str) -> Tuple[bool, str]:
        """
        Validate user prompt

        Args:
            prompt: Input prompt

        Returns:
            (is_valid, error_message)

        Example:
            >>> is_valid, error = validator.validate_prompt("Hello")
            >>> assert is_valid
        """
        # Check length
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            return False, f"Prompt too long ({len(prompt)} chars, max: {self.MAX_PROMPT_LENGTH})"

        # Check for empty
        if not prompt.strip():
            return False, "Prompt cannot be empty"

        # Check for dangerous patterns
        for pattern in self.patterns:
            if pattern.search(prompt):
                return False, f"Prompt contains dangerous pattern: {pattern.pattern}"

        return True, ""

    def validate_task_count(self, count: int) -> Tuple[bool, str]:
        """
        Validate task count

        Args:
            count: Number of tasks

        Returns:
            (is_valid, error_message)
        """
        if count < 1:
            return False, "Task count must be at least 1"

        if count > self.MAX_TASK_COUNT:
            return False, f"Too many tasks ({count}, max: {self.MAX_TASK_COUNT})"

        return True, ""

    def validate_workspace_path(self, path: str) -> Tuple[bool, str]:
        """
        Validate workspace path

        Args:
            path: Workspace path

        Returns:
            (is_valid, error_message)
        """
        # Check for path traversal
        if '..' in path:
            return False, "Path cannot contain '..'"

        # Check for absolute paths to sensitive locations
        sensitive_paths = ['/etc', '/sys', '/proc', '/dev', '/root']
        for sensitive in sensitive_paths:
            if path.startswith(sensitive):
                return False, f"Cannot use sensitive path: {sensitive}"

        # Check length
        if len(path) > 500:
            return False, f"Path too long ({len(path)} chars, max: 500)"

        return True, ""

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Sanitize prompt by removing/escaping dangerous content

        Args:
            prompt: Input prompt

        Returns:
            Sanitized prompt
        """
        # Truncate to max length
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            prompt = prompt[:self.MAX_PROMPT_LENGTH]

        # Remove null bytes
        prompt = prompt.replace('\x00', '')

        # Normalize whitespace
        prompt = ' '.join(prompt.split())

        return prompt

    def validate_all(
        self,
        prompt: Optional[str] = None,
        task_count: Optional[int] = None,
        workspace_path: Optional[str] = None
    ) -> List[str]:
        """
        Validate multiple inputs at once

        Args:
            prompt: Prompt to validate
            task_count: Task count to validate
            workspace_path: Workspace path to validate

        Returns:
            List of error messages (empty if all valid)

        Example:
            >>> errors = validator.validate_all(
            >>>     prompt="Hello",
            >>>     task_count=5,
            >>>     workspace_path="/tmp/workspace"
            >>> )
            >>> if errors:
            >>>     print(f"Errors: {errors}")
        """
        errors = []

        if prompt is not None:
            is_valid, error = self.validate_prompt(prompt)
            if not is_valid:
                errors.append(f"Prompt: {error}")

        if task_count is not None:
            is_valid, error = self.validate_task_count(task_count)
            if not is_valid:
                errors.append(f"Task count: {error}")

        if workspace_path is not None:
            is_valid, error = self.validate_workspace_path(workspace_path)
            if not is_valid:
                errors.append(f"Workspace path: {error}")

        return errors


# Global validator instance
_global_validator: Optional[InputValidator] = None


def get_validator() -> InputValidator:
    """Get global InputValidator instance"""
    global _global_validator
    if _global_validator is None:
        _global_validator = InputValidator()
    return _global_validator


# Convenience functions
def validate_prompt(prompt: str) -> Tuple[bool, str]:
    """Validate prompt using global validator"""
    return get_validator().validate_prompt(prompt)


def sanitize_prompt(prompt: str) -> str:
    """Sanitize prompt using global validator"""
    return get_validator().sanitize_prompt(prompt)


# Example usage
if __name__ == "__main__":
    validator = InputValidator()

    # Test valid prompt
    is_valid, error = validator.validate_prompt("Hello, world!")
    assert is_valid, error

    # Test dangerous prompt
    is_valid, error = validator.validate_prompt("Run: rm -rf /")
    assert not is_valid
    print(f"Blocked dangerous prompt: {error}")

    # Test sanitization
    dangerous = "Hello ; rm -rf / && echo done"
    sanitized = validator.sanitize_prompt(dangerous)
    print(f"Sanitized: {sanitized}")

    # Test workspace path
    is_valid, error = validator.validate_workspace_path("../../../etc/passwd")
    assert not is_valid
    print(f"Blocked path traversal: {error}")
