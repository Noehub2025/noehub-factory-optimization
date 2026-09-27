"""Deep current interface for one Frontier Batch.

The current local, serial workflow has one ordinary identity: the human Batch
handle. Git identifies retained project bytes. Reviews and Permissions keep
their own meaning. This module owns only Batch state, execution Attempts, real
Consequences, consumption, and the terminal result.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
import copy
import fcntl
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Protocol, TypeAlias

import yaml

from saved_git import SavedGitError, normalize_path, validate_selection


CONTRACT_VERSION = "frontier-batch/1"
BATCH_PATTERN = re.compile(r"^B[0-9]+$")
CONSEQUENCE_KINDS = {
    "spend",
    "external_submission",
    "sensitive_access",
    "irreversible_change",
    "single_use_consumption",
}
PERMISSION_REQUIRED_CONSEQUENCES = {
    "external_submission",
    "sensitive_access",
    "irreversible_change",
}
FINAL_STATUSES = {"completed", "stopped"}
OPERATION_STATUSES = {"completed", "failed", "uncertain"}


class BatchError(RuntimeError):
    """Base class for current Batch failures."""


class BatchFormatError(BatchError):
    """The current Batch record or a requested change is malformed."""


class ChangeRejected(BatchError):
    """A routine change does not preserve the current Batch."""


class ConsequenceBlocked(BatchError):
    """One action cannot begin under the current facts."""


class ConsequenceUncertain(BatchError):
    """An action may already have produced a result or Consequence."""


class StorageConflict(BatchError):
    """The authoritative Batch record cannot be updated safely."""


class OperationContractViolation(BatchError):
    """An operation produced behavior outside its declared envelope."""


@dataclass(frozen=True)
class GitReference:
    """One retained record owned outside Batch."""

    handle: str
    commit: str
    path: str


@dataclass(frozen=True)
class CandidateRevision:
    """Exact project bytes selected for work, checks, or execution."""

    commit: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class DefineBatch:
    """Create the first current-format description of a Batch."""

    objective: str
    acceptance: str
    scope: tuple[str, ...]
    reviews: tuple[GitReference, ...] = ()
    permissions: tuple[GitReference, ...] = ()
    resource_limits: Mapping[str, float | int] = field(default_factory=dict)
    expected_consequences: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviseBatch:
    """Change routine Batch facts while pursuing the same judged result."""

    rationale: str
    objective: str | None = None
    acceptance: str | None = None
    scope: tuple[str, ...] | None = None
    reviews: tuple[GitReference, ...] | None = None
    permissions: tuple[GitReference, ...] | None = None
    resource_limits: Mapping[str, float | int] | None = None
    expected_consequences: tuple[str, ...] | None = None
    measurement_definition: Mapping[str, Any] | None = None
    reopen: bool = False


@dataclass(frozen=True)
class SelectCandidate:
    """Select one exact Candidate Revision inside the current Batch."""

    candidate: CandidateRevision
    rationale: str


@dataclass(frozen=True)
class AdoptReview:
    """Reference a chosen saved R without copying its verdict or credentials."""

    revision: str
    path: str
    rationale: str
    handle: str | None = None


@dataclass(frozen=True)
class UpdateWorkingState:
    """Apply a same-result delta against the current state under the Batch lock."""

    rationale: str
    revision: str | None = None
    paths: tuple[str, ...] | None = None
    resource_limits: Mapping[str, float | int] | None = None
    measurement_updates: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RecordCheck:
    """Record an ordinary check against one exact Candidate Revision."""

    key: str
    candidate: CandidateRevision
    outcome: str
    evidence: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RecordObservation:
    """Record a routine observation without creating an Attempt."""

    key: str
    observation: Mapping[str, Any]
    candidate: CandidateRevision | None = None


@dataclass(frozen=True)
class ReconcileAttempt:
    """Resolve one uncertain Attempt from observed external or local facts."""

    attempt: int
    status: str
    rationale: str
    observations: tuple[Mapping[str, Any], ...] = ()
    consequences: tuple[Consequence, ...] = ()
    resource_use: Mapping[str, float | int] = field(default_factory=dict)
    resource_bounds: Mapping[str, Mapping[str, float | int | str]] = field(
        default_factory=dict
    )
    capacity_charge: Mapping[str, float | int] = field(default_factory=dict)
    result: Mapping[str, Any] = field(default_factory=dict)
    recovery_condition: str | None = None


@dataclass(frozen=True)
class ConcludeBatch:
    """Record the current terminal conclusion for the judged result."""

    status: str
    result: Mapping[str, Any]
    remaining_gap: str


RoutineChange: TypeAlias = (
    DefineBatch
    | ReviseBatch
    | SelectCandidate
    | AdoptReview
    | UpdateWorkingState
    | RecordCheck
    | RecordObservation
    | ReconcileAttempt
    | ConcludeBatch
)


@dataclass(frozen=True)
class Action:
    """One operation that may produce a measurement result or Consequence."""

    key: str
    operation: str
    kind: str
    candidate: CandidateRevision | None = None
    # Current-action requirements, not all retained references.reviews.
    required_reviews: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    required_checks: tuple[str, ...] = ()
    requested_resources: Mapping[str, float | int] = field(default_factory=dict)
    possible_consequences: tuple[str, ...] = ()
    repeatable: bool = False
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Consequence:
    """One actual effect whose repetition matters."""

    kind: str
    amount: float | int = 1
    external_reference: str | None = None
    idempotency_key: str | None = None
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperationResult:
    """Observed result returned by an operation adapter."""

    status: str
    observations: tuple[Mapping[str, Any], ...] = ()
    consequences: tuple[Consequence, ...] = ()
    resource_use: Mapping[str, float | int] = field(default_factory=dict)
    result: Mapping[str, Any] = field(default_factory=dict)
    recovery_condition: str | None = None


@dataclass(frozen=True)
class ReviewAssessment:
    applies: bool
    reason: str = ""


@dataclass(frozen=True)
class PermissionAssessment:
    allows: bool
    reason: str = ""
    resource_limits: Mapping[str, float | int] = field(default_factory=dict)
    permitted_consequences: tuple[str, ...] = ()


class GovernanceResolver(Protocol):
    """Resolve facts owned by Review and Permission without copying them."""

    def review(self, reference: GitReference, action: Action) -> ReviewAssessment:
        """Read saved R coverage for this action without writing or adopting it.

        Judge relevant inputs and assumptions, not whole-Batch byte equality.
        A caller may supply an unadopted R for an optional readiness check;
        perform separately requires its actual current Batch membership.
        See batch-current.md#review-applicability-and-adoption.
        """
        ...

    def permission(
        self,
        reference: GitReference,
        action: Action,
        actual_consumption: Mapping[str, float | int],
    ) -> PermissionAssessment:
        ...


class OperationAdapter(Protocol):
    """Perform one action after Batch has established its durable start."""

    def __call__(self, action: Action, context: Mapping[str, Any]) -> OperationResult:
        ...


@dataclass(frozen=True)
class OperationBinding:
    """Install one adapter with the protected effects inherent to that seam."""

    run: OperationAdapter
    protected_consequences: tuple[str, ...] = ()


LegacyProjector: TypeAlias = Callable[[Path, str], Mapping[str, Any] | None]


@dataclass(frozen=True)
class BatchView:
    """Batch facts from one snapshot, independent of the persisted record layout."""

    _record: Mapping[str, Any] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_record", copy.deepcopy(dict(self._record)))

    def export_record(self) -> dict[str, Any]:
        """Export a detached record for diagnostics and historical compatibility."""
        return copy.deepcopy(dict(self._record))

    @property
    def data(self) -> Mapping[str, Any]:
        """Compatibility export; ordinary callers should read named Batch facts."""
        return self.export_record()

    @property
    def batch(self) -> str:
        return str(self._record["batch"])

    @property
    def status(self) -> str:
        return str(self._record["current"]["status"])

    @property
    def defined(self) -> bool:
        return bool(self._record["definition"])

    @property
    def scope(self) -> tuple[str, ...]:
        return tuple(self._record["definition"].get("scope", ()))

    @property
    def candidate_revision(self) -> CandidateRevision | None:
        selected = self._record["current"].get("candidate_revision")
        return CandidateRevision(selected["commit"], tuple(selected["paths"])) if selected else None

    @property
    def reviews(self) -> tuple[GitReference, ...]:
        return tuple(GitReference(**row) for row in self._record["references"]["reviews"])

    @property
    def passed_checks(self) -> tuple[str, ...]:
        """Check keys passing on the current selection, without deciding requirements."""
        selected = self._record["current"].get("candidate_revision")
        return tuple(
            key for key, check in self._record["current"].get("checks", {}).items()
            if check["outcome"] == "passed" and check.get("candidate_revision") == selected
        )

    @property
    def measurement_definition(self) -> dict[str, Any] | None:
        """Return the owned definition; project-specific meaning stays with its owner."""
        return copy.deepcopy(self._record["current"].get("measurement_definition"))

    @property
    def remaining_capacity(self) -> dict[str, float | int]:
        """Subtract exact use and retained conservative charges for bounded use."""
        return _remaining_resources(self._record)

    @property
    def latest_attempt(self) -> dict[str, Any] | None:
        attempts = self._record["attempts"]
        return copy.deepcopy(attempts[-1]) if attempts else None


@dataclass(frozen=True)
class ActionOutcome:
    """One performed action and the resulting authoritative Batch view."""

    view: BatchView
    attempt: int | None
    operation_result: OperationResult


class Batch:
    """Own the current state and real execution history of one Batch."""

    def __init__(
        self,
        *,
        repo_root: Path,
        batch: str,
        state_path: Path,
        state: dict[str, Any],
        governance: GovernanceResolver | None,
        operations: Mapping[str, OperationBinding],
        projected_legacy: bool,
    ) -> None:
        self._repo_root = repo_root
        self._batch = batch
        self._state_path = state_path
        self._lock_path = state_path.with_suffix(state_path.suffix + ".lock")
        self._state = state
        self._governance = governance
        self._operations = _operation_bindings(operations)
        self._projected_legacy = projected_legacy

    @classmethod
    def open(
        cls,
        repo_root: Path,
        batch: str,
        *,
        state_path: Path | None = None,
        governance: GovernanceResolver | None = None,
        operations: Mapping[str, OperationBinding] | None = None,
        legacy_projector: LegacyProjector | None = None,
    ) -> "Batch":
        """Open one current Batch without creating another machine identity."""

        root = repo_root.resolve()
        if not (root / ".git").exists():
            raise BatchFormatError("Batch requires a Git repository")
        if not BATCH_PATTERN.fullmatch(batch):
            raise BatchFormatError(f"invalid Batch handle: {batch!r}")
        record = (
            state_path.resolve()
            if state_path is not None
            else root / "artifacts" / "frontier" / batch / "batch.yaml"
        )
        try:
            record.relative_to(root)
        except ValueError as exc:
            raise BatchFormatError("Batch state must remain inside the project repository") from exc

        projected = False
        if record.exists():
            state = _read_state(record)
        elif legacy_projector is not None:
            legacy = legacy_projector(root, batch)
            state = _empty_state(batch) if legacy is None else copy.deepcopy(dict(legacy))
            projected = legacy is not None
        else:
            state = _empty_state(batch)
        _validate_state(state, batch)
        return cls(
            repo_root=root,
            batch=batch,
            state_path=record,
            state=state,
            governance=governance,
            operations=operations or {},
            projected_legacy=projected,
        )

    @property
    def view(self) -> BatchView:
        return BatchView(self._state)

    def apply(self, change: RoutineChange) -> BatchView:
        """Apply one routine change without producing an execution result."""

        with _locked(self._lock_path):
            current = self._reload_for_write()
            updated = _apply_change(self._repo_root, current, change)
            _validate_state(updated, self._batch)
            if updated != current or not self._state_path.exists():
                _write_state(self._state_path, updated)
            self._state = updated
            self._projected_legacy = False
            return self.view

    def perform(self, action: Action) -> ActionOutcome:
        """Perform one action through its installed adapter and record its facts."""

        _validate_action(action)
        with _locked(self._lock_path):
            state = self._reload_for_write()
            if not state["definition"]:
                raise ConsequenceBlocked("Batch must be defined before an action can run")
            if state["current"]["status"] in FINAL_STATUSES:
                raise ConsequenceBlocked(
                    "Batch is concluded; apply an explicit same-result revision before continuing"
                )
            operation = self._operations.get(action.operation)
            if operation is None:
                raise ConsequenceBlocked(
                    f"no operation adapter is installed for {action.operation!r}"
                )

            measurement_definition = _measurement_definition_for_action(state, action)
            _validate_action_against_state(
                self._repo_root,
                state,
                action,
                operation.protected_consequences,
            )
            _validate_single_use_contract(
                measurement_definition,
                action,
                operation.protected_consequences,
            )
            _verify_resources(state, action.requested_resources)
            if measurement_definition is not None:
                _verify_measurement_resources(
                    state,
                    measurement_definition,
                    action.requested_resources,
                )
            self._verify_governance(
                state,
                action,
                operation.protected_consequences,
            )
            _verify_repeat(
                state,
                action,
                measurement_definition,
                operation.protected_consequences,
            )

            needs_attempt = bool(
                measurement_definition
                or action.possible_consequences
                or action.requested_resources
            )
            attempt_number: int | None = None
            if needs_attempt:
                unresolved = [
                    item
                    for item in state["attempts"]
                    if item["status"] in {"running", "uncertain"}
                ]
                if unresolved:
                    raise ConsequenceUncertain(
                        "a prior Attempt is unresolved; reconcile it before another affected action"
                    )
                attempt_number = len(state["attempts"]) + 1
                state["attempts"].append(
                    _started_attempt(
                        attempt_number,
                        action,
                        state["current"].get("checks", {}),
                        measurement_definition,
                    )
                )
                _write_state(self._state_path, state)
                self._state = copy.deepcopy(state)

            context = {
                "batch": self._batch,
                "attempt": attempt_number,
                "candidate": _candidate_dict(action.candidate),
                "measurement_definition": copy.deepcopy(
                    dict(measurement_definition)
                    if measurement_definition is not None
                    else None
                ),
                "remaining_resources": _remaining_resources(state),
            }
            try:
                result = operation.run(action, context)
                if not isinstance(result, OperationResult):
                    raise TypeError("operation adapter must return OperationResult")
            except Exception as exc:
                if attempt_number is not None:
                    state = _read_state(self._state_path)
                    attempt = state["attempts"][attempt_number - 1]
                    attempt["status"] = "uncertain"
                    attempt["recovery_condition"] = (
                        "Establish whether the operation produced a result, resource use, or "
                        "Consequence before retrying."
                    )
                    attempt["adapter_error"] = f"{type(exc).__name__}: {exc}"
                    _write_state(self._state_path, state)
                    self._state = state
                raise ConsequenceUncertain(
                    "the operation adapter failed after execution could have begun"
                ) from exc

            try:
                violations = _operation_violations(action, result)
            except (BatchError, TypeError, ValueError, AttributeError) as exc:
                state = (
                    _read_state(self._state_path)
                    if attempt_number is not None
                    else state
                )
                if attempt_number is None:
                    attempt_number = len(state["attempts"]) + 1
                    state["attempts"].append(
                        _started_attempt(
                            attempt_number,
                            action,
                            state["current"].get("checks", {}),
                            measurement_definition,
                        )
                    )
                _mark_attempt_uncertain(
                    state,
                    attempt_number,
                    f"Operation result could not be interpreted: {exc}",
                )
                _write_state(self._state_path, state)
                self._state = state
                raise OperationContractViolation(str(exc)) from exc

            state = _read_state(self._state_path) if attempt_number is not None else state
            if attempt_number is None and (result.consequences or result.resource_use):
                attempt_number = len(state["attempts"]) + 1
                state["attempts"].append(
                    _started_attempt(
                        attempt_number,
                        action,
                        state["current"].get("checks", {}),
                        measurement_definition,
                    )
                )
                violations.append(
                    "operation produced an effect that required an undeclared Attempt"
                )
            if result.status not in OPERATION_STATUSES:
                if attempt_number is None:
                    attempt_number = len(state["attempts"]) + 1
                    state["attempts"].append(
                        _started_attempt(
                            attempt_number,
                            action,
                            state["current"].get("checks", {}),
                            measurement_definition,
                        )
                    )
                _mark_attempt_uncertain(
                    state,
                    attempt_number,
                    "Operation adapter returned an unsupported status.",
                )
                state["attempts"][attempt_number - 1]["contract_violations"] = violations
                _write_state(self._state_path, state)
                self._state = state
                raise OperationContractViolation("; ".join(violations))
            recorded_state = copy.deepcopy(state)
            try:
                _record_operation_result(
                    recorded_state,
                    action,
                    attempt_number,
                    result,
                )
            except (BatchError, TypeError, ValueError, AttributeError) as exc:
                if attempt_number is None:
                    attempt_number = len(state["attempts"]) + 1
                    state["attempts"].append(
                        _started_attempt(
                            attempt_number,
                            action,
                            state["current"].get("checks", {}),
                            measurement_definition,
                        )
                    )
                _mark_attempt_uncertain(
                    state,
                    attempt_number,
                    f"Operation result could not be recorded: {exc}",
                )
                _write_state(self._state_path, state)
                self._state = state
                raise OperationContractViolation(str(exc)) from exc
            state = recorded_state
            if violations and attempt_number is not None:
                state["attempts"][attempt_number - 1]["contract_violations"] = violations
            _write_state(self._state_path, state)
            self._state = state

            if result.status == "uncertain":
                raise ConsequenceUncertain(
                    result.recovery_condition
                    or "establish the affected result and Consequences before retrying"
                )
            if violations:
                raise OperationContractViolation("; ".join(violations))
            return ActionOutcome(self.view, attempt_number, result)

    def _reload_for_write(self) -> dict[str, Any]:
        if self._state_path.exists():
            state = _read_state(self._state_path)
        else:
            state = copy.deepcopy(self._state)
        _validate_state(state, self._batch)
        return state

    def _verify_governance(
        self,
        state: dict[str, Any],
        action: Action,
        adapter_consequences: tuple[str, ...],
    ) -> None:
        protected = (
            set(action.possible_consequences) | set(adapter_consequences)
        ) & PERMISSION_REQUIRED_CONSEQUENCES
        measurement_definition = state["current"].get("measurement_definition")
        if (
            action.kind == "measurement"
            and isinstance(measurement_definition, Mapping)
            and measurement_definition.get("resource_owner") == "user"
            and "single_use_consumption"
            in (set(action.possible_consequences) | set(adapter_consequences))
        ):
            protected.add("single_use_consumption")
        if protected and not action.required_permissions:
            raise ConsequenceBlocked(
                "protected Consequences require an applicable Permission before execution: "
                + ", ".join(sorted(protected))
            )
        if not action.required_reviews and not action.required_permissions:
            return
        if self._governance is None:
            raise ConsequenceBlocked(
                "this action requires Review or Permission facts, "
                "but no owner resolver is installed"
            )
        reviews = _references_by_handle(state["references"]["reviews"])
        permissions = _references_by_handle(state["references"]["permissions"])
        for handle in action.required_reviews:
            reference = reviews.get(handle)
            if reference is None:
                raise ConsequenceBlocked(
                    f"required Review {handle} is not referenced by this Batch"
                )
            assessment = self._governance.review(reference, action)
            if not assessment.applies:
                raise ConsequenceBlocked(
                    assessment.reason or f"Review {handle} does not apply to this action"
                )
        permission_limits: list[Mapping[str, float | int]] = []
        permitted_consequences: set[str] = set()
        for handle in action.required_permissions:
            reference = permissions.get(handle)
            if reference is None:
                raise ConsequenceBlocked(
                    f"required Permission {handle} is not referenced by this Batch"
                )
            assessment = self._governance.permission(
                reference,
                action,
                _capacity_consumption(state),
            )
            if not assessment.allows:
                raise ConsequenceBlocked(
                    assessment.reason or f"Permission {handle} does not allow this action"
                )
            permission_limits.append(assessment.resource_limits)
            _validate_consequence_kinds(assessment.permitted_consequences)
            permitted_consequences.update(assessment.permitted_consequences)
        uncovered = protected - permitted_consequences
        if uncovered:
            raise ConsequenceBlocked(
                "referenced Permissions do not cover protected Consequences: "
                + ", ".join(sorted(uncovered))
            )
        for limits in permission_limits:
            _verify_requested_within_permission_limits(
                actual=_capacity_consumption(state),
                requested=action.requested_resources,
                limits=limits,
            )


def _empty_state(batch: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "batch": batch,
        "definition": {},
        "references": {"reviews": [], "permissions": []},
        "current": {
            "status": "draft",
            "candidate_revision": None,
            "measurement_definition": None,
            "checks": {},
            "observations": {},
            "conclusion": None,
        },
        "resource_limits": {},
        "consumption": {},
        "attempts": [],
    }


def _read_state(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise BatchFormatError(f"cannot read Batch state: {path}") from exc
    if not isinstance(loaded, dict):
        raise BatchFormatError("Batch state must contain a mapping")
    return loaded


def _write_state(path: Path, state: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(
        copy.deepcopy(dict(state)),
        sort_keys=False,
        allow_unicode=True,
    ).encode("utf-8")
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=path.name + ".",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary = stream.name
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        from frontier_context import refresh_active_work
        refresh_active_work(path)
    except OSError as exc:
        raise StorageConflict(f"cannot update Batch state: {path}") from exc
    finally:
        if temporary is not None:
            try:
                Path(temporary).unlink()
            except FileNotFoundError:
                pass


class _locked:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._stream: Any = None

    def __enter__(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self._path.open("a+b")
        try:
            fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX)
        except OSError as exc:
            self._stream.close()
            raise StorageConflict(f"cannot lock Batch state: {self._path}") from exc

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        assert self._stream is not None
        fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
        self._stream.close()


def _apply_change(
    repo_root: Path,
    state: dict[str, Any],
    change: RoutineChange,
) -> dict[str, Any]:
    updated = copy.deepcopy(state)
    if isinstance(change, AdoptReview):
        from frontier_references import prepare_review_reference

        _require_text(change.rationale, "rationale")
        saved = prepare_review_reference(repo_root, change.revision, change.path, change.handle)
        selected = GitReference(**saved["reference"])
        reviews = _references_by_handle(updated["references"]["reviews"])
        if reviews.get(selected.handle) == selected:
            return updated
        reviews[selected.handle] = selected
        return _apply_change(repo_root, updated, ReviseBatch(
            rationale=change.rationale, reviews=tuple(reviews.values()),
        ))

    if isinstance(change, UpdateWorkingState):
        from frontier_references import resolve_revision

        _require_text(change.rationale, "rationale")
        if (change.revision is None) != (change.paths is None):
            raise BatchFormatError("revision and paths must be supplied together")
        if change.revision is not None:
            updated = _apply_change(repo_root, updated, SelectCandidate(
                CandidateRevision(resolve_revision(repo_root, change.revision), change.paths),
                change.rationale,
            ))
        limits = None
        if change.resource_limits is not None:
            limits = dict(updated["resource_limits"])
            limits.update(_resource_mapping(change.resource_limits, "resource limit updates"))
        measurement = None
        if change.measurement_updates is not None:
            measurement = _merge_working_fields(
                updated["current"]["measurement_definition"] or {}, change.measurement_updates,
            )
        revised = _apply_change(repo_root, updated, ReviseBatch(
            rationale=change.rationale, resource_limits=limits, measurement_definition=measurement,
        ))
        # A replay of an effective delta is a no-op, including its rationale.
        if "revision_rationale" in state["current"]:
            revised["current"]["revision_rationale"] = state["current"]["revision_rationale"]
        else:
            revised["current"].pop("revision_rationale", None)
        if revised == state:
            return copy.deepcopy(state)
        revised["current"]["revision_rationale"] = change.rationale
        return revised

    if isinstance(change, DefineBatch):
        if updated["definition"]:
            raise ChangeRejected("Batch is already defined; use ReviseBatch")
        _require_text(change.objective, "objective")
        _require_text(change.acceptance, "acceptance")
        _require_text_tuple(change.scope, "scope")
        _validate_consequence_kinds(change.expected_consequences)
        updated["definition"] = {
            "objective": change.objective,
            "acceptance": change.acceptance,
            "scope": list(change.scope),
            "expected_consequences": list(change.expected_consequences),
        }
        updated["references"] = {
            "reviews": [_reference_dict(value) for value in change.reviews],
            "permissions": [_reference_dict(value) for value in change.permissions],
        }
        _validate_reference_list(repo_root, change.reviews, "Review")
        _validate_reference_list(repo_root, change.permissions, "Permission")
        updated["resource_limits"] = _resource_mapping(change.resource_limits, "resource_limits")
        updated["current"]["status"] = "open"
        return updated

    if not updated["definition"]:
        raise ChangeRejected("Batch must be defined before routine changes")

    if isinstance(change, ReviseBatch):
        _require_text(change.rationale, "rationale")
        if updated["current"]["status"] in FINAL_STATUSES and not change.reopen:
            raise ChangeRejected(
                "a concluded Batch requires reopen=True for same-result continuation"
            )
        if change.objective is not None:
            _require_text(change.objective, "objective")
            updated["definition"]["objective"] = change.objective
        if change.acceptance is not None:
            _require_text(change.acceptance, "acceptance")
            updated["definition"]["acceptance"] = change.acceptance
        if change.scope is not None:
            _require_text_tuple(change.scope, "scope")
            updated["definition"]["scope"] = list(change.scope)
        if change.expected_consequences is not None:
            _validate_consequence_kinds(change.expected_consequences)
            updated["definition"]["expected_consequences"] = list(
                change.expected_consequences
            )
        if change.reviews is not None:
            _validate_reference_list(repo_root, change.reviews, "Review")
            updated["references"]["reviews"] = [
                _reference_dict(value) for value in change.reviews
            ]
        if change.permissions is not None:
            _validate_reference_list(repo_root, change.permissions, "Permission")
            updated["references"]["permissions"] = [
                _reference_dict(value) for value in change.permissions
            ]
        if change.resource_limits is not None:
            limits = _resource_mapping(change.resource_limits, "resource_limits")
            for key, consumed in _capacity_consumption(updated).items():
                if key in limits and limits[key] < consumed:
                    raise ChangeRejected(
                        f"resource limit {key!r} cannot fall below recorded capacity use"
                    )
            updated["resource_limits"] = limits
        if change.measurement_definition is not None:
            normalized_definition = _normalize_measurement_definition(
                change.measurement_definition
            )
            _validate_measurement_definition(
                normalized_definition,
                require_resource_ceiling=True,
            )
            ceiling = _measurement_resource_ceiling(normalized_definition)
            for key, consumed in _measurement_capacity_consumption(updated).items():
                if key in ceiling and ceiling[key] < consumed:
                    raise ChangeRejected(
                        f"measurement resource ceiling {key!r} cannot fall below "
                        "recorded measurement capacity use"
                    )
            updated["current"]["measurement_definition"] = copy.deepcopy(
                normalized_definition
            )
        if change.reopen:
            updated["current"]["status"] = "open"
            updated["current"]["conclusion"] = None
        updated["current"]["revision_rationale"] = change.rationale
        return updated

    if isinstance(change, SelectCandidate):
        _require_text(change.rationale, "rationale")
        _validate_candidate(repo_root, change.candidate)
        if updated["current"]["candidate_revision"] == _candidate_dict(change.candidate):
            return updated
        updated["current"]["candidate_revision"] = _candidate_dict(change.candidate)
        updated["current"]["checks"] = {}
        updated["current"]["candidate_rationale"] = change.rationale
        return updated

    if isinstance(change, RecordCheck):
        _require_key(change.key, "check key")
        if change.outcome not in {"passed", "failed", "blocked"}:
            raise BatchFormatError("check outcome must be passed, failed, or blocked")
        _validate_candidate(repo_root, change.candidate)
        _require_current_candidate(updated, change.candidate)
        updated["current"]["checks"][change.key] = {
            "candidate_revision": _candidate_dict(change.candidate),
            "outcome": change.outcome,
            "evidence": copy.deepcopy(dict(change.evidence)),
        }
        return updated

    if isinstance(change, RecordObservation):
        _require_key(change.key, "observation key")
        if change.candidate is not None:
            _validate_candidate(repo_root, change.candidate)
            _require_current_candidate(updated, change.candidate)
        updated["current"]["observations"][change.key] = {
            "candidate_revision": _candidate_dict(change.candidate),
            "observation": copy.deepcopy(dict(change.observation)),
        }
        return updated

    if isinstance(change, ReconcileAttempt):
        _require_text(change.rationale, "rationale")
        if isinstance(change.attempt, bool) or not isinstance(change.attempt, int):
            raise BatchFormatError("Attempt number must be an integer")
        if change.attempt < 1 or change.attempt > len(updated["attempts"]):
            raise BatchFormatError("Attempt number is unavailable")
        if change.status not in {"completed", "failed"}:
            raise BatchFormatError("reconciled Attempt status must be completed or failed")
        attempt = updated["attempts"][change.attempt - 1]
        if attempt["status"] not in {"running", "uncertain"}:
            raise ChangeRejected("only a running or uncertain Attempt can be reconciled")
        resource_use = _resource_mapping(change.resource_use, "reconciled resource_use")
        resource_bounds = _resource_bounds(
            change.resource_bounds,
            "reconciled resource_bounds",
        )
        capacity_charge = _resource_mapping(
            change.capacity_charge,
            "reconciled capacity_charge",
        )
        _validate_ranged_resource_facts(
            resource_use=resource_use,
            resource_bounds=resource_bounds,
            capacity_charge=capacity_charge,
            name="reconciled resources",
        )
        if resource_bounds and change.status != "failed":
            raise BatchFormatError(
                "unknown exact resource use may only reconcile a failed Attempt"
            )
        previous_use = _resource_mapping(attempt.get("resource_use", {}), "prior resource_use")
        for key in set(previous_use) | set(resource_use):
            revised = (
                updated["consumption"].get(key, 0)
                - previous_use.get(key, 0)
                + resource_use.get(key, 0)
            )
            if revised < 0:
                raise BatchFormatError("reconciled consumption cannot be negative")
            if revised == 0 and key not in resource_use:
                updated["consumption"].pop(key, None)
            else:
                updated["consumption"][key] = revised
        for consequence in change.consequences:
            _validate_consequence(consequence)
        attempt["status"] = change.status
        attempt["observations"] = [
            copy.deepcopy(dict(value)) for value in change.observations
        ]
        attempt["actual_consequences"] = [
            _consequence_dict(value) for value in change.consequences
        ]
        attempt["resource_use"] = resource_use
        if resource_bounds:
            attempt["resource_bounds"] = resource_bounds
            attempt["capacity_charge"] = capacity_charge
        else:
            attempt.pop("resource_bounds", None)
            attempt.pop("capacity_charge", None)
        attempt["result"] = copy.deepcopy(dict(change.result))
        attempt["recovery_condition"] = change.recovery_condition
        attempt["reconciliation"] = {"rationale": change.rationale}
        return updated

    if isinstance(change, ConcludeBatch):
        if change.status not in FINAL_STATUSES:
            raise BatchFormatError("Batch conclusion must be completed or stopped")
        _require_text(change.remaining_gap, "remaining_gap")
        unresolved = [
            item for item in updated["attempts"] if item["status"] in {"running", "uncertain"}
        ]
        if unresolved:
            raise ChangeRejected("an unresolved Attempt prevents Batch conclusion")
        updated["current"]["status"] = change.status
        updated["current"]["conclusion"] = {
            "result": copy.deepcopy(dict(change.result)),
            "remaining_gap": change.remaining_gap,
        }
        return updated

    raise BatchFormatError(f"unsupported routine change: {type(change).__name__}")


def _validate_state(state: Mapping[str, Any], expected_batch: str) -> None:
    required = {
        "contract_version",
        "batch",
        "definition",
        "references",
        "current",
        "resource_limits",
        "consumption",
        "attempts",
    }
    if set(state) != required:
        raise BatchFormatError("current Batch state has an invalid top-level shape")
    if state["contract_version"] != CONTRACT_VERSION:
        raise BatchFormatError("current Batch contract version is unsupported")
    if state["batch"] != expected_batch:
        raise BatchFormatError("Batch state belongs to another Batch")
    if not isinstance(state["definition"], dict):
        raise BatchFormatError("Batch definition must be a mapping")
    if state["definition"]:
        for key in ("objective", "acceptance"):
            _require_text(state["definition"].get(key), f"definition.{key}")
        scope = state["definition"].get("scope")
        if not isinstance(scope, list) or not scope or not all(
            isinstance(item, str) and item.strip() for item in scope
        ):
            raise BatchFormatError("definition.scope must contain nonempty strings")
        consequences = state["definition"].get("expected_consequences")
        if not isinstance(consequences, list):
            raise BatchFormatError("definition.expected_consequences must be a list")
        _validate_consequence_kinds(tuple(consequences))
    references = state["references"]
    if not isinstance(references, dict) or set(references) != {"reviews", "permissions"}:
        raise BatchFormatError("Batch references have an invalid shape")
    if not all(isinstance(references[key], list) for key in references):
        raise BatchFormatError("Batch reference collections must be lists")
    current = state["current"]
    current_fields = {
        "status",
        "candidate_revision",
        "measurement_definition",
        "checks",
        "observations",
        "conclusion",
    }
    optional_current = {"revision_rationale", "candidate_rationale"}
    if not isinstance(current, dict) or not current_fields <= set(current):
        raise BatchFormatError("Batch current state is incomplete")
    if set(current) - current_fields - optional_current:
        raise BatchFormatError("Batch current state contains unknown fields")
    if current["status"] not in {"draft", "open", *FINAL_STATUSES}:
        raise BatchFormatError("Batch status is invalid")
    _validate_measurement_definition(current["measurement_definition"])
    if not isinstance(current["checks"], dict) or not isinstance(current["observations"], dict):
        raise BatchFormatError("Batch checks and observations must be mappings")
    resource_limits = _resource_mapping(state["resource_limits"], "resource_limits")
    _resource_mapping(state["consumption"], "consumption")
    attempts = state["attempts"]
    if not isinstance(attempts, list):
        raise BatchFormatError("Batch attempts must be a list")
    unresolved = 0
    summed_consumption: dict[str, float | int] = {}
    for index, attempt in enumerate(attempts, start=1):
        if not isinstance(attempt, dict) or attempt.get("attempt") != index:
            raise BatchFormatError("Batch Attempts must use a contiguous local sequence")
        if attempt.get("status") not in {"running", *OPERATION_STATUSES}:
            raise BatchFormatError("Batch Attempt status is invalid")
        if attempt["status"] in {"running", "uncertain"}:
            unresolved += 1
        resource_use = _resource_mapping(
            attempt.get("resource_use", {}),
            f"Attempt {index} resource_use",
        )
        resource_bounds = _resource_bounds(
            attempt.get("resource_bounds", {}),
            f"Attempt {index} resource_bounds",
        )
        capacity_charge = _resource_mapping(
            attempt.get("capacity_charge", {}),
            f"Attempt {index} capacity_charge",
        )
        _validate_ranged_resource_facts(
            resource_use=resource_use,
            resource_bounds=resource_bounds,
            capacity_charge=capacity_charge,
            name=f"Attempt {index} resources",
        )
        if resource_bounds:
            if attempt["status"] != "failed":
                raise BatchFormatError(
                    "unknown exact resource use requires a failed Attempt"
                )
            reconciliation = attempt.get("reconciliation")
            if not isinstance(reconciliation, Mapping):
                raise BatchFormatError(
                    "unknown exact resource use requires reconciliation facts"
                )
            _require_text(
                reconciliation.get("rationale"),
                f"Attempt {index} reconciliation rationale",
            )
        for key, amount in resource_use.items():
            summed_consumption[key] = summed_consumption.get(key, 0) + amount
    if unresolved > 1:
        raise BatchFormatError("only one current Attempt may be unresolved")
    if current["status"] in FINAL_STATUSES and unresolved:
        raise BatchFormatError("a concluded Batch cannot contain an unresolved Attempt")
    if _resource_mapping(state["consumption"], "consumption") != summed_consumption:
        raise BatchFormatError("Batch consumption must equal the sum of Attempt resource use")
    for key, amount in _capacity_consumption(state).items():
        if key in resource_limits and amount > resource_limits[key]:
            raise BatchFormatError(
                f"Batch capacity use for resource {key!r} exceeds its limit"
            )


def _validate_action(action: Action) -> None:
    _require_key(action.key, "action key")
    _require_key(action.operation, "operation adapter key")
    _require_key(action.kind, "action kind")
    _require_text_tuple(action.required_reviews, "required_reviews", allow_empty=True)
    _require_text_tuple(action.required_permissions, "required_permissions", allow_empty=True)
    _require_text_tuple(action.required_checks, "required_checks", allow_empty=True)
    _validate_consequence_kinds(action.possible_consequences)
    _resource_mapping(action.requested_resources, "requested_resources")


def _validate_action_against_state(
    repo_root: Path,
    state: Mapping[str, Any],
    action: Action,
    adapter_consequences: tuple[str, ...],
) -> None:
    if action.candidate is not None:
        _validate_candidate(repo_root, action.candidate)
        _require_current_candidate(state, action.candidate)
    elif action.required_checks:
        raise ConsequenceBlocked("an action with required checks needs a Candidate Revision")
    for key in action.required_checks:
        check = state["current"]["checks"].get(key)
        if not isinstance(check, dict) or check.get("outcome") != "passed":
            raise ConsequenceBlocked(f"required check {key!r} has not passed")
        if check.get("candidate_revision") != _candidate_dict(action.candidate):
            raise ConsequenceBlocked(f"required check {key!r} belongs to another revision")
    expected = set(state["definition"].get("expected_consequences", []))
    fixed = set(adapter_consequences)
    missing = fixed - set(action.possible_consequences)
    if missing:
        raise ConsequenceBlocked(
            "the installed adapter requires undeclared Consequences: "
            + ", ".join(sorted(missing))
        )
    undeclared = (set(action.possible_consequences) | fixed) - expected
    if undeclared:
        raise ConsequenceBlocked(
            "action could produce Consequences outside the Batch definition: "
            + ", ".join(sorted(undeclared))
        )


def _measurement_definition_for_action(
    state: Mapping[str, Any], action: Action
) -> Mapping[str, Any] | None:
    if action.kind != "measurement":
        return None
    definition = state["current"].get("measurement_definition")
    if not isinstance(definition, Mapping) or not definition:
        raise ConsequenceBlocked(
            "a measurement action requires the Batch-owned Measurement Definition"
        )
    return definition


def _verify_resources(state: Mapping[str, Any], requested: Mapping[str, float | int]) -> None:
    _verify_requested_within_limits(
        actual=_capacity_consumption(state),
        requested=requested,
        limits=state["resource_limits"],
        source="Batch",
    )


def _verify_measurement_resources(
    state: Mapping[str, Any],
    definition: Mapping[str, Any],
    requested: Mapping[str, float | int],
) -> None:
    try:
        ceiling = _measurement_resource_ceiling(definition)
    except BatchFormatError as exc:
        raise ConsequenceBlocked(
            "the current Measurement Definition must define a valid resource_ceiling"
        ) from exc
    actual = _measurement_capacity_consumption(state)
    normalized_requested = _resource_mapping(requested, "requested_resources")
    for key, limit in ceiling.items():
        if actual.get(key, 0) + normalized_requested.get(key, 0) > limit:
            raise ConsequenceBlocked(
                f"Measurement Definition resource ceiling {key!r} would be exceeded"
            )


def _verify_requested_within_limits(
    *,
    actual: Mapping[str, float | int],
    requested: Mapping[str, float | int],
    limits: Mapping[str, float | int],
    source: str,
) -> None:
    normalized = _resource_mapping(limits, f"{source} limits")
    for key, amount in _resource_mapping(requested, "requested_resources").items():
        if key not in normalized:
            raise ConsequenceBlocked(f"{source} does not define a limit for resource {key!r}")
        if actual.get(key, 0) + amount > normalized[key]:
            raise ConsequenceBlocked(f"{source} resource limit {key!r} would be exceeded")


def _verify_requested_within_permission_limits(
    *,
    actual: Mapping[str, float | int],
    requested: Mapping[str, float | int],
    limits: Mapping[str, float | int],
) -> None:
    normalized_limits = _resource_mapping(limits, "Permission limits")
    normalized_requested = _resource_mapping(requested, "requested_resources")
    for key in set(normalized_limits) & set(normalized_requested):
        if actual.get(key, 0) + normalized_requested[key] > normalized_limits[key]:
            raise ConsequenceBlocked(
                f"Permission resource limit {key!r} would be exceeded"
            )


def _verify_repeat(
    state: Mapping[str, Any],
    action: Action,
    measurement_definition: Mapping[str, Any] | None,
    adapter_consequences: tuple[str, ...],
) -> None:
    single_use_declared = "single_use_consumption" in (
        set(action.possible_consequences) | set(adapter_consequences)
    )
    current_unit = (
        _measurement_nonrepeatable_unit(measurement_definition)
        if single_use_declared
        else None
    )
    if current_unit is not None:
        for attempt in state["attempts"]:
            prior_definition = attempt.get("measurement_definition")
            if not isinstance(prior_definition, Mapping):
                continue
            if _measurement_nonrepeatable_unit(prior_definition) != current_unit:
                continue
            if attempt.get("status") in {"running", "uncertain"}:
                raise ConsequenceUncertain(
                    f"single-use unit {current_unit!r} has an unresolved prior Attempt"
                )
            if any(
                consequence.get("kind") == "single_use_consumption"
                for consequence in attempt.get("actual_consequences", ())
                if isinstance(consequence, Mapping)
            ):
                raise ConsequenceBlocked(
                    f"single-use unit {current_unit!r} was already consumed"
                )
    if action.repeatable:
        return
    for attempt in state["attempts"]:
        if attempt.get("action", {}).get("key") != action.key:
            continue
        if attempt.get("status") in {"running", "uncertain"}:
            raise ConsequenceUncertain(
                f"action {action.key!r} has an unresolved prior Attempt"
            )
        if attempt.get("status") == "completed":
            raise ConsequenceBlocked(
                f"action {action.key!r} already completed and is not repeatable"
            )


def _started_attempt(
    number: int,
    action: Action,
    current_checks: Mapping[str, Any],
    measurement_definition: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return {
        "attempt": number,
        "status": "running",
        "action": _action_dict(action),
        "measurement_definition": copy.deepcopy(
            dict(measurement_definition)
            if measurement_definition is not None
            else None
        ),
        "candidate_revision": _candidate_dict(action.candidate),
        "checks": {
            key: copy.deepcopy(current_checks[key])
            for key in action.required_checks
        },
        "observations": [],
        "actual_consequences": [],
        "resource_use": {},
        "result": {},
        "recovery_condition": None,
    }


def _mark_attempt_uncertain(
    state: dict[str, Any],
    attempt_number: int,
    reason: str,
) -> None:
    attempt = state["attempts"][attempt_number - 1]
    attempt["status"] = "uncertain"
    attempt["recovery_condition"] = (
        "Establish the actual result, resource use, and Consequences, then reconcile "
        "this Attempt before retrying."
    )
    attempt["adapter_error"] = reason


def _record_operation_result(
    state: dict[str, Any],
    action: Action,
    attempt_number: int | None,
    result: OperationResult,
) -> None:
    if result.status not in OPERATION_STATUSES:
        raise BatchFormatError("operation result status is invalid")
    resource_use = _resource_mapping(result.resource_use, "operation resource_use")
    for key, amount in resource_use.items():
        state["consumption"][key] = state["consumption"].get(key, 0) + amount
    consequence_values = [_consequence_dict(value) for value in result.consequences]
    if attempt_number is not None:
        attempt = state["attempts"][attempt_number - 1]
        attempt["status"] = result.status
        attempt["observations"] = [copy.deepcopy(dict(value)) for value in result.observations]
        attempt["actual_consequences"] = consequence_values
        attempt["resource_use"] = resource_use
        attempt["result"] = copy.deepcopy(dict(result.result))
        attempt["recovery_condition"] = result.recovery_condition
    else:
        state["current"]["observations"][f"action:{action.key}"] = {
            "candidate_revision": _candidate_dict(action.candidate),
            "observation": {
                "status": result.status,
                "observations": [copy.deepcopy(dict(value)) for value in result.observations],
                "result": copy.deepcopy(dict(result.result)),
            },
        }


def _operation_violations(action: Action, result: OperationResult) -> list[str]:
    violations: list[str] = []
    if result.status not in OPERATION_STATUSES:
        violations.append("operation returned an unsupported status")
    possible = set(action.possible_consequences)
    actual_kinds: set[str] = set()
    for consequence in result.consequences:
        try:
            _validate_consequence(consequence)
        except BatchFormatError as exc:
            violations.append(str(exc))
        actual_kinds.add(consequence.kind)
    unexpected = actual_kinds - possible
    if unexpected:
        violations.append(
            "operation produced undeclared Consequences: "
            + ", ".join(sorted(unexpected))
        )
    requested = _resource_mapping(action.requested_resources, "requested_resources")
    actual = _resource_mapping(result.resource_use, "operation resource_use")
    for key, amount in actual.items():
        if key not in requested or amount > requested[key]:
            violations.append(f"operation exceeded declared resource use for {key!r}")
    return violations


def _merge_working_fields(current: Mapping[str, Any], updates: Mapping[str, Any]) -> dict:
    """Merge supplied fields only; lists and scalar values replace the named field."""
    if not isinstance(updates, Mapping):
        raise BatchFormatError("measurement updates must be a mapping")
    result = copy.deepcopy(dict(current))
    for key, value in updates.items():
        if not isinstance(key, str) or not key:
            raise BatchFormatError("measurement update keys must be nonempty strings")
        if isinstance(value, Mapping):
            previous = result.get(key)
            result[key] = _merge_working_fields(previous if isinstance(previous, Mapping) else {}, value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def batch_facts(view: BatchView) -> dict[str, Any]:
    """Render Batch-owned facts only, never Campaign accounting or inferred charges."""
    state = view._record
    return copy.deepcopy({
        "batch": state["batch"],
        "status": state["current"]["status"],
        "candidate_revision": state["current"]["candidate_revision"],
        "reviews": state["references"]["reviews"],
        "resource_limits": state["resource_limits"],
        "attempt_consumption": state["consumption"],
        "remaining_capacity": view.remaining_capacity,
        "unresolved_attempts": [
            item["attempt"] for item in state["attempts"]
            if item["status"] in {"running", "uncertain"}
        ],
    })


def _remaining_resources(state: Mapping[str, Any]) -> dict[str, float | int]:
    capacity_consumption = _capacity_consumption(state)
    return {
        key: limit - capacity_consumption.get(key, 0)
        for key, limit in state["resource_limits"].items()
    }


def _validate_candidate(repo_root: Path, candidate: CandidateRevision) -> None:
    try:
        validate_selection(repo_root, candidate.commit, candidate.paths)
    except SavedGitError as exc:
        raise BatchFormatError(str(exc)) from exc


def _validate_reference_list(
    repo_root: Path,
    values: tuple[GitReference, ...],
    owner: str,
) -> None:
    seen: set[str] = set()
    for value in values:
        _require_key(value.handle, f"{owner} handle")
        if value.handle in seen:
            raise BatchFormatError(f"duplicate {owner} handle: {value.handle}")
        seen.add(value.handle)
        _validate_candidate(repo_root, CandidateRevision(value.commit, (value.path,)))


def _require_current_candidate(state: Mapping[str, Any], candidate: CandidateRevision) -> None:
    if state["current"].get("candidate_revision") != _candidate_dict(candidate):
        raise ConsequenceBlocked("the Candidate Revision is not the current selected revision")


def _references_by_handle(values: list[Mapping[str, Any]]) -> dict[str, GitReference]:
    return {
        str(value["handle"]): GitReference(
            str(value["handle"]),
            str(value["commit"]),
            str(value["path"]),
        )
        for value in values
    }


def _reference_dict(value: GitReference) -> dict[str, str]:
    return {"handle": value.handle, "commit": value.commit, "path": _repo_path(value.path)}


def _candidate_dict(value: CandidateRevision | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {"commit": value.commit, "paths": [_repo_path(path) for path in value.paths]}


def _action_dict(value: Action) -> dict[str, Any]:
    raw = asdict(value)
    raw["candidate"] = _candidate_dict(value.candidate)
    raw["required_reviews"] = list(value.required_reviews)
    raw["required_permissions"] = list(value.required_permissions)
    raw["required_checks"] = list(value.required_checks)
    raw["possible_consequences"] = list(value.possible_consequences)
    raw["requested_resources"] = dict(value.requested_resources)
    raw["details"] = copy.deepcopy(dict(value.details))
    return raw


def _operation_bindings(
    values: Mapping[str, OperationBinding],
) -> dict[str, OperationBinding]:
    normalized: dict[str, OperationBinding] = {}
    for key, binding in values.items():
        _require_key(key, "operation adapter key")
        if not isinstance(binding, OperationBinding) or not callable(binding.run):
            raise BatchFormatError(
                f"operation {key!r} must use an OperationBinding"
            )
        _validate_consequence_kinds(binding.protected_consequences)
        normalized[key] = binding
    return normalized


def _consequence_dict(value: Consequence) -> dict[str, Any]:
    return {
        "kind": value.kind,
        "amount": value.amount,
        "external_reference": value.external_reference,
        "idempotency_key": value.idempotency_key,
        "details": copy.deepcopy(dict(value.details)),
    }


def _validate_consequence(value: Consequence) -> None:
    if value.kind not in CONSEQUENCE_KINDS:
        raise BatchFormatError(f"unknown actual Consequence kind {value.kind!r}")
    _number(value.amount, "Consequence amount")


def _resource_mapping(value: Any, name: str) -> dict[str, float | int]:
    if not isinstance(value, Mapping):
        raise BatchFormatError(f"{name} must be a mapping")
    normalized: dict[str, float | int] = {}
    for key, amount in value.items():
        _require_key(key, f"{name} key")
        normalized[str(key)] = _number(amount, f"{name}.{key}")
    return normalized


def _resource_bounds(
    value: Any,
    name: str,
) -> dict[str, dict[str, float | int | str]]:
    if not isinstance(value, Mapping):
        raise BatchFormatError(f"{name} must be a mapping")
    normalized: dict[str, dict[str, float | int | str]] = {}
    for key, raw_bounds in value.items():
        _require_key(key, f"{name} key")
        if not isinstance(raw_bounds, Mapping) or set(raw_bounds) != {
            "minimum",
            "maximum",
            "exact",
        }:
            raise BatchFormatError(
                f"{name}.{key} must contain only minimum, maximum, and exact"
            )
        minimum = _number(raw_bounds["minimum"], f"{name}.{key}.minimum")
        maximum = _number(raw_bounds["maximum"], f"{name}.{key}.maximum")
        if minimum > maximum:
            raise BatchFormatError(f"{name}.{key} minimum cannot exceed maximum")
        if raw_bounds["exact"] != "unknown":
            raise BatchFormatError(f"{name}.{key}.exact must be 'unknown'")
        normalized[str(key)] = {
            "minimum": minimum,
            "maximum": maximum,
            "exact": "unknown",
        }
    return normalized


def _validate_ranged_resource_facts(
    *,
    resource_use: Mapping[str, float | int],
    resource_bounds: Mapping[str, Mapping[str, float | int | str]],
    capacity_charge: Mapping[str, float | int],
    name: str,
) -> None:
    overlap = set(resource_use) & set(resource_bounds)
    if overlap:
        raise BatchFormatError(
            f"{name} cannot record exact use and unknown bounds for the same resource: "
            + ", ".join(sorted(overlap))
        )
    if set(capacity_charge) != set(resource_bounds):
        raise BatchFormatError(
            f"{name} capacity_charge keys must exactly match resource_bounds"
        )
    for key, bounds in resource_bounds.items():
        if capacity_charge[key] != bounds["maximum"]:
            raise BatchFormatError(
                f"{name} capacity_charge.{key} must equal the conservative maximum"
            )


def _capacity_consumption(state: Mapping[str, Any]) -> dict[str, float | int]:
    """Return exact use plus conservative charges for exact-unknown resources."""

    total: dict[str, float | int] = {}
    for index, attempt in enumerate(state["attempts"], start=1):
        resource_use = _resource_mapping(
            attempt.get("resource_use", {}),
            f"Attempt {index} resource_use",
        )
        resource_bounds = _resource_bounds(
            attempt.get("resource_bounds", {}),
            f"Attempt {index} resource_bounds",
        )
        capacity_charge = _resource_mapping(
            attempt.get("capacity_charge", {}),
            f"Attempt {index} capacity_charge",
        )
        _validate_ranged_resource_facts(
            resource_use=resource_use,
            resource_bounds=resource_bounds,
            capacity_charge=capacity_charge,
            name=f"Attempt {index} resources",
        )
        for values in (resource_use, capacity_charge):
            for key, amount in values.items():
                total[key] = total.get(key, 0) + amount
    return total


def _measurement_capacity_consumption(
    state: Mapping[str, Any],
) -> dict[str, float | int]:
    """Return retained capacity use from measurement Attempts only."""

    measurement_state = {
        "attempts": [
            attempt
            for attempt in state["attempts"]
            if isinstance(attempt.get("measurement_definition"), Mapping)
        ]
    }
    return _capacity_consumption(measurement_state)


def _number(value: Any, name: str) -> float | int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BatchFormatError(f"{name} must be a nonnegative number")
    if not math.isfinite(value) or value < 0:
        raise BatchFormatError(f"{name} must be a nonnegative finite number")
    return value


def _repo_path(value: Any) -> str:
    try:
        return normalize_path(value)
    except SavedGitError as exc:
        raise BatchFormatError(str(exc)) from exc


def _require_text(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise BatchFormatError(f"{name} must be a nonempty string")


def _require_key(value: Any, name: str) -> None:
    _require_text(value, name)
    if any(character.isspace() for character in str(value)):
        raise BatchFormatError(f"{name} must not contain whitespace")


def _require_text_tuple(value: Any, name: str, *, allow_empty: bool = False) -> None:
    if not isinstance(value, tuple) or (not value and not allow_empty):
        raise BatchFormatError(f"{name} must be a {'possibly empty ' if allow_empty else ''}tuple")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise BatchFormatError(f"{name} values must be nonempty strings")
    if len(set(value)) != len(value):
        raise BatchFormatError(f"{name} values must be unique")


def _measurement_resource_ceiling(
    value: Mapping[str, Any],
) -> dict[str, float | int]:
    if "resource_ceiling" not in value:
        raise BatchFormatError("measurement_definition.resource_ceiling is required")
    return _resource_mapping(
        value["resource_ceiling"],
        "measurement_definition.resource_ceiling",
    )


def _measurement_nonrepeatable_unit(
    value: Mapping[str, Any] | None,
) -> str | None:
    """Read the current key and its historical alias without changing history."""

    if value is None:
        return None
    canonical_present = "nonrepeatable_unit" in value
    alias_present = "non_repeatable_unit" in value
    if not canonical_present and not alias_present:
        return None
    canonical = value.get("nonrepeatable_unit") if canonical_present else None
    alias = value.get("non_repeatable_unit") if alias_present else None
    if canonical_present:
        _require_text(canonical, "measurement_definition.nonrepeatable_unit")
    if alias_present:
        _require_text(alias, "measurement_definition.non_repeatable_unit")
    if canonical_present and alias_present and canonical != alias:
        raise BatchFormatError(
            "measurement_definition nonrepeatable_unit aliases disagree"
        )
    unit = str(canonical if canonical_present else alias)
    if unit.strip().lower() in {"none", "not applicable", "n/a"}:
        raise BatchFormatError(
            "omit the nonrepeatable unit when no real single-use unit exists"
        )
    return unit


def _normalize_measurement_definition(value: Mapping[str, Any]) -> dict[str, Any]:
    """Write the canonical unit key while accepting the historical alias."""

    if not isinstance(value, Mapping):
        raise BatchFormatError("measurement_definition must be a nonempty mapping")
    normalized = copy.deepcopy(dict(value))
    unit = _measurement_nonrepeatable_unit(normalized)
    normalized.pop("non_repeatable_unit", None)
    if unit is not None:
        normalized["nonrepeatable_unit"] = unit
    return normalized


def _validate_single_use_contract(
    measurement_definition: Mapping[str, Any] | None,
    action: Action,
    adapter_consequences: tuple[str, ...],
) -> None:
    """Require single-use controls only when the action can consume such a unit."""

    consequences = set(action.possible_consequences) | set(adapter_consequences)
    if "single_use_consumption" not in consequences:
        return
    if measurement_definition is None:
        raise ConsequenceBlocked(
            "single-use consumption requires a measurement Action and Measurement Definition"
        )
    try:
        if _measurement_nonrepeatable_unit(measurement_definition) is None:
            raise BatchFormatError(
                "measurement_definition.nonrepeatable_unit is required"
            )
        owner = measurement_definition.get("resource_owner")
        _require_text(owner, "measurement_definition.resource_owner")
        if owner not in {"workflow", "user"}:
            raise BatchFormatError(
                "measurement_definition.resource_owner must be workflow or user"
            )
        _require_text(
            measurement_definition.get("consumption_control"),
            "measurement_definition.consumption_control",
        )
    except BatchFormatError as exc:
        raise ConsequenceBlocked(str(exc)) from exc
    if action.repeatable:
        raise ConsequenceBlocked(
            "an Action that may consume a single-use unit must not be repeatable"
        )


def _validate_measurement_definition(
    value: Any,
    *,
    require_resource_ceiling: bool = False,
) -> None:
    """Validate the current measurement structure without interpreting its meaning."""

    if value is None:
        return
    if not isinstance(value, Mapping) or not value:
        raise BatchFormatError("measurement_definition must be a nonempty mapping")
    _measurement_nonrepeatable_unit(value)
    if require_resource_ceiling or "resource_ceiling" in value:
        _measurement_resource_ceiling(value)
    required = value.get("required_context_keys")
    if required is None:
        return
    if not isinstance(required, (list, tuple)):
        raise BatchFormatError("required_context_keys must be a list of nonempty strings")
    if not all(isinstance(item, str) and item.strip() for item in required):
        raise BatchFormatError("required_context_keys must contain nonempty strings")
    if len(set(required)) != len(required):
        raise BatchFormatError("required_context_keys must be unique")


def _validate_consequence_kinds(values: tuple[str, ...]) -> None:
    _require_text_tuple(values, "Consequence kinds", allow_empty=True)
    unknown = set(values) - CONSEQUENCE_KINDS
    if unknown:
        raise BatchFormatError(
            "unknown Consequence kinds: " + ", ".join(sorted(unknown))
        )


__all__ = [
    "Action",
    "ActionOutcome",
    "Batch",
    "BatchError",
    "BatchFormatError",
    "BatchView",
    "CandidateRevision",
    "ChangeRejected",
    "ConcludeBatch",
    "Consequence",
    "ConsequenceBlocked",
    "ConsequenceUncertain",
    "DefineBatch",
    "GitReference",
    "GovernanceResolver",
    "OperationAdapter",
    "OperationBinding",
    "OperationContractViolation",
    "OperationResult",
    "PermissionAssessment",
    "ReconcileAttempt",
    "RecordCheck",
    "RecordObservation",
    "ReviseBatch",
    "ReviewAssessment",
    "SelectCandidate",
    "StorageConflict",
]
