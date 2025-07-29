# Project Structure

## File Organization

```
├── README.md                           # Main documentation (English)
├── 快速開始.md                         # Quick start guide (Chinese)
├── requirements.txt                    # Python dependencies
├── keywords.csv                        # Sample CSV data for batch processing
├── chromedriver.exe                    # ChromeDriver binary (Windows)
├── start.py                           # Interactive launcher script
├── main.py                            # Main entry point for single searches
├── google_keyword_search.py           # Core search functionality
├── google_keyword_search_csv.py       # CSV batch processing module
└── __pycache__/                       # Python bytecode cache
```

## Core Modules

### `google_keyword_search.py`
- **Primary module** containing all core search functions
- Functions: `setup_driver()`, `search_google()`, `find_keyword_on_page()`, `find_and_click_result()`, `go_to_next_page()`
- Anti-detection utilities: `human_like_typing()`, `random_scroll()`, `check_for_captcha()`, `handle_captcha()`
- Comprehensive error handling and retry logic

### `main.py`
- Command-line interface for single keyword searches
- Imports and orchestrates functions from `google_keyword_search.py`
- Argument parsing with `argparse`
- Multi-keyword support and retry mechanisms

### `google_keyword_search_csv.py`
- Batch processing for CSV input files
- Functions: `read_csv_keywords()`, `process_keyword_pair()`
- Handles CSV parsing and result aggregation
- Supports multiple search terms per row with last column as target

### `start.py`
- Interactive menu-driven launcher
- Dependency checking and installation prompts
- User-friendly interface with colored terminal output
- Guides users through different execution modes

## Data Formats

### CSV Input Format
```csv
search_term1,search_term2,target_keyword
search_term3,search_term4,target_keyword
```
- Multiple search terms per row (comma-separated)
- Last column is always the target keyword
- Each search term will be used to search for the target keyword

### Proxy File Format
```
ip:port
ip:port
```
- One proxy per line
- Standard HTTP proxy format

## Code Conventions

- **Language**: Mixed Chinese/English (comments and strings in Chinese, code in English)
- **Encoding**: UTF-8 with explicit encoding declarations
- **Error Handling**: Comprehensive try-catch blocks with logging
- **Function Naming**: Snake_case with descriptive names
- **Constants**: Uppercase with underscores
- **Logging**: Structured logging with timestamps and levels
- **Retry Logic**: Configurable retry attempts with exponential backoff patterns