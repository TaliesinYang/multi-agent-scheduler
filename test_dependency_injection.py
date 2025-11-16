"""
Dependency Injection Unit Tests

Tests the DependencyInjector module for correct data extraction
and prompt enhancement.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scheduler import Task

# Import orchestration modules directly
sys.path.insert(0, str(Path(__file__).parent / "src" / "orchestration"))
from dependency_injector import DependencyInjector, DependencyInjectionError
from executor import TaskResult


def test_simple_field_extraction():
    """Test basic field extraction from parsed_data"""
    print("\n" + "="*60)
    print("TEST 1: Simple Field Extraction")
    print("="*60)

    # Create upstream task result
    task_a_result = TaskResult(
        task_id="task_a",
        success=True,
        output="Found 3 users",
        parsed_data={
            "users": ["alice", "bob", "charlie"],
            "count": 3
        }
    )

    # Create downstream task
    task_b = Task(
        id="task_b",
        prompt="Process user: {target_user}",
        depends_on=["task_a"]
    )

    # Inject dependencies
    injector = DependencyInjector(verbose=True)

    try:
        enhanced_prompt = injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={
                "target_user": "task_a.users[0]",
                "total_count": "task_a.count"
            }
        )

        print("\n✓ Injection successful")
        print("\nEnhanced prompt:")
        print("-" * 60)
        print(enhanced_prompt)
        print("-" * 60)

        # Validate
        assert "target_user" in enhanced_prompt
        assert '"alice"' in enhanced_prompt
        assert "total_count" in enhanced_prompt
        assert "3" in enhanced_prompt

        print("\n✅ PASSED: Simple field extraction")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_nested_field_extraction():
    """Test nested field extraction"""
    print("\n" + "="*60)
    print("TEST 2: Nested Field Extraction")
    print("="*60)

    # Upstream result with nested structure
    task_a_result = TaskResult(
        task_id="task_a",
        success=True,
        output="User data retrieved",
        parsed_data={
            "user": {
                "name": "alice",
                "profile": {
                    "age": 25,
                    "city": "NYC"
                }
            }
        }
    )

    task_b = Task(
        id="task_b",
        prompt="Process user from {city}",
        depends_on=["task_a"]
    )

    injector = DependencyInjector(verbose=True)

    try:
        enhanced_prompt = injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={
                "user_name": "task_a.user.name",
                "city": "task_a.user.profile.city",
                "age": "task_a.user.profile.age"
            }
        )

        print("\n✓ Injection successful")

        # Validate
        assert "user_name" in enhanced_prompt
        assert '"alice"' in enhanced_prompt
        assert "city" in enhanced_prompt
        assert '"NYC"' in enhanced_prompt
        assert "age" in enhanced_prompt
        assert "25" in enhanced_prompt

        print("\n✅ PASSED: Nested field extraction")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_array_wildcard():
    """Test array wildcard extraction (all elements)"""
    print("\n" + "="*60)
    print("TEST 3: Array Wildcard Extraction")
    print("="*60)

    task_a_result = TaskResult(
        task_id="task_a",
        success=True,
        output="Found multiple products",
        parsed_data={
            "product_ids": [101, 102, 103, 104]
        }
    )

    task_b = Task(
        id="task_b",
        prompt="Analyze products: {product_list}",
        depends_on=["task_a"]
    )

    injector = DependencyInjector(verbose=True)

    try:
        enhanced_prompt = injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={
                "product_list": "task_a.product_ids[*]"
            }
        )

        print("\n✓ Injection successful")

        # Validate
        assert "product_list" in enhanced_prompt
        assert "101" in enhanced_prompt
        assert "104" in enhanced_prompt

        print("\n✅ PASSED: Array wildcard extraction")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling for invalid paths"""
    print("\n" + "="*60)
    print("TEST 4: Error Handling")
    print("="*60)

    task_a_result = TaskResult(
        task_id="task_a",
        success=True,
        output="Data",
        parsed_data={"users": ["alice"]}
    )

    task_b = Task(
        id="task_b",
        prompt="Test task",
        depends_on=["task_a"]
    )

    injector = DependencyInjector(verbose=False)

    # Test 1: Non-existent task
    try:
        injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={"data": "task_b.users[0]"}  # task_b doesn't exist
        )
        print("❌ FAILED: Should have raised error for non-existent task")
        return False
    except DependencyInjectionError as e:
        print(f"✓ Correctly caught error: {e}")

    # Test 2: Non-existent field
    try:
        injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={"data": "task_a.nonexistent"}
        )
        print("❌ FAILED: Should have raised error for non-existent field")
        return False
    except DependencyInjectionError as e:
        print(f"✓ Correctly caught error: {e}")

    # Test 3: Array index out of range
    try:
        injector.inject_dependencies(
            task=task_b,
            upstream_results={"task_a": task_a_result},
            input_mapping={"data": "task_a.users[10]"}  # Only 1 user
        )
        print("❌ FAILED: Should have raised error for out-of-range index")
        return False
    except DependencyInjectionError as e:
        print(f"✓ Correctly caught error: {e}")

    print("\n✅ PASSED: Error handling")
    return True


def test_multiple_upstream_tasks():
    """Test injection from multiple upstream tasks"""
    print("\n" + "="*60)
    print("TEST 5: Multiple Upstream Tasks")
    print("="*60)

    task_a_result = TaskResult(
        task_id="task_a",
        success=True,
        output="Found 5 users",
        parsed_data={"users": ["alice", "bob"], "count": 2}
    )

    task_b_result = TaskResult(
        task_id="task_b",
        success=True,
        output="Found 3 files",
        parsed_data={"files": ["/home/test.txt"], "count": 3}
    )

    task_c = Task(
        id="task_c",
        prompt="Merge data from task_a and task_b",
        depends_on=["task_a", "task_b"]
    )

    injector = DependencyInjector(verbose=True)

    try:
        enhanced_prompt = injector.inject_dependencies(
            task=task_c,
            upstream_results={
                "task_a": task_a_result,
                "task_b": task_b_result
            },
            input_mapping={
                "first_user": "task_a.users[0]",
                "user_count": "task_a.count",
                "first_file": "task_b.files[0]",
                "file_count": "task_b.count"
            }
        )

        print("\n✓ Injection successful")

        # Validate
        assert "first_user" in enhanced_prompt
        assert '"alice"' in enhanced_prompt
        assert "user_count" in enhanced_prompt
        assert "2" in enhanced_prompt
        assert "first_file" in enhanced_prompt
        assert "/home/test.txt" in enhanced_prompt
        assert "file_count" in enhanced_prompt
        assert "3" in enhanced_prompt

        print("\n✅ PASSED: Multiple upstream tasks")
        return True

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all dependency injection tests"""
    print("\n" + "="*60)
    print("DEPENDENCY INJECTION UNIT TESTS")
    print("="*60)

    results = []
    results.append(("Simple Field Extraction", test_simple_field_extraction()))
    results.append(("Nested Field Extraction", test_nested_field_extraction()))
    results.append(("Array Wildcard", test_array_wildcard()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Multiple Upstream Tasks", test_multiple_upstream_tasks()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n🎉 All tests passed!")
        print("\n✅ Dependency Injection verified:")
        print("  ✓ Simple field extraction (task_a.field)")
        print("  ✓ Nested field extraction (task_a.nested.field)")
        print("  ✓ Array indexing (task_a.array[0])")
        print("  ✓ Array wildcard (task_a.array[*])")
        print("  ✓ Error handling")
        print("  ✓ Multiple upstream tasks")
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
