"""
Role Abstraction System

Enables specialized agent roles with delegation, hierarchies, and expertise-based routing.
Inspired by CrewAI and AutoGen role systems.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Callable
import asyncio


class RoleType(Enum):
    """Predefined agent role types"""
    MANAGER = "manager"              # Coordinates and delegates
    RESEARCHER = "researcher"        # Gathers information
    CODER = "coder"                 # Writes code
    REVIEWER = "reviewer"           # Reviews outputs
    TESTER = "tester"               # Tests implementations
    ARCHITECT = "architect"         # Designs systems
    ANALYST = "analyst"             # Analyzes data
    WRITER = "writer"               # Creates content
    CRITIC = "critic"               # Provides feedback
    EXECUTOR = "executor"           # Executes tasks
    SPECIALIST = "specialist"       # Domain expert


@dataclass
class AgentRole:
    """
    Agent role definition with capabilities and constraints
    """
    role_type: RoleType
    name: str
    description: str

    # Capabilities
    skills: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)

    # Behavior
    can_delegate: bool = True
    can_request_help: bool = True
    max_subtasks: int = 5

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def has_skill(self, skill: str) -> bool:
        """Check if role has specific skill"""
        return skill.lower() in [s.lower() for s in self.skills]

    def has_expertise(self, area: str) -> bool:
        """Check if role has expertise in area"""
        return area.lower() in [e.lower() for e in self.expertise_areas]

    def can_handle_task(
        self,
        required_skills: Optional[List[str]] = None,
        required_expertise: Optional[List[str]] = None
    ) -> bool:
        """Check if role can handle a task with given requirements"""
        if required_skills and not all(self.has_skill(s) for s in required_skills):
            return False
        if required_expertise and not all(self.has_expertise(e) for e in required_expertise):
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert role to dictionary"""
        return {
            "role_type": self.role_type.value,
            "name": self.name,
            "description": self.description,
            "skills": self.skills,
            "expertise_areas": self.expertise_areas,
            "can_delegate": self.can_delegate,
            "can_request_help": self.can_request_help,
            "max_subtasks": self.max_subtasks,
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AgentRole':
        """Create role from dictionary"""
        return AgentRole(
            role_type=RoleType(data["role_type"]),
            name=data["name"],
            description=data["description"],
            skills=data.get("skills", []),
            expertise_areas=data.get("expertise_areas", []),
            can_delegate=data.get("can_delegate", True),
            can_request_help=data.get("can_request_help", True),
            max_subtasks=data.get("max_subtasks", 5),
            metadata=data.get("metadata", {})
        )


class RoleRegistry:
    """Registry of available roles and their assignments"""

    def __init__(self):
        self.roles: Dict[str, AgentRole] = {}
        self.role_agents: Dict[str, str] = {}  # role_name -> agent_name

    def register_role(self, role: AgentRole, agent_name: str):
        """Register a role and assign to agent"""
        if role.name in self.roles:
            raise ValueError(f"Role '{role.name}' is already registered")
        self.roles[role.name] = role
        self.role_agents[role.name] = agent_name

    def unregister_role(self, role_name: str):
        """Unregister a role"""
        if role_name in self.roles:
            del self.roles[role_name]
        if role_name in self.role_agents:
            del self.role_agents[role_name]

    def has_role(self, role_name: str) -> bool:
        """Check if role is registered"""
        return role_name in self.roles

    def get_role(self, role_name: str) -> Optional[AgentRole]:
        """Get role by name"""
        return self.roles.get(role_name)

    def get_agent_for_role(self, role_name: str) -> Optional[str]:
        """Get agent assigned to role"""
        return self.role_agents.get(role_name)

    def get_roles_by_type(self, role_type: RoleType) -> List[AgentRole]:
        """Get all roles of a specific type"""
        return [role for role in self.roles.values() if role.role_type == role_type]

    def find_roles_with_skill(self, skill: str) -> List[AgentRole]:
        """Find all roles with specific skill"""
        return [role for role in self.roles.values() if role.has_skill(skill)]

    def get_roles_with_skill(self, skill: str) -> List[AgentRole]:
        """Alias for find_roles_with_skill"""
        return self.find_roles_with_skill(skill)

    def find_roles_with_expertise(self, area: str) -> List[AgentRole]:
        """Find all roles with expertise in area"""
        return [role for role in self.roles.values() if role.has_expertise(area)]

    def get_roles_with_expertise(self, area: str) -> List[AgentRole]:
        """Alias for find_roles_with_expertise"""
        return self.find_roles_with_expertise(area)

    def list_all_roles(self) -> List[AgentRole]:
        """List all registered roles"""
        return list(self.roles.values())


# Predefined role templates
def create_manager_role(name: str = "manager") -> AgentRole:
    """Create manager role for coordination"""
    return AgentRole(
        role_type=RoleType.MANAGER,
        name=name,
        description="Coordinates team, delegates tasks, ensures quality",
        skills=["planning", "delegation", "coordination", "decision_making"],
        expertise_areas=["project_management", "team_leadership"],
        can_delegate=True,
        max_subtasks=10
    )


def create_coder_role(name: str = "coder", languages: Optional[List[str]] = None) -> AgentRole:
    """Create coder role for implementation"""
    langs = languages or ["python", "javascript", "typescript"]
    return AgentRole(
        role_type=RoleType.CODER,
        name=name,
        description="Writes clean, efficient code",
        skills=["coding", "debugging", "refactoring"] + langs,
        expertise_areas=["software_development", "algorithms"],
        can_delegate=False,
        max_subtasks=3
    )


def create_reviewer_role(name: str = "reviewer") -> AgentRole:
    """Create reviewer role for quality assurance"""
    return AgentRole(
        role_type=RoleType.REVIEWER,
        name=name,
        description="Reviews code and provides feedback",
        skills=["code_review", "quality_assurance", "best_practices"],
        expertise_areas=["software_quality", "security"],
        can_delegate=False,
        max_subtasks=2
    )


def create_researcher_role(name: str = "researcher") -> AgentRole:
    """Create researcher role for information gathering"""
    return AgentRole(
        role_type=RoleType.RESEARCHER,
        name=name,
        description="Researches topics and gathers information",
        skills=["research", "analysis", "summarization"],
        expertise_areas=["information_retrieval", "data_analysis"],
        can_delegate=False,
        max_subtasks=5
    )


def create_architect_role(name: str = "architect") -> AgentRole:
    """Create architect role for system design"""
    return AgentRole(
        role_type=RoleType.ARCHITECT,
        name=name,
        description="Designs system architecture and APIs",
        skills=["system_design", "architecture", "api_design", "scalability"],
        expertise_areas=["software_architecture", "distributed_systems"],
        can_delegate=True,
        max_subtasks=5
    )


class RoleBasedRouter:
    """Routes tasks to appropriate roles based on requirements"""

    def __init__(self, registry: RoleRegistry):
        self.registry = registry

    def route_task(
        self,
        task_description: str,
        required_skills: Optional[List[str]] = None,
        required_expertise: Optional[List[str]] = None,
        preferred_role: Optional[RoleType] = None
    ) -> Optional[str]:
        """
        Route task to best matching role

        Args:
            task_description: Task description
            required_skills: Required skills
            required_expertise: Required expertise areas
            preferred_role: Preferred role type

        Returns:
            Agent name or None
        """
        candidates = list(self.registry.roles.values())

        # Filter by preferred role
        if preferred_role:
            candidates = [r for r in candidates if r.role_type == preferred_role]

        # Filter by required skills
        if required_skills:
            candidates = [
                r for r in candidates
                if all(r.has_skill(skill) for skill in required_skills)
            ]

        # Filter by required expertise
        if required_expertise:
            candidates = [
                r for r in candidates
                if all(r.has_expertise(area) for area in required_expertise)
            ]

        if not candidates:
            return None

        # Score candidates (simple heuristic)
        def score_role(role: AgentRole) -> float:
            score = 0.0
            if required_skills:
                score += len([s for s in required_skills if role.has_skill(s)]) * 2
            if required_expertise:
                score += len([e for e in required_expertise if role.has_expertise(e)]) * 3
            return score

        best_role = max(candidates, key=score_role)
        return self.registry.get_agent_for_role(best_role.name)

    def route_to_role_type(self, role_type: RoleType) -> Optional[str]:
        """Route to first agent with specified role type"""
        roles = self.registry.get_roles_by_type(role_type)
        if not roles:
            return None
        return self.registry.get_agent_for_role(roles[0].name)

    def get_available_skills(self) -> Set[str]:
        """Get all available skills across all registered roles"""
        skills = set()
        for role in self.registry.roles.values():
            skills.update(s.lower() for s in role.skills)
        return skills

    def get_available_expertise(self) -> Set[str]:
        """Get all available expertise areas across all registered roles"""
        expertise = set()
        for role in self.registry.roles.values():
            expertise.update(e.lower() for e in role.expertise_areas)
        return expertise


@dataclass
class DelegationRequest:
    """Request for task delegation"""
    task_id: str
    from_role: str
    to_role: Optional[str]
    task_description: str
    required_skills: List[str] = field(default_factory=list)
    required_expertise: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)


class DelegationManager:
    """Manages task delegation between roles"""

    def __init__(self, router: RoleBasedRouter, registry: RoleRegistry):
        self.registry = registry
        self.router = router
        self.delegation_history: List[Dict[str, Any]] = []
        self.agent_workload: Dict[str, int] = {}

    async def delegate(
        self,
        from_role: str,
        task_description: str,
        to_role: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        required_expertise: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Delegate task from one role to another

        Returns:
            Target agent name or None if delegation fails
        """
        # Check if delegating role can delegate
        from_role_obj = self.registry.get_role(from_role)
        if not from_role_obj or not from_role_obj.can_delegate:
            return None

        # Find target role
        if to_role:
            target_agent = self.registry.get_agent_for_role(to_role)
        else:
            target_agent = self.router.route_task(
                task_description,
                required_skills=required_skills,
                required_expertise=required_expertise
            )

        # Record delegation
        delegation = DelegationRequest(
            task_id=f"del_{len(self.delegation_history)}",
            from_role=from_role,
            to_role=to_role,
            task_description=task_description,
            required_skills=required_skills or [],
            required_expertise=required_expertise or [],
            context=context or {}
        )
        self.delegation_history.append({
            "task_id": delegation.task_id,
            "from_role": delegation.from_role,
            "to_role": delegation.to_role,
            "task_description": delegation.task_description,
            "agent": target_agent
        })

        return target_agent

    async def delegate_task(
        self,
        task_id: str,
        task_description: str,
        required_skills: Optional[List[str]] = None,
        required_expertise: Optional[List[str]] = None,
        fallback_agent: Optional[str] = None,
        executor: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Delegate task and optionally execute it

        Args:
            task_id: Task identifier
            task_description: Description of the task
            required_skills: Required skills for the task
            required_expertise: Required expertise areas
            fallback_agent: Fallback agent if no suitable agent found
            executor: Optional async function to execute the task

        Returns:
            Result dictionary with status and details
        """
        # Find suitable agent
        agent_name = self.router.route_task(
            task_description,
            required_skills=required_skills,
            required_expertise=required_expertise
        )

        if not agent_name:
            if fallback_agent:
                agent_name = fallback_agent
            else:
                return {
                    "status": "failed",
                    "error": "No capable agent found for task",
                    "task_id": task_id
                }

        # Track workload
        self.agent_workload[agent_name] = self.agent_workload.get(agent_name, 0) + 1

        # Record in history
        self.delegation_history.append({
            "task_id": task_id,
            "task_description": task_description,
            "agent": agent_name,
            "required_skills": required_skills or [],
            "required_expertise": required_expertise or []
        })

        # Execute if executor provided
        if executor:
            task = {
                "id": task_id,
                "description": task_description,
                "required_skills": required_skills,
                "required_expertise": required_expertise
            }
            result = await executor(agent_name, task)
            return result

        return {
            "status": "delegated",
            "agent": agent_name,
            "task_id": task_id
        }

    def get_delegation_chain(self) -> List[DelegationRequest]:
        """Get history of delegations"""
        return self.delegation_history.copy()

    def get_delegation_history(self) -> List[Dict[str, Any]]:
        """Get delegation history as dictionaries"""
        return self.delegation_history.copy()

    def get_agent_workload(self) -> Dict[str, int]:
        """Get workload statistics for each agent"""
        return self.agent_workload.copy()


# Integration with existing scheduler
class RoleBasedScheduler:
    """Scheduler extension with role-based routing"""

    def __init__(self, base_scheduler, role_registry: RoleRegistry):
        self.base_scheduler = base_scheduler
        self.registry = role_registry
        self.router = RoleBasedRouter(registry)
        self.delegation_manager = DelegationManager(registry, self.router)

    def assign_roles_to_agents(self, role_agent_map: Dict[str, str]):
        """Assign roles to existing agents"""
        for role_name, agent_name in role_agent_map.items():
            role = self.registry.get_role(role_name)
            if role and agent_name in self.base_scheduler.agents:
                self.registry.role_agents[role_name] = agent_name

    async def execute_with_roles(
        self,
        task_description: str,
        required_skills: Optional[List[str]] = None,
        required_expertise: Optional[List[str]] = None,
        preferred_role: Optional[RoleType] = None
    ) -> Any:
        """Execute task using role-based routing"""
        # Route to appropriate agent
        agent_name = self.router.route_task(
            task_description,
            required_skills=required_skills,
            required_expertise=required_expertise,
            preferred_role=preferred_role
        )

        if not agent_name:
            raise ValueError(f"No suitable agent found for task: {task_description}")

        # Execute using base scheduler
        from src.scheduler import Task
        task = Task(
            id=f"role_task_{id(task_description)}",
            prompt=task_description,
            task_type="role_based"
        )

        return await self.base_scheduler.execute_task(task, agent_name)
