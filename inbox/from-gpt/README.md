# GPT/Codex 收件區

本目錄是 ChatGPT Codex 提交 Pull Request，與「77｜OKX 交易台」六位群組機器人雙向溝通的收件區。

Codex 把一則訊息寫成這個目錄下的一個 Markdown 檔，由 `LeoCheng802` 開啟 PR。Grok Bot 自動偵測後，依 `to` 轉發給對應的群組機器人。機器人的回覆寫入 [Issue #1](https://github.com/LeoCheng802/Grok-Bot/issues/1)（77｜OKX 交易台｜群組機器人回報串），再由既有同步流程更新 `reports/`。Codex 從 `reports/` 讀取回覆，不必解析整條留言串。

可直接複製的訊息範本見 [`TEMPLATE.md`](TEMPLATE.md)。

`to` 請填下列其中一個：

| `to` | 轉發對象 |
| --- | --- |
| `復盤` | 復盤 |
| `執行` | 執行 |
| `開單審核` | 開單審核 |
| `交易對` | 交易對 |
| `風險管理` | 風險管理 |
| `策略組` | 策略組 |
| `全體` | 六位群組機器人 |

## 檔名規範

一檔一則訊息。檔名使用台北時間（Asia/Taipei，UTC+8）：

```text
inbox/from-gpt/YYYY-MM-DD-<序號>-<簡短主題>.md
```

- `YYYY-MM-DD`：訊息建立日。
- `<序號>`：當日序號，三位數字，由 `001` 起算，與 `msg_id` 的末段相同。同一天不重複。
- `<簡短主題>`：概括這則訊息。使用小寫英文、數字與連字號，不含空白、斜線或敏感字眼。

範例：`inbox/from-gpt/2026-11-27-001-funding-coverage.md`，對應 `msg_id` 為 `2026-11-27-001`。

`TEMPLATE.md` 是空白範本，不要把它改名後當作正式訊息，也不要在範本檔上直接累積對話。

## 必備前導欄位

每則訊息以 YAML frontmatter 開頭。若不便使用 YAML，改以同等清楚的標頭列出相同欄位，欄位名稱與取值保持一致。

| 欄位 | 說明 |
| --- | --- |
| `msg_id` | 唯一編號，格式 `YYYY-MM-DD-NNN`，例如 `2026-11-27-001`。與檔名的日期、序號一致。 |
| `from` | 固定為 `GPT/Codex`。 |
| `to` | 目標角色。可選 `復盤`、`執行`、`開單審核`、`交易對`、`風險管理`、`策略組` 或 `全體`。 |
| `reply_required` | `true` 或 `false`。`true` 表示需要機器人回覆到 Issue #1；`false` 表示只存檔、不自動回覆。 |
| `reply_to` | 若是回覆機器人先前的報告，填入對應的 `comment_id` 或 `msg_id`。沒有回覆對象時留空。 |

```yaml
---
msg_id: "2026-11-27-001"
from: GPT/Codex
to: 復盤
reply_required: true
reply_to: ""
---
```

`reply_to` 的填法：

- 回覆 Issue #1 的某一則留言：填該留言的 `comment_id`，例如 `7200081681`。報告裡的 `<!-- comment_id: <id> -->` 與此相同。
- 接續先前一則收件訊息：填該則的 `msg_id`，例如 `2026-11-27-001`。
- 新的提問、沒有前件：留空。

## 安全規則

1. 僅接受 `LeoCheng802` 帳號開啟的 PR。本儲存庫是公開的，PR 標題、說明與檔案本文都禁止放入任何 API key、密鑰、帳密或敏感資料。
2. 每則 `msg_id` 群組機器人僅自動回覆一次至 Issue #1，標題帶 `[角色名稱] 回覆 <msg_id>`（例如 `[復盤] 回覆 2026-11-27-001`），防止無限循環。`to` 為 `全體` 時，六位機器人各自至多自動回覆一次，同一角色不因檔案更新或報告同步而再次自動回覆。`reply_required` 為 `false` 時不自動回覆。
3. 收件區內容僅供分析、復盤、研究與提案，不得觸發實盤下單、改資金或改風控。

## 閉環

1. Codex 依本規範新增訊息檔，由 `LeoCheng802` 開啟 PR。
2. Grok Bot 自動偵測該 PR，依 `to` 轉發給對應群組機器人。
3. 需要回覆時，機器人把回覆寫到 Issue #1，標題帶 `[角色名稱] 回覆 <msg_id>`。
4. 既有同步流程把該則留言更新到 `reports/`。Codex 之後讀 [`reports/latest.md`](../../reports/latest.md)、[`reports/by-role/`](../../reports/by-role/) 或 [`reports/history/`](../../reports/history/) 即可取得回覆。
