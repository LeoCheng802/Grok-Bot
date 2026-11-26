"""Unit tests for scripts/sync_issue_comment.py."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.parse
from datetime import timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sync_issue_comment as sync  # noqa: E402


TOKEN = "ghs_reconcile_test_token_do_not_leak"


class ApiResponse:
    def __init__(self, payload: object, link: str = "") -> None:
        self._raw = json.dumps(payload).encode("utf-8")
        self.headers = {"Link": link}

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> "ApiResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def run_main() -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = sync.main()
    return code, stdout.getvalue(), stderr.getvalue()


def report_texts(reports: Path) -> dict[str, str]:
    if not reports.exists():
        return {}
    return {
        path.relative_to(reports).as_posix(): path.read_text(encoding="utf-8")
        for path in reports.rglob("*")
        if path.is_file()
    }


def comment(
    comment_id: int,
    body: str,
    created_at: str,
    updated_at: str | None = None,
    *,
    login: str = "LeoCheng802",
    association: str = "OWNER",
) -> dict:
    return {
        "id": comment_id,
        "body": body,
        "created_at": created_at,
        "updated_at": updated_at or created_at,
        "html_url": (
            "https://github.com/LeoCheng802/Grok-Bot/issues/1"
            f"#issuecomment-{comment_id}"
        ),
        "user": {"login": login},
        "author_association": association,
    }


class RoleAndTimeTests(unittest.TestCase):
    def test_role_tags_map_to_filenames(self) -> None:
        expected = {
            "[復盤] 日內": ("復盤", "review.md"),
            "[執行] 已送出": ("執行", "execution.md"),
            "[開單審核] 通過": ("開單審核", "order-audit.md"),
            "[交易對] BTC": ("交易對", "pairs.md"),
            "[風險管理] 正常": ("風險管理", "risk.md"),
            "[策略組] 研究 12": ("策略組", "strategy.md"),
            "沒有標籤的結論": ("一般", "general.md"),
        }
        for body, (label, filename) in expected.items():
            role = sync.detect_role(body)
            self.assertEqual(role.label, label)
            self.assertEqual(role.filename, filename)

    def test_tag_on_later_line_is_general(self) -> None:
        role = sync.detect_role("今天沒有標籤\n[復盤] 這行不算")
        self.assertEqual(role.filename, "general.md")

    def test_leading_blank_lines_still_see_the_tag(self) -> None:
        role = sync.detect_role("\n\n  [風險管理] 部位檢查\n")
        self.assertEqual(role.filename, "risk.md")

    def test_earlier_tag_on_the_first_line_wins(self) -> None:
        role = sync.detect_role("[執行] 順便提到 [復盤]")
        self.assertEqual(role.filename, "execution.md")

    def test_taipei_conversion_crosses_midnight(self) -> None:
        before = sync.parse_github_time("2026-11-26T15:59:59Z")
        after = sync.parse_github_time("2026-11-26T16:00:00.123Z")
        self.assertEqual(sync.format_taipei(before), "2026-11-26 23:59:59")
        self.assertEqual(sync.taipei_date(before), "2026-11-26")
        self.assertEqual(sync.format_taipei(after), "2026-11-27 00:00:00")
        self.assertEqual(sync.taipei_date(after), "2026-11-27")
        self.assertEqual(sync.to_taipei(after).utcoffset().total_seconds(), 8 * 3600)
        self.assertEqual(before.tzinfo, timezone.utc)

    def test_title_strips_tag_and_truncates(self) -> None:
        role = sync.detect_role("[復盤] " + ("甲" * 90))
        title = sync.extract_title("[復盤] " + ("甲" * 90), role)
        self.assertEqual(len(title), 80)
        self.assertTrue(title.endswith("…"))
        self.assertNotIn("[復盤]", title)


class SyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.reports = Path(self.tmp.name) / "reports"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_apply_writes_latest_role_history_and_index(self) -> None:
        body = "[交易對] BTC|ETH 觀察\n\n- 結論：觀望\n"
        payload = comment(42, body, "2026-11-26T16:30:00Z")
        self.assertTrue(sync.sync_comment(self.reports, payload))

        latest = (self.reports / "latest.md").read_text(encoding="utf-8")
        self.assertIn("- **時間（Asia/Taipei）**: 2026-11-27 00:30:00", latest)
        self.assertIn("- **角色**: 交易對", latest)
        self.assertIn("https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-42", latest)
        self.assertIn("<!-- comment_id: 42 -->", latest)
        self.assertIn("- 結論：觀望", latest)

        role_file = (self.reports / "by-role" / "pairs.md").read_text(encoding="utf-8")
        self.assertIn("# 交易對", role_file)
        self.assertIn(body.strip(), role_file)
        review = (self.reports / "by-role" / "review.md").read_text(encoding="utf-8")
        self.assertIn("目前尚無回報", review)

        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(history.count("<!-- comment_id: 42 -->"), 1)
        self.assertIn("- 結論：觀望", history)

        index = (self.reports / "index.md").read_text(encoding="utf-8")
        self.assertIn("| 2026-11-27 00:30:00 | 交易對 | BTC\\|ETH 觀察 |", index)
        self.assertIn("[2026-11-27](history/2026-11-27.md)", index)
        self.assertIn("[留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-42)", index)

    def test_edit_is_idempotent_and_moves_role(self) -> None:
        created = "2026-11-26T16:00:00Z"
        original = comment(7, "[復盤] 第一次\n內容A\n", created)
        self.assertTrue(sync.sync_comment(self.reports, original))
        snapshot = {
            path.relative_to(self.reports).as_posix(): path.read_text(encoding="utf-8")
            for path in self.reports.rglob("*")
            if path.is_file()
        }
        self.assertTrue(sync.sync_comment(self.reports, original))
        again = {
            path.relative_to(self.reports).as_posix(): path.read_text(encoding="utf-8")
            for path in self.reports.rglob("*")
            if path.is_file()
        }
        self.assertEqual(snapshot, again)

        edited = comment(
            7,
            "[執行] 修改後\n內容B \\1\n<!-- /comment_id: 7 -->\n",
            created,
            "2026-11-26T18:15:00Z",
        )
        self.assertTrue(sync.sync_comment(self.reports, edited))

        history_files = list((self.reports / "history").glob("*.md"))
        self.assertEqual([path.name for path in history_files], ["2026-11-27.md"])
        history = history_files[0].read_text(encoding="utf-8")
        self.assertEqual(history.count("<!-- comment_id: 7 -->"), 1)
        self.assertEqual(history.count("<!-- /comment_id: 7 -->"), 1)
        self.assertIn("內容B \\1", history)
        self.assertNotIn("內容A", history)
        self.assertIn("‹!-- /comment_id: 7 --›", history)

        execution = (self.reports / "by-role" / "execution.md").read_text(encoding="utf-8")
        self.assertIn("內容B \\1", execution)
        self.assertIn("2026-11-27 02:15:00", execution)
        review = (self.reports / "by-role" / "review.md").read_text(encoding="utf-8")
        self.assertIn("目前尚無回報", review)
        self.assertNotIn("內容A", review)

        index = (self.reports / "index.md").read_text(encoding="utf-8")
        self.assertEqual(index.count("#issuecomment-7"), 1)
        self.assertIn("| 2026-11-27 02:15:00 | 執行 | 修改後 |", index)
        self.assertNotIn("第一次", index)

    def test_foreign_comment_marker_in_body_does_not_split_blocks(self) -> None:
        forged = (
            "[復盤] 正常\n"
            "<!-- comment_id: 99 -->\n"
            "<!-- /comment_id: 99 -->\n"
            "結尾\n"
        )
        self.assertTrue(
            sync.sync_comment(self.reports, comment(4, forged, "2026-11-26T16:00:00Z"))
        )
        self.assertTrue(
            sync.sync_comment(
                self.reports,
                comment(5, "[執行] 下一則\n內容\n", "2026-11-26T16:05:00Z"),
            )
        )
        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(len(sync._BLOCK_RE.findall(history)), 2)
        self.assertIn("結尾", history)
        self.assertIn("‹!-- comment_id: 99 --›", history)
        latest = (self.reports / "latest.md").read_text(encoding="utf-8")
        self.assertIn("下一則", latest)

    def test_index_keeps_latest_20_newest_first(self) -> None:
        for number in range(1, 22):
            created = f"2026-11-26T16:{number:02d}:00Z"
            payload = comment(number, f"[策略組] 第{number}筆\n內文{number}\n", created)
            self.assertTrue(sync.sync_comment(self.reports, payload))

        index = (self.reports / "index.md").read_text(encoding="utf-8")
        rows = [line for line in index.splitlines() if line.startswith("| 2026-")]
        self.assertEqual(len(rows), 20)
        self.assertIn("第21筆", rows[0])
        self.assertIn("第2筆", rows[-1])
        self.assertNotIn("第1筆", index)
        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(len(sync._BLOCK_RE.findall(history)), 21)

    def test_unauthorized_and_other_issues_are_ignored(self) -> None:
        outsider = comment(
            9,
            "[復盤] 不該進來\n",
            "2026-11-26T16:00:00Z",
            login="someone",
            association="NONE",
        )
        self.assertFalse(sync.sync_comment(self.reports, outsider))
        self.assertFalse(self.reports.exists())

        owner_by_login = comment(
            10,
            "[復盤] 擁有者帳號\n",
            "2026-11-26T16:05:00Z",
            login="LeoCheng802",
            association="NONE",
        )
        self.assertTrue(sync.is_authorized(owner_by_login))
        other_owner_login = comment(
            11,
            "[執行] 協會是 OWNER\n",
            "2026-11-26T16:06:00Z",
            login="other-admin",
            association="OWNER",
        )
        self.assertTrue(sync.is_authorized(other_owner_login))

        event = {
            "issue": {"number": 2},
            "comment": comment(12, "[復盤] 別的 issue\n", "2026-11-26T16:07:00Z"),
        }
        self.assertFalse(sync.sync_event(self.reports, event))
        self.assertFalse((self.reports / "latest.md").exists())

    def test_main_skips_unauthorized_events_without_calling_api(self) -> None:
        event_path = Path(self.tmp.name) / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "action": "created",
                    "issue": {"number": 1},
                    "comment": comment(
                        16,
                        "[復盤] 外人\n",
                        "2026-11-26T17:00:00Z",
                        login="visitor",
                        association="NONE",
                    ),
                }
            ),
            encoding="utf-8",
        )
        env = {
            "GITHUB_EVENT_NAME": "issue_comment",
            "GITHUB_EVENT_PATH": str(event_path),
            "REPORTS_DIR": str(self.reports),
            "GITHUB_REPOSITORY": "LeoCheng802/Grok-Bot",
            "GITHUB_TOKEN": TOKEN,
        }
        with mock.patch.dict(os.environ, env, clear=False):
            with mock.patch.object(sync, "urlopen") as opened:
                code, stdout, stderr = run_main()
        self.assertEqual(code, 0)
        opened.assert_not_called()
        self.assertIn("略過", stdout)
        self.assertNotIn(TOKEN, stdout + stderr)
        self.assertFalse((self.reports / "latest.md").exists())

    def test_next_link_stays_on_github_api(self) -> None:
        header = (
            '<https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments?page=2>; rel="next", '
            '<https://evil.example/comments?page=2>; rel="prev"'
        )
        self.assertEqual(
            sync._next_link(header),
            "https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments?page=2",
        )
        self.assertIsNone(
            sync._next_link('<https://evil.example/steal>; rel="next"')
        )

    def test_placeholders_match_empty_refresh(self) -> None:
        sync.refresh_views(self.reports)
        self.assertEqual(
            (self.reports / "latest.md").read_text(encoding="utf-8"),
            sync.EMPTY_LATEST,
        )
        self.assertIn("目前尚無回報", (self.reports / "index.md").read_text(encoding="utf-8"))
        for role in sync.ALL_ROLES:
            text = (self.reports / "by-role" / role.filename).read_text(encoding="utf-8")
            self.assertEqual(text, sync.empty_role(role))
        self.assertTrue((self.reports / "history" / ".gitkeep").is_file())


class RebuildTests(unittest.TestCase):
    def test_rebuild_filters_and_orders_owner_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            comments = [
                comment(2, "[執行] 第二\n", "2026-11-26T16:02:00Z"),
                comment(
                    1,
                    "[復盤] 第一\n",
                    "2026-11-26T16:01:00Z",
                    login="stranger",
                    association="CONTRIBUTOR",
                ),
                comment(3, "[復盤] 第三\n", "2026-11-26T16:03:00Z", login="LeoCheng802", association="NONE"),
            ]
            count = sync.rebuild_owner_comments(reports, comments, repo="LeoCheng802/Grok-Bot")
            self.assertEqual(count, 2)
            latest = (reports / "latest.md").read_text(encoding="utf-8")
            self.assertIn("第三", latest)
            self.assertNotIn("第一", latest)
            history = (reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
            self.assertLess(history.index("comment_id: 2"), history.index("comment_id: 3"))


class PaginationTests(unittest.TestCase):
    def test_fetch_merges_every_page_and_drops_secret_query(self) -> None:
        outsider = comment(
            50,
            "[復盤] 外人\n",
            "2026-11-26T16:00:00Z",
            login="visitor",
            association="NONE",
        )
        first = comment(1, "[執行] 第一頁\n", "2026-11-26T16:01:00Z")
        second = comment(2, "[交易對] 第二頁\n", "2026-11-26T16:02:00Z")
        third = comment(3, "[策略組] 第三頁\n", "2026-11-26T16:03:00Z")
        pages = {
            1: [first, outsider],
            2: [second],
            3: [third],
        }
        seen: list[str] = []

        def fake(request, timeout=30):
            self.assertEqual(timeout, 30)
            self.assertTrue(request.get_header("Authorization") == f"Bearer {TOKEN}")
            seen.append(request.full_url)
            self.assertNotIn(TOKEN, request.full_url)
            self.assertNotIn("access_token", request.full_url)
            query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(request.full_url).query))
            page = int(query.get("page", "1"))
            link = ""
            if page == 1:
                link = (
                    "<https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments"
                    f"?page=2&access_token={TOKEN}>; rel=\"next\""
                )
            elif page == 2:
                link = (
                    "<https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments"
                    "?per_page=100&page=3>; rel=\"next\""
                )
            return ApiResponse(pages[page], link)

        with mock.patch.object(sync, "urlopen", fake):
            listed = sync.fetch_issue_comments("LeoCheng802/Grok-Bot", 1, TOKEN)
        self.assertEqual([item["id"] for item in listed], [1, 50, 2, 3])
        self.assertEqual(len(seen), 3)
        self.assertTrue(all("api.github.com" in url for url in seen))
        self.assertTrue(all(TOKEN not in url for url in seen))

        with tempfile.TemporaryDirectory() as tmp:
            reports = Path(tmp) / "reports"
            count = sync.rebuild_owner_comments(
                reports, listed, repo="LeoCheng802/Grok-Bot"
            )
            self.assertEqual(count, 3)
            history = (reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
            self.assertNotIn("外人", history)
            self.assertEqual(history.count("<!-- comment_id:"), 3)
            blob = "\n".join(report_texts(reports).values())
            self.assertNotIn(TOKEN, blob)

    def test_full_page_without_link_continues_until_a_short_page(self) -> None:
        pages = {
            1: [comment(1, "[執行] 一\n", "2026-11-26T16:01:00Z")],
            2: [comment(2, "[風險管理] 二\n", "2026-11-26T16:02:00Z")],
            3: [],
        }

        def fake(request, timeout=30):
            query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(request.full_url).query))
            page = int(query["page"])
            return ApiResponse(pages[page], "")

        with mock.patch.object(sync, "COMMENTS_PER_PAGE", 1):
            with mock.patch.object(sync, "urlopen", fake):
                listed = sync.fetch_issue_comments("LeoCheng802/Grok-Bot", 1, TOKEN)
        self.assertEqual([item["id"] for item in listed], [1, 2])

    def test_page_cap_does_not_return_a_partial_list_or_the_token(self) -> None:
        def fake(request, timeout=30):
            link = (
                "<https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments"
                "?page=2>; rel=\"next\""
            )
            return ApiResponse(
                [comment(1, "[執行] 滿頁\n", "2026-11-26T16:01:00Z")],
                link,
            )

        with mock.patch.object(sync, "MAX_COMMENT_PAGES", 1):
            with mock.patch.object(sync, "urlopen", fake):
                with self.assertRaises(sync.SyncError) as caught:
                    sync.fetch_issue_comments("LeoCheng802/Grok-Bot", 1, TOKEN)
        self.assertIn("too many comment pages", str(caught.exception))
        self.assertNotIn(TOKEN, str(caught.exception))
        self.assertNotIn("Authorization", str(caught.exception))


class ReconcileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.reports = Path(self.tmp.name) / "reports"
        self.event_path = Path(self.tmp.name) / "event.json"
        self.api_comments = [
            comment(7199008844, "[執行] 執行連線測試\n執行內文\n", "2026-11-26T17:26:03Z"),
            comment(7199012308, "[交易對] 交易對連線測試\n交易對內文\n", "2026-11-26T17:26:10Z"),
            comment(
                7199013635,
                "[開單審核] 開單審核連線測試\n開單審核內文\n",
                "2026-11-26T17:26:13Z",
            ),
            comment(
                7199015670,
                "[風險管理] 風險管理連線測試\n風險管理內文\n",
                "2026-11-26T17:26:17Z",
            ),
            comment(7199016066, "[策略組] 策略組連線測試\n策略組內文\n", "2026-11-26T17:26:18Z"),
            comment(7199107969, "[復盤] 復盤連線測試\n復盤內文\n", "2026-11-26T17:29:30Z"),
        ]
        self.outsider = comment(
            7199019999,
            "[復盤] 外人不要進來\n",
            "2026-11-26T17:27:00Z",
            login="visitor",
            association="NONE",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _env(self, event_name: str = "issue_comment") -> dict[str, str]:
        return {
            "GITHUB_EVENT_NAME": event_name,
            "GITHUB_EVENT_PATH": str(self.event_path),
            "REPORTS_DIR": str(self.reports),
            "GITHUB_REPOSITORY": "LeoCheng802/Grok-Bot",
            "GITHUB_TOKEN": TOKEN,
            "GH_TOKEN": "",
        }

    def _write_event(self, payload: dict) -> None:
        self.event_path.write_text(json.dumps(payload), encoding="utf-8")

    def _fake_api(self, request, timeout=30):
        self.assertTrue(request.get_header("Authorization") == f"Bearer {TOKEN}")
        self.assertNotIn(TOKEN, request.full_url)
        self.assertNotIn("Authorization", request.full_url)
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(request.full_url).query))
        page = int(query.get("page", "1"))
        chunks = [
            [self.api_comments[0], self.outsider, self.api_comments[1]],
            [self.api_comments[2], self.api_comments[3]],
            [self.api_comments[4], self.api_comments[5]],
        ]
        if page > len(chunks):
            return ApiResponse([], "")
        link = ""
        if page < len(chunks):
            link = (
                "<https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments"
                f"?per_page=100&page={page + 1}>; rel=\"next\""
            )
        return ApiResponse(chunks[page - 1], link)

    def _run(self, event_name: str = "issue_comment") -> tuple[int, str, str]:
        env = self._env(event_name)
        # clear=True drops a real token that the surrounding process may have.
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen", self._fake_api):
                return run_main()

    def test_rebuild_twice_does_not_duplicate_blocks_or_index_rows(self) -> None:
        original = comment(7, "[復盤] 第一次\n內容A\n", "2026-11-26T16:00:00Z")
        edited = comment(
            7,
            "[執行] 修改後\n內容B\n",
            "2026-11-26T16:00:00Z",
            "2026-11-26T18:15:00Z",
        )
        duplicate = comment(7, "[復盤] 第一次\n內容A\n", "2026-11-26T16:00:00Z")
        outsider = comment(
            8,
            "[風險管理] 不該留下\n",
            "2026-11-26T16:05:00Z",
            login="visitor",
            association="NONE",
        )
        sync.rebuild_owner_comments(
            self.reports, [original, outsider], repo="LeoCheng802/Grok-Bot"
        )
        first = report_texts(self.reports)
        sync.rebuild_owner_comments(
            self.reports,
            [outsider, duplicate, original],
            repo="LeoCheng802/Grok-Bot",
        )
        self.assertEqual(first, report_texts(self.reports))

        sync.rebuild_owner_comments(
            self.reports, [edited, edited], repo="LeoCheng802/Grok-Bot"
        )
        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(history.count("<!-- comment_id: 7 -->"), 1)
        self.assertEqual(history.count("<!-- /comment_id: 7 -->"), 1)
        self.assertIn("內容B", history)
        self.assertNotIn("內容A", history)
        index = (self.reports / "index.md").read_text(encoding="utf-8")
        self.assertEqual(index.count("#issuecomment-7"), 1)
        self.assertEqual(len([line for line in index.splitlines() if line.startswith("| 2026-")]), 1)
        execution = (self.reports / "by-role" / "execution.md").read_text(encoding="utf-8")
        self.assertIn("內容B", execution)
        review = (self.reports / "by-role" / "review.md").read_text(encoding="utf-8")
        self.assertIn("目前尚無回報", review)

        again = report_texts(self.reports)
        sync.rebuild_owner_comments(
            self.reports, [edited], repo="LeoCheng802/Grok-Bot"
        )
        self.assertEqual(again, report_texts(self.reports))

    def test_cancelled_jobs_are_backfilled_by_the_next_success(self) -> None:
        # 先前成功的任務只留下這四則；開單審核與風險管理的任務在排隊時被取消。
        landed = [
            self.api_comments[0],
            self.api_comments[1],
            self.api_comments[4],
            self.api_comments[5],
        ]
        for payload in landed:
            self.assertTrue(sync.sync_comment(self.reports, payload))
        self.assertIn(
            "目前尚無回報",
            (self.reports / "by-role" / "order-audit.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "目前尚無回報",
            (self.reports / "by-role" / "risk.md").read_text(encoding="utf-8"),
        )

        # 最後一次成功的任務是復盤那一則留言觸發的，但對帳必須補回全部角色。
        self._write_event(
            {
                "action": "created",
                "issue": {"number": 1},
                "comment": self.api_comments[5],
            }
        )
        code, stdout, stderr = self._run()
        self.assertEqual(code, 0)
        self.assertIn("6 則擁有者留言", stdout)
        self._assert_six_roles()
        self._assert_no_secret(stdout, stderr)
        snapshot = report_texts(self.reports)

        code, stdout, stderr = self._run()
        self.assertEqual(code, 0)
        self.assertEqual(snapshot, report_texts(self.reports))
        self._assert_no_secret(stdout, stderr)

        self.api_comments[2] = comment(
            7199013635,
            "[開單審核] 開單審核已更新\n審核更新內文\n",
            "2026-11-26T17:26:13Z",
            "2026-11-26T18:00:00Z",
        )
        self._write_event(
            {
                "action": "edited",
                "issue": {"number": 1},
                "comment": self.api_comments[2],
            }
        )
        code, stdout, stderr = self._run()
        self.assertEqual(code, 0)
        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(history.count("<!-- comment_id: 7199013635 -->"), 1)
        self.assertIn("審核更新內文", history)
        self.assertNotIn("開單審核內文", history)
        audit = (self.reports / "by-role" / "order-audit.md").read_text(encoding="utf-8")
        self.assertIn("審核更新內文", audit)
        self.assertIn("2026-11-27 02:00:00", audit)
        self._assert_no_secret(stdout, stderr)

        edited_snapshot = report_texts(self.reports)
        code, _stdout, _stderr = self._run()
        self.assertEqual(code, 0)
        self.assertEqual(edited_snapshot, report_texts(self.reports))

    def test_non_reconciling_events_do_not_fetch_or_leak_the_token(self) -> None:
        self._write_event(
            {
                "action": "deleted",
                "issue": {"number": 1},
                "comment": self.api_comments[2],
            }
        )
        env = self._env()
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen") as opened:
                code, stdout, stderr = run_main()
        self.assertEqual(code, 0)
        opened.assert_not_called()
        self.assertIn("略過", stdout)
        self.assertFalse(self.reports.exists())
        self._assert_no_secret(stdout, stderr)

        self._write_event(
            {
                "action": "created",
                "issue": {"number": 2},
                "comment": self.api_comments[2],
            }
        )
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen") as opened:
                code, stdout, stderr = run_main()
        self.assertEqual(code, 0)
        opened.assert_not_called()
        self._assert_no_secret(stdout, stderr)

    def test_workflow_dispatch_reconciles_without_an_event_comment(self) -> None:
        self._write_event({"ref": "main"})
        code, stdout, stderr = self._run("workflow_dispatch")
        self.assertEqual(code, 0)
        self.assertIn("6 則擁有者留言", stdout)
        self._assert_six_roles()
        self._assert_no_secret(stdout, stderr)

    def test_missing_token_fails_without_writing_reports(self) -> None:
        self._write_event(
            {
                "action": "created",
                "issue": {"number": 1},
                "comment": self.api_comments[5],
            }
        )
        env = self._env()
        env.pop("GITHUB_TOKEN")
        env.pop("GH_TOKEN")
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen") as opened:
                code, stdout, stderr = run_main()
        self.assertEqual(code, 1)
        opened.assert_not_called()
        self.assertIn("需要 GITHUB_TOKEN", stderr)
        self.assertNotIn("Bearer", stderr)
        self.assertFalse(self.reports.exists())

    def test_http_and_url_errors_do_not_print_the_token(self) -> None:
        self._write_event(
            {
                "action": "created",
                "issue": {"number": 1},
                "comment": self.api_comments[5],
            }
        )
        env = self._env()

        def raise_url(request, timeout=30):
            self.assertTrue(request.get_header("Authorization") == f"Bearer {TOKEN}")
            raise sync.URLError(f"boom Authorization: Bearer {TOKEN}")

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen", raise_url):
                code, stdout, stderr = run_main()
        self.assertEqual(code, 1)
        self.assertFalse(self.reports.exists())
        self._assert_no_secret(stdout, stderr)
        self.assertNotIn("Bearer ghs_", stderr)

        from email.message import Message

        def raise_http_clean(request, timeout=30):
            raise sync.HTTPError(
                "https://api.github.com/repos/LeoCheng802/Grok-Bot/issues/1/comments",
                401,
                f"Unauthorized Authorization: Bearer {TOKEN}",
                Message(),
                io.BytesIO(b""),
            )

        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(sync, "urlopen", raise_http_clean):
                code, stdout, stderr = run_main()
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", stderr)
        self._assert_no_secret(stdout, stderr)
        self.assertNotIn("Unauthorized Authorization", stderr)

    def _assert_six_roles(self) -> None:
        expected = {
            "review.md": ("復盤", "7199107969", "復盤內文"),
            "execution.md": ("執行", "7199008844", "執行內文"),
            "order-audit.md": ("開單審核", "7199013635", "開單審核內文"),
            "pairs.md": ("交易對", "7199012308", "交易對內文"),
            "risk.md": ("風險管理", "7199015670", "風險管理內文"),
            "strategy.md": ("策略組", "7199016066", "策略組內文"),
        }
        for filename, (label, comment_id, body) in expected.items():
            text = (self.reports / "by-role" / filename).read_text(encoding="utf-8")
            self.assertIn(f"# {label}", text)
            self.assertIn(f"<!-- comment_id: {comment_id} -->", text)
            self.assertIn(body, text)
            self.assertNotIn("目前尚無回報", text)
            self.assertNotIn(TOKEN, text)
            self.assertNotIn("外人不要進來", text)

        latest = (self.reports / "latest.md").read_text(encoding="utf-8")
        self.assertIn("<!-- comment_id: 7199107969 -->", latest)
        self.assertIn("復盤內文", latest)
        self.assertIn("2026-11-27 01:29:30", latest)
        self.assertNotIn(TOKEN, latest)

        index = (self.reports / "index.md").read_text(encoding="utf-8")
        rows = [line for line in index.splitlines() if line.startswith("| 2026-")]
        self.assertEqual(
            rows,
            [
                "| 2026-11-27 01:29:30 | 復盤 | 復盤連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199107969) |",
                "| 2026-11-27 01:26:18 | 策略組 | 策略組連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199016066) |",
                "| 2026-11-27 01:26:17 | 風險管理 | 風險管理連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199015670) |",
                "| 2026-11-27 01:26:13 | 開單審核 | 開單審核連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199013635) |",
                "| 2026-11-27 01:26:10 | 交易對 | 交易對連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199012308) |",
                "| 2026-11-27 01:26:03 | 執行 | 執行連線測試 | [2026-11-27](history/2026-11-27.md) | [留言](https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7199008844) |",
            ],
        )
        self.assertNotIn("外人", index)

        history = (self.reports / "history" / "2026-11-27.md").read_text(encoding="utf-8")
        self.assertEqual(len(sync._BLOCK_RE.findall(history)), 6)
        for comment_id in (
            "7199008844",
            "7199012308",
            "7199013635",
            "7199015670",
            "7199016066",
            "7199107969",
        ):
            self.assertEqual(history.count(f"<!-- comment_id: {comment_id} -->"), 1)
            self.assertEqual(history.count(f"<!-- /comment_id: {comment_id} -->"), 1)
        self.assertNotIn("外人不要進來", history)
        self.assertNotIn(TOKEN, history)
        general = (self.reports / "by-role" / "general.md").read_text(encoding="utf-8")
        self.assertIn("目前尚無回報", general)

    def _assert_no_secret(self, *chunks: str) -> None:
        blob = "\n".join([*chunks, *report_texts(self.reports).values()])
        self.assertNotIn(TOKEN, blob)
        self.assertNotIn(f"Bearer {TOKEN}", blob)
        self.assertNotIn("Authorization: Bearer", blob)
        self.assertNotIn("access_token", blob)


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_uses_least_privilege_and_does_not_embed_a_token(self) -> None:
        text = (ROOT / ".github/workflows/sync-reports.yml").read_text(encoding="utf-8")
        permissions: dict[str, str] = {}
        in_permissions = False
        for line in text.splitlines():
            if line.startswith("permissions:"):
                in_permissions = True
                continue
            if in_permissions:
                if line and not line.startswith((" ", "\t")):
                    break
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                key, value = stripped.split(":", 1)
                permissions[key.strip()] = value.strip()
        self.assertEqual(permissions, {"contents": "write", "issues": "read"})
        self.assertIn("group: sync-reports", text)
        self.assertIn("cancel-in-progress: false", text)
        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", text)
        self.assertIn("git diff --staged --quiet", text)
        self.assertIn("沒有需要提交的回報變更。", text)
        self.assertIn("git reset --hard origin/main", text)
        self.assertNotIn("push --force", text)
        self.assertNotIn("push -f", text)
        self.assertNotRegex(text, r"gh[pousr]_[A-Za-z0-9]{8,}")
        self.assertNotRegex(text, r"github_pat_[A-Za-z0-9_]{8,}")
        self.assertNotIn("echo \"$GITHUB_TOKEN\"", text)
        self.assertNotIn("echo $GITHUB_TOKEN", text)
        self.assertEqual(text.count("python scripts/sync_issue_comment.py"), 1)


if __name__ == "__main__":
    unittest.main()
