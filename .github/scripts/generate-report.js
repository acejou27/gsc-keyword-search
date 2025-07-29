/**
 * 生成搜索報告腳本
 * 創建 HTML 和 Markdown 格式的報告
 */

const fs = require('fs').promises;
const path = require('path');

class ReportGenerator {
  constructor() {
    this.latestResults = null;
  }

  async generate() {
    console.log('📊 開始生成搜索報告');
    
    try {
      // 讀取最新結果
      await this.loadLatestResults();
      
      // 生成 HTML 報告
      await this.generateHTMLReport();
      
      // 生成 Markdown 報告
      await this.generateMarkdownReport();
      
      // 更新 README
      await this.updateREADME();
      
      console.log('✅ 報告生成完成');
      
    } catch (error) {
      console.error('❌ 報告生成失敗:', error);
      process.exit(1);
    }
  }

  async loadLatestResults() {
    try {
      const data = await fs.readFile('results/latest.json', 'utf8');
      this.latestResults = JSON.parse(data);
    } catch (error) {
      throw new Error('無法讀取最新搜索結果');
    }
  }

  async generateHTMLReport() {
    const html = `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSC關鍵字搜索報告</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header .subtitle { opacity: 0.9; margin-top: 10px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .stat-label { color: #666; margin-top: 5px; }
        .results { padding: 0 30px 30px; }
        .search-result { margin-bottom: 30px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden; }
        .search-header { background: #f8f9fa; padding: 15px 20px; border-bottom: 1px solid #e9ecef; }
        .search-query { font-size: 1.2em; font-weight: bold; color: #333; }
        .search-meta { color: #666; font-size: 0.9em; margin-top: 5px; }
        .keywords { padding: 20px; }
        .keyword-result { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f0f0f0; }
        .keyword-result:last-child { border-bottom: none; }
        .keyword-name { font-weight: bold; min-width: 150px; }
        .status { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .status.found { background: #d4edda; color: #155724; }
        .status.not-found { background: #f8d7da; color: #721c24; }
        .result-details { margin-left: 20px; flex: 1; }
        .result-title { color: #1a0dab; text-decoration: none; }
        .result-title:hover { text-decoration: underline; }
        .result-snippet { color: #666; font-size: 0.9em; margin-top: 5px; }
        .footer { text-align: center; padding: 20px; color: #666; border-top: 1px solid #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 GSC關鍵字搜索報告</h1>
            <div class="subtitle">
                生成時間: ${new Date(this.latestResults.timestamp).toLocaleString('zh-TW')}
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">${this.latestResults.totalSearches}</div>
                <div class="stat-label">總搜索次數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.latestResults.successfulSearches}</div>
                <div class="stat-label">成功搜索</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${this.getFoundKeywordsCount()}</div>
                <div class="stat-label">找到關鍵字</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${Math.round(this.latestResults.duration / 1000)}s</div>
                <div class="stat-label">執行時間</div>
            </div>
        </div>
        
        <div class="results">
            ${this.generateResultsHTML()}
        </div>
        
        <div class="footer">
            <p>由 GitHub Actions 自動生成 | GSC關鍵字搜索工具 v2.0</p>
        </div>
    </div>
</body>
</html>`;

    await fs.writeFile('reports/latest-report.html', html);
  }

  generateResultsHTML() {
    return this.latestResults.results.map(result => {
      if (!result.success) {
        return `
          <div class="search-result">
            <div class="search-header">
              <div class="search-query">${result.searchQuery}</div>
              <div class="search-meta">❌ 搜索失敗: ${result.error}</div>
            </div>
          </div>`;
      }

      const keywordsHTML = result.targetKeywords.map(keyword => {
        const keywordResult = result.results[keyword];
        const statusClass = keywordResult.found ? 'found' : 'not-found';
        const statusText = keywordResult.found ? '✅ 已找到' : '❌ 未找到';

        return `
          <div class="keyword-result">
            <div class="keyword-name">${keyword}</div>
            <div class="status ${statusClass}">${statusText}</div>
            ${keywordResult.found ? `
              <div class="result-details">
                <div>第 ${keywordResult.page} 頁 第 ${keywordResult.position} 位</div>
                <a href="${keywordResult.url}" class="result-title" target="_blank">${keywordResult.title}</a>
                <div class="result-snippet">${keywordResult.snippet}</div>
              </div>
            ` : ''}
          </div>`;
      }).join('');

      return `
        <div class="search-result">
          <div class="search-header">
            <div class="search-query">${result.searchQuery}</div>
            <div class="search-meta">
              搜索時間: ${new Date(result.timestamp).toLocaleString('zh-TW')}
            </div>
          </div>
          <div class="keywords">
            ${keywordsHTML}
          </div>
        </div>`;
    }).join('');
  }

  async generateMarkdownReport() {
    const markdown = `# 🔍 GSC關鍵字搜索報告

**生成時間**: ${new Date(this.latestResults.timestamp).toLocaleString('zh-TW')}

## 📊 統計摘要

| 指標 | 數值 |
|------|------|
| 總搜索次數 | ${this.latestResults.totalSearches} |
| 成功搜索 | ${this.latestResults.successfulSearches} |
| 找到關鍵字 | ${this.getFoundKeywordsCount()} |
| 執行時間 | ${Math.round(this.latestResults.duration / 1000)}秒 |

## 🔍 搜索結果

${this.generateResultsMarkdown()}

---

*由 GitHub Actions 自動生成 | GSC關鍵字搜索工具 v2.0*`;

    await fs.writeFile('reports/latest-report.md', markdown);
  }

  generateResultsMarkdown() {
    return this.latestResults.results.map(result => {
      if (!result.success) {
        return `### ❌ ${result.searchQuery}

**狀態**: 搜索失敗  
**錯誤**: ${result.error}`;
      }

      const keywordsMarkdown = result.targetKeywords.map(keyword => {
        const keywordResult = result.results[keyword];
        
        if (keywordResult.found) {
          return `- ✅ **${keyword}**: 第 ${keywordResult.page} 頁第 ${keywordResult.position} 位
  - 標題: [${keywordResult.title}](${keywordResult.url})
  - 摘要: ${keywordResult.snippet}`;
        } else {
          return `- ❌ **${keyword}**: 未找到`;
        }
      }).join('\n');

      return `### 🔍 ${result.searchQuery}

**搜索時間**: ${new Date(result.timestamp).toLocaleString('zh-TW')}

${keywordsMarkdown}`;
    }).join('\n\n');
  }

  async updateREADME() {
    try {
      let readme = await fs.readFile('README.md', 'utf8');
      
      const statsSection = `## 📊 最新搜索統計

- **最後更新**: ${new Date(this.latestResults.timestamp).toLocaleString('zh-TW')}
- **總搜索次數**: ${this.latestResults.totalSearches}
- **成功率**: ${Math.round((this.latestResults.successfulSearches / this.latestResults.totalSearches) * 100)}%
- **找到關鍵字**: ${this.getFoundKeywordsCount()}

📈 [查看詳細報告](reports/latest-report.html) | 📋 [下載 CSV](reports/)`;

      // 查找並替換統計部分
      const statsRegex = /## 📊 最新搜索統計[\s\S]*?(?=\n## |\n---|\n\*|$)/;
      
      if (statsRegex.test(readme)) {
        readme = readme.replace(statsRegex, statsSection);
      } else {
        // 如果沒有找到統計部分，在文件開頭添加
        readme = statsSection + '\n\n' + readme;
      }
      
      await fs.writeFile('README.md', readme);
      
    } catch (error) {
      console.warn('⚠️ 無法更新 README:', error.message);
    }
  }

  getFoundKeywordsCount() {
    let count = 0;
    this.latestResults.results.forEach(result => {
      if (result.success) {
        result.targetKeywords.forEach(keyword => {
          if (result.results[keyword].found) {
            count++;
          }
        });
      }
    });
    return count;
  }
}

// 執行報告生成
if (require.main === module) {
  const generator = new ReportGenerator();
  generator.generate();
}