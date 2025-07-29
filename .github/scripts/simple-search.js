/**
 * 簡化版搜索腳本 - 用於測試
 */

const fs = require('fs').promises;

async function createTestResults() {
    console.log('🧪 創建測試結果...');
    
    // 確保目錄存在
    try {
        await fs.mkdir('results', { recursive: true });
        await fs.mkdir('reports', { recursive: true });
    } catch (error) {
        console.log('目錄已存在或創建失敗:', error.message);
    }
    
    // 創建測試結果
    const testResults = {
        timestamp: new Date().toISOString(),
        totalSearches: 3,
        successfulSearches: 3,
        duration: 5000,
        results: [
            {
                searchQuery: "Python 教學",
                targetKeywords: ["Django"],
                success: true,
                timestamp: new Date().toISOString(),
                results: {
                    "Django": {
                        found: true,
                        page: 1,
                        position: 3,
                        title: "Django 官方教學文件",
                        url: "https://docs.djangoproject.com/",
                        snippet: "Django 是一個高級的 Python Web 框架..."
                    }
                }
            },
            {
                searchQuery: "SEO 優化",
                targetKeywords: ["Google"],
                success: true,
                timestamp: new Date().toISOString(),
                results: {
                    "Google": {
                        found: true,
                        page: 1,
                        position: 1,
                        title: "Google 搜索引擎優化指南",
                        url: "https://developers.google.com/search",
                        snippet: "了解如何讓您的網站在 Google 搜索中表現更好..."
                    }
                }
            },
            {
                searchQuery: "數位行銷",
                targetKeywords: ["Facebook"],
                success: true,
                timestamp: new Date().toISOString(),
                results: {
                    "Facebook": {
                        found: true,
                        page: 2,
                        position: 5,
                        title: "Facebook 商業廣告平台",
                        url: "https://business.facebook.com/",
                        snippet: "使用 Facebook 廣告來推廣您的業務..."
                    }
                }
            }
        ]
    };
    
    // 保存結果
    await fs.writeFile('results/latest.json', JSON.stringify(testResults, null, 2));
    
    // 創建簡單的 HTML 報告
    const htmlReport = `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSC 搜索結果報告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; border-radius: 8px; }
        .result { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
        .found { background: #e8f5e8; }
        .not-found { background: #ffe8e8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 GSC 關鍵字搜索報告</h1>
        <p>生成時間: ${new Date().toLocaleString('zh-TW')}</p>
    </div>
    
    <h2>📊 統計摘要</h2>
    <ul>
        <li>總搜索次數: ${testResults.totalSearches}</li>
        <li>成功搜索: ${testResults.successfulSearches}</li>
        <li>成功率: 100%</li>
    </ul>
    
    <h2>🔍 搜索結果</h2>
    ${testResults.results.map(result => `
        <div class="result found">
            <h3>${result.searchQuery}</h3>
            <p><strong>目標關鍵字:</strong> ${result.targetKeywords.join(', ')}</p>
            ${Object.entries(result.results).map(([keyword, data]) => `
                <p><strong>${keyword}:</strong> 
                ${data.found ? `✅ 在第 ${data.page} 頁第 ${data.position} 位找到` : '❌ 未找到'}
                </p>
                ${data.found ? `<p><a href="${data.url}" target="_blank">${data.title}</a></p>` : ''}
            `).join('')}
        </div>
    `).join('')}
    
    <footer style="margin-top: 40px; text-align: center; color: #666;">
        <p>🤖 由 GitHub Actions 自動生成</p>
    </footer>
</body>
</html>`;
    
    await fs.writeFile('reports/latest-report.html', htmlReport);
    
    console.log('✅ 測試結果創建完成！');
}

// 執行
if (require.main === module) {
    createTestResults().catch(console.error);
}