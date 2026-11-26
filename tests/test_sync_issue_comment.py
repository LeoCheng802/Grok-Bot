"""Unit tests for scripts/sync_issue_comment.py."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sync_issue_comment as sync  # noqa: E402


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

    def test_main_reads_event_file_and_skips_other_authors(self) -> None:
        event_path = Path(self.tmp.name) / "event.json"
        event_path.write_text(
            json.dumps(
                {
                    "action": "created",
                    "issue": {"number": 1},
                    "comment": comment(15, "[開單審核] 通過\n細節\n", "2026-11-26T16:40:00Z"),
                }
            ),
            encoding="utf-8",
        )
        env = {
            "GITHUB_EVENT_NAME": "issue_comment",
            "GITHUB_EVENT_PATH": str(event_path),
            "REPORTS_DIR": str(self.reports),
            "GITHUB_REPOSITORY": "LeoCheng802/Grok-Bot",
        }
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(sync.main(), 0)
        latest = (self.reports / "latest.md").read_text(encoding="utf-8")
        self.assertIn("2026-11-27 00:40:00", latest)
        self.assertIn("細節", latest)
        audit = (self.reports / "by-role" / "order-audit.md").read_text(encoding="utf-8")
        self.assertIn("通過", audit)

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
        before = (self.reports / "latest.md").read_text(encoding="utf-8")
        with mock.patch.dict(os.environ, env, clear=False):
            self.assertEqual(sync.main(), 0)
        self.assertEqual((self.reports / "latest.md").read_text(encoding="utf-8"), before)
        self.assertNotIn("外人", before)

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


if __name__ == "__main__":
    unittest.main()
