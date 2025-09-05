# YouTube 影片心智圖工具

> 🎬 將 YouTube 影片轉換為互動式心智圖，讓學習和內容導航變得更加直觀

一個創新的網頁應用程式，將 YouTube 影片轉換為互動式心智圖，讓使用者通過視覺化節點導航內容，組織影片到播放清單，並執行跨影片內容的智能搜尋。

[![GitHub Issues](https://img.shields.io/github/issues/pocchincv/youtube-mindmap-tool)](https://github.com/pocchincv/youtube-mindmap-tool/issues)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## ✨ 主要功能

### 🎬 影片分析引擎
- **YouTube 連結處理**：輸入 YouTube 連結，自動提取影片內容
- **語音轉文字**：支援 CC 字幕下載或使用 STT 服務（OpenAI、Google、本地 Whisper）
- **心智圖生成**：將影片內容自動轉換為結構化心智圖

### 🗂️ 播放清單管理
- **智能分類**：自動將影片歸類到「未分類」播放清單
- **拖拽操作**：直觀的拖拽界面管理影片歸屬
- **播放清單**：新增/刪除播放清單功能

### 🔍 智能搜尋系統
- **自然語言查詢**：使用自然語言搜尋影片內容
- **精準匹配**：找出與查詢最相關的影片段落
- **智能結果**：自動存放到「Smart Search Result」播放清單

### 🎯 互動式心智圖
- **節點導航**：點擊節點從特定時間點開始播放
- **動態高亮**：播放進度與心智圖節點同步高亮
- **縮放功能**：支援心智圖縮放和展開
- **美觀設計**：水平樹狀結構，視覺效果優美

### ⚙️ 系統設定
- **API 管理**：支援 OpenAI、Google 等 API 金鑰配置
- **Google OAuth**：整合 Google 帳戶認證
- **資料同步**：中央資料庫與使用者端資料同步

## 🚀 快速開始

### 前置需求
- Node.js 18+
- Python 3.11+
- npm 或 yarn
- pip

### 安裝步驟

1. **複製專案**
```bash
git clone https://github.com/pocchincv/youtube-mindmap-tool.git
cd youtube-mindmap-tool
```

2. **設置環境變數**
```bash
cp .env.example .env
# 編輯 .env 檔案，填入必要的 API 金鑰
```

3. **啟動開發環境**
```bash
./scripts/start-dev.sh
```

4. **開啟瀏覽器**
- 前端應用：http://localhost:5173
- 後端 API：http://localhost:8000
- API 文檔：http://localhost:8000/docs

## 🛠️ 技術架構

- **前端**：React + Vite + TypeScript + Tailwind CSS
- **後端**：Python + FastAPI
- **資料庫**：SQLite (開發) / PostgreSQL (生產)
- **語音處理**：OpenAI API / Google API / 本地 Whisper
- **認證**：Google OAuth
- **專案管理**：Claude Code PM 系統

## 📋 開發進度

專案使用 Claude Code PM 系統進行管理，包含：

- ✅ **PRD**：完整產品需求文件
- ✅ **Epic**：7 個主要功能模組
- ✅ **Issues**：23 個詳細開發任務

查看 [GitHub Issues](https://github.com/pocchincv/youtube-mindmap-tool/issues) 了解開發進度。

### 開發階段
1. **基礎設施** ✅ (Issue #1)
2. **影片分析引擎** (Issues #2-5)
3. **主要應用介面** (Issues #6-10)
4. **播放清單管理** (Issues #11, 16)
5. **智能搜尋系統** (Issue #14)
6. **效能最佳化** (Issues #20-21)
7. **測試與部署** (Issues #18, 22-23)

## 📚 文檔

- [開發指南](docs/DEVELOPMENT.md)
- [API 文檔](http://localhost:8000/docs) (啟動後端後可用)
- [專案管理](/.claude/)

## 🤝 貢獻

1. Fork 此專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📄 授權

此專案使用 MIT 授權 - 查看 [LICENSE](LICENSE) 檔案了解詳情。

## 🎯 產品願景

打造一個革命性的影片學習工具，讓使用者能夠：
- 快速理解長影片內容結構
- 精確定位感興趣的影片段落
- 建立個人化的影片知識庫
- 透過智能搜尋發現相關內容

---

⭐ 如果這個專案對您有幫助，請給我們一顆星星！