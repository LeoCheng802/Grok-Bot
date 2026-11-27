#!/usr/bin/env python3
"""Bounded isolated synthetic checks for the offline packaging draft.

Stdlib only. Extracts unmodified target functions with ast and runs
--dry-check in a subprocess. Does not import strategy, shared_risk, or
engine modules, and does not call the study main() loop.

Scope is helper/function-layer plus the dry-check CLI. It does not claim
full historical study execution. Candidates, strategy rules, costs, and
full history stay 待驗. FIB-4H-LONG-V3 stays NO-GO. LONG-STRUCT-02 is
not implemented.
"""

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PINNED_SHA256 = {
    "FIB_4H_Long_v3.py": "17b46a4e7ce898d9db8cd23078a2a62cd47309cf136597a5068e9f8c385d26d7",
    "RETEST24_R1_R2_Switchable_v1_5_auditfix.py": "c2b00a987150c20d16f22500a5d6dc0f0dca00ccaac62851f4014a343f664b04",
    "run_l1_tp_study.py": "c9b5571c942ac863845e6863d814ae6a1d7f0501b4b73acf5e057b86ef579d94",
}
FIXED_COMMIT = "c5f28d0b79593847bfa95a881127b89094e0d0ab"
OFFLINE_PREFIX = "OFFLINE_RESEARCH_COPY_NETWORK_DISABLED"
ENGINE_FILES = (
    "audit_v3_1_full.py",
    "sim_50k_v3_2_sl_fix.py",
    "run_q38_audit_01.py",
    "b6_sim_portable.py",
)
BANNED_IMPORT_ROOTS = (
    "FIB_4H_Long_v3",
    "audit_v3_1_full",
    "b6_sim_portable",
    "fib_long_orig",
    "run_q38_audit_01",
    "shared_risk",
    "shared_risk_chk",
    "sim_50k_v3_2_sl_fix",
)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def redact(text: str, replacements) -> str:
    out = text
    for src, dst in replacements:
        if src:
            out = out.replace(src, dst)
    return out


class TransportGuard:
    """Outer socket / urllib.request / http.client blocker with a hit list."""

    def __init__(self):
        self.hits = []
        self._saved = None

    def install(self):
        import http.client
        import socket
        import urllib.request
        self._saved = (
            socket.socket,
            socket.create_connection,
            urllib.request.urlopen,
            http.client.HTTPConnection,
            http.client.HTTPSConnection,
        )

        def blocked(kind):
            def inner(*_args, **_kwargs):
                self.hits.append(kind)
                raise RuntimeError("synthetic transport blocked: " + kind)
            return inner

        socket.socket = blocked("socket.socket")
        socket.create_connection = blocked("socket.create_connection")
        urllib.request.urlopen = blocked("urllib.request.urlopen")
        http.client.HTTPConnection = blocked("http.client.HTTPConnection")
        http.client.HTTPSConnection = blocked("http.client.HTTPSConnection")

    def restore(self):
        if self._saved is None:
            return
        import http.client
        import socket
        import urllib.request
        (
            socket.socket,
            socket.create_connection,
            urllib.request.urlopen,
            http.client.HTTPConnection,
            http.client.HTTPSConnection,
        ) = self._saved
        self._saved = None


def extract_symbols(path: Path, wanted):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    found = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        segment = "".join(lines[node.lineno - 1:node.end_lineno])
        if node.name in wanted:
            found[node.name] = {
                "lstart": node.lineno,
                "lend": node.end_lineno,
                "source": segment,
            }
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                key = node.name + "." + item.name
                if key in wanted:
                    found[key] = {
                        "lstart": item.lineno,
                        "lend": item.end_lineno,
                        "source": segment,
                    }
    missing = sorted(set(wanted) - set(found))
    if missing:
        raise RuntimeError("missing symbols in " + path.name + ": " + ", ".join(missing))
    return found


def exec_symbols(symbols, names, namespace):
    seen = []
    for name in names:
        source = symbols[name]["source"]
        if source in seen:
            continue
        seen.append(source)
        exec(compile(source, "<extracted:" + name + ">", "exec"), namespace)
    return namespace


def expect_offline(fn, label, transport: TransportGuard):
    before = len(transport.hits)
    try:
        fn()
    except RuntimeError as exc:
        message = str(exc)
        ok = message.startswith(OFFLINE_PREFIX) and len(transport.hits) == before
        return {
            "label": label,
            "expected": "RuntimeError " + OFFLINE_PREFIX + " and transport_hits unchanged",
            "actual": type(exc).__name__ + ": " + message,
            "transport_hits": len(transport.hits),
            "pass": ok,
        }
    except Exception as exc:
        return {
            "label": label,
            "expected": "RuntimeError " + OFFLINE_PREFIX,
            "actual": type(exc).__name__ + ": " + str(exc),
            "transport_hits": len(transport.hits),
            "pass": False,
        }
    return {
        "label": label,
        "expected": "RuntimeError " + OFFLINE_PREFIX,
        "actual": "returned without error",
        "transport_hits": len(transport.hits),
        "pass": False,
    }


def run_syn_net(code_dir: Path, transport: TransportGuard):
    fib = code_dir / "FIB_4H_Long_v3.py"
    retest = code_dir / "RETEST24_R1_R2_Switchable_v1_5_auditfix.py"
    study = code_dir / "run_l1_tp_study.py"
    fib_syms = extract_symbols(fib, {"notify", "Exchange", "Exchange.call", "Exchange.pages"})
    retest_syms = extract_symbols(
        retest,
        {"OkxClient", "OkxClient.__init__", "OkxClient.public_get", "OkxClient.private_req", "load_config_credentials"},
    )
    study_syms = extract_symbols(study, {"fetch_okx_funding", "backfill_missing_funding"})
    fib_ns = exec_symbols(fib_syms, ["notify", "Exchange"], {})
    typing_ns = {"Optional": Optional, "Dict": Dict, "Any": Any, "Tuple": Tuple}
    retest_ns = exec_symbols(retest_syms, ["OkxClient", "load_config_credentials"], typing_ns)
    study_ns = exec_symbols(study_syms, ["fetch_okx_funding", "backfill_missing_funding"], {"Path": Path})

    cases = []
    exchange = fib_ns["Exchange"]({})
    cases.append(expect_offline(lambda: fib_ns["notify"]("synthetic"), "FIB.notify", transport))
    cases.append(expect_offline(lambda: exchange.call("account/config"), "Exchange.call", transport))
    cases.append(expect_offline(lambda: exchange.pages("market/candles", {}, "ts"), "Exchange.pages", transport))
    client = retest_ns["OkxClient"]
    cases.append(expect_offline(lambda: client(), "OkxClient.__init__", transport))
    cases.append(expect_offline(lambda: client.public_get(object(), "/api/v5/public/time"), "OkxClient.public_get", transport))
    cases.append(expect_offline(lambda: client.private_req(object(), "GET", "/api/v5/account/balance"), "OkxClient.private_req", transport))
    creds = retest_ns["load_config_credentials"]()
    cases.append({
        "label": "load_config_credentials",
        "expected": '("", "", "")',
        "actual": repr(creds),
        "transport_hits": len(transport.hits),
        "pass": creds == ("", "", ""),
    })

    db_dir = Path(tempfile.mkdtemp(prefix="syn-net-db-"))
    db_path = db_dir / "missing_funding.sqlite"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE funding_archive (inst_id TEXT, ts_snapped INTEGER, ts_raw INTEGER, rate REAL, source_ym TEXT)"
        )
        conn.execute("INSERT INTO funding_archive VALUES ('SYN', 1, 1, 0.0, 'synthetic')")
        conn.commit()
        conn.close()
        before = sha_file(db_path)
        before_rows = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0]
        fetch_case = expect_offline(
            lambda: study_ns["fetch_okx_funding"]("SYN-USDT-SWAP", 0, 1),
            "fetch_okx_funding",
            transport,
        )
        cases.append(fetch_case)
        backfill_case = expect_offline(
            lambda: study_ns["backfill_missing_funding"](db_path, [("stub", "SYN-USDT-SWAP", 0, "miss_8h")]),
            "backfill_missing_funding",
            transport,
        )
        after = sha_file(db_path)
        after_rows = sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM funding_archive").fetchone()[0]
        backfill_case["sha_before"] = before
        backfill_case["sha_after"] = after
        backfill_case["rows_before"] = before_rows
        backfill_case["rows_after"] = after_rows
        backfill_case["pass"] = bool(
            backfill_case["pass"] and before == after and before_rows == after_rows == 1
        )
        backfill_case["expected"] = backfill_case["expected"] + "; sqlite sha unchanged; no zero-fill"
        cases.append(backfill_case)
    finally:
        shutil.rmtree(db_dir, ignore_errors=True)

    spans = {
        "FIB_4H_Long_v3.py": {name: {"lstart": item["lstart"], "lend": item["lend"]} for name, item in fib_syms.items()},
        "RETEST24_R1_R2_Switchable_v1_5_auditfix.py": {
            name: {"lstart": item["lstart"], "lend": item["lend"]} for name, item in retest_syms.items()
        },
        "run_l1_tp_study.py": {
            name: {"lstart": item["lstart"], "lend": item["lend"]} for name, item in study_syms.items()
        },
    }
    return {
        "scope": "helper/function layer extracted from unmodified source; not full main() study execution",
        "file_sha256": {name: sha_file(code_dir / name) for name in spans},
        "line_spans": spans,
        "transport_hits": len(transport.hits),
        "cases": cases,
        "pass": all(case["pass"] for case in cases) and len(transport.hits) == 0,
    }


SITECUSTOMIZE = '''import os
import sys

_transport_log = os.environ.get("SYN_TRANSPORT_LOG", "")
_module_log = os.environ.get("SYN_MODULE_LOG", "")
_banned = set(%(banned)s)

def _append(path, line):
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\\n")

def _block(kind):
    def inner(*_args, **_kwargs):
        _append(_transport_log, kind)
        raise RuntimeError("synthetic transport blocked: " + kind)
    return inner

import socket
import urllib.request
import http.client
socket.socket = _block("socket.socket")
socket.create_connection = _block("socket.create_connection")
urllib.request.urlopen = _block("urllib.request.urlopen")
http.client.HTTPConnection = _block("http.client.HTTPConnection")
http.client.HTTPSConnection = _block("http.client.HTTPSConnection")

class _SentinelFinder:
    def find_spec(self, fullname, path, target=None):
        root = fullname.split(".")[0]
        if root in _banned or fullname in _banned:
            _append(_module_log, "meta_path:" + fullname)
        return None

sys.meta_path.insert(0, _SentinelFinder())
'''

SENTINEL_BODY = '''import os
_log = os.environ.get("SYN_MODULE_LOG", "")
if _log:
    with open(_log, "a", encoding="utf-8") as _handle:
        _handle.write("executed:{name}\\n")
raise SystemExit("synthetic module executed: {name}")
'''


def write_sentinel(path: Path, name: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SENTINEL_BODY.format(name=name), encoding="utf-8")


def build_pack(root: Path):
    files = {
        "scripts/FIB_4H_Long_v3.py": "scripts/FIB_4H_Long_v3.py",
        "scripts/shared_risk.py": "scripts/shared_risk.py",
    }
    for filename in ENGINE_FILES:
        files["engine/" + filename] = "engine/" + filename
    written = {}
    for rel in files:
        path = root / rel
        write_sentinel(path, rel)
        written[rel] = {"sha256": sha_file(path)}
    unregistered = root / "unregistered_fib.py"
    write_sentinel(unregistered, "unregistered_fib.py")
    manifest = {"files": written}
    manifest_path = root / "REPRO_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path, unregistered


def snapshot_files(paths):
    return {label: sha_file(path) for label, path in paths if path.is_file()}


def run_dry_check(mode, runner, pack, manifest, orig, shared, work, replacements):
    transport_log = work / "transport.log"
    module_log = work / "module.log"
    transport_log.write_text("", encoding="utf-8")
    module_log.write_text("", encoding="utf-8")
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(work),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "SYN_TRANSPORT_LOG": str(transport_log),
        "SYN_MODULE_LOG": str(module_log),
    }
    cmd = [sys.executable]
    if mode == "python3 -O":
        cmd.append("-O")
    cmd.extend([
        str(runner),
        "--dry-check",
        "--manifest", str(manifest),
        "--orig-long", str(orig),
        "--shared-risk", str(shared),
        "--funding-db", str(pack / "unused_funding.sqlite"),
        "--out-dir", str(pack / "out"),
        "--cache-dir", str(pack / "cache"),
    ])
    (pack / "unused_funding.sqlite").write_bytes(b"synthetic-funding-not-read")
    tracked = [
        ("manifest", manifest),
        ("orig-long", orig),
        ("shared-risk", shared),
        ("funding-db", pack / "unused_funding.sqlite"),
    ]
    for filename in ENGINE_FILES:
        tracked.append((filename, pack / "engine" / filename))
    before = snapshot_files(tracked)
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=120)
    after = snapshot_files(tracked)
    display_cmd = [mode, "<code>/run_l1_tp_study.py", "--dry-check", "--manifest", "<tmpdir>/REPRO_MANIFEST.json",
                   "--orig-long", "<orig>", "--shared-risk", "<shared>", "--funding-db", "<tmpdir>/unused_funding.sqlite",
                   "--out-dir", "<tmpdir>/out", "--cache-dir", "<tmpdir>/cache"]
    stdout = redact(proc.stdout, replacements)
    stderr = redact(proc.stderr, replacements)
    module_hits = [line for line in module_log.read_text(encoding="utf-8").splitlines() if line]
    transport_hits = [line for line in transport_log.read_text(encoding="utf-8").splitlines() if line]
    parsed = None
    if proc.returncode == 0:
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            parsed = None
    return {
        "command": display_cmd,
        "exit_code": proc.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "parsed_dry_check": None if parsed is None else parsed.get("dry_check"),
        "module_sentinel_hits": module_hits,
        "transport_hits": transport_hits,
        "sha_before": before,
        "sha_after": after,
        "sha_unchanged": before == after,
    }


def run_syn_manifest(code_dir: Path, work: Path):
    runner = code_dir / "run_l1_tp_study.py"
    pack = work / "pack"
    (work / "sitecustomize.py").write_text(
        SITECUSTOMIZE % {"banned": repr(BANNED_IMPORT_ROOTS)},
        encoding="utf-8",
    )
    manifest, unregistered = build_pack(pack)
    replacements = [
        (str(work), "<tmpdir>"),
        (str(code_dir), "<code>"),
        (str(runner), "<code>/run_l1_tp_study.py"),
    ]
    modes = ("python3", "python3 -O")
    cases = []
    for mode in modes:
        valid_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        scenarios = []

        scenarios.append(("valid_control", valid_manifest, pack / "scripts" / "FIB_4H_Long_v3.py", 0, "PASS"))

        mismatch = json.loads(json.dumps(valid_manifest))
        mismatch["files"]["scripts/shared_risk.py"]["sha256"] = "0" * 64
        scenarios.append(("hash_mismatch", mismatch, pack / "scripts" / "FIB_4H_Long_v3.py", "nonzero", None))

        scenarios.append(("empty_files_map", {"files": {}}, pack / "scripts" / "FIB_4H_Long_v3.py", "nonzero", None))

        missing = json.loads(json.dumps(valid_manifest))
        del missing["files"]["scripts/FIB_4H_Long_v3.py"]
        scenarios.append(("missing_required_entry", missing, pack / "scripts" / "FIB_4H_Long_v3.py", "nonzero", None))

        scenarios.append(("unregistered_explicit_path", valid_manifest, unregistered, "nonzero", None))

        for name, body, orig, expected_exit, expected_flag in scenarios:
            scenario_manifest = pack / ("manifest_" + mode.replace(" ", "_") + "_" + name + ".json")
            scenario_manifest.write_text(json.dumps(body, indent=2), encoding="utf-8")
            result = run_dry_check(mode, runner, pack, scenario_manifest, orig, pack / "scripts" / "shared_risk.py", work, replacements)
            if expected_exit == 0:
                exit_ok = result["exit_code"] == 0 and result["parsed_dry_check"] == expected_flag
            else:
                exit_ok = result["exit_code"] != 0
            sentinel_ok = result["module_sentinel_hits"] == [] and result["transport_hits"] == []
            result.update({
                "mode": mode,
                "label": name,
                "expected_exit": expected_exit,
                "expected_dry_check": expected_flag,
                "pass": bool(exit_ok and sentinel_ok and result["sha_unchanged"]),
            })
            cases.append(result)
    return {
        "scope": "subprocess --dry-check only; sentinel modules must not execute",
        "cases": cases,
        "pass": all(case["pass"] for case in cases),
    }


def file_sha_map(paths):
    return {path.name: sha_file(path) for path in paths if path.exists()}


def expect_runtime(fn, label, watched):
    before = {str(path): sha_file(path) for path in watched if path.exists()}
    existed = {str(path): path.exists() for path in watched}
    try:
        fn()
    except RuntimeError as exc:
        after = {str(path): sha_file(path) for path in watched if path.exists()}
        still = {str(path): path.exists() for path in watched}
        unchanged = before == after and existed == still
        return {
            "label": label,
            "expected": "RuntimeError before cleanup; watched SHA unchanged",
            "actual": "RuntimeError: " + str(exc),
            "pass": unchanged,
            "sha_unchanged": unchanged,
        }
    except Exception as exc:
        return {
            "label": label,
            "expected": "RuntimeError",
            "actual": type(exc).__name__ + ": " + str(exc),
            "pass": False,
            "sha_unchanged": False,
        }
    return {
        "label": label,
        "expected": "RuntimeError",
        "actual": "returned without error",
        "pass": False,
        "sha_unchanged": False,
    }


def make_sqlite(path: Path, marker: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS synthetic (marker BLOB)")
    conn.execute("DELETE FROM synthetic")
    conn.execute("INSERT INTO synthetic VALUES (?)", (marker,))
    conn.commit()
    conn.close()


def run_syn_db(code_dir: Path, work: Path):
    study = code_dir / "run_l1_tp_study.py"
    wanted = {
        "sha",
        "_paths_overlap",
        "_verify_output_paths_disjoint",
        "_atomic_write_text",
        "_discard_final_report",
        "_bind_isolated_funding_db",
    }
    symbols = extract_symbols(study, wanted)
    ns = {
        "Path": Path,
        "os": os,
        "json": json,
        "shutil": shutil,
        "hashlib": hashlib,
    }
    exec_symbols(
        symbols,
        ["sha", "_paths_overlap", "_atomic_write_text", "_discard_final_report", "_verify_output_paths_disjoint", "_bind_isolated_funding_db"],
        ns,
    )
    bind = ns["_bind_isolated_funding_db"]
    verify = ns["_verify_output_paths_disjoint"]
    discard = ns["_discard_final_report"]
    digest = ns["sha"]
    root = work / "db"
    root.mkdir(parents=True, exist_ok=True)
    source_a = root / "source_a.sqlite"
    source_b = root / "source_b.sqlite"
    make_sqlite(source_a, b"source-a")
    make_sqlite(source_b, b"source-b")
    cases = []

    create_dir = root / "create"
    l1 = create_dir / "funding_archive_l1_isolated.sqlite"
    meta = Path(str(l1) + ".source_meta.json")
    created = bind(source_a, l1, meta)
    meta_body = json.loads(meta.read_text(encoding="utf-8"))
    cases.append({
        "label": "clean_bind_create",
        "expected": "sidecar records source and derived hashes",
        "actual": "created",
        "pass": bool(
            created == digest(source_a)
            and meta_body.get("b6_source_sha256") == digest(source_a)
            and meta_body.get("derived_l1_db_sha256") == digest(l1)
        ),
    })
    reused = bind(source_a, l1, meta)
    cases.append({
        "label": "clean_bind_reuse",
        "expected": "second bind returns the same source hash and leaves bytes unchanged",
        "actual": "reused" if reused == created else "hash changed",
        "pass": reused == created and meta_body == json.loads(meta.read_text(encoding="utf-8")),
    })

    l1_before = digest(l1)
    b_before = digest(source_b)
    a_before = digest(source_a)
    case = expect_runtime(lambda: bind(source_b, l1, meta), "source_changed", [source_a, source_b, l1, meta])
    case["pass"] = bool(case["pass"] and digest(l1) == l1_before and digest(source_b) == b_before and digest(source_a) == a_before)
    cases.append(case)

    mutated = root / "mutated" / "funding_archive_l1_isolated.sqlite"
    mutated_meta = Path(str(mutated) + ".source_meta.json")
    bind(source_a, mutated, mutated_meta)
    mutated.write_bytes(mutated.read_bytes() + b"mutated")
    mutated_sha = digest(mutated)
    meta_sha = digest(mutated_meta)
    case = expect_runtime(lambda: bind(source_a, mutated, mutated_meta), "stale_sidecar_derived_mutated", [source_a, mutated, mutated_meta])
    case["pass"] = bool(case["pass"] and digest(mutated) == mutated_sha and digest(mutated_meta) == meta_sha)
    cases.append(case)

    missing_l1 = root / "missing-meta" / "funding_archive_l1_isolated.sqlite"
    missing_meta = Path(str(missing_l1) + ".source_meta.json")
    bind(source_a, missing_l1, missing_meta)
    missing_meta.unlink()
    missing_sha = digest(missing_l1)
    case = expect_runtime(lambda: bind(source_a, missing_l1, missing_meta), "missing_sidecar", [source_a, missing_l1])
    case["pass"] = bool(case["pass"] and digest(missing_l1) == missing_sha and not missing_meta.exists())
    cases.append(case)

    corrupt_l1 = root / "corrupt" / "funding_archive_l1_isolated.sqlite"
    corrupt_meta = Path(str(corrupt_l1) + ".source_meta.json")
    bind(source_a, corrupt_l1, corrupt_meta)
    corrupt_meta.write_text("{", encoding="utf-8")
    corrupt_l1_sha = digest(corrupt_l1)
    corrupt_meta_sha = digest(corrupt_meta)
    case = expect_runtime(lambda: bind(source_a, corrupt_l1, corrupt_meta), "corrupt_sidecar", [source_a, corrupt_l1, corrupt_meta])
    case["pass"] = bool(case["pass"] and digest(corrupt_l1) == corrupt_l1_sha and digest(corrupt_meta) == corrupt_meta_sha)
    cases.append(case)

    overlap_source = digest(source_a)
    other_meta = root / "overlap-db-meta.json"
    case = expect_runtime(lambda: bind(source_a, source_a, other_meta), "overlap_b6_vs_l1", [source_a])
    case["pass"] = bool(case["pass"] and digest(source_a) == overlap_source and not other_meta.exists())
    cases.append(case)

    side_l1 = root / "overlap-side" / "derived.sqlite"
    case = expect_runtime(lambda: bind(source_a, side_l1, source_a), "overlap_b6_vs_sidecar", [source_a])
    case["pass"] = bool(case["pass"] and digest(source_a) == overlap_source and not side_l1.exists())
    cases.append(case)

    report = root / "out" / "l1_tp_result.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_bytes(b"fixed-report-input")
    report_sha = digest(report)
    report_tmp = Path(str(report) + ".tmp")
    outputs = (
        ("final report", report),
        ("final report temp", report_tmp),
    )
    fixed = (("funding-db", report), ("manifest", source_a))
    case = expect_runtime(lambda: verify(outputs, fixed), "overlap_funding_vs_report_verify", [report, source_a])
    case["pass"] = bool(case["pass"] and digest(report) == report_sha)
    cases.append(case)
    case = expect_runtime(lambda: discard(report, fixed), "overlap_funding_vs_report_discard", [report, source_a])
    case["pass"] = bool(case["pass"] and digest(report) == report_sha and report.exists())
    cases.append(case)

    report_tmp.write_bytes(b"fixed-report-tmp-input")
    tmp_sha = digest(report_tmp)
    report_sha = digest(report)
    outputs = (
        ("final report", report),
        ("final report temp", report_tmp),
    )
    fixed = (("funding-db", report_tmp),)
    case = expect_runtime(lambda: verify(outputs, fixed), "overlap_funding_vs_report_tmp_verify", [report, report_tmp, source_a])
    case["pass"] = bool(case["pass"] and digest(report_tmp) == tmp_sha and digest(report) == report_sha and digest(source_a) == overlap_source)
    cases.append(case)
    case = expect_runtime(
        lambda: discard(report, fixed),
        "overlap_funding_vs_report_tmp_discard",
        [report, report_tmp, source_a],
    )
    case["pass"] = bool(
        case["pass"]
        and report.exists() and digest(report) == report_sha
        and report_tmp.exists() and digest(report_tmp) == tmp_sha
        and digest(source_a) == overlap_source
    )
    cases.append(case)

    same = root / "same-output.sqlite"
    make_sqlite(same, b"same-output")
    same_sha = digest(same)
    case = expect_runtime(
        lambda: verify((("L1_DB", same), ("final report", same)), (("funding-db", source_a),)),
        "overlap_output_vs_output",
        [same, source_a],
    )
    case["pass"] = bool(case["pass"] and digest(same) == same_sha and digest(source_a) == overlap_source)
    cases.append(case)

    alias = root / "source_a_alias.sqlite"
    alias.symlink_to(source_a)
    case = expect_runtime(
        lambda: verify((("L1_DB", alias),), (("funding-db", source_a),)),
        "overlap_symlink_alias",
        [source_a],
    )
    case["pass"] = bool(case["pass"] and digest(source_a) == overlap_source and alias.is_symlink())
    cases.append(case)

    return {
        "scope": "function layer of unmodified DB and path guards; two synthetic sqlite files; not full main()",
        "file_sha256": sha_file(study),
        "line_spans": {name: {"lstart": item["lstart"], "lend": item["lend"]} for name, item in symbols.items()},
        "cases": cases,
        "pass": all(case["pass"] for case in cases),
    }


def main():
    code_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    pins = []
    for name, expected in PINNED_SHA256.items():
        actual = sha_file(code_dir / name)
        pins.append({"file": name, "expected": expected, "actual": actual, "pass": actual == expected})
    if not all(item["pass"] for item in pins):
        payload = {
            "fixed_commit": FIXED_COMMIT,
            "overall": "FAIL",
            "reason": "target file SHA-256 does not match the fixed commit",
            "pins": pins,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        raise SystemExit(1)

    transport = TransportGuard()
    work = Path(tempfile.mkdtemp(prefix="syn-hardening-"))
    try:
        transport.install()
        net = run_syn_net(code_dir, transport)
        transport.restore()
        manifest = run_syn_manifest(code_dir, work)
        db = run_syn_db(code_dir, work)
    finally:
        transport.restore()
        shutil.rmtree(work, ignore_errors=True)

    harness_sha = sha_file(Path(__file__).resolve())
    payload = {
        "fixed_commit": FIXED_COMMIT,
        "scope_note": "Packaging refusal checks only. FIB-4H-LONG-V3 remains NO-GO. LONG-STRUCT-02 is not implemented. Candidates, strategy rules, costs, and full history remain 待驗.",
        "harness_sha256": harness_sha,
        "pins": pins,
        "groups": {
            "SYN-NET-01": net,
            "SYN-MANIFEST-02": manifest,
            "SYN-DB-03": db,
        },
        "overall": "PASS" if net["pass"] and manifest["pass"] and db["pass"] else "FAIL",
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if payload["overall"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
