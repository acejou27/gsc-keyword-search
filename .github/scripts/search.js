/**
 * GitHub Actions 搜索腳本
 * 在 GitHub 環境中執行關鍵字搜索
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');
const csv = require('csv-parser');

class GitHubSearchEngine {
  constructor() {
    this.results = [];
    this.startTime = new Date();
  }

  async run() {
    console.log('🚀 開始執行 GitHub Actions 關鍵字搜索');
    
    try {
      // 確保結果目錄存在
      await this.ensureDirectories();
      
      // 獲取搜索參數
      const searchParams = await this.getSearchParameters();
      console.log('📋 搜索參數:', searchParams);
      
      // 執行搜索
      for (const params of searchParams) {
        await this.executeSearch(params);
      }
      
      // 保存結果
      await this.saveResults();
      
      console.log('✅ 搜索任務完成');
      
    } catch (error) {
      console.error('❌ 搜索任務失敗:', error);
      process.exit(1);
    }
  }

  async ensureDirectories() {
    const dirs = ['results', 'reports'];
    for (const dir of dirs) {
      try {
        await fs.mkdir(dir, { recursive: true });
      } catch (error) {
        // 目錄已存在，忽略錯誤
      }
    }
  }

  async getSearchParameters() {
    const params = [];
    
    // 從環境變量獲取參數（手動觸發）
    if (process.env.SEARCH_QUERY && process.env.TARGET_KEYWORDS) {
      params.push({
        searchQuery: process.env.SEARCH_QUERY,
        targetKeywords: process.env.TARGET_KEYWORDS.split(',').map(k => k.trim()),
        maxPages: parseInt(process.env.MAX_PAGES) || 5
      });
    } else {
      // 從 CSV 文件讀取參數（定時觸發）
      try {
        const csvData = await this.readCSVFile('keywords.csv');
        params.push(...csvData);
      } catch (error) {
        console.warn('⚠️ 無法讀取 CSV 文件，使用默認參數');
        params.push({
          searchQuery: 'Python 教學',
          targetKeywords: ['Django', 'Flask'],
          maxPages: 5
        });
      }
    }
    
    return params;
  }

  async readCSVFile(filePath) {
    const results = [];
    
    return new Promise((resolve, reject) => {
      const stream = require('fs').createReadStream(filePath)
        .pipe(csv({ headers: false }))
        .on('data', (row) => {
          const values = Object.values(row).filter(v => v && v.trim());
          if (values.length >= 2) {
            const targetKeyword = values[values.length - 1];
            const searchKeywords = values.slice(0, -1);
            
            searchKeywords.forEach(searchQuery => {
              results.push({
                searchQuery: searchQuery.trim(),
                targetKeywords: [targetKeyword.trim()],
                maxPages: 5
              });
            });
          }
        })
        .on('end', () => resolve(results))
        .on('error', reject);
    });
  }

  async executeSearch({ searchQuery, targetKeywords, maxPages }) {
    console.log(`🔍 搜索: "${searchQuery}" -> [${targetKeywords.join(', ')}]`);
    
    let browser;
    try {
      browser = await puppeteer.launch({
        headless: 'new',
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--no-first-run'
        ]
      });

      const page = await browser.newPage();
      await this.setupPage(page);
      
      const searchResults = await this.performSearch(page, searchQuery, targetKeywords, maxPages);
      
      this.results.push({
        searchQuery,
        targetKeywords,
        results: searchResults,
        timestamp: new Date().toISOString(),
        success: true
      });
      
      console.log(`✅ 完成搜索: ${searchQuery}`);
      
    } catch (error) {
      console.error(`❌ 搜索失敗 "${searchQuery}":`, error.message);
      
      this.results.push({
        searchQuery,
        targetKeywords,
        error: error.message,
        timestamp: new Date().toISOString(),
        success: false
      });
    } finally {
      if (browser) {
        await browser.close();
      }
    }
  }

  async setupPage(page) {
    // 設置用戶代理
    await page.setUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    
    // 設置視窗大小
    await page.setViewport({ width: 1366, height: 768 });
    
    // 設置語言
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
    });
  }

  async performSearch(page, searchQuery, targetKeywords, maxPages) {
    const results = {};
    
    // 初始化結果
    targetKeywords.forEach(keyword => {
      results[keyword] = { found: false };
    });

    // 訪問 Google 搜索
    const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}&hl=zh-TW`;
    await page.goto(searchUrl, { waitUntil: 'networkidle2' });

    // 搜索多頁
    for (let currentPage = 1; currentPage <= maxPages; currentPage++) {
      console.log(`  📄 搜索第 ${currentPage} 頁`);
      
      try {
        await page.waitForSelector('#search', { timeout: 10000 });
        
        // 搜索關鍵字
        const pageResults = await this.searchKeywordsOnPage(page, targetKeywords, currentPage);
        
        // 更新結果
        Object.keys(pageResults).forEach(keyword => {
          if (pageResults[keyword].found && !results[keyword].found) {
            results[keyword] = pageResults[keyword];
          }
        });

        // 檢查是否都找到了
        const allFound = targetKeywords.every(keyword => results[keyword].found);
        if (allFound) break;

        // 下一頁
        if (currentPage < maxPages) {
          const hasNext = await this.goToNextPage(page);
          if (!hasNext) break;
        }
        
      } catch (error) {
        console.warn(`  ⚠️ 第 ${currentPage} 頁搜索出錯:`, error.message);
        break;
      }
    }

    return results;
  }

  async searchKeywordsOnPage(page, targetKeywords, pageNumber) {
    const results = {};
    
    const searchResults = await page.$$eval('#search .g', (elements) => {
      return elements.map((el, index) => {
        const titleEl = el.querySelector('h3');
        const linkEl = el.querySelector('a');
        const snippetEl = el.querySelector('.VwiC3b, .s3v9rd, .st');
        
        return {
          position: index + 1,
          title: titleEl ? titleEl.textContent : '',
          url: linkEl ? linkEl.href : '',
          snippet: snippetEl ? snippetEl.textContent : ''
        };
      });
    });

    for (const keyword of targetKeywords) {
      results[keyword] = { found: false };
      
      for (const result of searchResults) {
        const searchText = `${result.title} ${result.snippet}`.toLowerCase();
        
        if (searchText.includes(keyword.toLowerCase())) {
          results[keyword] = {
            found: true,
            page: pageNumber,
            position: result.position,
            url: result.url,
            title: result.title,
            snippet: result.snippet
          };
          
          console.log(`    ✅ 找到 "${keyword}" 在第 ${pageNumber} 頁第 ${result.position} 位`);
          break;
        }
      }
    }

    return results;
  }

  async goToNextPage(page) {
    try {
      const nextButton = await page.$('#pnnext');
      if (!nextButton) return false;

      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2' }),
        nextButton.click()
      ]);

      await new Promise(resolve => setTimeout(resolve, 2000));
      return true;
    } catch (error) {
      return false;
    }
  }

  async saveResults() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    
    // 保存詳細結果
    const detailedResults = {
      timestamp: new Date().toISOString(),
      duration: new Date() - this.startTime,
      totalSearches: this.results.length,
      successfulSearches: this.results.filter(r => r.success).length,
      results: this.results
    };
    
    await fs.writeFile(
      `results/search-results-${timestamp}.json`,
      JSON.stringify(detailedResults, null, 2)
    );
    
    // 保存簡化的 CSV 報告
    const csvContent = this.generateCSVReport();
    await fs.writeFile(`reports/search-report-${timestamp}.csv`, csvContent);
    
    // 保存最新結果（用於 README 顯示）
    await fs.writeFile('results/latest.json', JSON.stringify(detailedResults, null, 2));
    
    console.log(`💾 結果已保存到 results/ 和 reports/ 目錄`);
  }

  generateCSVReport() {
    const headers = ['搜索詞', '目標關鍵字', '是否找到', '頁數', '位置', '標題', '網址'];
    const rows = [headers.join(',')];
    
    this.results.forEach(result => {
      if (result.success) {
        result.targetKeywords.forEach(keyword => {
          const keywordResult = result.results[keyword];
          rows.push([
            `"${result.searchQuery}"`,
            `"${keyword}"`,
            keywordResult.found ? '是' : '否',
            keywordResult.page || '',
            keywordResult.position || '',
            `"${keywordResult.title || ''}"`,
            `"${keywordResult.url || ''}"`
          ].join(','));
        });
      } else {
        result.targetKeywords.forEach(keyword => {
          rows.push([
            `"${result.searchQuery}"`,
            `"${keyword}"`,
            '錯誤',
            '',
            '',
            `"${result.error}"`,
            ''
          ].join(','));
        });
      }
    });
    
    return rows.join('\n');
  }
}

// 執行搜索
if (require.main === module) {
  const engine = new GitHubSearchEngine();
  engine.run();
}