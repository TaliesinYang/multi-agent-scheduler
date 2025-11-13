"""
Comprehensive tests for role abstraction system
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from src.role_abstraction import (
    RoleType, AgentRole, RoleRegistry, RoleBasedRouter, DelegationManager,
    create_manager_role, create_coder_role, create_reviewer_role,
    create_researcher_role, create_architect_role
)


class TestAgentRole:
    """Test AgentRole class"""

    def test_create_role(self):
        """Test creating a role"""
        role = AgentRole(
            role_type=RoleType.CODER,
            name="senior_coder",
            description="Senior Python developer",
            skills=["python", "async", "testing"],
            expertise_areas=["backend", "apis"]
        )

        assert role.role_type == RoleType.CODER
        assert role.name == "senior_coder"
        assert "python" in role.skills
        assert role.can_delegate is True

    def test_has_skill(self):
        """Test skill checking"""
        role = AgentRole(
            role_type=RoleType.CODER,
            name="python_dev",
            description="Python developer",
            skills=["python", "django", "fastapi"]
        )

        assert role.has_skill("python") is True
        assert role.has_skill("javascript") is False

    def test_has_expertise(self):
        """Test expertise checking"""
        role = AgentRole(
            role_type=RoleType.ARCHITECT,
            name="system_architect",
            description="System architect",
            expertise_areas=["microservices", "distributed_systems"]
        )

        assert role.has_expertise("microservices") is True
        assert role.has_expertise("frontend") is False

    def test_can_handle_task(self):
        """Test task handling capability"""
        role = AgentRole(
            role_type=RoleType.CODER,
            name="fullstack_dev",
            description="Full-stack developer",
            skills=["python", "react", "sql"],
            expertise_areas=["web", "databases"]
        )

        # Should handle if has required skills
        assert role.can_handle_task(
            required_skills=["python", "sql"]
        ) is True

        # Should not handle if missing skills
        assert role.can_handle_task(
            required_skills=["rust", "golang"]
        ) is False

        # Should handle if has expertise
        assert role.can_handle_task(
            required_expertise=["databases"]
        ) is True

    def test_to_dict(self):
        """Test serialization"""
        role = AgentRole(
            role_type=RoleType.TESTER,
            name="qa_engineer",
            description="QA engineer",
            skills=["pytest", "selenium"]
        )

        role_dict = role.to_dict()
        assert role_dict["role_type"] == "tester"
        assert role_dict["name"] == "qa_engineer"
        assert "pytest" in role_dict["skills"]

    def test_from_dict(self):
        """Test deserialization"""
        data = {
            "role_type": "reviewer",
            "name": "code_reviewer",
            "description": "Code reviewer",
            "skills": ["static_analysis", "security"],
            "expertise_areas": ["code_quality"],
            "can_delegate": False
        }

        role = AgentRole.from_dict(data)
        assert role.role_type == RoleType.REVIEWER
        assert role.name == "code_reviewer"
        assert role.can_delegate is False


class TestRoleRegistry:
    """Test RoleRegistry class"""

    def test_register_role(self):
        """Test registering a role"""
        registry = RoleRegistry()
        role = create_coder_role("coder")

        registry.register_role(role, "agent_1")

        assert registry.has_role("coder")
        assert registry.get_agent_for_role("coder") == "agent_1"

    def test_register_duplicate_role(self):
        """Test registering duplicate role name"""
        registry = RoleRegistry()
        role1 = create_coder_role("coder")
        role2 = create_coder_role("coder")

        registry.register_role(role1, "agent_1")

        # Should raise error
        with pytest.raises(ValueError, match="already registered"):
            registry.register_role(role2, "agent_2")

    def test_unregister_role(self):
        """Test unregistering a role"""
        registry = RoleRegistry()
        role = create_reviewer_role("reviewer")

        registry.register_role(role, "agent_1")
        registry.unregister_role("reviewer")

        assert not registry.has_role("reviewer")

    def test_get_role(self):
        """Test getting role by name"""
        registry = RoleRegistry()
        role = create_researcher_role("researcher")

        registry.register_role(role, "agent_1")
        retrieved_role = registry.get_role("researcher")

        assert retrieved_role is not None
        assert retrieved_role.role_type == RoleType.RESEARCHER

    def test_get_roles_by_type(self):
        """Test getting roles by type"""
        registry = RoleRegistry()

        # Register multiple coders
        registry.register_role(create_coder_role("agent_1"), "agent_1")
        registry.register_role(
            AgentRole(RoleType.CODER, "senior_coder", "Senior dev", ["python"]),
            "agent_2"
        )

        coders = registry.get_roles_by_type(RoleType.CODER)
        assert len(coders) == 2

    def test_get_roles_with_skill(self):
        """Test finding roles with specific skill"""
        registry = RoleRegistry()

        registry.register_role(
            AgentRole(RoleType.CODER, "python_dev", "Python dev", ["python", "django"]),
            "agent_1"
        )
        registry.register_role(
            AgentRole(RoleType.CODER, "js_dev", "JS dev", ["javascript", "react"]),
            "agent_2"
        )

        python_roles = registry.get_roles_with_skill("python")
        assert len(python_roles) == 1
        assert python_roles[0].name == "python_dev"

    def test_get_roles_with_expertise(self):
        """Test finding roles with specific expertise"""
        registry = RoleRegistry()

        registry.register_role(
            AgentRole(
                RoleType.ARCHITECT, "cloud_architect", "Cloud architect",
                expertise_areas=["aws", "kubernetes"]
            ),
            "agent_1"
        )

        experts = registry.get_roles_with_expertise("aws")
        assert len(experts) == 1
        assert experts[0].name == "cloud_architect"

    def test_list_all_roles(self):
        """Test listing all roles"""
        registry = RoleRegistry()

        registry.register_role(create_coder_role("agent_1"), "agent_1")
        registry.register_role(create_reviewer_role("agent_2"), "agent_2")

        roles = registry.list_all_roles()
        assert len(roles) == 2
        assert any(r.role_type == RoleType.CODER for r in roles)
        assert any(r.role_type == RoleType.REVIEWER for r in roles)


class TestRoleBasedRouter:
    """Test RoleBasedRouter class"""

    def test_route_by_skill(self):
        """Test routing task by required skill"""
        registry = RoleRegistry()
        registry.register_role(
            AgentRole(RoleType.CODER, "python_dev", "Python dev", ["python", "fastapi"]),
            "agent_python"
        )
        registry.register_role(
            AgentRole(RoleType.CODER, "js_dev", "JS dev", ["javascript", "react"]),
            "agent_js"
        )

        router = RoleBasedRouter(registry)

        # Should route to Python developer
        agent = router.route_task(
            "Implement REST API",
            required_skills=["python", "fastapi"]
        )

        assert agent == "agent_python"

    def test_route_by_expertise(self):
        """Test routing task by expertise area"""
        registry = RoleRegistry()
        registry.register_role(
            AgentRole(
                RoleType.ARCHITECT, "backend_arch", "Backend architect",
                expertise_areas=["microservices", "databases"]
            ),
            "agent_backend"
        )
        registry.register_role(
            AgentRole(
                RoleType.ARCHITECT, "frontend_arch", "Frontend architect",
                expertise_areas=["react", "performance"]
            ),
            "agent_frontend"
        )

        router = RoleBasedRouter(registry)

        agent = router.route_task(
            "Design microservices architecture",
            required_expertise=["microservices"]
        )

        assert agent == "agent_backend"

    def test_route_by_role_type(self):
        """Test routing to specific role type"""
        registry = RoleRegistry()
        registry.register_role(create_reviewer_role("agent_1"), "agent_1")
        registry.register_role(create_coder_role("agent_2"), "agent_2")

        router = RoleBasedRouter(registry)

        agent = router.route_to_role_type(RoleType.REVIEWER)
        assert agent == "agent_1"

    def test_route_no_match(self):
        """Test routing when no role matches"""
        registry = RoleRegistry()
        registry.register_role(
            AgentRole(RoleType.CODER, "python_dev", "Python dev", ["python"]),
            "agent_1"
        )

        router = RoleBasedRouter(registry)

        # No one has Rust skills
        agent = router.route_task(
            "Implement in Rust",
            required_skills=["rust", "tokio"]
        )

        assert agent is None

    def test_route_best_match(self):
        """Test routing to best matching role"""
        registry = RoleRegistry()

        # Junior dev with 1 skill match
        registry.register_role(
            AgentRole(RoleType.CODER, "junior", "Junior", ["python"]),
            "agent_junior"
        )

        # Senior dev with all skills
        registry.register_role(
            AgentRole(RoleType.CODER, "senior", "Senior", ["python", "django", "postgres"]),
            "agent_senior"
        )

        router = RoleBasedRouter(registry)

        # Should route to senior dev (better match)
        agent = router.route_task(
            "Build Django app with PostgreSQL",
            required_skills=["python", "django", "postgres"]
        )

        assert agent == "agent_senior"

    def test_get_available_skills(self):
        """Test getting all available skills"""
        registry = RoleRegistry()
        registry.register_role(
            AgentRole(RoleType.CODER, "dev1", "Dev 1", ["python", "react"]),
            "agent_1"
        )
        registry.register_role(
            AgentRole(RoleType.CODER, "dev2", "Dev 2", ["rust", "react"]),
            "agent_2"
        )

        router = RoleBasedRouter(registry)
        skills = router.get_available_skills()

        assert "python" in skills
        assert "rust" in skills
        assert "react" in skills
        assert len(skills) == 3

    def test_get_available_expertise(self):
        """Test getting all available expertise areas"""
        registry = RoleRegistry()
        registry.register_role(
            AgentRole(RoleType.ARCHITECT, "arch1", "Arch 1", expertise_areas=["cloud", "security"]),
            "agent_1"
        )
        registry.register_role(
            AgentRole(RoleType.ARCHITECT, "arch2", "Arch 2", expertise_areas=["mobile", "cloud"]),
            "agent_2"
        )

        router = RoleBasedRouter(registry)
        expertise = router.get_available_expertise()

        assert "cloud" in expertise
        assert "security" in expertise
        assert "mobile" in expertise


class TestDelegationManager:
    """Test DelegationManager class"""

    @pytest.mark.asyncio
    async def test_delegate_task(self):
        """Test delegating a task"""
        registry = RoleRegistry()
        registry.register_role(create_coder_role("agent_coder"), "agent_coder")

        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        # Mock executor
        async def mock_executor(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "completed", "agent": agent_name, "task_id": task["id"]}

        result = await delegation_manager.delegate_task(
            task_id="task_1",
            task_description="Write Python code",
            required_skills=["python"],
            executor=mock_executor
        )

        assert result["status"] == "completed"
        assert result["agent"] == "agent_coder"

    @pytest.mark.asyncio
    async def test_delegate_no_capable_agent(self):
        """Test delegation when no agent can handle task"""
        registry = RoleRegistry()
        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        async def mock_executor(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "completed"}

        result = await delegation_manager.delegate_task(
            task_id="task_1",
            task_description="Impossible task",
            required_skills=["nonexistent_skill"],
            executor=mock_executor
        )

        assert result["status"] == "failed"
        assert "No capable agent found" in result["error"]

    @pytest.mark.asyncio
    async def test_delegate_with_fallback(self):
        """Test delegation with fallback agent"""
        registry = RoleRegistry()
        registry.register_role(create_manager_role("agent_manager"), "agent_manager")

        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        async def mock_executor(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "completed", "agent": agent_name}

        result = await delegation_manager.delegate_task(
            task_id="task_1",
            task_description="Some task",
            required_skills=["nonexistent"],
            fallback_agent="agent_manager",
            executor=mock_executor
        )

        assert result["status"] == "completed"
        assert result["agent"] == "agent_manager"

    @pytest.mark.asyncio
    async def test_get_delegation_history(self):
        """Test getting delegation history"""
        registry = RoleRegistry()
        registry.register_role(create_coder_role("agent_1"), "agent_1")

        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        async def mock_executor(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "completed"}

        # Delegate multiple tasks
        await delegation_manager.delegate_task(
            task_id="task_1",
            task_description="Task 1",
            required_skills=["python"],
            executor=mock_executor
        )

        await delegation_manager.delegate_task(
            task_id="task_2",
            task_description="Task 2",
            required_skills=["python"],
            executor=mock_executor
        )

        history = delegation_manager.get_delegation_history()
        assert len(history) == 2
        assert history[0]["task_id"] == "task_1"
        assert history[1]["task_id"] == "task_2"

    @pytest.mark.asyncio
    async def test_get_agent_workload(self):
        """Test getting agent workload statistics"""
        registry = RoleRegistry()
        registry.register_role(create_coder_role("agent_1"), "agent_1")

        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        async def mock_executor(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "completed"}

        # Delegate tasks
        await delegation_manager.delegate_task("task_1", "Task 1", required_skills=["python"], executor=mock_executor)
        await delegation_manager.delegate_task("task_2", "Task 2", required_skills=["python"], executor=mock_executor)

        workload = delegation_manager.get_agent_workload()
        assert "agent_1" in workload
        assert workload["agent_1"] == 2


class TestRoleFactoryFunctions:
    """Test role factory functions"""

    def test_create_manager_role(self):
        """Test creating manager role"""
        role = create_manager_role("agent_1")

        assert role.role_type == RoleType.MANAGER
        assert role.can_delegate is True
        assert "coordination" in role.skills

    def test_create_coder_role(self):
        """Test creating coder role"""
        role = create_coder_role("agent_1")

        assert role.role_type == RoleType.CODER
        assert "python" in role.skills

    def test_create_reviewer_role(self):
        """Test creating reviewer role"""
        role = create_reviewer_role("agent_1")

        assert role.role_type == RoleType.REVIEWER
        assert "code_review" in role.skills

    def test_create_researcher_role(self):
        """Test creating researcher role"""
        role = create_researcher_role("agent_1")

        assert role.role_type == RoleType.RESEARCHER
        assert "research" in role.skills

    def test_create_architect_role(self):
        """Test creating architect role"""
        role = create_architect_role("agent_1")

        assert role.role_type == RoleType.ARCHITECT
        assert "system_design" in role.skills


class TestIntegration:
    """Integration tests for role abstraction system"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete role-based workflow"""
        # Setup
        registry = RoleRegistry()
        registry.register_role(create_manager_role("manager"), "agent_manager")
        registry.register_role(create_coder_role("coder"), "agent_coder")
        registry.register_role(create_reviewer_role("reviewer"), "agent_reviewer")

        router = RoleBasedRouter(registry)
        delegation_manager = DelegationManager(router, registry)

        # Mock task executor
        executed_tasks = []

        async def execute_task(agent_name: str, task: Dict[str, Any]) -> Dict[str, Any]:
            executed_tasks.append({
                "agent": agent_name,
                "task_id": task["id"],
                "description": task["description"]
            })
            return {"status": "completed", "agent": agent_name}

        # Delegate coding task
        result1 = await delegation_manager.delegate_task(
            task_id="code_task",
            task_description="Write Python function",
            required_skills=["python"],
            executor=execute_task
        )

        # Delegate review task
        result2 = await delegation_manager.delegate_task(
            task_id="review_task",
            task_description="Review code",
            required_skills=["code_review"],
            executor=execute_task
        )

        # Verify routing
        assert result1["status"] == "completed"
        assert result2["status"] == "completed"
        assert executed_tasks[0]["agent"] == "agent_coder"
        assert executed_tasks[1]["agent"] == "agent_reviewer"

        # Check workload
        workload = delegation_manager.get_agent_workload()
        assert workload["agent_coder"] == 1
        assert workload["agent_reviewer"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
