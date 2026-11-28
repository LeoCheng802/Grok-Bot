# 最新回報

這是 Issue #1 最新一筆擁有者回報，供 ChatGPT 優先閱讀。

- **時間（Asia/Taipei）**: 2026-11-28 21:01:27
- **角色**: 一般
- **留言**: https://github.com/LeoCheng802/Grok-Bot/issues/1#issuecomment-7239633889

<!-- comment_id: 7239633889 -->

【2026-11-28 21:03 台北時間（UTC+8）】
[執行] v1.25 PR #8 非 8H 未知項補正

依 ChatGPT v1.25（#7239505073）補正 v1.23，並納入 復盤 要求的 old-fails/new-passes 檢查。離線、只用已存檔案；無 refetch、無回測、無 zero-fill、無插補、未改任何真實費率。v1.23 檔案原樣保留；新檔在新資料夾 `research/funding_sources_nonh8_v1_25/`。

**Pinned**：PR #8 head `71ebc39d4b989de71d6b482709f565d91770dd04`，parent `3280b7a6975d272c24238476af80820c9668b6c7`（其 parent f1280dc4）。一般 push，無 force-push，PR 維持 draft。
**執行時間（UTC）**：生成器 2026-11-28T12:53:19Z – 12:59:09Z；合成測試 12:59:36Z（old/new 各一次）；push 約 13:00Z。

## 1. 2H 誤分類（已修）
v1.23 `analyze_month` 只認 1H/4H/8H，常數 2H 月被歸成 `not_determinable_internal_gaps` 並寫 inferred 1H——這是分類錯誤。v1.25：單一常數觀測間隔不論幾小時都保留為 observed；`official_schedule_status=unknown_no_official_schedule_source_used`；2H 的預期筆數只是 inferred，非官方。`inferred_interval` 僅在單一常數間隔時填寫，非常數月留空。常數的非 1H/4H/8H 完整月份用新狀態 `inferred_constant_full_month_nonstandard_interval`。`interval_change_visible` 只代表存檔資料中看到的變化，不證明官方間隔變更。

**8 個月 before / after（denominator_status ／ inferred ／ expected）**
| inst | CST 月 | 觀測筆數 | v1.23 | v1.25 |
|---|---|---:|---|---|
| API3-USDT-SWAP | 2025-04 | 360 | internal_gaps ／ 1H ／ 空 | 觀測 2H：inferred_constant_full_month_nonstandard_interval ／ 2H ／ 360 |
| AUCTION-USDT-SWAP | 2025-04 | 360 | 同上 | 同上（2H／360） |
| KAITO-USDT-SWAP | 2025-04 | 360 | 同上 | 同上（2H／360） |
| LAYER-USDT-SWAP | 2025-04 | 360 | 同上 | 同上（2H／360） |
| LAYER-USDT-SWAP | 2025-03 | 372 | 同上 | 同上（2H／372） |
| BARD-USDT-SWAP | 2025-09 | 144 | 同上 | 觀測 2H：not_determinable_span_shorter_than_month（月中上市）／ 2H ／ 空 |
| SOPH-USDT-SWAP | 2025-08 | 372 | 同上 | 2H／372 |
| SYRUP-USDT-SWAP | 2025-08 | 372 | 同上 | 2H／372 |
官方排程一律 unknown。

**其他未識別間隔檢查**：125 個月出現 1H/4H/8H 以外的觀測間隔——124 個 2H、1 個 132H（4H+8H+132H）。狀態分布：117 interval_change_or_gaps、7 constant_full_month_nonstandard_interval、1 span_shorter_than_month（BARD）。資料中沒有其他間隔（如 3H、6H）。
另一個同源錯誤：v1.23 對 196 列 `interval_change_or_gaps`（195 個非 8H 月 + ZK 2024-06 已知缺口列）也寫了 inferred 1H，現已留空。

**Diff vs v1.23（3,122 個非 8H 月；列集合相同，共 3,128 列，204 列有變動，0 非預期欄位變動）**
| denominator_status | v1.23 | v1.25 |
|---|---:|---:|
| inferred_constant_full_month | 2,499 | 2,499 |
| inferred_constant_full_month_nonstandard_interval | 0 | 7 |
| not_determinable_window_truncated | 198 | 198 |
| not_determinable_interval_change_or_gaps | 195 | 195 |
| not_determinable_span_shorter_than_month | 121 | 122 |
| not_determinable_interval_change | 99 | 99 |
| not_determinable_internal_gaps | 8 | 0 |
| not_determinable_insufficient_points | 2 | 2 |

inferred_interval：4H 2,814→2,814；1H 207→4；2H 0→8；空白 101→296。

## 2. 時間基準：raw vs snap
早先的 parse_zip_numeric / parse_rest_numeric 先 snap 到整點（無容忍度）再去重，故 v1.23 的 6,109 是 snap 後數字。v1.25 從已存檔的官方 ZIP 與 REST（2026-11 為 parsed JSON，非原始 bytes）讀 raw 毫秒值，兩個基準分開報：
- 解析列數 1,046,023（ZIP 941,283 + REST 104,740）；有限費率 1,046,021；2 列 ZIP null（OL 2025-10、ZK 2024-06）。
- raw 與 snap 偏移：0 偏移 950,550 列；非 0 偏移 95,471 列（皆在 ZIP；REST 全為 0）；最大偏移 45,000 ms。
- raw ts 與 snapped ts 落在不同 CST 月：0；不同 UTC 月：0。raw 與 snap 時間集合不同的月份：0。
- 檔內 snap 碰撞（多個 raw 列 → 同一 snapped key）：0；同 key 不同費率：0。
- 跨月邊界 settlement（最後 UTC 日 ≥16:00Z），非 8H 月：**snap 基準 6,109，raw 基準 6,109**，兩者不同的月份 0，與 v1.23 欄位比對 0 mismatch。含 8H 月（有檔者）兩基準皆 10,387。CST 2026-11 為 partial，窗內無月底跨越。
- 跨檔同 snapped key：65,703，全部是已存的 REST 2026-11 檔（含 CST 2026-11 以前的歷史列）與官方月 ZIP 的重疊；不同費率：0；ZIP 對 ZIP：0。重疊列不用來新增或改變任何值。檔案範圍外被排除列 65,773（REST 較早 CST 月 65,703；ZIP 早於窗口起點 70）。
- **unknown**（未存 raw 時間）：4 個 404_reason_unknown 月（CC 2025-10、INJ 2023-11、MEGA 2026-04、ORDER 2025-09）。RVN 2026-11 有已存的 REST 51001 回應，資料列 0。v1.7/v1.9 原始 body 與 frozen DB 未作為時間來源，其 raw 時間在本分支為 unknown。

## 3. 明確「未驗證」
- same-key-different-rate 與 snap 碰撞：只在上述已存 ZIP/REST 檔內檢查；未跨 frozen DB、v1.7、v1.9、v1.10、b1–b3c deltas 重跑（各批 manifest 自報衝突數，未在此重驗）。
- ZIP/REST hash 清單不等於逐檔 manifest 驗收，也不是全費率完整性聲明。
- frozen DB `23ebdab561d5fa48ae34394b451d55b97d3e09af4e8a8809eef93422c40783cc` 只與 b3b/b3c manifest 引用相符；列數相同不代表與其他版本相同。
- 未使用任何官方結算排程來源；所有間隔與分母皆為 inferred、未驗證。complete=true 僅代表該批 source 與比對範圍通過；空白為 unknown。

## 4. 文字更正
v1.23 貼文把 2,499 個月寫成「可推斷（非常數全月區間，非官方）」，用語錯誤。這 2,499 個月是**常數**完整月份（`inferred_constant_full_month`：單一觀測常數間隔涵蓋窗內完整 CST 月）。已在同批更正，無額外重跑。

## 5. 合成測試（old FAIL / new PASS）
`test_2h_classification_v1_25.py`：僅合成資料。A 完整月常數 2H、B 4H 對照、C 2H 缺一格、D 2H 月中上市、E（僅 v1.25）raw/snap 偏移與不同費率碰撞。從 repo 根目錄用相對路徑執行。
- 舊邏輯（3280b7a6 的 v1.23 腳本）：**FAIL**，17 項中 10 項失敗，exit 1（internal_gaps + inferred 1H）。log：`test_2h_run_old_3280b7a6.log`
- 新邏輯（v1.25 腳本）：**PASS**，22/22，exit 0。log：`test_2h_run_new_v1_25.log`

## 檔案 bytes / SHA-256（`research/funding_sources_nonh8_v1_25/`）
| 檔案 | bytes | SHA-256 |
|---|---:|---|
| build_sources_nonh8_v1_25_public.py（公開腳本） | 58,855 | 81372910192660bc31cba6b3d5c93880f86e0b7975dae020e0ee7f54620f31e0 |
| funding_sources_nonh8_v1_25_manifest.json | 7,582 | d8a1cba7f5a3ffef36e2abb4cc98f421aa3d9f32ad060deeab18806d90d980c1 |
| CHANGELOG.md | 9,106 | 0a96b2e6d8d205a3238f2001fa719554a2d4d10ca7e0973ca9c3e2ae3c58b5de |
| nonh8_completeness_unknowns_v1_25.csv（3,128 列） | 4,397,399 | 8cbcdd66047298d3550f1601d6dea147537447de89de88f9e5ef7bb3328810c2 |
| nonh8_completeness_unknowns_v1_25.md | 542,432 | 1a121d8fbfb4034ff8fb8b2a677b02121e2a95f936772cf7957171bde135319a |
| nonh8_v1_25_vs_v1_23_changed_rows.csv（204 列） | 32,233 | 740fa27fd3eb9bd7cad7f6428e0ad8afbaf5da8b095c226bf4d5390be50a6777 |
| eight_2h_months_before_after_v1_25.csv（8 列） | 2,158 | 3b67da0d89bc5acc53ee3adff4eeb54d4fc76a0795575d96e15bc5f07e729e03 |
| time_basis_evidence_v1_25.json | 2,695 | 565e68a2d7186ca802a2abea2261dd3023276613a0c86b1300982220377ba9d5 |
| test_2h_classification_v1_25.py | 6,824 | 6bae1eb422e6489de5773d88c123d32151c08e1271c78033d1fb15f7ba6672a4 |
| test_2h_run_old_3280b7a6.log | 2,265 | b30662abda2f2da316df118a7f448269b956709b879f2183178b176ac128a369 |
| test_2h_run_new_v1_25.log | 2,084 | 8c068360ce1cdb77a34f0354b5b84e348166c31912cbda40dd969379c1be0243 |

輸入 SHA：inventory r5 `27361ccc0aeec209979965d72fa235f8fb80818b2c9c813927f80469cf6603f9`；v1.23 CSV `dc4689a663b7552ef8688d6392b18ca8eba3cfec14096d2350502899df8938ce`（保留不變）；v1.23 腳本 `19d1b69acc6655e8756bc49ac877cf40195202b26d26641a4e60cd44d047f6b6`。

## 限制
自行掃描屬團隊執行證據，不是 ChatGPT runtime 認證。所有分母皆 inferred、無官方排程來源。未提交 counts sidecar。無績效數字、無倉位、無憑證、無本機路徑。

FIB-4H-LONG-V3 仍為 **NO-GO**；live_approved 仍為 **false**。PR #8 維持 draft，不 merge。
