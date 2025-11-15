"""
Example 2: Human-in-the-Loop
==============================

This example demonstrates how to use the Human-in-the-Loop system for
workflow approval and feedback.
"""

import asyncio
from src.human_in_the_loop import (
    HumanInputManager,
    InputType,
    CallbackInputHandler
)


async def main():
    """Run human-in-the-loop example"""

    print("=" * 60)
    print("Example 2: Human-in-the-Loop Workflow")
    print("=" * 60)

    # Step 1: Create a custom input handler
    print("\n📦 Step 1: Creating input handler...")

    async def approval_callback(input_request):
        """Custom approval callback"""
        print(f"\n⏸️  APPROVAL REQUIRED")
        print(f"  Prompt: {input_request.prompt}")
        print(f"  Context: {input_request.context}")

        # In a real application, this would wait for user input
        # For this example, we'll automatically approve
        await asyncio.sleep(0.1)
        return True  # Approve

    handler = CallbackInputHandler(approval_callback)
    manager = HumanInputManager(handler)
    print("✓ Input handler created")

    # Step 2: Request approval
    print("\n📦 Step 2: Requesting approval...")
    approved = await manager.request_approval(
        prompt="Approve deployment to production?",
        context={
            'environment': 'production',
            'changes': 5,
            'tests_passed': True
        }
    )

    print(f"\n✅ Approval result: {approved}")

    # Step 3: Request feedback
    print("\n📦 Step 3: Requesting feedback...")

    async def feedback_callback(input_request):
        """Custom feedback callback"""
        print(f"\n💬 FEEDBACK REQUESTED")
        print(f"  Prompt: {input_request.prompt}")
        return "Looks good! Please proceed."

    feedback_handler = CallbackInputHandler(feedback_callback)
    manager_feedback = HumanInputManager(feedback_handler)

    feedback = await manager_feedback.request_feedback(
        prompt="Please review the implementation",
        context={'code_changes': 10, 'files_modified': 3}
    )

    print(f"  Feedback received: {feedback}")

    # Step 4: Request rating
    print("\n📦 Step 4: Requesting rating...")

    async def rating_callback(input_request):
        """Custom rating callback"""
        print(f"\n⭐ RATING REQUESTED")
        print(f"  Prompt: {input_request.prompt}")
        return 5  # 5-star rating

    rating_handler = CallbackInputHandler(rating_callback)
    manager_rating = HumanInputManager(rating_handler)

    rating = await manager_rating.request_rating(
        prompt="Rate the quality of the output"
    )

    print(f"  Rating received: {rating}/5")

    # Step 5: Review history
    print("\n📦 Step 5: Reviewing input history...")
    history = manager.get_input_history()
    print(f"✓ Total inputs: {len(history)}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
