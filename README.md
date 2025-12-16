# Universal Website Scraper (MVP) + JSON Viewer

A full-stack web scraping service with static and JavaScript rendering capabilities, built with FastAPI and Playwright.

## Features

- Static HTML scraping with httpx and BeautifulSoup
- JavaScript rendering fallback using Playwright
- Smart section detection and content extraction
- Interactive element handling (tabs, load more buttons, pagination)
- Infinite scroll support
- Noise filtering (cookie banners, popups)
- JSON viewer UI with download capability

## Requirements

- Python 3.10+
- Unix-like environment (Linux, macOS, WSL)

## Installation & Running

```bash
chmod +x run.sh
./run.sh
```

The script will:

1. Create a virtual environment
2. Install all Python dependencies
3. Install Playwright Chromium browser
4. Start the server

**Access the application at: http://localhost:8000**

## Manual Setup

If you prefer manual setup:

**On Linux/Mac:**

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host localhost --port 8000
```

**On Windows:**

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn main:app --host localhost --port 8000
```

**Then open your browser to: http://localhost:8000**

## Usage

### Web Interface

Navigate to http://localhost:8000 and enter a URL to scrape.

### API Endpoints

**Health Check**

```
GET /healthz
```

**Scrape URL**

```
POST /scrape
Content-Type: application/json

{
  "url": "https://example.com"
}
```

## Test URLs

### Static Page

```
https://example.com
https://www.w3.org/Style/Examples/011/firstcss.en.html
```

### JS-Heavy Page

```
https://react.dev
https://vuejs.org
```

### Pagination / Infinite Scroll

```
https://news.ycombinator.com
https://github.com/trending
```

## Known Limitations

- Playwright browser installation required (500+ MB)
- JavaScript rendering adds 3-10 seconds latency
- Some anti-bot protections may block requests
- Complex SPAs may require custom wait strategies
- Infinite scroll detection is heuristic-based
- Heavy pages may have truncated HTML sections
- CAPTCHA-protected sites not supported
- Rate limiting not implemented for production use

## Project Structure

```
.
├── main.py                 # FastAPI application entry
├── scraper.py              # Core scraping logic
├── parsers.py              # HTML parsing and extraction
├── interactions.py         # Click and scroll handlers
├── templates/
│   └── index.html         # Frontend UI
├── run.sh                 # Setup and run script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── design_notes.md       # Technical design decisions
└── capabilities.json     # Feature flags
```

