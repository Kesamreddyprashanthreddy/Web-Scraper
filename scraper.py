import httpx
from datetime import datetime
from typing import Dict, Any, List
import logging

from parsers import extract_meta, parse_sections, should_use_js_fallback
from interactions import perform_interactions

logger = logging.getLogger(__name__)


async def scrape_static(url: str) -> tuple[str, Dict[str, Any], List[str]]:
    errors = []
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            html = response.text
            
            meta = extract_meta(html)
            
            return html, meta, errors
    except httpx.TimeoutException:
        errors.append({"message": "Request timeout", "phase": "fetch"})
        raise
    except httpx.HTTPStatusError as e:
        errors.append({"message": f"HTTP {e.response.status_code}", "phase": "fetch"})
        raise
    except Exception as e:
        errors.append({"message": str(e), "phase": "fetch"})
        raise


async def scrape_with_js(url: str) -> tuple[str, Dict[str, Any], Dict[str, Any], List[str]]:
    errors = []
    interactions = {"clicks": [], "scrolls": 0, "pages": []}
    
    browser = None
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(1000)
                
                interactions = await perform_interactions(page, url)
                
                html = await page.content()
                
                meta = extract_meta(html)
                
                await browser.close()
                
                return html, meta, interactions, errors
            except Exception as e:
                logger.error(f"Page interaction error: {e}")
                errors.append({"message": str(e), "phase": "render"})
                if browser:
                    await browser.close()
                raise
    except Exception as e:
        logger.error(f"Playwright error: {e}")
        if "render" not in [err["phase"] for err in errors]:
            errors.append({"message": str(e), "phase": "render"})
        if browser:
            try:
                await browser.close()
            except:
                pass
        raise


async def scrape_url(url: str) -> Dict[str, Any]:
    errors = []
    scraped_at = datetime.utcnow().isoformat() + "Z"
    interactions = {"clicks": [], "scrolls": 0, "pages": []}
    
    meta = {
        "title": "",
        "description": "",
        "language": "en",
        "canonical": None
    }
    sections = []
    
    try:
        html, meta, fetch_errors = await scrape_static(url)
        errors.extend(fetch_errors)
        
        sections = parse_sections(html, url)
        
        logger.info(f"Attempting JS rendering for interactions: {url}")
        try:
            html_js, meta_js, interactions_js, js_errors = await scrape_with_js(url)
            errors.extend(js_errors)
            
            sections_js = parse_sections(html_js, url)
            if len(sections_js) > len(sections):
                sections = sections_js
            
            if meta_js.get('title'):
                meta = meta_js
            interactions = interactions_js
        except Exception as e:
            logger.warning(f"JS rendering failed, using static result: {e}")
            errors.append({"message": "JS rendering failed, no interactions performed", "phase": "render"})
        
    except Exception as e:
        logger.error(f"Scraping failure for {url}: {e}")
        errors.append({"message": str(e), "phase": "fetch"})
    
    return {
        "url": url,
        "scrapedAt": scraped_at,
        "meta": meta,
        "sections": sections,
        "interactions": interactions,
        "errors": errors
    }
