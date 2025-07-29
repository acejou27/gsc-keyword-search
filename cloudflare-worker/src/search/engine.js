/**
 * 搜索引擎核心模組
 * 使用 Puppeteer 進行無頭瀏覽器搜索
 */

import puppeteer from '@cloudflare/puppeteer';

export class SearchEngine {
  constructor(env, logger) {
    this.env = env;
    this.logger = logger;
    this.maxRetries = parseInt(env.DEFAULT_RETRY_COUNT) || 3;
  }

  /**
   * 執行關鍵字搜索
   */
  async search({ searchQuery, targetKeywords, maxPages = 5 }) {
    this.logger.info(`Starting search for: ${searchQuery}`);
    
    let browser;
    try {
      // 啟動瀏覽器
      browser = await puppeteer.launch({
        args: [
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-gpu',
          '--no-first-run',
          '--no-zygote',
          '--single-process'
        ]
      });

      const page = await browser.newPage();
      
      // 設置反檢測機制
      await this.setupAntiDetection(page);
      
      // 執行搜索
      const results = await this.performSearch(page, searchQuery, targetKeywords, maxPages);
      
      return {
        success: true,
        searchQuery,
        targetKeywords,
        results,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      this.logger.error('Search error:', error);
      throw error;
    } finally {
      if (browser) {
        await browser.close();
      }
    }
  }

  /**
   * 設置反檢測機制
   */
  async setupAntiDetection(page) {
    // 設置用戶代理
    const userAgents = [
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ];
    
    const randomUA = userAgents[Math.floor(Math.random() * userAgents.length)];
    await page.setUserAgent(randomUA);

    // 設置視窗大小
    await page.setViewport({
      width: 1366 + Math.floor(Math.random() * 100),
      height: 768 + Math.floor(Math.random() * 100)
    });

    // 隱藏 webdriver 屬性
    await page.evaluateOnNewDocument(() => {
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
      });
    });

    // 設置語言和時區
    await page.setExtraHTTPHeaders({
      'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8'
    });
  }

  /**
   * 執行搜索邏輯
   */
  async performSearch(page, searchQuery, targetKeywords, maxPages) {
    const results = {};
    
    // 初始化結果結構
    targetKeywords.forEach(keyword => {
      results[keyword] = {
        found: false,
        page: null,
        position: null,
        url: null,
        title: null,
        snippet: null
      };
    });

    try {
      // 訪問 Google 搜索
      const searchUrl = `https://www.google.com/search?q=${encodeURIComponent(searchQuery)}&hl=zh-TW`;
      await page.goto(searchUrl, { waitUntil: 'networkidle2' });

      // 檢查是否有驗證碼
      if (await this.checkForCaptcha(page)) {
        throw new Error('CAPTCHA detected - search blocked');
      }

      // 搜索多頁結果
      for (let currentPage = 1; currentPage <= maxPages; currentPage++) {
        this.logger.info(`Searching page ${currentPage} for: ${searchQuery}`);
        
        // 等待搜索結果加載
        await page.waitForSelector('#search', { timeout: 10000 });
        
        // 在當前頁面搜索目標關鍵字
        const pageResults = await this.searchKeywordsOnPage(page, targetKeywords, currentPage);
        
        // 更新結果
        Object.keys(pageResults).forEach(keyword => {
          if (pageResults[keyword].found && !results[keyword].found) {
            results[keyword] = pageResults[keyword];
          }
        });

        // 檢查是否所有關鍵字都已找到
        const allFound = targetKeywords.every(keyword => results[keyword].found);
        if (allFound) {
          this.logger.info('All keywords found, stopping search');
          break;
        }

        // 如果不是最後一頁，點擊下一頁
        if (currentPage < maxPages) {
          const hasNextPage = await this.goToNextPage(page);
          if (!hasNextPage) {
            this.logger.info('No more pages available');
            break;
          }
        }
      }

    } catch (error) {
      this.logger.error('Search execution error:', error);
      throw error;
    }

    return results;
  }

  /**
   * 在當前頁面搜索關鍵字
   */
  async searchKeywordsOnPage(page, targetKeywords, pageNumber) {
    const results = {};
    
    // 獲取所有搜索結果
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

    // 檢查每個目標關鍵字
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
          
          this.logger.info(`Found keyword "${keyword}" on page ${pageNumber}, position ${result.position}`);
          break;
        }
      }
    }

    return results;
  }

  /**
   * 檢查是否有驗證碼
   */
  async checkForCaptcha(page) {
    try {
      const captchaSelectors = [
        '#captcha-form',
        '.g-recaptcha',
        '[src*="recaptcha"]',
        'iframe[src*="recaptcha"]'
      ];

      for (const selector of captchaSelectors) {
        const element = await page.$(selector);
        if (element) {
          return true;
        }
      }

      // 檢查頁面標題是否包含驗證相關文字
      const title = await page.title();
      if (title.includes('驗證') || title.includes('Captcha') || title.includes('unusual traffic')) {
        return true;
      }

      return false;
    } catch (error) {
      this.logger.warn('Error checking for captcha:', error);
      return false;
    }
  }

  /**
   * 跳轉到下一頁
   */
  async goToNextPage(page) {
    try {
      // 等待並點擊下一頁按鈕
      const nextButton = await page.$('#pnnext');
      
      if (!nextButton) {
        return false;
      }

      // 檢查按鈕是否可點擊
      const isDisabled = await page.evaluate(el => {
        return el.style.display === 'none' || el.hasAttribute('disabled');
      }, nextButton);

      if (isDisabled) {
        return false;
      }

      // 點擊下一頁
      await Promise.all([
        page.waitForNavigation({ waitUntil: 'networkidle2' }),
        nextButton.click()
      ]);

      // 隨機延遲，模擬人類行為
      await this.randomDelay(1000, 3000);

      return true;
    } catch (error) {
      this.logger.warn('Error going to next page:', error);
      return false;
    }
  }

  /**
   * 隨機延遲
   */
  async randomDelay(min, max) {
    const delay = Math.floor(Math.random() * (max - min + 1)) + min;
    await new Promise(resolve => setTimeout(resolve, delay));
  }
}