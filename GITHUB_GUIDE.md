# 🐙 GitHub 版本使用指南

## 為什麼選擇 GitHub？

✅ **文件管理超方便**：直接在網頁上編輯 `keywords.csv`  
✅ **自動執行**：每次更新文件自動觸發搜索  
✅ **結果永久保存**：所有搜索結果都存在倉庫裡  
✅ **版本控制**：可以看到每次修改的歷史  
✅ **免費使用**：GitHub Actions 每月 2000 分鐘免費額度  
✅ **隨時隨地**：任何設備都能管理和查看結果  

## 🚀 5分鐘快速設置

### 步驟 1: Fork 倉庫
1. 點擊右上角的 **Fork** 按鈕
2. 選擇你的 GitHub 帳號
3. 等待 Fork 完成

### 步驟 2: 啟用 Actions
1. 進入你 Fork 的倉庫
2. 點擊 **Actions** 頁籤
3. 點擊 **"I understand my workflows, go ahead and enable them"**

### 步驟 3: 編輯關鍵字
1. 點擊 `keywords.csv` 文件
2. 點擊 ✏️ **Edit this file**
3. 按照格式添加你的關鍵字：
   ```csv
   Python 教學,Django,Flask,FastAPI,目標關鍵字
   AI 工具,機器學習,深度學習,ChatGPT
   ```
4. 點擊 **Commit changes**

### 步驟 4: 觸發搜索
文件更新後會自動觸發搜索，或者：
1. 進入 **Actions** → **GSC關鍵字搜索**
2. 點擊 **Run workflow**
3. 輸入搜索參數並執行

## 📝 日常使用流程

### 🔄 定期更新關鍵字

1. **直接在 GitHub 網頁編輯**：
   - 進入倉庫 → 點擊 `keywords.csv`
   - 點擊 ✏️ 編輯按鈕
   - 修改內容後 Commit

2. **批量更新**：
   - 可以複製貼上大量關鍵字
   - 支援 Excel 複製格式

3. **版本管理**：
   - 每次修改都有記錄
   - 可以回滾到之前的版本

### 📊 查看搜索結果

1. **即時查看**：
   - Actions 頁面看執行狀態
   - 綠色 ✅ = 成功，紅色 ❌ = 失敗

2. **詳細報告**：
   - `reports/` 資料夾：HTML 和 Markdown 報告
   - `results/` 資料夾：JSON 格式詳細數據

3. **下載結果**：
   - 點擊 Actions 中的執行記錄
   - 下載 Artifacts 壓縮檔

## 🛠️ 進階配置

### 修改執行頻率

編輯 `.github/workflows/keyword-search.yml`：

```yaml
schedule:
  - cron: '0 */6 * * *'  # 每6小時執行
  # - cron: '0 9 * * *'   # 每天早上9點執行
  # - cron: '0 9 * * 1'   # 每週一早上9點執行
```

### 設置通知

1. **Email 通知**：
   - Settings → Notifications
   - 勾選 "Actions" 相關選項

2. **手機通知**：
   - 安裝 GitHub 手機 App
   - 開啟推送通知

### 自定義搜索參數

在 workflow 文件中修改默認值：

```yaml
env:
  MAX_PAGES: '10'        # 最大搜索頁數
  RETRY_COUNT: '3'       # 重試次數
  DELAY_SECONDS: '2'     # 延遲秒數
```

## 📱 手機管理

### GitHub 手機 App
1. 下載 GitHub 官方 App
2. 可以直接編輯 `keywords.csv`
3. 查看 Actions 執行狀態
4. 接收通知

### 網頁版手機操作
1. 手機瀏覽器打開 GitHub
2. 所有功能都可正常使用
3. 編輯文件、查看結果都很方便

## 🔍 實用技巧

### 1. 關鍵字格式技巧

```csv
# ✅ 推薦格式
搜索詞1,搜索詞2,目標關鍵字

# ✅ 多個搜索詞對應一個目標
Python 教學,Python 入門,Python 基礎,Django
AI 工具,人工智能,機器學習,ChatGPT

# ✅ 使用引號包含特殊字符
"Python 3.9",Python最新版,Python更新

# ❌ 避免空行和格式錯誤
```

### 2. 批量管理技巧

```csv
# 按主題分組
# === SEO 相關 ===
SEO 優化,關鍵字研究,搜索引擎優化,Google

# === 程式設計 ===
Python 教學,程式設計,編程學習,Django

# === 行銷工具 ===
數位行銷,網路行銷,行銷工具,Facebook
```

### 3. 結果分析技巧

1. **查看趨勢**：
   - 比較不同時間的搜索結果
   - 觀察關鍵字排名變化

2. **優化策略**：
   - 找到排名較低的關鍵字
   - 調整搜索詞組合

3. **競爭分析**：
   - 搜索競爭對手的關鍵字
   - 分析他們的排名情況

## 🚨 常見問題解決

### Q: Actions 執行失敗怎麼辦？
A: 
1. 檢查 `keywords.csv` 格式是否正確
2. 查看 Actions 日誌的錯誤信息
3. 可能是 Google 反爬蟲，等待一段時間重試

### Q: 如何增加搜索成功率？
A:
1. 降低搜索頻率（修改 cron 設定）
2. 增加隨機延遲時間
3. 分批處理大量關鍵字

### Q: 結果文件太多怎麼管理？
A:
1. 定期清理舊的結果文件
2. 只保留最近的報告
3. 下載重要結果到本地

### Q: 如何分享結果給團隊？
A:
1. 將倉庫設為 Public（如果內容允許）
2. 生成 GitHub Pages 展示報告
3. 定期匯出 CSV 分享

## 📈 最佳實踐

### 1. 關鍵字管理
- 定期檢查和更新關鍵字列表
- 移除不再需要的關鍵字
- 按主題或項目分組管理

### 2. 執行頻率
- 新項目：每天執行
- 穩定項目：每週執行
- 監控項目：每小時執行

### 3. 結果利用
- 定期分析搜索報告
- 根據結果調整 SEO 策略
- 與團隊分享重要發現

## 🎯 進階應用

### 1. 多項目管理
為不同項目創建不同的 CSV 文件：
- `keywords-project-a.csv`
- `keywords-project-b.csv`
- 修改 workflow 支援多文件

### 2. 自動報告
設置自動發送報告到 Email 或 Slack：
```yaml
- name: Send Report
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 465
    username: ${{secrets.MAIL_USERNAME}}
    password: ${{secrets.MAIL_PASSWORD}}
    subject: GSC搜索報告
    body: file://reports/latest-report.md
```

### 3. 數據分析
結合其他工具分析搜索數據：
- 匯出到 Google Sheets
- 使用 Python 分析趨勢
- 建立 Dashboard 展示

---

🎉 **恭喜！** 你現在可以完全在 GitHub 上管理你的關鍵字搜索工具了！

有任何問題歡迎在 Issues 中提出，我們會盡快回覆。