# 開發指南

## 🛠️ 開發環境設置

### 前置需求
- Node.js 18+ 
- Python 3.11+
- npm 或 yarn
- pip

### 快速開始

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

或手動啟動：

**後端 (FastAPI)**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app/main.py
```

**前端 (React)**
```bash
cd frontend
npm install
npm run dev
```

### 開發伺服器
- 前端: http://localhost:5173
- 後端 API: http://localhost:8000
- API 文檔: http://localhost:8000/docs

## 📁 專案結構

```
youtube-mindmap-tool/
├── frontend/                # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/      # React 元件
│   │   ├── pages/          # 頁面元件
│   │   ├── services/       # API 呼叫
│   │   ├── types/          # TypeScript 類型定義
│   │   └── utils/          # 工具函數
│   └── package.json
├── backend/                 # FastAPI + Python
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心設定
│   │   ├── models/         # 資料模型
│   │   ├── services/       # 業務邏輯
│   │   └── utils/          # 工具函數
│   └── requirements.txt
├── docs/                   # 文檔
├── scripts/                # 開發腳本
└── .claude/               # PM 專案管理
```

## 🔧 開發工作流程

1. 檢視 Claude Code PM 系統中的任務
2. 從高優先級任務開始實作
3. 遵循 API 文檔標準
4. 確保前後端 CORS 正確設定
5. 提交前執行測試

## 📋 API 文檔標準

所有 API 介面必須遵循以下格式：

```python
/**
* 介面名稱
* 功能描述
* 輸入參數
* 返回參數
* URL 地址
* 請求方式
**/
```

## 🚀 部署

開發環境配置完成後，可按照後續 Issues 進行功能開發。

## 🤝 貢獻

查看 GitHub Issues 以了解目前的開發任務和優先級。