#!/usr/bin/env python3
"""Sync repository-owner comments on Issue #1 into Markdown reports.

The comment body is read from the GitHub event JSON file (or the issues API
on a manual run). It is never interpolated into a shell command.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OWNER_LOGIN = "LeoCheng802"
ISSUE_NUMBER = 1
DEFAULT_REPO = "LeoCheng802/Grok-Bot"
TAIPEI = timezone(timedelta(hours=8), name="Asia/Taipei")
MAX_TITLE_LEN = 80
MAX_COMMENT_PAGES = 20

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_BLOCK_RE = re.compile(
    r"<!-- comment_id: (\d+) -->(.*?)<!-- /comment_id: \1 -->",
    re.DOTALL,
)


@dataclass(frozen=True)
class Role:
    tag: str
    label: str
    filename: str


ROLES: tuple[Role, ...] = (
    Role("[復盤]", "復盤", "review.md"),
    Role("[執行]", "執行", "execution.md"),
    Role("[開單審核]", "開單審核", "order-audit.md"),
    Role("[交易對]", "交易對", "pairs.md"),
    Role("[風險管理]", "風險管理", "risk.md"),
    Role("[策略組]", "策略組", "strategy.md"),
)
GENERAL = Role("", "一般", "general.md")
ALL_ROLES: tuple[Role, ...] = (*ROLES, GENERAL)

EMPTY_LATEST = """# 最新回報

目前尚無回報。

請讀此檔取得 Issue #1（77｜OKX 交易台｜群組機器人回報串）的最新一筆擁有者留言。同步後會包含台北時間（Asia/Taipei，UTC+8）、角色、留言網址與全文。

各機器人的最新回報在 `by-role/`，最近 20 筆索引在 `index.md`，每日全文在 `history/`。
"""

INDEX_INTRO = (
    "最近 20 筆「77｜OKX 交易台」回報。"
    "時間為 Asia/Taipei（UTC+8）。"
    "歷史檔連結指向當日全文，留言連結指向 GitHub 原文。"
)


class SyncError(RuntimeError):
    """A sync step failed without writing a usable report."""


@dataclass(frozen=True)
class StoredReport:
    comment_id: int
    role_label: str
    role_file: str
    taipei_time: str
    title: str
    url: str
    body: str
    history_name: str


def to_taipei(dt: datetime) -> datetime:
    """Convert a datetime to Asia/Taipei (fixed UTC+8, no daylight saving)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TAIPEI)


def parse_github_time(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_taipei(dt: datetime) -> str:
    return to_taipei(dt).strftime("%Y-%m-%d %H:%M:%S")


def taipei_date(dt: datetime) -> str:
    return to_taipei(dt).strftime("%Y-%m-%d")


def first_nonempty_line(body: str) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def detect_role(body: str) -> Role:
    """Route a comment by the role tag on its first non-empty line."""
    line = first_nonempty_line(body)
    found: tuple[int, Role] | None = None
    for role in ROLES:
        index = line.find(role.tag)
        if index == -1:
            continue
        if found is None or index < found[0]:
            found = (index, role)
    return found[1] if found else GENERAL


def extract_title(body: str, role: Role) -> str:
    line = first_nonempty_line(body)
    if role.tag and role.tag in line:
        line = line.replace(role.tag, "", 1)
    line = re.sub(r"\s+", " ", line).strip()
    line = line.replace("-->", "—>")
    if not line:
        return "（無標題）"
    if len(line) > MAX_TITLE_LEN:
        return line[: MAX_TITLE_LEN - 1] + "…"
    return line


def is_authorized(comment: dict) -> bool:
    """True only for the repository owner.

    Public visitors can comment on Issue #1. Sync those only when GitHub marks
    the author as OWNER, or the login is the owner account.
    """
    if comment.get("author_association") == "OWNER":
        return True
    user = comment.get("user") or {}
    return user.get("login") == OWNER_LOGIN


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _shield_marker_text(marker: str) -> str:
    return marker.replace("<!--", "‹!--", 1).replace("-->", "--›", 1)


def _shield_marker(match: re.Match[str]) -> str:
    return _shield_marker_text(match.group(0))


def shield_body(body: str, comment_id: int) -> str:
    """Stop a comment from forging the markers that bound any report block.

    Every comment_id marker in the body is rewritten, including this note's
    own id, so one note cannot close or impersonate another.
    """
    text = normalize_newlines(body).rstrip("\n")
    own_id = int(comment_id)
    for marker in (
        f"<!-- comment_id: {own_id} -->",
        f"<!-- /comment_id: {own_id} -->",
    ):
        text = text.replace(marker, _shield_marker_text(marker))
    text = re.sub(r"<!--\s*/?\s*comment_id:[^>]*-->", _shield_marker, text)
    text = text.replace("<!-- raw_body -->", "‹!-- raw_body --›")
    return text


def comment_url(comment: dict, repo: str) -> str:
    url = comment.get("html_url")
    if isinstance(url, str) and url.startswith("https://"):
        return url
    comment_id = int(comment["id"])
    return f"https://github.com/{repo}/issues/{ISSUE_NUMBER}#issuecomment-{comment_id}"


def render_history_block(
    *,
    comment_id: int,
    role: Role,
    taipei_time: str,
    created_time: str,
    title: str,
    url: str,
    body: str,
) -> str:
    created_line = ""
    if created_time != taipei_time:
        created_line = f"- **建立時間（Asia/Taipei）**: {created_time}\n"
    safe_body = shield_body(body, comment_id)
    return (
        f"<!-- comment_id: {comment_id} -->\n"
        f"<!-- role: {role.label} -->\n"
        f"<!-- role_file: {role.filename} -->\n"
        f"<!-- taipei_time: {taipei_time} -->\n"
        f"<!-- title: {title} -->\n"
        f"<!-- comment_url: {url} -->\n"
        f"## {taipei_time} · {role.label}\n"
        f"\n"
        f"- **時間（Asia/Taipei）**: {taipei_time}\n"
        f"- **角色**: {role.label}\n"
        f"- **留言**: {url}\n"
        f"{created_line}"
        f"\n"
        f"<!-- raw_body -->\n"
        f"{safe_body}\n"
        f"<!-- /comment_id: {comment_id} -->\n"
    )


def history_header(date: str) -> str:
    return (
        f"# {date} 回報紀錄\n"
        "\n"
        f"Asia/Taipei（UTC+8）{date} 的 Issue #1 擁有者留言全文。"
        "編輯同一則留言時，以該則的 comment_id 標記原地更新。\n"
        "\n"
    )


def _block_pattern(comment_id: int) -> re.Pattern[str]:
    return re.compile(
        rf"<!-- comment_id: {int(comment_id)} -->.*?<!-- /comment_id: {int(comment_id)} -->\n?",
        re.DOTALL,
    )


def upsert_history(reports_root: Path, comment: dict, repo: str) -> Path:
    comment_id = int(comment["id"])
    body = comment.get("body") or ""
    if not isinstance(body, str):
        body = str(body)
    created = parse_github_time(comment["created_at"])
    updated = parse_github_time(comment.get("updated_at") or comment["created_at"])
    role = detect_role(body)
    title = extract_title(body, role)
    url = comment_url(comment, repo)
    created_time = format_taipei(created)
    taipei_time = format_taipei(updated)
    block = render_history_block(
        comment_id=comment_id,
        role=role,
        taipei_time=taipei_time,
        created_time=created_time,
        title=title,
        url=url,
        body=body,
    )

    history_dir = reports_root / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    marker = f"<!-- comment_id: {comment_id} -->"
    existing = None
    for path in sorted(history_dir.glob("*.md")):
        if marker in path.read_text(encoding="utf-8"):
            existing = path
            break

    target = existing or (history_dir / f"{taipei_date(created)}.md")
    pattern = _block_pattern(comment_id)
    if target.exists():
        text = target.read_text(encoding="utf-8")
    else:
        text = history_header(taipei_date(created))

    if pattern.search(text):
        text = pattern.sub(lambda _match: block, text, count=1)
        if len(pattern.findall(text)) > 1:
            first = True

            def _drop_extra(match: re.Match[str]) -> str:
                nonlocal first
                if first:
                    first = False
                    return match.group(0)
                return ""

            text = pattern.sub(_drop_extra, text)
    else:
        text = text.rstrip() + "\n\n" + block

    if not text.endswith("\n"):
        text += "\n"
    target.write_text(text, encoding="utf-8")
    return target


def _parse_block_inner(inner: str) -> tuple[dict[str, str], str]:
    raw_at = inner.find("<!-- raw_body -->")
    head = inner if raw_at == -1 else inner[:raw_at]
    body = ""
    if raw_at != -1:
        body = inner[raw_at + len("<!-- raw_body -->") :]
        if body.startswith("\n"):
            body = body[1:]
        if body.endswith("\n"):
            body = body[:-1]
    meta: dict[str, str] = {}
    for key in ("role", "role_file", "taipei_time", "title", "comment_url"):
        match = re.search(rf"^<!-- {key}: (.*) -->$", head, re.MULTILINE)
        meta[key] = match.group(1).strip() if match else ""
    return meta, body


def load_reports(reports_root: Path) -> list[StoredReport]:
    history_dir = reports_root / "history"
    reports: list[StoredReport] = []
    if not history_dir.exists():
        return reports
    for path in sorted(history_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in _BLOCK_RE.finditer(text):
            meta, body = _parse_block_inner(match.group(2))
            reports.append(
                StoredReport(
                    comment_id=int(match.group(1)),
                    role_label=meta.get("role") or GENERAL.label,
                    role_file=meta.get("role_file") or GENERAL.filename,
                    taipei_time=meta.get("taipei_time") or "",
                    title=meta.get("title") or "（無標題）",
                    url=meta.get("comment_url") or "",
                    body=body,
                    history_name=path.name,
                )
            )
    reports.sort(key=lambda report: (report.taipei_time, report.comment_id), reverse=True)
    return reports


def empty_role(role: Role) -> str:
    if role is GENERAL:
        detail = "留言第一個非空白行沒有角色標籤時，最新一筆會寫在這個檔案。"
    else:
        detail = f"角色標籤是 `{role.tag}`。"
    return f"# {role.label}\n\n此檔是「{role.label}」的最新回報。{detail}目前尚無回報。\n"


def render_latest(report: StoredReport) -> str:
    body = report.body.rstrip("\n")
    return (
        "# 最新回報\n"
        "\n"
        "這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。\n"
        "\n"
        f"- **時間（Asia/Taipei）**: {report.taipei_time}\n"
        f"- **角色**: {report.role_label}\n"
        f"- **留言**: {report.url}\n"
        "\n"
        f"<!-- comment_id: {report.comment_id} -->\n"
        "\n"
        f"{body}\n"
    )


def render_role(report: StoredReport) -> str:
    body = report.body.rstrip("\n")
    return (
        f"# {report.role_label}\n"
        "\n"
        f"此檔是「{report.role_label}」的最新回報。\n"
        "\n"
        f"- **時間（Asia/Taipei）**: {report.taipei_time}\n"
        f"- **角色**: {report.role_label}\n"
        f"- **留言**: {report.url}\n"
        "\n"
        f"<!-- comment_id: {report.comment_id} -->\n"
        "\n"
        f"{body}\n"
    )


def _table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_index(reports: list[StoredReport]) -> str:
    lines = [
        "# 回報索引",
        "",
        INDEX_INTRO,
        "",
        "| 時間（台北） | 角色 | 標題 | 歷史檔 | 留言 |",
        "| --- | --- | --- | --- | --- |",
    ]
    if not reports:
        lines.extend(["", "目前尚無回報。", ""])
        return "\n".join(lines)
    for report in reports[:20]:
        date_label = report.history_name.removesuffix(".md")
        lines.append(
            "| {time} | {role} | {title} | [{date}](history/{filename}) | [留言]({url}) |".format(
                time=_table_cell(report.taipei_time),
                role=_table_cell(report.role_label),
                title=_table_cell(report.title),
                date=date_label,
                filename=report.history_name,
                url=report.url,
            )
        )
    lines.append("")
    return "\n".join(lines)


def refresh_views(reports_root: Path) -> None:
    """Rewrite latest, index, and per-role files from history blocks."""
    reports_root.mkdir(parents=True, exist_ok=True)
    (reports_root / "by-role").mkdir(parents=True, exist_ok=True)
    history_dir = reports_root / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = history_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    reports = load_reports(reports_root)
    latest = render_latest(reports[0]) if reports else EMPTY_LATEST
    (reports_root / "latest.md").write_text(latest, encoding="utf-8")
    (reports_root / "index.md").write_text(render_index(reports), encoding="utf-8")

    newest_by_file: dict[str, StoredReport] = {}
    for report in reports:
        newest_by_file.setdefault(report.role_file, report)
    for role in ALL_ROLES:
        current = newest_by_file.get(role.filename)
        text = render_role(current) if current else empty_role(role)
        (reports_root / "by-role" / role.filename).write_text(text, encoding="utf-8")


def sync_comment(reports_root: Path, comment: dict, *, repo: str = DEFAULT_REPO) -> bool:
    """Write one authorized comment. Return False when the author is ignored."""
    if not is_authorized(comment):
        return False
    validate_repo(repo)
    upsert_history(reports_root, comment, repo)
    refresh_views(reports_root)
    return True


def sync_event(reports_root: Path, event: dict, *, repo: str = DEFAULT_REPO) -> bool:
    """Sync a GitHub issue_comment payload. Ignore every issue except #1."""
    issue = event.get("issue") or {}
    if issue.get("number") != ISSUE_NUMBER:
        return False
    comment = event.get("comment") or {}
    return sync_comment(reports_root, comment, repo=repo)


def validate_repo(repo: str) -> str:
    if not _REPO_RE.fullmatch(repo):
        raise SyncError(f"invalid repository name: {repo!r}")
    return repo


def _next_link(header: str) -> str | None:
    for part in header.split(","):
        section = part.strip()
        if not section.endswith('rel="next"'):
            continue
        match = re.search(r"<([^>]+)>", section)
        if not match:
            return None
        url = match.group(1)
        if url.startswith("https://api.github.com/"):
            return url
        return None
    return None


def fetch_issue_comments(repo: str, issue_number: int, token: str) -> list[dict]:
    """List issue comments. The token stays in the request header only."""
    validate_repo(repo)
    if issue_number != ISSUE_NUMBER:
        raise SyncError(f"refusing to read issue #{issue_number}")
    comments: list[dict] = []
    url: str | None = (
        f"https://api.github.com/repos/{repo}/issues/{issue_number}/comments"
        "?per_page=100&page=1"
    )
    for _page in range(MAX_COMMENT_PAGES):
        if not url:
            break
        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "grok-bot-sync-reports",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                link = response.headers.get("Link", "")
        except HTTPError as exc:
            raise SyncError(f"GitHub API returned HTTP {exc.code} while listing comments") from exc
        except URLError as exc:
            raise SyncError(f"GitHub API request failed: {exc.reason}") from exc
        if not isinstance(payload, list):
            raise SyncError("GitHub API returned an unexpected comments payload")
        comments.extend(payload)
        url = _next_link(link)
    else:
        if url:
            raise SyncError("stopped after too many comment pages")
    return comments


def rebuild_owner_comments(reports_root: Path, comments: list[dict], *, repo: str) -> int:
    ordered = sorted(
        (comment for comment in comments if is_authorized(comment)),
        key=lambda comment: (str(comment.get("created_at") or ""), int(comment.get("id") or 0)),
    )
    for comment in ordered:
        upsert_history(reports_root, comment, repo)
    refresh_views(reports_root)
    return len(ordered)


def _load_event() -> dict | None:
    path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not path:
        return None
    file = Path(path)
    if not file.is_file():
        return None
    return json.loads(file.read_text(encoding="utf-8"))


def main() -> int:
    reports_root = Path(os.environ.get("REPORTS_DIR", "reports"))
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    repo = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO)
    try:
        validate_repo(repo)
        if event_name == "workflow_dispatch":
            token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
            if not token:
                raise SyncError("workflow_dispatch requires GITHUB_TOKEN")
            comments = fetch_issue_comments(repo, ISSUE_NUMBER, token)
            count = rebuild_owner_comments(reports_root, comments, repo=repo)
            print(f"rebuilt reports from {count} owner comments")
            return 0

        event = _load_event()
        if not event or "comment" not in event:
            print("no issue comment in event; nothing to do")
            return 0
        issue_number = (event.get("issue") or {}).get("number")
        if issue_number != ISSUE_NUMBER:
            print(f"skip: issue {issue_number} is not #{ISSUE_NUMBER}")
            return 0
        comment = event.get("comment") or {}
        if not is_authorized(comment):
            login = (comment.get("user") or {}).get("login")
            print(f"skip: comment by {login} is not the repository owner")
            return 0
        sync_comment(reports_root, comment, repo=repo)
        print(f"synced comment {comment.get('id')}")
        return 0
    except (SyncError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
