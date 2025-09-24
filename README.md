# 身分證辨識系統 (ID Card Extractor)

一個基於 OpenCV 和 OCR 技術的身分證資訊自動擷取系統，能夠識別身分證正反面資訊並儲存至 CSV 檔案。

## 🚀 快速開始

### 安裝環境

```bash
make install
source .venv/bin/activate
```

### 安裝 pre-commit (開發使用)

```bash
pre-commit install
```

## 🎯 功能特色

- **自動辨識**：支援身分證正反面圖片自動識別
- **影像處理**：使用 OpenCV 進行影像前處理和優化
- **OCR 識別**：整合 EasyOCR 進行文字識別
- **資訊擷取**：精確提取身分證上的各項欄位資訊
- **格式輸出**：將識別結果儲存為結構化的 CSV 檔案

## 📋 支援欄位

### 正面欄位

- 姓名 (Name)
- 出生年月日 (Birthday)
- 發證日期 (Issue Date)
- 性別 (Gender)
- 身分證號 (ID Number)

### 反面欄位

- 父母姓名 (Parent Name)
- 配偶姓名 (Spouse Name)
- 役別 (Service Type)
- 出生地 (Birth Place)
- 戶籍地址 (Address)

## 🏗️ 系統架構

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

## 🔧 技術棧

- **Python 3.12+**：主要開發語言
- **OpenCV**：影像處理和前處理
- **EasyOCR**：光學字元識別
- **Pandas**：資料處理和 CSV 輸出
- **Pydantic**：資料驗證和設定管理
- **FastAPI**：Web API 介面 (可選)

## 📝 實作步驟

### 第一階段：影像處理模組

1. **影像前處理**
   - 影像讀取和格式轉換
   - 噪點去除和銳化
   - 邊緣檢測和角度校正
   - 對比度和亮度調整

2. **身分證檢測**
   - 身分證區域定位
   - 正反面自動判別
   - 影像裁切和標準化

### 第二階段：OCR 識別引擎

1. **OCR 引擎整合**
   - EasyOCR 初始化和配置
   - 中文繁體字識別優化
   - 文字區域檢測

2. **文字後處理**
   - OCR 結果清理和過濾
   - 字元校正和格式化
   - 信心度評估

### 第三階段：欄位提取邏輯

1. **正面欄位提取**
   - 姓名識別
   - 出生年月日解析
   - 發證年月日解析
   - 性別提取
   - 身分證號碼格式檢查

2. **反面欄位提取**
   - 父母姓名識別
   - 配偶姓名識別
   - 役別識別
   - 出生地識別
   - 戶籍地址識別

### 第四階段：資料輸出

1. **CSV 檔案生成**
   - 資料結構化處理
   - CSV 格式化輸出
   - 檔案命名和路徑管理

2. **結果驗證**
    - 資料完整性檢查
    - 格式驗證
    - 錯誤處理和日誌記錄

### 第五階段：介面開發

1. **命令列介面**
    - CLI 參數解析
    - 批次處理功能
    - 進度顯示

2. **Web 介面 (可選)**
    - FastAPI 後端 API
    - 檔案上傳介面
    - 結果下載功能

### 第六階段：測試和優化

1. **單元測試**
    - 各模組功能測試
    - 邊界條件測試
    - 錯誤處理測試

2. **效能優化**
    - OCR 準確度調優
    - 處理速度優化
    - 記憶體使用優化
