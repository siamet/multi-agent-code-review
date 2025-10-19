"""Refactoring model for representing code transformations."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from src.models.source_location import SourceLocation


class RefactoringType(str, Enum):
    """Types of refactoring operations."""

    # Method-level refactorings
    EXTRACT_METHOD = "extract_method"
    INLINE_METHOD = "inline_method"
    RENAME_METHOD = "rename_method"
    MOVE_METHOD = "move_method"
    CHANGE_SIGNATURE = "change_signature"

    # Class-level refactorings
    EXTRACT_CLASS = "extract_class"
    EXTRACT_INTERFACE = "extract_interface"
    MOVE_CLASS = "move_class"
    RENAME_CLASS = "rename_class"
    PULL_UP_METHOD = "pull_up_method"
    PUSH_DOWN_METHOD = "push_down_method"

    # Variable refactorings
    RENAME_VARIABLE = "rename_variable"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE_VARIABLE = "inline_variable"

    # Other
    REMOVE_DEAD_CODE = "remove_dead_code"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    REPLACE_MAGIC_NUMBER = "replace_magic_number"


class RefactoringStatus(str, Enum):
    """Status of a refactoring operation."""

    PROPOSED = "proposed"  # Suggested but not yet reviewed
    APPROVED = "approved"  # Approved for application
    IN_PROGRESS = "in_progress"  # Currently being applied
    APPLIED = "applied"  # Successfully applied
    FAILED = "failed"  # Application failed
    ROLLED_BACK = "rolled_back"  # Was applied but rolled back
    REJECTED = "rejected"  # Rejected by user


class Refactoring(BaseModel):
    """Represents a code refactoring operation.

    This model stores information about proposed or applied refactorings,
    including their type, impact, and validation results.

    Attributes:
        id: Unique identifier
        type: Type of refactoring
        status: Current status
        location: Source code location to refactor
        issue_id: ID of issue this refactoring addresses (if any)
        agent_id: ID of agent that proposed this
        title: Short description
        description: Detailed description
        rationale: Why this refactoring is beneficial
        impact_score: Expected impact (0.0 to 1.0, higher = more beneficial)
        effort_estimate: Estimated effort in minutes
        risk_score: Risk of breaking changes (0.0 to 1.0, higher = riskier)
        dependencies: IDs of other refactorings this depends on
        conflicts_with: IDs of refactorings this conflicts with
        affected_entities: IDs of affected code entities
        code_changes: Description of changes to be made
        validation_results: Results from semantic verification
        test_results: Test outcomes after application
        proposed_at: When this was proposed
        applied_at: When this was applied (if applicable)
        rollback_info: Information for rollback if needed
        metadata: Additional context
    """

    id: str = Field(..., description="Unique identifier")
    type: RefactoringType = Field(..., description="Refactoring type")
    status: RefactoringStatus = Field(..., description="Current status")
    location: SourceLocation = Field(..., description="Target location")

    issue_id: Optional[str] = Field(default=None, description="Related issue ID")
    agent_id: str = Field(..., description="Agent that proposed this")

    title: str = Field(..., description="Short description")
    description: str = Field(..., description="Detailed description")
    rationale: str = Field(..., description="Why this is beneficial")

    impact_score: float = Field(..., ge=0.0, le=1.0, description="Expected impact (0-1)")
    effort_estimate: int = Field(..., ge=1, description="Effort in minutes")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk level (0-1)")

    dependencies: List[str] = Field(default_factory=list, description="Dependent refactoring IDs")
    conflicts_with: List[str] = Field(
        default_factory=list, description="Conflicting refactoring IDs"
    )
    affected_entities: List[str] = Field(default_factory=list, description="Affected entity IDs")

    code_changes: Dict[str, Any] = Field(default_factory=dict, description="Description of changes")
    validation_results: Dict[str, Any] = Field(
        default_factory=dict, description="Semantic verification results"
    )
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Test outcomes")

    proposed_at: datetime = Field(default_factory=datetime.utcnow, description="Proposal timestamp")
    applied_at: Optional[datetime] = Field(default=None, description="Application timestamp")

    rollback_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Rollback information"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_applied(self) -> bool:
        """Check if refactoring has been applied.

        Returns:
            True if status is applied
        """
        return self.status == RefactoringStatus.APPLIED

    def is_pending(self) -> bool:
        """Check if refactoring is pending (proposed or approved).

        Returns:
            True if pending application
        """
        return self.status in {RefactoringStatus.PROPOSED, RefactoringStatus.APPROVED}

    def can_apply(self) -> bool:
        """Check if refactoring can be applied.

        Returns:
            True if refactoring is approved and has no unmet dependencies
        """
        if self.status != RefactoringStatus.APPROVED:
            return False

        # In full implementation, would check if dependencies are applied
        return len(self.dependencies) == 0 or self._dependencies_satisfied()

    def _dependencies_satisfied(self) -> bool:
        """Check if all dependencies are satisfied.

        Returns:
            True if all dependencies are applied

        Note:
            This is a placeholder. Full implementation would check actual dependencies.
        """
        # Would query database to check if all dependency refactorings are applied
        return True

    def priority_score(self) -> float:
        """Calculate priority score for scheduling.

        Returns:
            Priority score (0-10, higher = more important)
        """
        # Combine impact and risk (prefer high impact, low risk)
        base_score = (self.impact_score * 0.7) + ((1.0 - self.risk_score) * 0.3)

        # Adjust by effort (prefer low effort)
        effort_factor = 1.0 / (1.0 + (self.effort_estimate / 60.0))  # Normalize by hour

        final_score = base_score * 10.0 * (0.7 + 0.3 * effort_factor)

        return min(final_score, 10.0)

    def add_dependency(self, refactoring_id: str) -> None:
        """Add a dependency on another refactoring.

        Args:
            refactoring_id: ID of refactoring this depends on
        """
        if refactoring_id not in self.dependencies:
            self.dependencies.append(refactoring_id)

    def add_conflict(self, refactoring_id: str) -> None:
        """Mark a conflict with another refactoring.

        Args:
            refactoring_id: ID of conflicting refactoring
        """
        if refactoring_id not in self.conflicts_with:
            self.conflicts_with.append(refactoring_id)

    def mark_applied(self) -> None:
        """Mark this refactoring as successfully applied."""
        self.status = RefactoringStatus.APPLIED
        self.applied_at = datetime.utcnow()

    def mark_failed(self, error: str) -> None:
        """Mark this refactoring as failed.

        Args:
            error: Error message describing the failure
        """
        self.status = RefactoringStatus.FAILED
        self.metadata["error"] = error
        self.metadata["failed_at"] = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "location": self.location.to_string(),
            "title": self.title,
            "impact_score": self.impact_score,
            "effort_estimate": self.effort_estimate,
            "risk_score": self.risk_score,
            "priority_score": self.priority_score(),
            "is_applied": self.is_applied(),
            "has_dependencies": len(self.dependencies) > 0,
            "has_conflicts": len(self.conflicts_with) > 0,
        }

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "id": "refactoring_54321",
                "type": "extract_method",
                "status": "proposed",
                "location": {
                    "file_path": "src/services/order_processor.py",
                    "start_line": 145,
                    "end_line": 178,
                    "symbol_name": "process_order",
                },
                "issue_id": "issue_98765",
                "agent_id": "architecture_agent",
                "title": "Extract method: validate_order_items",
                "description": "Extract validation logic into separate method",
                "rationale": "Reduces method complexity from 15 to 8",
                "impact_score": 0.75,
                "effort_estimate": 15,
                "risk_score": 0.2,
                "code_changes": {
                    "new_method_name": "validate_order_items",
                    "parameters": ["items", "inventory"],
                    "return_type": "bool",
                },
            }
        }
