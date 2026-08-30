"""Technology-neutral workflow source-module closure validation."""

from __future__ import annotations

import ast
from pathlib import Path, PurePosixPath
from typing import Any

from .content import ProvenanceError, artifact_entry, authority_payload, compute_content_root


SOURCE_MODULE_CONTRACT = "frontier-source-modules/1"


def _path(value: Any, role: str) -> str:
    if not isinstance(value, str) or not value:
        raise ProvenanceError(f"{role} must be a nonempty relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        raise ProvenanceError(f"{role} is not canonical: {value!r}")
    return value


def validate_source_modules(document: dict[str, Any], source_root: Path) -> dict[str, set[str]]:
    if not isinstance(document, dict) or set(document) != {"contract_version", "modules"}:
        raise ProvenanceError("source-module manifest has an invalid shape")
    if document["contract_version"] != SOURCE_MODULE_CONTRACT:
        raise ProvenanceError(f"source-module contract must be {SOURCE_MODULE_CONTRACT}")
    modules = document["modules"]
    if not isinstance(modules, dict) or not modules:
        raise ProvenanceError("source-module manifest requires modules")
    normalized: dict[str, tuple[set[str], set[str]]] = {}
    for name, value in modules.items():
        if not isinstance(name, str) or not name or not isinstance(value, dict):
            raise ProvenanceError("source-module name and body must be mappings")
        if set(value) != {"depends_on", "files"}:
            raise ProvenanceError(f"source module {name} has an invalid shape")
        dependencies = value["depends_on"]
        files = value["files"]
        if not isinstance(dependencies, list) or not all(
            isinstance(item, str) and item for item in dependencies
        ):
            raise ProvenanceError(f"source module {name} dependencies are invalid")
        if not isinstance(files, list) or not files:
            raise ProvenanceError(f"source module {name} requires files")
        normalized_files = {_path(item, f"source module {name} file") for item in files}
        for relative in normalized_files:
            path = (source_root / relative).resolve()
            try:
                path.relative_to(source_root.resolve())
            except ValueError as exc:
                raise ProvenanceError(f"source module {name} path escapes root") from exc
            if not path.is_file() or path.is_symlink():
                raise ProvenanceError(f"source module {name} file is missing: {relative}")
        normalized[name] = (set(dependencies), normalized_files)
    unknown = sorted(
        dependency
        for dependencies, _ in normalized.values()
        for dependency in dependencies
        if dependency not in normalized
    )
    if unknown:
        raise ProvenanceError(f"source modules cite unknown dependencies: {unknown}")

    expanded: dict[str, set[str]] = {}
    active: set[str] = set()

    def expand(name: str) -> set[str]:
        if name in active:
            raise ProvenanceError(f"source-module dependency cycle at {name}")
        if name in expanded:
            return expanded[name]
        active.add(name)
        dependencies, files = normalized[name]
        closure = set(files)
        for dependency in sorted(dependencies):
            closure.update(expand(dependency))
        active.remove(name)
        expanded[name] = closure
        return closure

    for name in sorted(normalized):
        expand(name)
    return expanded


def source_module_root(
    document: dict[str, Any], source_root: Path, module: str
) -> str:
    closure = validate_source_modules(document, source_root)
    if module not in closure:
        raise ProvenanceError(f"unknown source module: {module}")
    artifacts = []
    for relative in sorted(closure[module]):
        raw = (source_root / relative).read_bytes()
        artifacts.append(
            artifact_entry(
                f"release/{relative}",
                raw,
                behavioral_metadata={"source_module": module},
            )
        )
    payload = authority_payload(artifacts, [], domain="workflow-release")
    return compute_content_root(payload)


def audit_python_dependencies(
    document: dict[str, Any], source_root: Path
) -> dict[str, set[str]]:
    """Audit local Python imports for this Python implementation's release closure."""

    closure = validate_source_modules(document, source_root)
    root = source_root.resolve()
    python_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.py")
        if path.is_file() and not path.is_symlink()
    }
    for module, members in closure.items():
        for relative in sorted(path for path in members if path.endswith(".py")):
            tree = ast.parse((source_root / relative).read_text(), filename=relative)
            dependencies: set[str] = set()
            current = PurePosixPath(relative)
            import_roots = _python_import_roots(current, python_files)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.update(
                            _resolve_absolute_import(
                                alias.name.split("."), import_roots, python_files
                            )
                        )
                elif isinstance(node, ast.ImportFrom):
                    module_parts = node.module.split(".") if node.module else []
                    if node.level:
                        base = current.parent
                        for _ in range(node.level - 1):
                            base = base.parent
                        if base.as_posix() == ".." or base.as_posix().startswith("../"):
                            raise ProvenanceError(
                                f"relative import of {relative} escapes source root"
                            )
                        dependencies.update(
                            _resolve_module(base, module_parts, python_files)
                        )
                        alias_base = base.joinpath(*module_parts)
                    else:
                        dependencies.update(
                            _resolve_absolute_import(
                                module_parts, import_roots, python_files
                            )
                        )
                        alias_base = None
                        for import_root in import_roots:
                            candidate = import_root.joinpath(*module_parts)
                            if _resolve_module(import_root, module_parts, python_files):
                                alias_base = candidate
                                break
                    if alias_base is not None:
                        for alias in node.names:
                            if alias.name != "*":
                                dependencies.update(
                                    _resolve_module(
                                        alias_base, [alias.name], python_files
                                    )
                                )
            dependencies.discard(relative)
            missing = sorted(dependencies - members)
            if missing:
                raise ProvenanceError(
                    f"source module {module} omits Python dependencies of {relative}: {missing}"
                )
    return closure


def _python_import_roots(
    current: PurePosixPath, available: set[str]
) -> list[PurePosixPath]:
    directory = current.parent
    package_root = directory
    while (package_root / "__init__.py").as_posix() in available:
        package_root = package_root.parent
    roots = [package_root if package_root != directory else directory]
    source_root = PurePosixPath(".")
    if source_root not in roots:
        roots.append(source_root)
    return roots


def _resolve_absolute_import(
    parts: list[str], roots: list[PurePosixPath], available: set[str]
) -> set[str]:
    for root in roots:
        resolved = _resolve_module(root, parts, available)
        if resolved:
            return resolved
    return set()


def _resolve_module(
    base: PurePosixPath, parts: list[str], available: set[str]
) -> set[str]:
    if not parts:
        package_init = (base / "__init__.py").as_posix()
        return {package_init} if package_init in available else set()
    resolved: set[str] = set()
    prefix = base
    for part in parts[:-1]:
        prefix /= part
        package_init = (prefix / "__init__.py").as_posix()
        if package_init in available:
            resolved.add(package_init)
    target = prefix / parts[-1]
    module_file = target.with_suffix(".py").as_posix()
    package_init = (target / "__init__.py").as_posix()
    if module_file in available:
        resolved.add(module_file)
    elif package_init in available:
        resolved.add(package_init)
    return resolved
