# Grok-Bot

本儲存庫把「77｜OKX 交易台」六位群組機器人的回報，從 [Issue #1](https://github.com/LeoCheng802/Grok-Bot/issues/1)（77｜OKX 交易台｜群組機器人回報串）同步成穩定的 Markdown，讓 ChatGPT 直接讀檔，不必解析整條留言串。

## ChatGPT 請這樣讀

只要最新一筆（不分機器人）時，讀 [`reports/latest.md`](reports/latest.md)。檔內有台北時間、角色、留言網址與全文。

要某一個機器人的最新回報時，讀 `reports/by-role/` 裡對應的檔案：

| 機器人 | 留言第一個非空白行的標籤 | 最新回報 |
| --- | --- | --- |
| 復盤 | `[復盤]` | [`reports/by-role/review.md`](reports/by-role/review.md) |
| 執行 | `[執行]` | [`reports/by-role/execution.md`](reports/by-role/execution.md) |
| 開單審核 | `[開單審核]` | [`reports/by-role/order-audit.md`](reports/by-role/order-audit.md) |
| 交易對 | `[交易對]` | [`reports/by-role/pairs.md`](reports/by-role/pairs.md) |
| 風險管理 | `[風險管理]` | [`reports/by-role/risk.md`](reports/by-role/risk.md) |
| 策略組 | `[策略組]` | [`reports/by-role/strategy.md`](reports/by-role/strategy.md) |

第一個非空白行沒有上面的標籤時，寫入 [`reports/by-role/general.md`](reports/by-role/general.md)。

要瀏覽最近回報時，讀 [`reports/index.md`](reports/index.md)。表內最多 20 列，每列有台北時間、角色、標題、歷史檔連結與留言連結。

要某一天的全文時，讀 `reports/history/YYYY-MM-DD.md`。日期是 Asia/Taipei（UTC+8）。

## 目錄

- `reports/latest.md`：全庫最新一筆回報。
- `reports/index.md`：最近 20 筆的索引表。
- `reports/by-role/`：六位機器人各自的最新回報，以及未標記者的 `general.md`。
- `reports/history/`：依台北日期累積的全文。同一則留言被編輯時，以 `<!-- comment_id: <id> -->` 原地更新，不會再附加一份。

## 同步方式

[`.github/workflows/sync-reports.yml`](.github/workflows/sync-reports.yml) 在下列情況執行。每一次有效觸發都會透過 GitHub REST API **重新讀取 Issue #1 的全部留言**（依分頁直到最後一頁），不只處理觸發那一則：

- Issue #1 有新留言或留言被編輯（`issue_comment` 的 `created` / `edited`），而且留言者是儲存庫擁有者（`author_association` 為 `OWNER`，或帳號為 `LeoCheng802`）。
- 手動執行 `workflow_dispatch`。

腳本只保留擁有者留言，再依 `comment_id` 冪等寫入 `reports/history/YYYY-MM-DD.md`（日期為 Asia/Taipei，UTC+8）。同一則留言不會重複新增；內容被編輯時，更新原來的那一筆。接著依照已歸檔的擁有者留言，重新產生 `reports/index.md`、`reports/latest.md` 與 `reports/by-role/*.md`。

因此，若有同步任務在排隊時被取消、那一則當時沒寫進報告，之後任何一次成功的同步都會把缺漏的留言補齊。報告內容與儲存庫現況完全相同時，不會建立空的 commit。

此儲存庫是公開的，所以工作流程先檢查 Issue 編號與作者，Python 腳本 [`scripts/sync_issue_comment.py`](scripts/sync_issue_comment.py) 會再檢查一次。留言內文只在腳本裡處理，不會拼進 shell。

同步步驟以環境變數 `GITHUB_TOKEN` 接收 GitHub Actions 內建的 `${{ secrets.GITHUB_TOKEN }}`。Token 不會寫進程式碼、報告檔、commit 訊息或日誌。工作流程權限只開 `contents: write`（推送報告）與 `issues: read`（讀取留言）。

`concurrency` 讓同一個群組同時只有一個任務寫入並推送報告，避免互相覆蓋。進行中的任務不會被新的留言取消。GitHub 仍可能取消同群組裡較早排隊、尚未開始的任務；被取消的那幾則會由下一次成功的全量對帳補回。若推送時 `main` 已前進，會先抓取最新的 `main`、重新對帳後再推一次。

有變更時，以 `github-actions[bot]` 提交到 `main`，提交訊息含 `[skip ci]`。

時間一律轉成 Asia/Taipei（UTC+8）。歷史檔日期用留言建立時間；畫面上的時間在編輯後會改為更新時間。

## 留言格式

在第一個非空白行放角色標籤，同一行接著標題：

```
[風險管理] 部位上限檢查
- 狀態：正常
- 資料截止：2026-11-27 00:00（台北）
```

請只寫研究結論、回測數據、風險與執行狀態、研究編號、資料截止時間和輸出位置摘要。不要貼上 API Key、Secret、Passphrase、憑證、帳號密碼或未脫敏的腳本。

## 測試

```bash
python3 -m unittest tests/test_sync_issue_comment.py
```
