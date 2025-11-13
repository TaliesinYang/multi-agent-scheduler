"""
Human-in-the-Loop (HITL) System

Enables human oversight, approval workflows, and feedback collection
in automated multi-agent workflows.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime


class InputType(Enum):
    """Type of human input required"""
    APPROVAL = "approval"              # Binary approve/reject
    FEEDBACK = "feedback"              # Text feedback
    CHOICE = "choice"                  # Select from options
    RATING = "rating"                  # Numeric rating
    REVIEW = "review"                  # Detailed review with comments
    VALIDATION = "validation"          # Validate output correctness


class InputStatus(Enum):
    """Status of human input request"""
    PENDING = "pending"
    SUBMITTED = "submitted"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class HumanInput:
    """
    Human input request

    Stores information about requested human input and the response.
    """
    input_id: str
    input_type: InputType
    prompt: str

    # Request details
    context: Dict[str, Any] = field(default_factory=dict)
    options: Optional[List[str]] = None
    default_value: Optional[Any] = None
    timeout: Optional[float] = None

    # Response
    response: Optional[Any] = None
    status: InputStatus = InputStatus.PENDING
    submitted_at: Optional[float] = None

    # Metadata
    requested_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'input_id': self.input_id,
            'input_type': self.input_type.value,
            'prompt': self.prompt,
            'context': self.context,
            'options': self.options,
            'default_value': self.default_value,
            'timeout': self.timeout,
            'response': self.response,
            'status': self.status.value,
            'submitted_at': self.submitted_at,
            'requested_at': self.requested_at,
            'metadata': self.metadata
        }


class InputHandler(ABC):
    """Abstract input handler for different input methods"""

    @abstractmethod
    async def request_input(self, input_request: HumanInput) -> Any:
        """
        Request input from human

        Args:
            input_request: Input request details

        Returns:
            Human response
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this handler is available"""
        pass


class ConsoleInputHandler(InputHandler):
    """Console-based input handler using stdin"""

    def __init__(self):
        self.executor = None

    def is_available(self) -> bool:
        """Console is always available"""
        return True

    async def request_input(self, input_request: HumanInput) -> Any:
        """Request input from console"""
        print("\n" + "=" * 60)
        print("🙋 HUMAN INPUT REQUIRED")
        print("=" * 60)
        print(f"Type: {input_request.input_type.value}")
        print(f"Prompt: {input_request.prompt}")

        if input_request.context:
            print(f"\nContext:")
            for key, value in input_request.context.items():
                print(f"  {key}: {value}")

        if input_request.options:
            print(f"\nOptions:")
            for i, option in enumerate(input_request.options, 1):
                print(f"  {i}. {option}")

        if input_request.timeout:
            print(f"\nTimeout: {input_request.timeout}s")

        print("=" * 60)

        # Get input based on type
        if input_request.input_type == InputType.APPROVAL:
            response = await self._get_approval()
        elif input_request.input_type == InputType.CHOICE:
            response = await self._get_choice(input_request.options)
        elif input_request.input_type == InputType.RATING:
            response = await self._get_rating()
        elif input_request.input_type == InputType.FEEDBACK:
            response = await self._get_feedback()
        elif input_request.input_type == InputType.REVIEW:
            response = await self._get_review()
        elif input_request.input_type == InputType.VALIDATION:
            response = await self._get_validation()
        else:
            response = await self._get_text()

        return response

    async def _get_approval(self) -> bool:
        """Get approval (yes/no)"""
        loop = asyncio.get_event_loop()
        while True:
            response = await loop.run_in_executor(
                None,
                input,
                "Approve? (yes/no): "
            )
            response = response.lower().strip()
            if response in ['yes', 'y', 'approve', 'approved']:
                return True
            elif response in ['no', 'n', 'reject', 'rejected']:
                return False
            else:
                print("Invalid response. Please enter 'yes' or 'no'.")

    async def _get_choice(self, options: Optional[List[str]]) -> str:
        """Get choice from options"""
        if not options:
            return await self._get_text()

        loop = asyncio.get_event_loop()
        while True:
            response = await loop.run_in_executor(
                None,
                input,
                f"Select option (1-{len(options)}): "
            )
            try:
                index = int(response) - 1
                if 0 <= index < len(options):
                    return options[index]
                else:
                    print(f"Invalid choice. Please enter 1-{len(options)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    async def _get_rating(self) -> int:
        """Get numeric rating (1-5)"""
        loop = asyncio.get_event_loop()
        while True:
            response = await loop.run_in_executor(
                None,
                input,
                "Rating (1-5): "
            )
            try:
                rating = int(response)
                if 1 <= rating <= 5:
                    return rating
                else:
                    print("Invalid rating. Please enter 1-5.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    async def _get_feedback(self) -> str:
        """Get text feedback"""
        return await self._get_text("Feedback: ")

    async def _get_review(self) -> Dict[str, Any]:
        """Get detailed review"""
        print("\nDetailed Review:")
        approved = await self._get_approval()
        rating = await self._get_rating()
        comments = await self._get_text("Comments: ")

        return {
            'approved': approved,
            'rating': rating,
            'comments': comments
        }

    async def _get_validation(self) -> Dict[str, Any]:
        """Get validation response"""
        print("\nValidation:")
        valid = await self._get_approval()
        if not valid:
            issues = await self._get_text("Issues found: ")
            return {'valid': False, 'issues': issues}
        return {'valid': True}

    async def _get_text(self, prompt: str = "Response: ") -> str:
        """Get text input"""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, input, prompt)
        return response.strip()


class CallbackInputHandler(InputHandler):
    """
    Callback-based input handler for programmatic input

    Useful for testing, web interfaces, or custom integrations.
    """

    def __init__(self, callback: Optional[Callable] = None):
        """
        Initialize with callback function

        Args:
            callback: Async function(HumanInput) -> response
        """
        self.callback = callback
        self._pending_inputs: Dict[str, HumanInput] = {}

    def is_available(self) -> bool:
        """Available if callback is set or inputs are pending"""
        return self.callback is not None or len(self._pending_inputs) > 0

    async def request_input(self, input_request: HumanInput) -> Any:
        """Request input via callback or queue"""
        if self.callback:
            # Use callback
            return await self.callback(input_request)
        else:
            # Queue for later retrieval
            self._pending_inputs[input_request.input_id] = input_request

            # Wait for response
            timeout = input_request.timeout or 300.0  # 5 min default
            start_time = time.time()

            while time.time() - start_time < timeout:
                if input_request.status == InputStatus.SUBMITTED:
                    return input_request.response
                await asyncio.sleep(0.5)

            # Timeout
            input_request.status = InputStatus.TIMEOUT
            return input_request.default_value

    def submit_response(self, input_id: str, response: Any) -> bool:
        """
        Submit response for pending input

        Args:
            input_id: Input request ID
            response: Response value

        Returns:
            True if submitted successfully
        """
        if input_id in self._pending_inputs:
            input_request = self._pending_inputs[input_id]
            input_request.response = response
            input_request.status = InputStatus.SUBMITTED
            input_request.submitted_at = time.time()
            return True
        return False

    def get_pending_inputs(self) -> List[HumanInput]:
        """Get all pending input requests"""
        return [
            inp for inp in self._pending_inputs.values()
            if inp.status == InputStatus.PENDING
        ]


class HumanInputManager:
    """
    Human-in-the-loop manager

    Manages human input requests, handlers, and workflow integration.
    """

    def __init__(
        self,
        handlers: Optional[List[InputHandler]] = None,
        default_timeout: float = 300.0,  # 5 minutes
        auto_approve: bool = False
    ):
        """
        Initialize HITL manager

        Args:
            handlers: List of input handlers (defaults to console)
            default_timeout: Default timeout for input requests
            auto_approve: Auto-approve all requests (for testing)
        """
        self.handlers = handlers or [ConsoleInputHandler()]
        self.default_timeout = default_timeout
        self.auto_approve = auto_approve

        self.input_history: List[HumanInput] = []

    async def request_input(
        self,
        input_type: InputType,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[List[str]] = None,
        default_value: Optional[Any] = None,
        timeout: Optional[float] = None,
        required: bool = True
    ) -> Any:
        """
        Request human input

        Args:
            input_type: Type of input
            prompt: Prompt text
            context: Additional context
            options: Options for choice input
            default_value: Default value if timeout/skip
            timeout: Request timeout
            required: If False, can skip on timeout

        Returns:
            Human response

        Example:
            >>> manager = HumanInputManager()
            >>> approved = await manager.request_input(
            ...     InputType.APPROVAL,
            ...     "Approve deployment to production?",
            ...     context={'environment': 'prod', 'version': '1.2.3'}
            ... )
        """
        # Auto-approve mode
        if self.auto_approve:
            if input_type == InputType.APPROVAL:
                return True
            elif input_type == InputType.RATING:
                return 5
            elif input_type == InputType.VALIDATION:
                return {'valid': True}
            elif input_type == InputType.REVIEW:
                return {'approved': True, 'rating': 5, 'comments': 'Auto-approved'}
            elif default_value is not None:
                return default_value
            elif options:
                return options[0]
            else:
                return "Auto-response"

        # Create input request
        import uuid
        input_request = HumanInput(
            input_id=f"input_{uuid.uuid4().hex[:8]}",
            input_type=input_type,
            prompt=prompt,
            context=context or {},
            options=options,
            default_value=default_value,
            timeout=timeout or self.default_timeout
        )

        # Try handlers in order
        response = None
        for handler in self.handlers:
            if handler.is_available():
                try:
                    # Request with timeout
                    response = await asyncio.wait_for(
                        handler.request_input(input_request),
                        timeout=input_request.timeout
                    )

                    input_request.response = response
                    input_request.status = InputStatus.SUBMITTED
                    input_request.submitted_at = time.time()
                    break

                except asyncio.TimeoutError:
                    print(f"⏱️  Input request timed out after {input_request.timeout}s")
                    input_request.status = InputStatus.TIMEOUT

                    if not required and default_value is not None:
                        response = default_value
                        input_request.response = response
                        break
                    elif required:
                        raise TimeoutError(f"Required input timed out: {prompt}")

                except Exception as e:
                    print(f"❌ Input handler error: {e}")
                    continue

        # Record in history
        self.input_history.append(input_request)

        return response

    async def request_approval(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Request approval (convenience method)

        Returns:
            True if approved, False if rejected
        """
        return await self.request_input(
            InputType.APPROVAL,
            prompt,
            context=context,
            timeout=timeout,
            default_value=False
        )

    async def request_feedback(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Request text feedback (convenience method)"""
        return await self.request_input(
            InputType.FEEDBACK,
            prompt,
            context=context,
            timeout=timeout,
            default_value=""
        )

    async def request_choice(
        self,
        prompt: str,
        options: List[str],
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> str:
        """Request choice selection (convenience method)"""
        return await self.request_input(
            InputType.CHOICE,
            prompt,
            options=options,
            context=context,
            timeout=timeout,
            default_value=options[0] if options else None
        )

    async def request_rating(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> int:
        """Request numeric rating (convenience method)"""
        return await self.request_input(
            InputType.RATING,
            prompt,
            context=context,
            timeout=timeout,
            default_value=3
        )

    async def request_review(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Request detailed review (convenience method)"""
        return await self.request_input(
            InputType.REVIEW,
            prompt,
            context=context,
            timeout=timeout,
            default_value={'approved': False, 'rating': 3, 'comments': ''}
        )

    def get_input_history(
        self,
        input_type: Optional[InputType] = None,
        status: Optional[InputStatus] = None
    ) -> List[HumanInput]:
        """
        Get input history with filters

        Args:
            input_type: Filter by input type
            status: Filter by status

        Returns:
            List of matching input requests
        """
        results = self.input_history

        if input_type:
            results = [inp for inp in results if inp.input_type == input_type]

        if status:
            results = [inp for inp in results if inp.status == status]

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about input requests"""
        total = len(self.input_history)

        if total == 0:
            return {'total': 0}

        by_type = {}
        by_status = {}
        response_times = []

        for inp in self.input_history:
            # Count by type
            type_key = inp.input_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by status
            status_key = inp.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            # Response time
            if inp.submitted_at:
                response_time = inp.submitted_at - inp.requested_at
                response_times.append(response_time)

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            'total': total,
            'by_type': by_type,
            'by_status': by_status,
            'avg_response_time': avg_response_time,
            'approval_rate': self._calculate_approval_rate()
        }

    def _calculate_approval_rate(self) -> Optional[float]:
        """Calculate approval rate for approval requests"""
        approvals = [
            inp for inp in self.input_history
            if inp.input_type == InputType.APPROVAL
            and inp.status == InputStatus.SUBMITTED
        ]

        if not approvals:
            return None

        approved_count = sum(1 for inp in approvals if inp.response is True)
        return approved_count / len(approvals)
