# Technology Stack

## Core Technologies (v2.0 Cloud Architecture)

### Cloud Platforms
- **GitHub Actions**: CI/CD and scheduled task execution
- **Cloudflare Workers**: Serverless edge computing platform
- **Cloudflare KV**: Key-value storage for results and configuration

### Runtime & Languages
- **Node.js 18+**: Primary runtime environment
- **JavaScript/TypeScript**: Main programming languages
- **Puppeteer**: Headless browser automation (replaces Selenium)

### Legacy Technologies (v1.0 Local)
- **Python 3.6+**: Original programming language
- **Selenium WebDriver**: Browser automation framework
- **Chrome/Chromium**: Target browser for automation
- **ChromeDriver**: Browser driver (auto-managed via webdriver-manager)

## Key Dependencies

- `selenium>=4.1.0`: Web browser automation
- `webdriver-manager`: Automatic ChromeDriver management
- Standard library modules: `csv`, `logging`, `argparse`, `random`, `time`, `urllib.parse`

## Architecture Patterns

- **Modular Design**: Core functionality separated into reusable functions
- **Error Handling**: Comprehensive try-catch blocks with retry mechanisms
- **Anti-Detection**: Human-like behavior simulation with random delays and scrolling
- **Logging**: Structured logging throughout the application
- **Configuration**: Command-line argument parsing with sensible defaults

## Common Commands

### Cloud Version (v2.0)

#### GitHub Actions
```bash
# Fork and setup
gh repo fork your-username/gsc-keyword-search
cd gsc-keyword-search

# Install dependencies
npm run setup

# Manual trigger via GitHub CLI
gh workflow run keyword-search.yml

# Local testing
npm start
```

#### Cloudflare Workers
```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Deploy worker
npm run deploy:worker

# Local development
npm run dev:worker

# API usage
curl -X POST https://your-worker.workers.dev/api/search \
  -H "Content-Type: application/json" \
  -d '{"searchQuery": "Python", "targetKeywords": ["Django"]}'
```

### Local Version (v1.0 Legacy)

#### Installation
```bash
# Install Python dependencies
pip install -r requirements.txt

# Alternative installation
python3 -m pip install selenium webdriver-manager
```

#### Running the Application
```bash
# Interactive launcher (recommended)
python3 start.py

# Single keyword search
python3 main.py "search term" "target keyword1" "target keyword2"

# CSV batch processing
python3 google_keyword_search_csv.py keywords.csv [max_pages]

# With proxy support
python3 main.py "search term" "target" --proxy-file proxies.txt
```

### Development
```bash
# Run with debug logging
python3 main.py "search term" "target" --max-pages 3

# Test CSV processing
python3 google_keyword_search_csv.py keywords.csv 5
```

## Browser Configuration

- **Headless Mode**: Available but disabled by default for debugging
- **User Agent Rotation**: Multiple predefined user agents for macOS/Chrome
- **Anti-Detection Features**: Disabled automation indicators, custom preferences
- **Proxy Support**: HTTP proxy configuration through Chrome options