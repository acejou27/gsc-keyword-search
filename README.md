# GSC關鍵字搜索工具 v2.0 🚀

## 📊 最新搜索統計

- **最後更新**: 等待首次執行
- **總搜索次數**: 0
- **成功率**: 0%
- **找到關鍵字**: 0

📈 [查看詳細報告](reports/latest-report.html) | 📋 [下載 CSV](reports/)

---

這個工具提供**本地版本**和**雲端版本**兩種執行方式，可以在Google搜尋結果中自動尋找特定關鍵字。雲端版本無需本地資源，完全在 GitHub Actions 和 Cloudflare Workers 上執行。

## 🌟 功能特點

### 雲端版本 (推薦)
- ☁️ **無需本地資源**: 完全在雲端執行，不佔用電腦資源
- 🔄 **自動定時執行**: GitHub Actions 每6小時自動執行
- 📊 **實時報告**: 自動生成 HTML/Markdown 報告
- 🌍 **全球部署**: Cloudflare Workers 邊緣計算
- 📱 **Web 界面**: 現代化的網頁操作界面
- 🔔 **結果通知**: 自動提交結果到 GitHub 倉庫

### 本地版本 (傳統)
- 🔍 在Google搜尋結果中自動搜尋關鍵字
- 📄 如果當前頁面沒有找到關鍵字，自動翻到下一頁
- 🎯 找到關鍵字後高亮顯示
- ⚡ 找到關鍵字後自動結束程式
- 💻 支持命令行參數傳入搜尋詞和目標關鍵字

## 安裝需求

1. Python 3.6 或更高版本
2. Selenium 庫
3. Chrome 瀏覽器
4. ChromeDriver (與您的Chrome版本相匹配)

## 安裝步驟

1. 安裝 Python 依賴：

```bash
pip install selenium
```

2. 下載 ChromeDriver：

請訪問 [ChromeDriver 官方網站](https://sites.google.com/a/chromium.org/chromedriver/downloads) 下載與您的Chrome瀏覽器版本相匹配的 ChromeDriver。

3. 確保 ChromeDriver 在系統路徑中，或者在腳本中指定其路徑。

## 🚀 快速開始

### 🐙 GitHub 版本 (強烈推薦！)

**為什麼選擇 GitHub 版本？**
- ✅ **超級方便**：直接在網頁上編輯 `keywords.csv`，無需安裝任何軟體
- ✅ **自動執行**：每次更新關鍵字自動觸發搜索
- ✅ **結果永久保存**：所有搜索結果都存在你的倉庫裡
- ✅ **隨時隨地**：手機、平板、電腦都能管理
- ✅ **完全免費**：GitHub Actions 每月 2000 分鐘免費額度

#### 📱 5分鐘快速設置

1. **🍴 Fork 這個倉庫**
   - 點擊右上角的 **Fork** 按鈕
   - 選擇你的 GitHub 帳號

2. **⚡ 啟用 Actions**
   - 進入你的倉庫 → **Actions** 頁面
   - 點擊 **"I understand my workflows, go ahead and enable them"**

3. **📝 編輯關鍵字**
   - 點擊 `keywords.csv` 文件
   - 點擊 ✏️ **Edit this file**
   - 按格式添加你的關鍵字：
     ```csv
     Python 教學,Django,Flask,FastAPI,目標關鍵字
     AI 工具,機器學習,深度學習,ChatGPT
     ```
   - 點擊 **Commit changes**

4. **🚀 開始搜索**
   - 文件更新後會自動觸發搜索
   - 或手動執行：**Actions** → **GSC關鍵字搜索** → **Run workflow**

5. **📊 查看結果**
   - 🌐 [在線查看結果](https://your-username.github.io/gsc-keyword-search/)
   - 📁 結果文件：`results/` 和 `reports/` 資料夾
   - 📧 自動通知：會創建 Issue 通知你結果

#### 📱 手機管理

- 📲 下載 **GitHub 手機 App**
- 🌐 或直接用手機瀏覽器訪問 GitHub
- ✏️ 隨時隨地編輯關鍵字文件
- 📊 查看搜索結果和報告

---

### 其他部署選項

#### 2. Cloudflare Workers 部署

#### 2. Cloudflare Workers 部署

```bash
# 1. 安裝 Wrangler CLI
npm install -g wrangler

# 2. 登入 Cloudflare
wrangler login

# 3. 部署到 Cloudflare Workers
cd cloudflare-worker
npm install
wrangler deploy
```

部署後可通過 Web 界面使用：`https://your-worker.your-subdomain.workers.dev`

#### 3. API 使用方式

```bash
# 單次搜索
curl -X POST https://your-worker.your-subdomain.workers.dev/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "searchQuery": "Python 教學",
    "targetKeywords": ["Django", "Flask"],
    "maxPages": 5
  }'

# 批量搜索
curl -X POST https://your-worker.your-subdomain.workers.dev/api/batch \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": [
      {"searchQuery": "Python 教學", "targetKeywords": ["Django"]},
      {"searchQuery": "AI 工具", "targetKeywords": ["ChatGPT"]}
    ],
    "maxPages": 5
  }'
```

---

### 本地版本

#### 方法一：使用啟動腳本（推薦）

1. 運行啟動腳本：

   ```bash
   python3 start.py
   ```
   
   注意：在macOS系統上，請使用`python3`命令而不是`python`命令。

2. 按照提示選擇功能並輸入相關參數。

### 方法二：基本使用

```bash
python3 google_keyword_search.py [搜尋詞] [目標關鍵字]
```

### 例如：

```bash
python3 google_keyword_search.py "Python 教學" "Django"
```

這將在Google上搜尋「Python 教學」，然後在搜尋結果中尋找「Django」這個關鍵字。

### 使用代理功能

使用新的main.py腳本可以啟用代理功能，支持GSA Proxy導出的代理列表：

```bash
python3 main.py [搜尋詞] [目標關鍵字] --proxy-file [代理文件路徑]
```

例如：

```bash
python3 main.py "Python 教學" "Django" --proxy-file proxies.txt
```

### 代理文件格式

代理文件應為純文本文件，每行一個代理，格式為IP:端口，例如：

```
192.168.1.1:8080
192.168.1.2:8080
```

### 完整命令行參數

```bash
python3 main.py [搜尋詞] [目標關鍵字] [選項]
```

可用選項：
- `--max-pages N`: 設置最大搜尋頁數（默認：5）
- `--max-retries N`: 設置最大重試次數（默認：3）
- `--proxy-file FILE`: 指定GSA Proxy導出的代理列表文件
- `--gsa-api-url URL`: 指定GSA Proxy API的URL（如果使用API獲取代理）
- `--max-failed-attempts N`: 設置代理失敗嘗試的最大次數（默認：3）
- `--refresh-interval N`: 設置刷新代理列表的時間間隔（秒）（默認：600）

### CSV模式使用方法

```bash
python3 google_keyword_search_csv.py keywords.csv [最大頁數]
```

#### CSV格式

CSV檔案格式為：關鍵字1,關鍵字2,關鍵字3,目標關鍵字

- 第一個關鍵字作為主要搜尋詞
- 中間的關鍵字作為額外的搜尋詞
- 最後一個關鍵字作為目標關鍵字

#### 例如：

```
Python 教學,Python 程式設計,Python 入門,Django
```

這將使用「Python 教學」作為主要搜尋詞，並在搜尋結果中尋找「Django」這個目標關鍵字。

## 注意事項

- 程序默認最多搜尋10頁結果
- 找到關鍵字後會高亮顯示並暫停5秒
- 找到關鍵字後會自動結束程式
- 如果沒有找到關鍵字，程序結束前會等待用戶按Enter鍵
- 如需在背景運行（無界面模式），請取消腳本中相應註釋

## 新增功能

1. **防機器人檢測**：腳本現在包含多種防止被檢測為自動化工具的機制：
   - 隨機用戶代理
   - 隨機延遲和暫停
   - 模擬人類打字和滾動行為
   - 隱藏自動化特徵

2. **驗證碼處理**：當檢測到Google驗證碼時，腳本會：
   - 自動暫停並通知用戶
   - 等待用戶手動完成驗證
   - 驗證完成後自動繼續執行

3. **增強的錯誤處理**：
   - 自動重試機制
   - 詳細的日誌記錄
   - 更友好的錯誤提示

## 使用方法

### 基本使用

基本用法：
```
python google_keyword_search.py "搜尋詞" "目標關鍵字"
```

指定最大搜尋頁數：
```
python google_keyword_search.py "搜尋詞" "目標關鍵字" 10
```

## 可能的問題與解決方案

1. **ChromeDriver 版本不匹配**：確保下載的 ChromeDriver 版本與您的 Chrome 瀏覽器版本相匹配。

2. **Google 驗證碼**：當遇到驗證碼時，請按照屏幕提示手動完成驗證，然後按Enter繼續。

3. **元素定位失敗**：Google 可能會更改其頁面結構。如果腳本無法正常工作，可能需要更新元素定位方式。

4. **網絡問題**：確保您的網絡連接穩定，特別是在處理驗證碼時。