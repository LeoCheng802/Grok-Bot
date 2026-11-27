#!/usr/bin/env python3
"""Public-directory static verifier for research/long_struct_01/code.

Separated from private-pack --dry-check. This file only reads source text.
It does not import trading or engine modules, does not call main(), and does
not execute --dry-check, historical replay, or any market-data path.

Allowed imports: ast, hashlib, json, pathlib, re.
"""

import ast
import hashlib
import json
import re
from pathlib import Path

DECLARED_IMPORTS = ("ast", "hashlib", "json", "pathlib", "re")
REQUIRED_FILES = (
    "FIB_4H_Long_v3.py",
    "RETEST24_R1_R2_Switchable_v1_5_auditfix.py",
    "run_l1_tp_study.py",
    "offline_static_check.py",
    "engine/b6_sim_portable.py",
    "engine/sim_50k_v3_2_sl_fix.py",
    "engine/audit_v3_1_full.py",
    "engine/run_q38_audit_01.py",
    "requirements.txt",
)
FORBIDDEN_TOP_LEVEL_IMPORTS = {
    "FIB_4H_Long_v3",
    "audit_v3_1_full",
    "b6_sim_portable",
    "run_q38_audit_01",
    "shared_risk",
    "sim_50k_v3_2_sl_fix",
}
DEFERRED_LOADERS = {
    "_load_registered_module",
    "_load_runtime_modules",
    "load_orig_module",
}
GUARD_PREFIX = "OFFLINE_RESEARCH_COPY_NETWORK_DISABLED"

FIB_MSG = (
    "OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: network/OKX HTTP access is "
    "permanently disabled in this sanitized research copy."
)
OKX_MSG = (
    "OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: OkxClient network access is "
    "permanently disabled in this sanitized research copy."
)
FUND_MSG = (
    "OFFLINE_RESEARCH_COPY_NETWORK_DISABLED: funding fetch/backfill is disabled; "
    "missing funding must fail explicitly without zero-fill or network download."
)

REQUIRED_GUARDS = {
    "FIB_4H_Long_v3.py": {
        ("notify",): FIB_MSG,
        ("Exchange", "call"): FIB_MSG,
    },
    "RETEST24_R1_R2_Switchable_v1_5_auditfix.py": {
        ("OkxClient", "__init__"): OKX_MSG,
        ("OkxClient", "public_get"): OKX_MSG,
        ("OkxClient", "private_req"): OKX_MSG,
    },
    "run_l1_tp_study.py": {
        ("fetch_okx_funding",): FUND_MSG,
        ("backfill_missing_funding",): FUND_MSG,
    },
}

HARD_BLOCKS = {
    "FIB_4H_Long_v3.py": {
        ("main",): "SystemExit",
    },
    "RETEST24_R1_R2_Switchable_v1_5_auditfix.py": {
        ("main",): "SystemExit",
        ("load_config_credentials",): "empty-credentials",
    },
}

FORBIDDEN_PACK_SNIPPETS = (
    'PACK_ROOT / "REPRO_MANIFEST.json"',
    "PACK_ROOT / 'REPRO_MANIFEST.json'",
    'PACK_ROOT / "scripts" / "shared_risk.py"',
    "PACK_ROOT / 'scripts' / 'shared_risk.py'",
)

SECRET_RES = (
    re.compile(
        r"(?i)\b(?:api[_-]?key|secret(?:_key)?|passphrase|access[_-]?token)\b"
        r"\s*[:=]\s*['\"][0-9A-Za-z+/_=\-]{16,}['\"]"
    ),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
)

HTTP_METHOD_ATTRS = {"get", "post", "put", "delete", "patch", "request", "head"}


def host_patterns():
    """Host-path patterns built so this source does not contain the prefixes.

    Unix home and workspace prefixes are literal. A Windows C: or D: prefix
    must start at a non-identifier boundary so a Python newline escape glued
    to an identifier (for example a trailing letter before ``\\n``) is not
    treated as a drive path.
    """
    slash = "/"
    home = slash + "home" + slash
    workspace = slash + "workspace" + slash
    drive = r"(?<![A-Za-z0-9_])[CcDd]:\\"
    return (
        re.compile(re.escape(home)),
        re.compile(re.escape(workspace)),
        re.compile(drive),
    )


def symlink_escapes(root, path):
    """True when a symlink is broken or its target is outside root."""
    if not path.is_symlink():
        return False
    root_real = root.resolve()
    try:
        target = path.resolve(strict=True)
    except OSError:
        return True
    try:
        target.relative_to(root_real)
    except ValueError:
        return True
    return False


def iter_tree(root):
    """Yield files and symlinks. Do not descend through symlinked directories."""
    found = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if "__pycache__" in child.parts or child.suffix == ".pyc":
                continue
            found.append(child)
            if child.is_symlink():
                continue
            if child.is_dir():
                stack.append(child)
    found.sort(key=lambda item: item.relative_to(root).as_posix())
    return found


def required_symlink_component(root, rel):
    """Return the first symlink on the path from root to rel, or an empty string."""
    current = root
    for part in Path(rel).parts:
        current = current / part
        if current.is_symlink():
            return current.relative_to(root).as_posix()
    return ""


def check_required_files(root, failures, notes):
    if not REQUIRED_FILES:
        failures.append("REQUIRED_FILES is empty")
        return
    for rel in REQUIRED_FILES:
        link = required_symlink_component(root, rel)
        if link:
            failures.append(rel + ": required path component is a symlink: " + link)
            continue
        if not (root / rel).is_file():
            failures.append(rel + ": required file missing")
    blocked = (
        "REQUIRED_FILES is empty",
        ": required file missing",
        ": required path component is a symlink:",
    )
    if not any(item == blocked[0] or item.endswith(blocked[1]) or blocked[2] in item for item in failures):
        notes.append("required files present and no required-path symlink: " + str(len(REQUIRED_FILES)))


def function_index(tree):
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[(node.name,)] = node
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    found[(node.name, item.name)] = item
    return found


def guard_text(func):
    """Return the leading RuntimeError message, or None if it is not unconditional."""
    if not func.body:
        return None
    stmt = func.body[0]
    if not isinstance(stmt, ast.Raise) or not isinstance(stmt.exc, ast.Call):
        return None
    callee = stmt.exc.func
    if not isinstance(callee, ast.Name) or callee.id != "RuntimeError":
        return None
    if len(stmt.exc.args) != 1 or stmt.exc.keywords:
        return None
    arg = stmt.exc.args[0]
    if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
        return None
    return arg.value


def raise_name(func):
    if not func.body:
        return None
    stmt = func.body[0]
    if not isinstance(stmt, ast.Raise) or not isinstance(stmt.exc, ast.Call):
        return None
    callee = stmt.exc.func
    if isinstance(callee, ast.Name):
        return callee.id
    return None


def is_network_call(node):
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id in {"urlopen", "urlretrieve"}:
        return True
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr in {"urlopen", "urlretrieve", "HTTPSConnection", "HTTPConnection"}:
        return True
    if func.attr == "Session" and isinstance(func.value, ast.Name) and func.value.id == "requests":
        return True
    if func.attr == "create_connection" and isinstance(func.value, ast.Name) and func.value.id == "socket":
        return True
    if func.attr in HTTP_METHOD_ATTRS:
        value = func.value
        if isinstance(value, ast.Name) and value.id in {"session", "requests"}:
            return True
        if isinstance(value, ast.Attribute) and value.attr == "session":
            return True
    return False


def parent_map(tree):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def enclosing_function(parents, node):
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def imported_roots(tree):
    roots = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            roots.append((node.module or "").split(".")[0])
    return roots


def empty_credential_return(func):
    if len(func.body) != 1 or not isinstance(func.body[0], ast.Return):
        return False
    value = func.body[0].value
    if not isinstance(value, ast.Tuple) or len(value.elts) != 3:
        return False
    return all(isinstance(elt, ast.Constant) and elt.value == "" for elt in value.elts)


def qual_label(key):
    return ".".join(key)


def check_tree(rel, tree, text, failures, notes):
    if rel == "offline_static_check.py":
        roots = imported_roots(tree)
        extra = sorted(set(roots) - set(DECLARED_IMPORTS))
        if extra or sorted(set(roots)) != sorted(DECLARED_IMPORTS):
            failures.append(rel + ": imports must be exactly " + ", ".join(DECLARED_IMPORTS))
        else:
            notes.append(rel + ": imports limited to ast, hashlib, json, pathlib, re")
    required = REQUIRED_GUARDS.get(rel, {})
    index = function_index(tree)
    for key, expected in required.items():
        func = index.get(key)
        if func is None:
            failures.append(rel + ": missing network entrypoint " + qual_label(key))
            continue
        got = guard_text(func)
        if got != expected:
            failures.append(rel + ": " + qual_label(key) + " missing unconditional offline RuntimeError")
        elif not got.startswith(GUARD_PREFIX):
            failures.append(rel + ": " + qual_label(key) + " guard prefix mismatch")
        else:
            notes.append(rel + ": " + qual_label(key) + " unconditional offline guard")
    for key, kind in HARD_BLOCKS.get(rel, {}).items():
        func = index.get(key)
        if func is None:
            failures.append(rel + ": missing hard block " + qual_label(key))
            continue
        if kind == "SystemExit":
            if raise_name(func) != "SystemExit":
                failures.append(rel + ": " + qual_label(key) + " is not a leading SystemExit")
            else:
                notes.append(rel + ": " + qual_label(key) + " remains SystemExit hard block")
        elif kind == "empty-credentials":
            if not empty_credential_return(func):
                failures.append(rel + ": load_config_credentials is not an empty-credential return")
            else:
                notes.append(rel + ": load_config_credentials remains empty-credential block")
    parents = parent_map(tree)
    seen_network = []
    for node in ast.walk(tree):
        if not is_network_call(node):
            continue
        func = enclosing_function(parents, node)
        label = "<module>" if func is None else func.name
        seen_network.append(label)
        message = None if func is None else guard_text(func)
        if message is None or not message.startswith(GUARD_PREFIX):
            failures.append(rel + ": network call in " + label + " lacks a leading offline RuntimeError")
    if rel == "run_l1_tp_study.py":
        for snippet in FORBIDDEN_PACK_SNIPPETS:
            if snippet in text:
                failures.append(rel + ": still hardcodes private pack path " + snippet)
        for flag in ('"--manifest"', '"--shared-risk"', '"--orig-long"'):
            if flag not in text:
                failures.append(rel + ": missing explicit CLI flag " + flag)
        if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
            failures.append(rel + ": integrity assert remains and python -O could strip it")
        top_roots = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_roots.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_roots.append(node.module.split(".")[0])
            elif not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in DEFERRED_LOADERS:
                        failures.append(rel + ": loader called outside a function: " + sub.func.id)
        banned = sorted(set(top_roots) & FORBIDDEN_TOP_LEVEL_IMPORTS)
        if banned:
            failures.append(rel + ": top-level import of " + ", ".join(banned))
        for name in ("_verify_manifest_bindings", "_load_runtime_modules", "_bind_isolated_funding_db"):
            if (name,) not in index:
                failures.append(rel + ": missing " + name)
        if "b6_source_sha256" not in text or "derived_l1_db_sha256" not in text or ".source_meta.json" not in text:
            failures.append(rel + ": missing L1_DB source and content hash binding")
        if not any(item.startswith(rel + ":") for item in failures):
            notes.append(rel + ": explicit paths, deferred loaders, no assert, L1_DB source and content binding")
    return seen_network


def main():
    root = Path(__file__).resolve().parent
    failures = []
    notes = []
    inventory = []
    patterns = host_patterns()
    network_sites = {}
    escaping = []
    checked_required_py = set()
    required_py = [rel for rel in REQUIRED_FILES if rel.endswith(".py")]
    check_required_files(root, failures, notes)
    for path in iter_tree(root):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink() and symlink_escapes(root, path):
            escaping.append(rel)
            failures.append(rel + ": symlink escapes check root")
            continue
        if path.is_symlink() or not path.is_file():
            continue
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        inventory.append({"path": rel, "bytes": len(data), "sha256": digest})
        print("FILE bytes=" + str(len(data)) + " sha256=" + digest + " path=" + rel)
        try:
            text = data.decode("utf-8")
        except UnicodeError as exc:
            failures.append(rel + ": not utf-8 (" + type(exc).__name__ + ")")
            continue
        if any(pattern.search(text) for pattern in patterns):
            failures.append(rel + ": host-path marker present")
        for pattern in SECRET_RES:
            if pattern.search(text):
                failures.append(rel + ": secret-shaped literal present")
                break
        if path.suffix == ".py":
            try:
                tree = ast.parse(text, filename=rel)
            except SyntaxError as exc:
                failures.append(rel + ": syntax error line " + str(exc.lineno))
                continue
            network_sites[rel] = check_tree(rel, tree, text, failures, notes)
            if rel in required_py:
                checked_required_py.add(rel)
    unchecked = [rel for rel in required_py if rel not in checked_required_py]
    if unchecked:
        for rel in unchecked:
            failures.append(rel + ": required python file did not complete AST, leak, and network-guard checks")
    if not escaping:
        notes.append("no symlink escapes the check root")
    if not unchecked:
        notes.append("required python files completed AST, leak, and network-guard checks: " + str(len(required_py)))
    result = {
        "result": "PASS" if not failures else "FAIL",
        "root": "research/long_struct_01/code",
        "required_files": list(REQUIRED_FILES),
        "checked_required_py": sorted(checked_required_py),
        "escaping_symlinks": escaping,
        "files": inventory,
        "network_call_functions": network_sites,
        "notes": notes,
        "failures": failures,
        "process": {
            "declared_imports": list(DECLARED_IMPORTS),
            "imported_trading_modules": [],
            "executed_strategy_main": False,
            "ran_private_pack_dry_check": False,
            "method": "ast.parse and text scan only",
        },
    }
    print("STATIC_CHECK " + result["result"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
