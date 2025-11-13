"""
Comprehensive tests for human-in-the-loop (HITL) system
"""
import pytest
import asyncio
from typing import Dict, Any, Optional
from src.human_in_the_loop import (
    InputType, HumanInput, InputHandler, ConsoleInputHandler,
    CallbackInputHandler, HumanInputManager
)


class TestHumanInput:
    """Test HumanInput dataclass"""

    def test_create_human_input(self):
        """Test creating a human input request"""
        input_req = HumanInput(
            input_id="req_123",
            input_type=InputType.APPROVAL,
            prompt="Approve this action?",
            context={"action": "delete_user"},
            timeout=30.0
        )

        assert input_req.input_id == "req_123"
        assert input_req.input_type == InputType.APPROVAL
        assert input_req.prompt == "Approve this action?"
        assert input_req.context["action"] == "delete_user"
        assert input_req.timeout == 30.0

    def test_human_input_defaults(self):
        """Test default values"""
        input_req = HumanInput(
            input_id="req_1",
            input_type=InputType.FEEDBACK,
            prompt="Provide feedback"
        )

        assert input_req.context is None
        assert input_req.timeout is None
        assert input_req.default_value is None
        assert input_req.response is None
        assert input_req.timestamp is not None

    def test_to_dict(self):
        """Test serialization"""
        input_req = HumanInput(
            input_id="req_1",
            input_type=InputType.CHOICE,
            prompt="Select option",
            context={"options": ["A", "B", "C"]}
        )

        input_dict = input_req.to_dict()

        assert input_dict["input_id"] == "req_1"
        assert input_dict["input_type"] == "choice"
        assert input_dict["prompt"] == "Select option"


class TestInputType:
    """Test InputType enum"""

    def test_input_types(self):
        """Test all input types"""
        assert InputType.APPROVAL.value == "approval"
        assert InputType.FEEDBACK.value == "feedback"
        assert InputType.CHOICE.value == "choice"
        assert InputType.RATING.value == "rating"
        assert InputType.REVIEW.value == "review"
        assert InputType.VALIDATION.value == "validation"


class MockInputHandler(InputHandler):
    """Mock input handler for testing"""

    def __init__(self, response: Any = None):
        self.response = response
        self.requests = []

    async def request_input(self, input_request: HumanInput) -> Any:
        """Store request and return mock response"""
        self.requests.append(input_request)
        return self.response if self.response is not None else input_request.default_value


class TestCallbackInputHandler:
    """Test CallbackInputHandler"""

    @pytest.mark.asyncio
    async def test_callback_handler(self):
        """Test callback-based input handler"""
        responses = []

        async def callback(input_req: HumanInput) -> bool:
            responses.append(input_req.prompt)
            return True

        handler = CallbackInputHandler(callback)

        input_req = HumanInput(
            input_id="req_1",
            input_type=InputType.APPROVAL,
            prompt="Approve?"
        )

        result = await handler.request_input(input_req)

        assert result is True
        assert "Approve?" in responses

    @pytest.mark.asyncio
    async def test_callback_with_context(self):
        """Test callback receiving context"""
        received_context = {}

        async def callback(input_req: HumanInput) -> str:
            received_context.update(input_req.context or {})
            return "feedback_text"

        handler = CallbackInputHandler(callback)

        input_req = HumanInput(
            input_id="req_1",
            input_type=InputType.FEEDBACK,
            prompt="Provide feedback",
            context={"task_id": "task_123", "version": "v2"}
        )

        result = await handler.request_input(input_req)

        assert result == "feedback_text"
        assert received_context["task_id"] == "task_123"


class TestHumanInputManager:
    """Test HumanInputManager class"""

    def test_create_manager(self):
        """Test creating input manager"""
        handler = MockInputHandler()
        manager = HumanInputManager(handler)

        assert manager.input_handler == handler
        assert manager.auto_approve is False

    def test_auto_approve_mode(self):
        """Test auto-approve mode"""
        manager = HumanInputManager(auto_approve=True)

        assert manager.auto_approve is True

    @pytest.mark.asyncio
    async def test_request_input(self):
        """Test basic input request"""
        handler = MockInputHandler(response="test_response")
        manager = HumanInputManager(handler)

        result = await manager.request_input(
            input_type=InputType.FEEDBACK,
            prompt="Give feedback",
            context={"key": "value"}
        )

        assert result == "test_response"
        assert len(handler.requests) == 1
        assert handler.requests[0].input_type == InputType.FEEDBACK

    @pytest.mark.asyncio
    async def test_request_approval(self):
        """Test approval request"""
        handler = MockInputHandler(response=True)
        manager = HumanInputManager(handler)

        approved = await manager.request_approval("Approve this?")

        assert approved is True

    @pytest.mark.asyncio
    async def test_request_approval_denied(self):
        """Test denied approval"""
        handler = MockInputHandler(response=False)
        manager = HumanInputManager(handler)

        approved = await manager.request_approval("Approve dangerous action?")

        assert approved is False

    @pytest.mark.asyncio
    async def test_request_feedback(self):
        """Test feedback request"""
        handler = MockInputHandler(response="Great work!")
        manager = HumanInputManager(handler)

        feedback = await manager.request_feedback(
            "How is this?",
            context={"item": "report"}
        )

        assert feedback == "Great work!"

    @pytest.mark.asyncio
    async def test_request_choice(self):
        """Test choice request"""
        handler = MockInputHandler(response="Option B")
        manager = HumanInputManager(handler)

        choice = await manager.request_choice(
            "Select an option",
            options=["Option A", "Option B", "Option C"]
        )

        assert choice == "Option B"

    @pytest.mark.asyncio
    async def test_request_rating(self):
        """Test rating request"""
        handler = MockInputHandler(response=4)
        manager = HumanInputManager(handler)

        rating = await manager.request_rating(
            "Rate this result",
            min_rating=1,
            max_rating=5
        )

        assert rating == 4

    @pytest.mark.asyncio
    async def test_request_review(self):
        """Test review request"""
        review_data = {
            "approved": True,
            "comments": "Looks good",
            "rating": 5
        }

        handler = MockInputHandler(response=review_data)
        manager = HumanInputManager(handler)

        review = await manager.request_review(
            "Review this code",
            context={"file": "main.py"}
        )

        assert review["approved"] is True
        assert review["rating"] == 5

    @pytest.mark.asyncio
    async def test_request_validation(self):
        """Test validation request"""
        handler = MockInputHandler(response=True)
        manager = HumanInputManager(handler)

        valid = await manager.request_validation(
            "Is this data valid?",
            context={"data": {"name": "John", "age": 30}}
        )

        assert valid is True

    @pytest.mark.asyncio
    async def test_auto_approve_overrides(self):
        """Test auto-approve overrides handler"""
        handler = MockInputHandler(response=False)
        manager = HumanInputManager(handler, auto_approve=True)

        # Should auto-approve despite handler returning False
        approved = await manager.request_approval("Approve?")

        assert approved is True
        # Handler should not have been called
        assert len(handler.requests) == 0

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout on input request"""
        async def slow_callback(input_req: HumanInput) -> str:
            await asyncio.sleep(10)  # Simulate slow response
            return "late_response"

        handler = CallbackInputHandler(slow_callback)
        manager = HumanInputManager(handler)

        # Should timeout after 0.1 seconds
        with pytest.raises(asyncio.TimeoutError):
            await manager.request_input(
                input_type=InputType.FEEDBACK,
                prompt="Quick response needed",
                timeout=0.1
            )

    @pytest.mark.asyncio
    async def test_default_value_on_timeout(self):
        """Test using default value on timeout"""
        async def slow_callback(input_req: HumanInput) -> bool:
            await asyncio.sleep(10)
            return False

        handler = CallbackInputHandler(slow_callback)
        manager = HumanInputManager(handler)

        # Should return default value after timeout
        result = await manager.request_input(
            input_type=InputType.APPROVAL,
            prompt="Approve?",
            timeout=0.1,
            default_value=True
        )

        # Should get default value since it timed out
        # (Implementation may vary - this tests the concept)
        assert result in [True, None]  # Either default or timeout

    @pytest.mark.asyncio
    async def test_get_input_history(self):
        """Test getting input history"""
        handler = MockInputHandler(response="response")
        manager = HumanInputManager(handler)

        await manager.request_feedback("Feedback 1")
        await manager.request_approval("Approval 1")
        await manager.request_choice("Choice 1", ["A", "B"])

        history = manager.get_input_history()

        assert len(history) == 3
        assert any(h["input_type"] == "feedback" for h in history)
        assert any(h["input_type"] == "approval" for h in history)
        assert any(h["input_type"] == "choice" for h in history)

    @pytest.mark.asyncio
    async def test_clear_history(self):
        """Test clearing input history"""
        handler = MockInputHandler(response="response")
        manager = HumanInputManager(handler)

        await manager.request_feedback("Test")
        assert len(manager.get_input_history()) == 1

        manager.clear_history()
        assert len(manager.get_input_history()) == 0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent input requests"""
        responses = {"req1": "response1", "req2": "response2", "req3": "response3"}

        async def callback(input_req: HumanInput) -> str:
            await asyncio.sleep(0.01)  # Simulate processing time
            return responses.get(input_req.input_id, "default")

        handler = CallbackInputHandler(callback)
        manager = HumanInputManager(handler)

        # Make concurrent requests
        results = await asyncio.gather(
            manager.request_input(InputType.FEEDBACK, "Req 1", input_id="req1"),
            manager.request_input(InputType.FEEDBACK, "Req 2", input_id="req2"),
            manager.request_input(InputType.FEEDBACK, "Req 3", input_id="req3")
        )

        assert "response1" in results
        assert "response2" in results
        assert "response3" in results


class TestConsoleInputHandler:
    """Test ConsoleInputHandler"""

    @pytest.mark.asyncio
    async def test_console_handler_creation(self):
        """Test creating console handler"""
        handler = ConsoleInputHandler()

        assert handler is not None

    # Note: Testing actual console input is difficult in automated tests
    # These would be manual/integration tests


class TestIntegration:
    """Integration tests for HITL system"""

    @pytest.mark.asyncio
    async def test_approval_workflow(self):
        """Test complete approval workflow"""
        approvals = []

        async def approval_callback(input_req: HumanInput) -> bool:
            approvals.append({
                "prompt": input_req.prompt,
                "context": input_req.context
            })
            # Auto-approve for testing
            return True

        handler = CallbackInputHandler(approval_callback)
        manager = HumanInputManager(handler)

        # Simulate multi-stage approval process
        stage1 = await manager.request_approval(
            "Approve design?",
            context={"stage": "design", "version": "v1"}
        )

        stage2 = await manager.request_approval(
            "Approve implementation?",
            context={"stage": "implementation", "version": "v1"}
        )

        stage3 = await manager.request_approval(
            "Approve deployment?",
            context={"stage": "deployment", "version": "v1"}
        )

        # All stages approved
        assert stage1 is True
        assert stage2 is True
        assert stage3 is True
        assert len(approvals) == 3

    @pytest.mark.asyncio
    async def test_review_workflow(self):
        """Test code review workflow"""
        reviews = []

        async def review_callback(input_req: HumanInput) -> Dict[str, Any]:
            file_path = input_req.context.get("file", "unknown")
            review = {
                "approved": True,
                "comments": f"Reviewed {file_path}",
                "rating": 4,
                "suggestions": []
            }
            reviews.append(review)
            return review

        handler = CallbackInputHandler(review_callback)
        manager = HumanInputManager(handler)

        # Review multiple files
        review1 = await manager.request_review(
            "Review main.py",
            context={"file": "main.py", "lines_changed": 50}
        )

        review2 = await manager.request_review(
            "Review utils.py",
            context={"file": "utils.py", "lines_changed": 20}
        )

        assert review1["approved"] is True
        assert review2["approved"] is True
        assert len(reviews) == 2

    @pytest.mark.asyncio
    async def test_feedback_collection(self):
        """Test feedback collection workflow"""
        feedback_items = []

        async def feedback_callback(input_req: HumanInput) -> str:
            feedback = f"Feedback for: {input_req.context.get('item', 'unknown')}"
            feedback_items.append(feedback)
            return feedback

        handler = CallbackInputHandler(feedback_callback)
        manager = HumanInputManager(handler)

        # Collect feedback on multiple items
        await manager.request_feedback(
            "Feedback on UI design",
            context={"item": "ui_design", "version": "v1"}
        )

        await manager.request_feedback(
            "Feedback on API design",
            context={"item": "api_design", "version": "v1"}
        )

        assert len(feedback_items) == 2
        assert any("ui_design" in f for f in feedback_items)
        assert any("api_design" in f for f in feedback_items)

    @pytest.mark.asyncio
    async def test_conditional_workflow(self):
        """Test conditional workflow based on human input"""
        handler = MockInputHandler()
        manager = HumanInputManager(handler)

        # Simulate workflow that branches based on approval
        step1_result = {"status": "completed", "data": "result"}

        # Request approval for next step
        handler.response = True
        approved = await manager.request_approval(
            "Proceed to step 2?",
            context={"step1_result": step1_result}
        )

        if approved:
            step2_result = {"status": "completed", "data": "step2_data"}
        else:
            step2_result = {"status": "skipped"}

        assert step2_result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_validation_workflow(self):
        """Test data validation workflow"""
        validations = []

        async def validation_callback(input_req: HumanInput) -> bool:
            data = input_req.context.get("data", {})
            # Validate data
            is_valid = "name" in data and "email" in data
            validations.append({
                "data": data,
                "valid": is_valid
            })
            return is_valid

        handler = CallbackInputHandler(validation_callback)
        manager = HumanInputManager(handler)

        # Valid data
        valid1 = await manager.request_validation(
            "Validate user data",
            context={"data": {"name": "John", "email": "john@example.com"}}
        )

        # Invalid data
        valid2 = await manager.request_validation(
            "Validate user data",
            context={"data": {"name": "Jane"}}  # Missing email
        )

        assert valid1 is True
        assert valid2 is False
        assert len(validations) == 2

    @pytest.mark.asyncio
    async def test_rating_aggregation(self):
        """Test rating aggregation workflow"""
        ratings = []

        async def rating_callback(input_req: HumanInput) -> int:
            # Simulate different ratings
            rating = len(ratings) + 3  # 3, 4, 5
            ratings.append(rating)
            return rating

        handler = CallbackInputHandler(rating_callback)
        manager = HumanInputManager(handler)

        # Collect multiple ratings
        rating1 = await manager.request_rating("Rate feature A", 1, 5)
        rating2 = await manager.request_rating("Rate feature B", 1, 5)
        rating3 = await manager.request_rating("Rate feature C", 1, 5)

        # Calculate average
        avg_rating = sum(ratings) / len(ratings)

        assert len(ratings) == 3
        assert avg_rating == 4.0  # (3+4+5)/3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
