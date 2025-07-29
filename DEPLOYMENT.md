# 🚀 部署指南

本指南將幫助你將 GSC關鍵字搜索工具部署到雲端平台。

## 📋 部署選項

### 選項 1: GitHub Actions (推薦新手)

**優勢**: 免費、簡單、自動化
**適用**: 定時搜索、結果存檔

#### 步驟：

1. **Fork 倉庫**
   ```bash
   # 在 GitHub 上點擊 Fork 按鈕
   # 或使用 GitHub CLI
   gh repo fork your-username/gsc-keyword-search
   ```

2. **配置關鍵字**
   - 編輯 `keywords.csv` 文件
   - 格式：`搜索詞1,搜索詞2,目標關鍵字`

3. **啟用 Actions**
   - 進入你的倉庫 → Settings → Actions
   - 選擇 "Allow all actions and reusable workflows"

4. **手動執行**
   - Actions → GSC關鍵字搜索 → Run workflow

5. **查看結果**
   - 結果會自動提交到 `results/` 和 `reports/` 目錄

### 選項 2: Cloudflare Workers (推薦進階用戶)

**優勢**: 高性能、全球部署、Web界面
**適用**: API服務、即時搜索

#### 前置需求：
- Cloudflare 帳號
- Node.js 18+

#### 步驟：

1. **安裝 Wrangler**
   ```bash
   npm install -g wrangler
   ```

2. **登入 Cloudflare**
   ```bash
   wrangler login
   ```

3. **配置 KV 存儲**
   ```bash
   # 創建 KV 命名空間
   wrangler kv:namespace create "SEARCH_RESULTS"
   wrangler kv:namespace create "CONFIG"
   
   # 更新 wrangler.toml 中的 KV ID
   ```

4. **部署**
   ```bash
   cd cloudflare-worker
   npm install
   wrangler deploy
   ```

5. **配置環境變量**
   ```bash
   wrangler secret put API_KEY
   # 輸入你的 API 密鑰
   ```

### 選項 3: 混合部署 (推薦企業用戶)

結合 GitHub Actions 和 Cloudflare Workers：
- GitHub Actions 負責定時任務和結果存檔
- Cloudflare Workers 提供 API 和 Web 界面

## 🔧 配置說明

### GitHub Actions 配置

編輯 `.github/workflows/keyword-search.yml`：

```yaml
# 修改執行頻率
schedule:
  - cron: '0 */6 * * *'  # 每6小時執行一次

# 修改默認參數
env:
  MAX_PAGES: '10'
  DEFAULT_RETRY_COUNT: '3'
```

### Cloudflare Workers 配置

編輯 `cloudflare-worker/wrangler.toml`：

```toml
# 修改執行環境
[vars]
MAX_SEARCH_PAGES = "10"
RATE_LIMIT_PER_MINUTE = "60"

# 添加定時觸發
[[triggers]]
crons = ["0 */6 * * *"]
```

### 關鍵字配置

編輯 `keywords.csv`：

```csv
Python 教學,Django,Flask,FastAPI,目標關鍵字
AI 工具,機器學習,深度學習,ChatGPT
SEO 優化,關鍵字研究,搜索引擎,Google
```

格式說明：
- 每行代表一組搜索任務
- 最後一列是目標關鍵字
- 前面的列都是搜索詞

## 🔐 安全配置

### API 密鑰保護

```bash
# GitHub Secrets
gh secret set API_KEY --body "your-secret-key"

# Cloudflare Workers
wrangler secret put API_KEY
```

### 速率限制

```javascript
// 在 Cloudflare Workers 中
const rateLimiter = new RateLimiter({
  requestsPerMinute: 60,
  requestsPerHour: 1000
});
```

## 📊 監控和日誌

### GitHub Actions 監控

- 查看 Actions 頁面的執行歷史
- 檢查 Artifacts 中的結果文件
- 設置失敗通知

### Cloudflare Workers 監控

```bash
# 查看日誌
wrangler tail

# 查看分析數據
wrangler analytics
```

## 🚨 故障排除

### 常見問題

1. **GitHub Actions 執行失敗**
   ```bash
   # 檢查權限設置
   # Settings → Actions → General → Workflow permissions
   # 選擇 "Read and write permissions"
   ```

2. **Cloudflare Workers 部署失敗**
   ```bash
   # 檢查 wrangler.toml 配置
   # 確保 KV 命名空間 ID 正確
   wrangler kv:namespace list
   ```

3. **搜索被 Google 封鎖**
   ```bash
   # 降低搜索頻率
   # 添加更多隨機延遲
   # 使用代理服務
   ```

### 調試模式

```bash
# GitHub Actions 本地測試
act -j search

# Cloudflare Workers 本地開發
wrangler dev
```

## 📈 性能優化

### GitHub Actions 優化

- 使用 cache 加速依賴安裝
- 並行執行多個搜索任務
- 優化 Puppeteer 配置

### Cloudflare Workers 優化

- 使用 KV 緩存搜索結果
- 實現智能重試機制
- 優化 Puppeteer 資源使用

## 🔄 升級指南

### 從本地版本升級

1. 備份現有的 `keywords.csv`
2. Fork 新版本倉庫
3. 複製關鍵字配置
4. 按照部署步驟執行

### 版本更新

```bash
# 同步上游更新
git remote add upstream https://github.com/original-repo/gsc-keyword-search.git
git fetch upstream
git merge upstream/main
```

## 💡 最佳實踐

1. **關鍵字管理**
   - 定期更新關鍵字列表
   - 分組管理不同類型的關鍵字
   - 監控搜索成功率

2. **結果分析**
   - 定期檢查生成的報告
   - 分析關鍵字排名變化
   - 調整搜索策略

3. **資源管理**
   - 合理設置搜索頻率
   - 監控 API 使用量
   - 優化搜索參數

## 📞 支援

如果遇到問題：

1. 查看 [Issues](https://github.com/your-repo/issues) 頁面
2. 檢查 [Wiki](https://github.com/your-repo/wiki) 文檔
3. 提交新的 Issue 描述問題

---

🎉 恭喜！你已經成功部署了 GSC關鍵字搜索工具的雲端版本！