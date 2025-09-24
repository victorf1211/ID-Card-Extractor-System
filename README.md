# 身分證辨識系統 (ID Card Extractor)

一個基於 OpenCV 和 OCR 技術的身分證資訊自動擷取系統，能夠識別身分證正反面資訊並儲存至 CSV 檔案。(An automated ID card information extraction system based on OpenCV and OCR technology. It can recognize information on both the front and back of ID cards and save the results to a CSV file.)

## 🚀 快速開始 (Quick Start)

### 安裝環境 (Set up environment)

```bash
make install
source .venv/bin/activate
```

### 安裝 pre-commit (開發使用) (Install pre-commit (for development))

```bash
pre-commit install
```

## 🎯 功能特色 (Features)

- **自動辨識**：支援身分證正反面圖片自動識別 (Automatic Recognition: Supports automatic recognition of both front and back ID card images)
- **影像處理**：使用 OpenCV 進行影像前處理和優化 (Image Processing: Uses OpenCV for preprocessing and optimization)
- **OCR 識別**：整合 EasyOCR 進行文字識別 (OCR Recognition: Integrates EasyOCR for text recognition)
- **資訊擷取**：精確提取身分證上的各項欄位資訊 (Information Extraction: Accurately extracts various fields from ID cards)
- **格式輸出**：將識別結果儲存為結構化的 CSV 檔案 (Structured Output: Saves recognition results as structured CSV files)

## 📋 支援欄位 (Supported Fields)

### 正面欄位 (Front Side)

- 姓名 (Name)
- 出生年月日 (Birthday)
- 發證日期 (Issue Date)
- 性別 (Gender)
- 身分證號 (ID Number)

### 反面欄位 (Back Side)

- 父母姓名 (Parent Name)
- 配偶姓名 (Spouse Name)
- 役別 (Service Type)
- 出生地 (Birth Place)
- 戶籍地址 (Address)

## 🏗️ 系統架構 (System Architecture)

```text
idcard-extractor/
├── src/
│   └── idcard_extractor/
│       ├── backend/           # 後端處理邏輯
│       │   ├── image_processor.py   # 影像前處理
│       │   ├── ocr_engine.py        # OCR 文字識別
│       │   ├── field_extractor.py   # 欄位資訊提取
│       │   ├── csv_exporter.py      # CSV 檔案輸出
│       │   └── models.py            # 資料模型定義
│       └── frontend/          # 前端介面 (可選)
│           ├── web_interface.py     # Web 介面
│           └── cli_interface.py     # 命令列介面
├── data/
│   ├── input/      # 輸入圖片目錄
│   ├── output/     # 輸出 CSV 目錄
│   └── temp/       # 暫存處理檔案
└── settings.yaml   # 系統設定檔案
```

## 🔧 技術棧 (Tech Stack)

- **Python 3.12+**：主要開發語言
- **OpenCV**：影像處理和前處理
- **EasyOCR**：光學字元識別
- **Pandas**：資料處理和 CSV 輸出
- **Pydantic**：資料驗證和設定管理
- **FastAPI**：Web API 介面 (可選)

## 📝 實作步驟 (Implementation Steps)

### 第一階段：影像處理模組 (Phase 1: Image Processing Module)

1. **影像前處理 (Preprocessing)**
   - 影像讀取和格式轉換 (Image loading and format conversion)
   - 噪點去除和銳化 (Noise removal and sharpening)
   - 邊緣檢測和角度校正 (Edge detection and angle correction)
   - 對比度和亮度調整 (Contrast and brightness adjustment)

2. **身分證檢測 (ID Card Detection)**
   - 身分證區域定位 (Locate ID card region)
   - 正反面自動判別 (Automatic front/back detection)
   - 影像裁切和標準化 (Image cropping and normalization)

### 第二階段：OCR 識別引擎 (Phase 2: OCR Recognition Engine)

1. **OCR 引擎整合 (OCR Engine Integration)**
   - EasyOCR 初始化和配置 (EasyOCR initialization and configuration)
   - 中文繁體字識別優化 (Traditional Chinese recognition optimization)
   - 文字區域檢測 (Text region detection)

2. **文字後處理 (Post-processing)**
   - OCR 結果清理和過濾 (Cleaning and filtering OCR results)
   - 字元校正和格式化 (Character correction and formatting)
   - 信心度評估 (Confidence score evaluation)

### 第三階段：欄位提取邏輯 (Phase 3: Field Extraction Logic)

1. **正面欄位提取 (Front-side Extraction)**
   - 姓名識別 (Name recognition)
   - 出生年月日解析 (Birthday parsing)
   - 發證年月日解析 (Issue date parsing)
   - 性別提取 (Gender extraction)
   - 身分證號碼格式檢查 (ID number format validation)

2. **反面欄位提取 (Back-side Extraction)**
   - 父母姓名識別 (Parent name recognition)
   - 配偶姓名識別 (Spouse name recognition)
   - 役別識別 (Service type recognition)
   - 出生地識別 (Birthplace recognition)
   - 戶籍地址識別 (Address recognition)

### 第四階段：資料輸出 (Phase 4: Data Output)

1. **CSV 檔案生成 (CSV Generation)**
   - 資料結構化處理 (Structured data handling)
   - CSV 格式化輸出 (CSV formatting and export)
   - 檔案命名和路徑管理 (File naming and path management)

2. **結果驗證 (Result Validation)**
    - 資料完整性檢查 (Data integrity checks)
    - 格式驗證 (Format validation)
    - 錯誤處理和日誌記錄 (Error handling and logging)

### 第五階段：介面開發 (Phase 5: Interface Development)

1. **命令列介面 (Command-line Interface)**
    - CLI 參數解析 (CLI parameter parsing)
    - 批次處理功能 (Batch processing)
    - 進度顯示 (Progress display)

2. **Web 介面 (Web Interface)**
    - FastAPI 後端 API (FastAPI backend API)
    - 檔案上傳介面 (File upload interface)
    - 結果下載功能 (Result download feature)

### 第六階段：測試和優化 (Phase 6: Testing and Optimization)

1. **單元測試 (Unit Testing)**
    - 各模組功能測試 (Module functionality tests)
    - 邊界條件測試 (Edge case tests)
    - 錯誤處理測試 (Error handling tests)

2. **效能優化 (Performance Optimization)**
    - OCR 準確度調優 (OCR accuracy tuning)
    - 處理速度優化 (Processing speed optimization)
    - 記憶體使用優化 (Memory usage optimization)

