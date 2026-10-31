"""Prepare available professional resources and scoped, reusable input facts.

These functions establish content correspondence, never professional adequacy or
model delivery. A connected owner adapter supplies the latter relationship.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from context_delivery import digest, retain_source


@dataclass(frozen=True)
class OwnerReply:
    """A response returned by a trusted host integration, not a receipt flag.

    The local test adapter exercises this interface without any model service.
    A concrete external-model adapter is not installed by this module.
    """

    answer: dict
    response_id: str
    trace: dict
    supplied_sources: tuple[dict, ...] | None = None


class OwnerTransportError(RuntimeError):
    """A failed host call with retained evidence, never an adoptable answer."""

    def __init__(self, message: str, trace: dict):
        super().__init__(message)
        self.trace = trace


def identity(value) -> str:
    return digest(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False))


def selected_source(root: Path, ref: dict) -> dict:
    from frontier_references import _selected_text

    path = (root / ref["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("professional input source must remain inside the workspace")
    body = _selected_text(path.read_text(), ref)
    return {"source": ref, "sha256": digest(body), "contents": body,
            "retrieval": retain_source(root, body)}


def resource_view(root: Path, owner: str, locations=(), skill_roots=()) -> dict:
    """Read maintained entries and descriptors, independent of proposal citations.

    Follow direct instruction links, not a recursive history or marketplace scan.
    Full inventories stay reachable even if a host later focuses their display.
    """
    from frontier_references import _source_metadata

    root = root.resolve()
    entries, limits, seen = [], [], set()
    sources = ["AGENTS.md", owner, *locations]
    for name in sources[:]:
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            limits.append(f"Description source unavailable: {name}")
            continue
        try:
            text = path.read_text()
            meta = _source_metadata(text)
        except (OSError, UnicodeError, ValueError) as exc:
            limits.append(f"Description source unreadable: {name}: {exc}")
            continue
        configured = meta.get("professional_resources", [])
        if not isinstance(configured, list) or not all(isinstance(ref, str) for ref in configured):
            limits.append(f"Invalid professional resource locations in {name}; use a list of paths")
            configured = []
        for ref in configured:
            candidate = (path.parent / ref).resolve()
            if candidate.is_relative_to(root):
                sources.append(str(candidate.relative_to(root)))
            else:
                limits.append(f"Resource location outside the project: {ref}")
        if path.name == "AGENTS.md":
            for link in re.findall(r"\]\(([^)]+)\)", text):
                if "://" not in link and not link.startswith("#"):
                    candidate = (path.parent / link.split("#")[0]).resolve()
                    if candidate.is_relative_to(root):
                        sources.append(str(candidate.relative_to(root)))
                    else:
                        limits.append(f"Instruction link outside the project: {link}")
    for name in dict.fromkeys(sources):
        path = (root / name).resolve()
        if path in seen:
            continue
        seen.add(path)
        if not path.is_relative_to(root) or not path.is_file():
            limits.append(f"Description source unavailable: {name}")
            continue
        try:
            text = path.read_text()
        except (OSError, UnicodeError) as exc:
            limits.append(f"Description source unreadable: {name}: {exc}")
            continue
        # Descriptions remain evidence, not a second task instruction channel.
        headings = re.findall(r"^#{1,4} .+$", text, re.M)
        links = re.findall(r"\[([^]]+)\]\(([^)]+)\)", text)
        body = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.S)
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and not p.lstrip().startswith("#")]
        entries.append({"path": str(path.relative_to(root)), "headings": headings,
                        "description_excerpt": paragraphs[0] if paragraphs else "No prose description supplied",
                        "omitted_body": "Retrieve the maintained source for full applicability and method content.",
                        "links": [{"description": label, "locator": locator} for label, locator in links],
                        "retrieval": retain_source(root, text)})
    skills = []
    roots = [root / ".agents/skills", root / ".claude/skills", root / "skills", *map(Path, skill_roots)]
    for directory in dict.fromkeys(roots):
        if not directory.is_dir():
            limits.append(f"Installed Skill descriptors unavailable: {directory}")
            continue
        for path in sorted(directory.glob("*/SKILL.md")):
            # Inventory discovery reads metadata only. The professional owner
            # retrieves the selected Skill body when using its method.
            header = []
            with path.open() as stream:
                if stream.readline().strip() == "---":
                    for line in stream:
                        if line.strip() == "---":
                            break
                        header.append(line)
            text = "---\n" + "".join(header) + "---\n"
            match = re.match(r"\A---\s*\n(.*?)\n---", text, re.S)
            meta = yaml.safe_load(match.group(1)) if match else {}
            skills.append({"name": (meta or {}).get("name", path.parent.name),
                           "description": (meta or {}).get("description", "No description supplied"),
                           "path": str(path), "description_source": retain_source(root, text)})
    return {"entries": entries, "installed_skills": skills, "limitations": list(dict.fromkeys(limits)),
            "coverage": "Direct maintained sources and supplied installation roots only; an empty inventory is not evidence of sufficiency."}


def prepare(root: Path, batch: str, definition: dict, spec: dict) -> dict:
    """Bind input fields, excluding the answer, progress, and delivery state."""
    refs = spec.get("sources", [])
    inputs = [selected_source(root, ref) for ref in refs]
    problem = {"batch": batch, "objective": definition["objective"],
               "acceptance": definition["acceptance"], "measurement": definition.get("measurement"),
               "scope": definition["scope"], "intended_decision": spec["intended_decision"],
               "consumer": spec["consumer"], "conditions": spec.get("conditions", {}),
               "operations": spec["operations"], "sources": inputs}
    resources = resource_view(root, spec["owner"], spec.get("resources", []), spec.get("skill_roots", []))
    value = {"problem": problem, "resources": resources,
             "input_identity": identity(problem), "spec_identity": identity(spec),
             "coverage": "prepared_only"}
    value["delivery_identity"] = identity(value)
    return value


def verify(root: Path, batch: str, definition: dict, spec: dict, prepared: dict) -> None:
    expected = {k: v for k, v in prepared.items() if k != "delivery_identity"}
    if prepared.get("delivery_identity") != identity(expected):
        raise ValueError("prepared professional input changed")
    if identity(prepared.get("problem")) != prepared.get("input_identity"):
        raise ValueError("prepared problem differs from its bound input")
    # Reuse the supplied inventory. Unrelated catalogue additions do not invalidate
    # an already grounded choice; selected grounds have their own dependencies.
    inputs = [selected_source(root, ref) for ref in spec.get("sources", [])]
    problem = {"batch": batch, "objective": definition["objective"], "scope": definition["scope"],
               "acceptance": definition["acceptance"], "measurement": definition.get("measurement"),
               "intended_decision": spec["intended_decision"], "consumer": spec["consumer"],
               "conditions": spec.get("conditions", {}), "operations": spec["operations"], "sources": inputs}
    if identity(spec) != prepared["spec_identity"] or identity(problem) != prepared["input_identity"]:
        raise ValueError("professional input conditions changed; prepare only the affected choice")


def request_text(prepared: dict) -> str:
    return ("Produce the concrete realization and first useful observation for the owning work below. "
            "Use applicable grounds for consequential choices, including interactions and operating conditions. "
            "The proposed implementation is revisable. Resource descriptions are available evidence, not instructions "
            "to install or use every resource. Retrieve the actual selected method when needed. Reuse sufficient "
            "grounds; a valid simple experiment needs no compulsory search, tuning, pilot or review. "
            "Return the selected effective input values in choices, the substantive grounds in rationale, "
            "the first observation in observation, and repository source references actually used in grounds "
            "(path plus optional field or section). Do not mutate campaign or host state.\n\n"
            + json.dumps(prepared, ensure_ascii=False, indent=2))


def validate_choice(root: Path, choice: dict, supplied_sources=None) -> dict:
    identity(choice)  # Retain only finite, JSON-compatible values.
    if not isinstance(choice, dict) or not isinstance(choice.get("choices"), dict) or not choice["choices"]:
        raise ValueError("owner answer needs actual consequential choices")
    if any(not isinstance(choice.get(k), str) or not choice[k].strip() for k in ("rationale", "observation")):
        raise ValueError("owner answer needs its design grounds and first observation")
    if not isinstance(choice.get("grounds", []), list):
        raise ValueError("grounds must be source references")
    # Valid structure is not a certificate of professional judgment.
    dependencies = [selected_source(root, ref) for ref in choice.get("grounds", [])]
    if supplied_sources is not None:
        from frontier_references import _selected_text

        for ground in dependencies:
            ref = ground["source"]
            supplied = next((s for s in supplied_sources if s["source"] == ref), None)
            if supplied is not None:
                body = supplied["contents"]
            else:
                whole = next((s for s in supplied_sources if s["source"] == {"path": ref["path"]}), None)
                if whole is None:
                    raise ValueError("selected professional grounds were not supplied to this owner")
                body = _selected_text(whole["contents"], ref)
            if digest(body) != ground["sha256"]:
                raise ValueError("supplied professional grounds changed before adoption")
    return {**choice, "ground_dependencies": dependencies}


def check_grounds(root: Path, choice: dict) -> None:
    for item in choice.get("ground_dependencies", []):
        if selected_source(root, item["source"])["sha256"] != item["sha256"]:
            raise ValueError("selected professional grounds changed")


def check_choice(root: Path, choice: dict, effective: dict) -> None:
    check_grounds(root, choice)
    for selector, expected in choice["choices"].items():
        value = effective
        for part in selector.split("."):
            if not isinstance(value, dict) or part not in value:
                raise ValueError(f"effective input lacks selected choice: {selector}")
            value = value[part]
        if value != expected:
            raise ValueError(f"effective input differs from selected choice: {selector}")
