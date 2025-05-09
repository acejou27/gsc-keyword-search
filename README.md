# 網頁關鍵字搜尋工具

這個工具可以在Google搜尋結果中自動尋找特定關鍵字，如果當前頁面沒有找到則自動翻到下一頁繼續搜尋。

## 功能特點

- 在Google搜尋結果中自動搜尋關鍵字
- 如果當前頁面沒有找到關鍵字，自動翻到下一頁
- 找到關鍵字後高亮顯示
- 找到關鍵字後自動結束程式
- 支持命令行參數傳入搜尋詞和目標關鍵字

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

## 使用方法

### 基本使用

```bash
python google_keyword_search.py [搜尋詞] [目標關鍵字]
```

### 例如：

```bash
python google_keyword_search.py "Python 教學" "Django"
```

這將在Google上搜尋「Python 教學」，然後在搜尋結果中尋找「Django」這個關鍵字。

### 使用代理功能

使用新的main.py腳本可以啟用代理功能，支持GSA Proxy導出的代理列表：

```bash
python main.py [搜尋詞] [目標關鍵字] --proxy-file [代理文件路徑]
```

例如：

```bash
python main.py "Python 教學" "Django" --proxy-file proxies.txt
```

### 代理文件格式

代理文件應為純文本文件，每行一個代理，格式為IP:端口，例如：

```
192.168.1.1:8080
192.168.1.2:8080
```

### 完整命令行參數

```bash
python main.py [搜尋詞] [目標關鍵字] [選項]
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
python google_keyword_search_csv.py keywords.csv [最大頁數]
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

- 程序默認最多搜尋5頁結果
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