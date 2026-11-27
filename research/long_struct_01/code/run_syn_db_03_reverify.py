#!/usr/bin/env python3
"""DB-only re-verification of SYN-DB-03.

Stdlib only. Does not run SYN-NET-01 or SYN-MANIFEST-02, does not import
strategy, shared_risk, or engine modules, and does not call the study main()
loop. The outer transport blocker stays installed until every sub-case ends.
"""

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

WANTED = (
    "sha",
    "_paths_overlap",
    "_verify_output_paths_disjoint",
    "_atomic_write_text",
    "_discard_final_report",
    "_bind_isolated_funding_db",
)
BANNED = (
    "FIB_4H_Long_v3",
    "shared_risk",
    "b6_sim_portable",
    "sim_50k_v3_2_sl_fix",
    "audit_v3_1_full",
    "run_q38_audit_01",
)


class Sentinel:
    def __init__(self):
        self.transport_hits = []
        self.module_sentinel_hits = []
        self._saved = None

    def install(self):
        import http.client
        import socket
        import urllib.request
        self._saved = (
            socket.create_connection,
            socket.socket.connect,
            socket.socket.connect_ex,
            urllib.request.urlopen,
            http.client.HTTPConnection.connect,
            http.client.HTTPSConnection.connect,
        )

        def blocked(kind):
            def inner(*_args, **_kwargs):
                self.transport_hits.append(kind)
                raise RuntimeError("synthetic transport blocked: " + kind)
            return inner

        socket.create_connection = blocked("socket.create_connection")
        socket.socket.connect = blocked("socket.socket.connect")
        socket.socket.connect_ex = blocked("socket.socket.connect_ex")
        urllib.request.urlopen = blocked("urllib.request.urlopen")
        http.client.HTTPConnection.connect = blocked("http.client.HTTPConnection.connect")
        http.client.HTTPSConnection.connect = blocked("http.client.HTTPSConnection.connect")

        sentinel = self

        class Finder:
            def find_spec(self, fullname, path, target=None):
                root = fullname.split(".")[0]
                if root in BANNED or fullname in BANNED:
                    sentinel.module_sentinel_hits.append(fullname)
                return None

        sys.meta_path.insert(0, Finder())
        self._finder = Finder

    def restore(self):
        if self._saved is None:
            return
        import http.client
        import socket
        import urllib.request
        (
            socket.create_connection,
            socket.socket.connect,
            socket.socket.connect_ex,
            urllib.request.urlopen,
            http.client.HTTPConnection.connect,
            http.client.HTTPSConnection.connect,
        ) = self._saved
        self._saved = None
        if getattr(self, "_finder", None) in sys.meta_path:
            sys.meta_path.remove(self._finder)


def sha_file(path: Path):
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def watch(items):
    state = {}
    for label, path in items:
        state[label] = {"exists": os.path.lexists(path), "sha256": sha_file(path)}
    return state


def extract(path: Path):
    text = path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    found = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in WANTED:
            found[node.name] = {
                "lstart": node.lineno,
                "lend": node.end_lineno,
                "source": "".join(lines[node.lineno - 1:node.end_lineno]),
            }
    missing = [name for name in WANTED if name not in found]
    if missing:
        raise RuntimeError("missing extracted helpers: " + ", ".join(missing))
    return found


def load_helpers(symbols):
    ns = {"Path": Path, "os": os, "json": json, "shutil": shutil, "hashlib": hashlib}
    seen = []
    for name in WANTED:
        source = symbols[name]["source"]
        if source in seen:
            continue
        seen.append(source)
        exec(compile(source, "<extracted:" + name + ">", "exec"), ns)
    return ns


def make_sqlite(path: Path, marker: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE IF NOT EXISTS synthetic (marker BLOB)")
    conn.execute("DELETE FROM synthetic")
    conn.execute("INSERT INTO synthetic VALUES (?)", (marker,))
    conn.commit()
    conn.close()


def unchanged(before, after):
    return before == after


def run_case(label, action, watched, expect_error):
    before = watch(watched)
    caught = None
    try:
        action()
        actual = "returned without error"
    except Exception as exc:
        caught = exc
        actual = type(exc).__name__ + ": " + str(exc)
    after = watch(watched)
    same = unchanged(before, after)
    if expect_error:
        ok = isinstance(caught, RuntimeError) and same
    else:
        ok = caught is None
    return {
        "label": label,
        "expected": "RuntimeError and watched files unchanged" if expect_error else "success with recorded before/after state",
        "actual": actual,
        "exception": None if caught is None else type(caught).__name__,
        "before": before,
        "after": after,
        "pass": ok,
    }


def both_reports_held(case, report_label, tmp_label):
    before = case["before"]
    after = case["after"]
    for label in (report_label, tmp_label):
        if not before[label]["exists"] or not after[label]["exists"]:
            return False
        if before[label]["sha256"] != after[label]["sha256"]:
            return False
    return True


def main():
    started = datetime.now(timezone.utc).isoformat()
    json_out = None
    args = sys.argv[1:]
    code_dir = Path(__file__).resolve().parent
    if "--json-out" in args:
        json_out = Path(args[args.index("--json-out") + 1])
    if args and not args[0].startswith("--"):
        code_dir = Path(args[0]).resolve()

    sentinel = Sentinel()
    sentinel.install()
    work = Path(tempfile.mkdtemp(prefix="syn-db03-"))
    cases = []
    symbols = {}
    study_sha = None
    error = None
    try:
        study = code_dir / "run_l1_tp_study.py"
        study_sha = sha_file(study)
        symbols = extract(study)
        ns = load_helpers(symbols)
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

        create_l1 = root / "create" / "funding_archive_l1_isolated.sqlite"
        create_meta = Path(str(create_l1) + ".source_meta.json")
        create_watched = (("source_a", source_a), ("l1_db", create_l1), ("sidecar", create_meta))
        before_create = watch(create_watched)
        created = bind(source_a, create_l1, create_meta)
        after_create = watch(create_watched)
        meta_body = json.loads(create_meta.read_text(encoding="utf-8"))
        cases.append({
            "label": "control_clean_bind_create",
            "expected": "sidecar records source and derived hashes; source_a unchanged",
            "actual": "created" if created == digest(source_a) else "unexpected return",
            "exception": None,
            "before": before_create,
            "after": after_create,
            "pass": bool(
                created == digest(source_a)
                and before_create["source_a"] == after_create["source_a"]
                and after_create["l1_db"]["exists"]
                and after_create["sidecar"]["exists"]
                and meta_body.get("b6_source_sha256") == digest(source_a)
                and meta_body.get("derived_l1_db_sha256") == digest(create_l1)
            ),
        })

        reuse_watched = (("source_a", source_a), ("l1_db", create_l1), ("sidecar", create_meta))
        before_reuse = watch(reuse_watched)
        reused = bind(source_a, create_l1, create_meta)
        after_reuse = watch(reuse_watched)
        cases.append({
            "label": "control_clean_bind_reuse",
            "expected": "source_a, l1_db, and sidecar exists+sha256 unchanged",
            "actual": "reused" if reused == created else "unexpected return",
            "exception": None,
            "before": before_reuse,
            "after": after_reuse,
            "pass": bool(reused == created and before_reuse == after_reuse),
        })

        cases.append(run_case(
            "source_changed_rejected",
            lambda: bind(source_b, create_l1, create_meta),
            (("source_a", source_a), ("source_b", source_b), ("l1_db", create_l1), ("sidecar", create_meta)),
            True,
        ))

        mutated = root / "mutated" / "funding_archive_l1_isolated.sqlite"
        mutated_meta = Path(str(mutated) + ".source_meta.json")
        bind(source_a, mutated, mutated_meta)
        mutated.write_bytes(mutated.read_bytes() + b"mutated")
        cases.append(run_case(
            "stale_sidecar_derived_mutated_rejected",
            lambda: bind(source_a, mutated, mutated_meta),
            (("source_a", source_a), ("l1_db", mutated), ("sidecar", mutated_meta)),
            True,
        ))

        missing_l1 = root / "missing-meta" / "funding_archive_l1_isolated.sqlite"
        missing_meta = Path(str(missing_l1) + ".source_meta.json")
        bind(source_a, missing_l1, missing_meta)
        missing_meta.unlink()
        cases.append(run_case(
            "missing_sidecar_rejected",
            lambda: bind(source_a, missing_l1, missing_meta),
            (("source_a", source_a), ("l1_db", missing_l1), ("sidecar", missing_meta)),
            True,
        ))

        corrupt_l1 = root / "corrupt" / "funding_archive_l1_isolated.sqlite"
        corrupt_meta = Path(str(corrupt_l1) + ".source_meta.json")
        bind(source_a, corrupt_l1, corrupt_meta)
        corrupt_meta.write_text("{", encoding="utf-8")
        cases.append(run_case(
            "corrupt_sidecar_rejected",
            lambda: bind(source_a, corrupt_l1, corrupt_meta),
            (("source_a", source_a), ("l1_db", corrupt_l1), ("sidecar", corrupt_meta)),
            True,
        ))

        other_meta = root / "overlap-db-meta.json"
        cases.append(run_case(
            "overlap_b6_with_l1_db",
            lambda: bind(source_a, source_a, other_meta),
            (("source_a", source_a), ("sidecar", other_meta)),
            True,
        ))

        side_l1 = root / "overlap-side" / "derived.sqlite"
        cases.append(run_case(
            "overlap_b6_with_sidecar",
            lambda: bind(source_a, side_l1, source_a),
            (("source_a", source_a), ("l1_db", side_l1)),
            True,
        ))

        report = root / "out" / "l1_tp_result.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_bytes(b"fixed-report-input")
        report_tmp = Path(str(report) + ".tmp")
        report_tmp.write_bytes(b"fixed-report-tmp-input")
        report_outputs = (("final report", report), ("final report temp", report_tmp))
        report_watched = (("l1_tp_result.json", report), ("l1_tp_result.json.tmp", report_tmp), ("source_a", source_a))

        def run_both(label, fixed):
            before = watch(report_watched)
            messages = []
            raised = 0
            for fn in (lambda: verify(report_outputs, fixed), lambda: discard(report, fixed)):
                try:
                    fn()
                    messages.append("returned without error")
                except RuntimeError as exc:
                    raised += 1
                    messages.append(str(exc))
                except Exception as exc:
                    messages.append(type(exc).__name__ + ": " + str(exc))
            after = watch(report_watched)
            case = {
                "label": label,
                "expected": "verify and discard each raise RuntimeError; report and tmp exists+sha256 unchanged",
                "actual": " | ".join(messages),
                "exception": "RuntimeError" if raised == 2 else None,
                "before": before,
                "after": after,
                "pass": False,
            }
            case["pass"] = bool(raised == 2 and both_reports_held(case, "l1_tp_result.json", "l1_tp_result.json.tmp") and before["source_a"] == after["source_a"])
            return case

        cases.append(run_both("overlap_funding_db_with_final_report", (("funding-db", report), ("manifest", source_a))))
        cases.append(run_both("overlap_funding_db_with_final_report_tmp", (("funding-db", report_tmp),)))

        same = root / "same-output.sqlite"
        make_sqlite(same, b"same-output")
        cases.append(run_case(
            "overlap_output_with_output",
            lambda: verify((("L1_DB", same), ("final report", same)), (("funding-db", source_a),)),
            (("same_output", same), ("source_a", source_a)),
            True,
        ))

        alias = root / "source_a_alias.sqlite"
        alias.symlink_to(source_a)
        cases.append(run_case(
            "overlap_symlink_alias_with_fixed_input",
            lambda: verify((("L1_DB", alias),), (("funding-db", source_a),)),
            (("source_a", source_a), ("alias", alias)),
            True,
        ))
    except Exception as exc:
        error = type(exc).__name__ + ": " + str(exc)
    finally:
        finished = datetime.now(timezone.utc).isoformat()
        shutil.rmtree(work, ignore_errors=True)
        sentinel.restore()

    payload = {
        "group": "SYN-DB-03",
        "scope": "DB-only function layer. SYN-NET-01 and SYN-MANIFEST-02 were not run. Not full main().",
        "started_utc": started,
        "finished_utc": finished,
        "transport_blocker_active_entire_run": True,
        "transport_hits": list(sentinel.transport_hits),
        "module_sentinel_hits": list(sentinel.module_sentinel_hits),
        "run_l1_tp_study_sha256": study_sha,
        "line_spans": {name: {"lstart": item["lstart"], "lend": item["lend"]} for name, item in symbols.items()},
        "harness_sha256": sha_file(Path(__file__).resolve()),
        "cases": cases,
        "harness_error": error,
        "overall": "PASS" if error is None and cases and all(case["pass"] for case in cases) and not sentinel.transport_hits and not sentinel.module_sentinel_hits else "FAIL",
        "status_note": "FIB-4H-LONG-V3 remains NO-GO. LONG-STRUCT-02 is not implemented. Candidates, strategy rules, costs, and full history remain 待驗.",
    }
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if json_out is not None:
        json_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    if payload["overall"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
