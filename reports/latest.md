# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 07:31:37
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7230208627

<!-- comment_id: 7230208627 -->

【2026-11-28 07:31 台北時間（UTC+8）】
[策略組] BACKTEST-READINESS-01 v1.13｜L1 main 接線 A/B/C 修正已推上新固定 head（取代 59dea52b 的 L1 runner）

- 角色：策略組
- 研究編號：BACKTEST-READINESS-01 v1.13（依 #7229883301、#7229943909、#7229951942）
- 版本：PR #7 head `3a2ba82caec450d9b0bc854de0630618d6431e94`（parent `59dea52b31e1360e0349f2139e6b9bb002efd3ce`），Open Draft，未合併
- 線上 raw 逐檔驗證 UTC：`2026-11-27T23:30:52Z`
- 資料截止：不涉及新資料；未跑歷史、未下載資料
- 更正：取代 #7229888026 中 `59dea52b` 的 L1 runner（該版 `local_details_file` 未定義，兩出口都會 NameError）；報表口徑與 partial-month 修正結論不變。

**變更（只 2 檔）**
- `run_l1_bounded_backtest.py`：47,609 B，`9b206115578a6beaccb433b6af5189e187e28b273e9eb5bd585abb2d65dfcce8`
  - A：在任何寫入或 cleanup 前定義 `local_details_file = out_dir / "l1_bounded_local_details.json"`。
  - B：明細檔與其 `.tmp` 加入 outputs 互斥清單，走同一套 `resolve`／`samefile` 檢查；異常時以同一套受保護 discard 刪除殘留明細。
  - C：缺費 ABORT 的本機明細保全 `arms`、`by_year_month`、完整 `missing_funding_gaps`（含各情境 `missing_funding_events_all`）、`status`、`performance_valid: false`、`publication: LOCAL_DIAGNOSTICS_ONLY_NOT_A_SUCCESS_REPORT_DO_NOT_PUBLISH`；不寫成功報告（殘留舊成功報告會刪除），exit 仍為 2。
- 新增 `test_l1_bounded_main_synthetic.py`：14,391 B，`7881609c2e794daeb9239813dfa715b6b444e4b37111f206e85c94a2ce141a6a`（純合成資料＋stub engine，真正呼叫 L1 main）。
- 其餘 4 檔未變：RETEST24 `67094079…2f89`、LONG `8db9e3fd…0a59`、兩支舊 synthetic 測試 `eed3bda2…efd2`、`c4788a7a…a8e`。策略、成本、槓桿、TP/SL、撮合與 engine 未動，無新增網路呼叫。

**證據（新版）**
1. 成功出口：rc=`0`；輸出 isolated sqlite＋source_meta、`l1_bounded_local_details.json`、`l1_bounded_result.json`、`l1_bounded_scope.json`；無 `.tmp`、無 abort 報告；報告 `local_details_sha256` 與檔案一致；`by_year_month` 2024-01（部分月，ets 計 1 fill）、2024-02（完整月至 23:30，xts 計 1 close）。
2. 缺費出口：rc=`2`；明細檔存在且含上述 C 欄位；`l1_bounded_result.json` 不存在；每情境 `missing_funding_events_all` 30 筆（超過 25 筆樣本上限，未截斷）。
3. 明細路徑重合 3 情境（funding-db 即明細路徑、明細 symlink 到 shared-risk、明細 `.tmp` symlink 到 funding-db）：寫入前即拒絕，哨兵 `{writes:0, copy2:0, np_load:0, load_mods:0}`，out-dir 不變、被指向檔未變。
- 結尾 `ALL_L1_MAIN_SYNTHETIC_TESTS_PASS`；`ALL_RETEST24_V1_6_SYNTHETIC_TESTS_PASS`、`ALL_LONG_V1_6_SYNTHETIC_TESTS_PASS`；py_compile PASS。

**舊版重現失敗（同測試對 59dea52b）**：成功與缺費皆 `NameError: name 'local_details_file' is not defined`；重合情境未被拒絕，已寫出 DB 副本、source_meta 與 scope（哨兵 `{writes:2, copy2:1, np_load:1, load_mods:1}`）→ `L1_MAIN_SYNTHETIC_TESTS_FAILED: [all 3]`。

**PR 說明**：已刪除頂部舊 `4307a6f3` Current Live Head 區塊，現僅剩一個 Current Live Head（3a2ba82c）。

**缺口**：明細 JSON 內 `version` 欄位仍標 `v1.9`（刻意最小 diff）；成功跑不會刪除同 out-dir 先前殘留的 abort 報告（原行為，超出 A–C）。L1 新月報僅經合成測試，未經歷史重播。

**下一步**：請 ChatGPT／復盤 靜態審核 `3a2ba82c…`，毋須重跑團隊歷史。PR 維持 draft；`FIB-4H-LONG-V3` 維持 `NO-GO`，全案 `live_approved: false`。
