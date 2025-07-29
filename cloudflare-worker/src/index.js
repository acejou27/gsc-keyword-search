/**
 * GSC關鍵字搜索工具 - Cloudflare Workers版本
 * 
 * 主要功能：
 * - 無伺服器關鍵字搜索
 * - 支援批量處理
 * - 結果存儲到KV
 * - RESTful API接口
 */

import { SearchEngine } from './search/engine.js';
import { ResultProcessor } from './processors/results.js';
import { RateLimiter } from './utils/rateLimiter.js';
import { Logger } from './utils/logger.js';

export default {
  async fetch(request, env, ctx) {
    const logger = new Logger(env.ENVIRONMENT);
    const rateLimiter = new RateLimiter(env);
    
    try {
      // CORS 處理
      if (request.method === 'OPTIONS') {
        return handleCORS();
      }

      // 速率限制檢查
      const clientIP = request.headers.get('CF-Connecting-IP');
      if (!(await rateLimiter.checkLimit(clientIP))) {
        return new Response('Rate limit exceeded', { status: 429 });
      }

      const url = new URL(request.url);
      const path = url.pathname;

      // 路由處理
      switch (path) {
        case '/api/search':
          return handleSearch(request, env, logger);
        
        case '/api/batch':
          return handleBatchSearch(request, env, logger);
        
        case '/api/results':
          return handleGetResults(request, env, logger);
        
        case '/api/status':
          return handleStatus(request, env, logger);
        
        case '/':
          return handleWebInterface();
        
        default:
          return new Response('Not Found', { status: 404 });
      }

    } catch (error) {
      logger.error('Worker error:', error);
      return new Response('Internal Server Error', { 
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: error.message })
      });
    }
  },

  // 定時任務處理
  async scheduled(controller, env, ctx) {
    const logger = new Logger(env.ENVIRONMENT);
    logger.info('Scheduled task triggered');
    
    try {
      // 執行預設的關鍵字搜索任務
      await executeScheduledSearch(env, logger);
    } catch (error) {
      logger.error('Scheduled task error:', error);
    }
  }
};

/**
 * 處理單次搜索請求
 */
async function handleSearch(request, env, logger) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const body = await request.json();
  const { searchQuery, targetKeywords, maxPages = 5 } = body;

  if (!searchQuery || !targetKeywords) {
    return new Response('Missing required parameters', { status: 400 });
  }

  const searchEngine = new SearchEngine(env, logger);
  const results = await searchEngine.search({
    searchQuery,
    targetKeywords: Array.isArray(targetKeywords) ? targetKeywords : [targetKeywords],
    maxPages: parseInt(maxPages)
  });

  // 存儲結果到KV
  const resultId = generateResultId();
  await env.SEARCH_RESULTS.put(resultId, JSON.stringify({
    ...results,
    timestamp: new Date().toISOString(),
    searchQuery,
    targetKeywords
  }));

  return new Response(JSON.stringify({
    success: true,
    resultId,
    results
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 處理批量搜索請求
 */
async function handleBatchSearch(request, env, logger) {
  if (request.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 });
  }

  const body = await request.json();
  const { keywords, maxPages = 5 } = body;

  if (!keywords || !Array.isArray(keywords)) {
    return new Response('Invalid keywords format', { status: 400 });
  }

  const searchEngine = new SearchEngine(env, logger);
  const batchId = generateResultId();
  const results = [];

  for (const keywordSet of keywords) {
    const { searchQuery, targetKeywords } = keywordSet;
    
    try {
      const result = await searchEngine.search({
        searchQuery,
        targetKeywords: Array.isArray(targetKeywords) ? targetKeywords : [targetKeywords],
        maxPages: parseInt(maxPages)
      });
      
      results.push({
        searchQuery,
        targetKeywords,
        result,
        status: 'success'
      });
    } catch (error) {
      logger.error(`Search failed for ${searchQuery}:`, error);
      results.push({
        searchQuery,
        targetKeywords,
        error: error.message,
        status: 'failed'
      });
    }
  }

  // 存儲批量結果
  await env.SEARCH_RESULTS.put(`batch_${batchId}`, JSON.stringify({
    batchId,
    results,
    timestamp: new Date().toISOString(),
    totalQueries: keywords.length,
    successCount: results.filter(r => r.status === 'success').length
  }));

  return new Response(JSON.stringify({
    success: true,
    batchId,
    summary: {
      total: keywords.length,
      successful: results.filter(r => r.status === 'success').length,
      failed: results.filter(r => r.status === 'failed').length
    },
    results
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 獲取搜索結果
 */
async function handleGetResults(request, env, logger) {
  const url = new URL(request.url);
  const resultId = url.searchParams.get('id');

  if (!resultId) {
    return new Response('Missing result ID', { status: 400 });
  }

  const result = await env.SEARCH_RESULTS.get(resultId);
  
  if (!result) {
    return new Response('Result not found', { status: 404 });
  }

  return new Response(result, {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * 系統狀態檢查
 */
async function handleStatus(request, env, logger) {
  return new Response(JSON.stringify({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    environment: env.ENVIRONMENT,
    version: '2.0.0'
  }), {
    headers: { 'Content-Type': 'application/json' }
  });
}

/**
 * Web 界面
 */
function handleWebInterface() {
  const html = `
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GSC關鍵字搜索工具</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, textarea, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .results { margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 4px; }
    </style>
</head>
<body>
    <h1>🔍 GSC關鍵字搜索工具</h1>
    <p>雲端版本 - 無需本地資源，快速高效</p>
    
    <form id="searchForm">
        <div class="form-group">
            <label for="searchQuery">搜索詞：</label>
            <input type="text" id="searchQuery" required placeholder="例如：Python 教學">
        </div>
        
        <div class="form-group">
            <label for="targetKeywords">目標關鍵字（一行一個）：</label>
            <textarea id="targetKeywords" rows="4" required placeholder="Django&#10;Flask&#10;FastAPI"></textarea>
        </div>
        
        <div class="form-group">
            <label for="maxPages">最大搜索頁數：</label>
            <select id="maxPages">
                <option value="3">3頁</option>
                <option value="5" selected>5頁</option>
                <option value="10">10頁</option>
            </select>
        </div>
        
        <button type="submit">開始搜索</button>
    </form>
    
    <div id="results" class="results" style="display: none;">
        <h3>搜索結果</h3>
        <div id="resultContent"></div>
    </div>

    <script>
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const searchQuery = document.getElementById('searchQuery').value;
            const targetKeywords = document.getElementById('targetKeywords').value.split('\\n').filter(k => k.trim());
            const maxPages = document.getElementById('maxPages').value;
            
            const resultsDiv = document.getElementById('results');
            const resultContent = document.getElementById('resultContent');
            
            resultContent.innerHTML = '<p>搜索中，請稍候...</p>';
            resultsDiv.style.display = 'block';
            
            try {
                const response = await fetch('/api/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ searchQuery, targetKeywords, maxPages })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    resultContent.innerHTML = \`
                        <h4>搜索完成！</h4>
                        <p><strong>結果ID：</strong> \${data.resultId}</p>
                        <pre>\${JSON.stringify(data.results, null, 2)}</pre>
                    \`;
                } else {
                    resultContent.innerHTML = '<p style="color: red;">搜索失敗，請稍後重試。</p>';
                }
            } catch (error) {
                resultContent.innerHTML = \`<p style="color: red;">錯誤：\${error.message}</p>\`;
            }
        });
    </script>
</body>
</html>`;

  return new Response(html, {
    headers: { 'Content-Type': 'text/html' }
  });
}

/**
 * CORS 處理
 */
function handleCORS() {
  return new Response(null, {
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }
  });
}

/**
 * 執行定時搜索任務
 */
async function executeScheduledSearch(env, logger) {
  // 從配置中獲取預設關鍵字
  const config = await env.CONFIG.get('scheduled_keywords');
  
  if (!config) {
    logger.info('No scheduled keywords configured');
    return;
  }

  const keywords = JSON.parse(config);
  const searchEngine = new SearchEngine(env, logger);
  
  for (const keywordSet of keywords) {
    try {
      await searchEngine.search(keywordSet);
      logger.info(`Scheduled search completed for: ${keywordSet.searchQuery}`);
    } catch (error) {
      logger.error(`Scheduled search failed for ${keywordSet.searchQuery}:`, error);
    }
  }
}

/**
 * 生成結果ID
 */
function generateResultId() {
  return `result_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}