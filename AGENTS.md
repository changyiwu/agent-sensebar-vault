# agent-sensebar-vault（專案藍圖）

> 本檔為跨 Agent 通用的專案藍圖（AGENTS.md 開放標準）。任何 Agent 的每個 session 都應先讀本檔＋`handoff.md`。

## 專案簡介

透過「動手實作」與「循序漸進」的方式，從零開始理解並學習 AI Agent 的核心概念與設計模式。同時包含 Sensebar 影片字幕擷取工具，把外部影音內容整理成可用的知識素材。

開發環境：Python 3.10+，核心依賴 `google-genai`（Gemini 作為大腦）、`python-dotenv`、`colorama`。這三個是 Stage 1 的**計畫**依賴，尚無程式碼 import，因此在 `requirements.txt` 內維持註解狀態。

> **SDK 一律用 `google-genai`（`from google import genai`）**，不要用 upstream 寫的 `google-generativeai`——後者是已淘汰的舊版，兩者 API 不相容。網路上多數 ReAct／Function Calling 教學仍是舊版寫法，照抄會跑不起來。

本 repo fork 自 <https://github.com/mathruffian-dot/sensebar-agent-knowledge-vault-builder>（未設 upstream remote）。Stage 1～5 路線圖沿用 upstream，其中 `tools.py`、`simple_agent.py` 在 upstream 也**從未實作**——查證過 upstream 全部檔案與本 repo 全 git 歷史皆無此二檔。**Stage 1 是待辦，不是已完成，不要再把它勾起來。**

## 關鍵時程

<!-- 目前無固定時程 -->

## 目標與路線圖

### Stage 1：基礎 ReAct（Reasoning & Action）Agent — 當前目標

從零手寫 ReAct 循環，理解 Agent 如何自主思考、選擇工具、觀察結果。

- [ ] 設計 System Prompt 讓大模型理解 ReAct 規則（Thought → Action → Observation）
- [ ] 提供簡單的自訂 Python 函數作為 Tool（如計算機、模擬搜尋）
- [ ] 實作 Agent Loop 控制器，解析模型輸出並調用 Tool
- [ ] 使用彩色終端輸出，視覺化展示思考過程

### Stage 2：工具與函數調用（Function Calling）

從正則表達式解析／純文字 Prompt 轉換成原生的 Function Calling 機制。

- [ ] 學習如何將 Python 函數轉換成 API 規範的 JSON Schema
- [ ] 使用 Gemini / OpenAI 的 Native Function Calling
- [ ] 提升工具調用的穩定性與結構化參數解析

### Stage 3：記憶與狀態管理（Memory & State）

- [ ] 實作滑動視窗（Sliding Window）或摘要型記憶以避免 Token 爆炸
- [ ] 儲存對話歷史到本地 JSON / SQLite
- [ ] 建立簡單的用戶 Profile 記憶

### Stage 4：檢索增強生成（RAG）整合

- [ ] 文件切片（Chunking）與向量化（Embedding）
- [ ] 串接 Vector Database（如 ChromaDB、FAISS）
- [ ] 實作「檢索工具」供 Agent 自主調用

### Stage 5：多 Agent 協作（Multi-Agent System）

- [ ] 角色定義（Role Playing）與任務分配
- [ ] 實作路由機制（Routing）或群聊機制（Group Chat）
- [ ] 引入人類反饋機制（Human-in-the-loop）

### 素材工具線

- [x] `download_all_subs.py`、`extract_videos.py` 改為可攜路徑（原始固定目錄不存在時改用專案目錄）
- [x] 影片擷取同步更新 Markdown 與 URL 清單，加入 EP01 影片
- [x] 在專案目錄實際執行 `extract_videos.py`，確認影片清單與 URL 輸出
- [x] 補齊 `requirements.txt`（依賴定義）
- [x] 實際執行 `download_all_subs.py`，確認字幕下載與清洗輸出
- [x] `download_all_subs.py` 加入 Whisper 後備轉錄（影片沒字幕時自動轉錄）
- [ ] 移植 `media-youtube-publish` 的錯字對照表（`replacements.md`）到 Whisper 轉錄，含規則順序、英文詞邊界與保護詞
- [ ] 建立可重複執行的驗證流程

## 資料夾結構

```
agent-sensebar-vault/
├─ download_all_subs.py       # 批次下載字幕
├─ extract_videos.py          # 擷取影片清單，同步 Markdown 與 URL 清單
├─ sensebar_ai_videos.md      # 影片清單（Markdown）
├─ sensebar_ai_urls.txt       # 影片網址清單
├─ subtitles/                 # 下載的字幕（不進 git）
├─ output/                    # 產出與試跑結果（不進 git）
├─ requirements.txt           # 依賴定義（Whisper 相關為選用、註解狀態）
├─ README.md                  # 專案導覽與概念說明
├─ AGENTS.md                  # 本檔：專案藍圖
├─ handoff.md                 # 交接檔（每次收工必更新）
└─ .gitignore
```

> 尚未建立：`tools.py`（自訂工具庫）、`simple_agent.py`（ReAct 核心邏輯）。

## 同步層級（本專案初始化至第 3 層級）

| 層級 | 平台 | 位置 | 讀取時機 |
|------|------|------|---------|
| L1 | 本地（GDrive） | `AGENTS.md`＋`handoff.md` | 每個 session |
| L2 | GitHub | https://github.com/changyiwu/agent-sensebar-vault （公開） | 指定時 |
| L3 | Obsidian | `agent-sensebar-vault/專案工作流程.md` | 有需要時 |

## 三個檔案的職責（依「時效性」分家，不是依「詳細程度」）

| 檔案 | 時效 | 寫入方式 | 放什麼 |
|------|------|---------|--------|
| `handoff.md` | **只對下一個 session 有效**，過期即丟 | 每次收工整份重寫 | 做到哪、下一步、**這次**的暫時 workaround |
| `AGENTS.md`（本檔） | **長期有效**，每個 session 都適用 | 只有規則本身變了才改 | 目標、路線圖、常設規則、結構 |
| Obsidian／`git log` | **歷史**：發生過什麼、為什麼 | 只增不刪 | 決策紀錄、踩坑完整版、逐次進度 |

驗收標準：**`handoff.md` 整份刪掉，不應損失任何長期資訊**——會的話代表該升級進本檔卻沒升級。

**本檔不要出現的東西**：❌ `## 最近進度`／逐次工作紀錄、❌ 決策理由與踩坑完整版。2026-08-03 移除了 `## 最近進度`，內容逐條比對後已在 L3 筆記的〈🗓️ 最近更動紀錄〉——**是主動移除，不是遺漏，不要補回來**。踩過的坑只把**結論**收斂成一條祈使句寫進〈工作約定〉，原因留 L3。

## 工作約定

- 任何 Agent、任何電腦：**開工先讀 `handoff.md`，收工必更新 `handoff.md`**
- 修改共用檔案前先讀最新內容，避免覆蓋其他 Agent 的變更
- 所有回應與文件使用繁體中文
- 修改前先檢查 Git 狀態，只處理本次任務相關變更
- 不提交 API key、登入 cookie、下載憑證或私人字幕來源
- 新電腦開工先跑 `pip install -r requirements.txt`；兩支腳本依賴的是 `yt_dlp` **Python 模組**，只裝 CLI（如 `uv tool install`）不算數
- 寫 Markdown 的 mermaid 圖時，節點與邊的標籤一律加雙引號，且不要出現 `@`（Mermaid v11 起是保留語法，會讓整張圖不渲染）
- **產出一律放 `output/`**：本專案產生的檔案或資料夾（成品、匯出、報表、生成圖、渲染等）預設放專案根目錄的 `output/`，不另開 `outputs/`、`exports/`、`generated/`、`out/` 之類的資料夾，方便找；`output/` 不進 git。部署工具指定的建置目錄（`dist/`、`build/`）不在此限

## 字幕清理規則

`download_all_subs.py` 以 `yt-dlp` 下載 VTT 字幕後，必須依序執行下列清洗步驟：

1. 移除 VTT 元資料檔頭與時間戳記（如 `00:00:01.000 --> 00:00:03.000`）
2. 移除 HTML／XML 標籤
3. **滾動式去重**：YouTube 自動字幕會有重複的滾動行，需以連續行去重演算法生成流暢段落
4. 輸出為 Markdown，將影片標題作為 H1，並包含原始 YouTube 連結

Whisper 後備轉錄的規則：

- 轉錄稿一律以 OpenCC `s2twp` 轉成台灣正體，並標註「字幕來源: Whisper 轉錄，非官方字幕」
- 不要開 `carry_initial_prompt`：實測會漏掉整段內容
- 修正聽錯字不可加入 `Cloud → Claude` 這類短規則，除非同時實作詞邊界與保護詞（否則會誤傷 `iCloud`、`Google Cloud`）
- 轉錄失敗不可寫佔位檔：檔案存在就會被跳過，暫時性的 403 會變成永久缺字幕

## 知識維護規範

- `01-Clippings/` 下的原始字幕檔**不可直接修改**（外部輸入）
- 知識庫整理成果輸出至 `02-知識庫/`，並主動更新其 `index.md` 與 `log.md`
- Vault 實際結構為編號四層：`00-每日筆記/`、`01-Clippings/`、`02-知識庫/`、`03-創作庫/`
