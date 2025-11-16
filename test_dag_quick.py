"""
Quick DAG Scheduler Unit Test (No CLI execution)

Tests topological sort logic without executing tasks via CLI.
Fast validation of core DAG scheduling functionality.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scheduler import Task

# Import DAG scheduler directly
sys.path.insert(0, str(Path(__file__).parent / "src" / "orchestration"))
from dag_scheduler import DAGScheduler


def test_topological_sort_three_levels():
    """Test 3-level dependency tree topological sort"""
    print("\n" + "="*60)
    print("TEST 1: 3-Level Topological Sort")
    print("="*60)

    tasks = [
        # Level 0: Base tasks (no dependencies)
        Task(id="A", prompt="Task A", depends_on=[]),
        Task(id="B", prompt="Task B", depends_on=[]),

        # Level 1: Depends on Level 0
        Task(id="C", prompt="Task C", depends_on=["A"]),
        Task(id="D", prompt="Task D", depends_on=["A"]),
        Task(id="E", prompt="Task E", depends_on=["B"]),
        Task(id="F", prompt="Task F", depends_on=["B"]),

        # Level 2: Depends on Level 1
        Task(id="G", prompt="Task G", depends_on=["C"]),
        Task(id="H", prompt="Task H", depends_on=["D"]),
        Task(id="I", prompt="Task I", depends_on=["E"]),
        Task(id="J", prompt="Task J", depends_on=["F"]),
    ]

    # Use a mock executor (we won't actually execute)
    class MockExecutor:
        initialized = True
        async def execute(self, **kwargs):
            pass
        async def initialize(self, **kwargs):
            pass
        async def shutdown(self):
            pass

    scheduler = DAGScheduler(MockExecutor(), verbose=False)

    # Test topological sort
    try:
        batches = scheduler.topological_sort(tasks)

        print(f"\nTopological sort result: {len(batches)} batches")
        for i, batch in enumerate(batches, 1):
            task_ids = [t.id for t in batch]
            print(f"  Batch {i}: {task_ids}")

        # Validate
        passed = True

        # Check batch count
        if len(batches) != 3:
            print(f"\n❌ Expected 3 batches, got {len(batches)}")
            passed = False
        else:
            print(f"\n✅ Batch count: 3")

        # Check batch 1: should be A, B
        batch1_ids = set(t.id for t in batches[0])
        if batch1_ids != {"A", "B"}:
            print(f"❌ Batch 1 should be {{A, B}}, got {batch1_ids}")
            passed = False
        else:
            print(f"✅ Batch 1: {{A, B}}")

        # Check batch 2: should be C, D, E, F
        batch2_ids = set(t.id for t in batches[1])
        if batch2_ids != {"C", "D", "E", "F"}:
            print(f"❌ Batch 2 should be {{C, D, E, F}}, got {batch2_ids}")
            passed = False
        else:
            print(f"✅ Batch 2: {{C, D, E, F}}")

        # Check batch 3: should be G, H, I, J
        batch3_ids = set(t.id for t in batches[2])
        if batch3_ids != {"G", "H", "I", "J"}:
            print(f"❌ Batch 3 should be {{G, H, I, J}}, got {batch3_ids}")
            passed = False
        else:
            print(f"✅ Batch 3: {{G, H, I, J}}")

        return passed

    except Exception as e:
        print(f"\n❌ Topological sort failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_diamond_pattern():
    """Test diamond dependency pattern"""
    print("\n" + "="*60)
    print("TEST 2: Diamond Pattern")
    print("="*60)

    tasks = [
        Task(id="A", prompt="Task A", depends_on=[]),
        Task(id="B", prompt="Task B", depends_on=["A"]),
        Task(id="C", prompt="Task C", depends_on=["A"]),
        Task(id="D", prompt="Task D", depends_on=["B", "C"]),
    ]

    class MockExecutor:
        initialized = True
        async def execute(self, **kwargs):
            pass
        async def initialize(self, **kwargs):
            pass
        async def shutdown(self):
            pass

    scheduler = DAGScheduler(MockExecutor(), verbose=False)

    try:
        batches = scheduler.topological_sort(tasks)

        print(f"\nTopological sort result: {len(batches)} batches")
        for i, batch in enumerate(batches, 1):
            task_ids = [t.id for t in batch]
            print(f"  Batch {i}: {task_ids}")

        passed = True

        # Should be 3 batches: [A] -> [B, C] -> [D]
        if len(batches) != 3:
            print(f"\n❌ Expected 3 batches, got {len(batches)}")
            passed = False
        else:
            print(f"\n✅ Batch count: 3")

        batch1_ids = set(t.id for t in batches[0])
        if batch1_ids != {"A"}:
            print(f"❌ Batch 1 should be {{A}}, got {batch1_ids}")
            passed = False
        else:
            print(f"✅ Batch 1: {{A}}")

        batch2_ids = set(t.id for t in batches[1])
        if batch2_ids != {"B", "C"}:
            print(f"❌ Batch 2 should be {{B, C}}, got {batch2_ids}")
            passed = False
        else:
            print(f"✅ Batch 2: {{B, C}}")

        batch3_ids = set(t.id for t in batches[2])
        if batch3_ids != {"D"}:
            print(f"❌ Batch 3 should be {{D}}, got {batch3_ids}")
            passed = False
        else:
            print(f"✅ Batch 3: {{D}}")

        return passed

    except Exception as e:
        print(f"\n❌ Topological sort failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_circular_dependency():
    """Test circular dependency detection"""
    print("\n" + "="*60)
    print("TEST 3: Circular Dependency Detection")
    print("="*60)

    tasks = [
        Task(id="A", prompt="Task A", depends_on=["C"]),  # A -> C
        Task(id="B", prompt="Task B", depends_on=["A"]),  # B -> A
        Task(id="C", prompt="Task C", depends_on=["B"]),  # C -> B (circular!)
    ]

    class MockExecutor:
        initialized = True
        async def execute(self, **kwargs):
            pass
        async def initialize(self, **kwargs):
            pass
        async def shutdown(self):
            pass

    scheduler = DAGScheduler(MockExecutor(), verbose=False)

    try:
        batches = scheduler.topological_sort(tasks)

        # Should NOT reach here
        print(f"\n❌ Circular dependency not detected! Got {len(batches)} batches")
        return False

    except ValueError as e:
        error_msg = str(e)
        if "Circular dependency detected" in error_msg:
            print(f"\n✅ Circular dependency correctly detected: {error_msg}")
            return True
        else:
            print(f"\n❌ Wrong error message: {error_msg}")
            return False

    except Exception as e:
        print(f"\n❌ Unexpected exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all unit tests"""
    print("\n" + "="*60)
    print("DAG SCHEDULER UNIT TESTS (Quick)")
    print("="*60)

    results = []
    results.append(("3-Level Sort", test_topological_sort_three_levels()))
    results.append(("Diamond Pattern", test_diamond_pattern()))
    results.append(("Circular Detection", test_circular_dependency()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All unit tests passed!")
        print("\n✅ DAG Scheduler core logic verified:")
        print("  ✓ 3-level dependency tree topological sort")
        print("  ✓ Diamond pattern resolution")
        print("  ✓ Circular dependency detection")
    else:
        print("\n⚠️  Some tests failed.")

    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
