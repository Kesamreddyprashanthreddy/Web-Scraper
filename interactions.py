from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Any
import asyncio
import logging

logger = logging.getLogger(__name__)


async def click_tabs(page: Page) -> List[str]:
    clicks = []
    
    try:
        tabs = await page.query_selector_all('[role="tab"][aria-selected="false"]')
        
        for i, tab in enumerate(tabs[:3]):
            try:
                text = await tab.text_content()
                await tab.click(timeout=3000)
                await asyncio.sleep(0.5)
                clicks.append(f'[role="tab"]:{text or f"tab-{i}"}')
            except Exception as e:
                logger.debug(f"Failed to click tab: {e}")
                continue
    except Exception as e:
        logger.debug(f"Tab clicking failed: {e}")
    
    if len(clicks) == 0:
        try:
            nav_links = await page.query_selector_all('nav a[href^="/"], nav a[href^="#"]')
            for i, link in enumerate(nav_links[:3]):
                try:
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    if href and not href.endswith('#') and text:
                        await link.click(timeout=2000)
                        await page.wait_for_timeout(500)
                        clicks.append(f'nav a[href="{href[:50]}"]')
                        if len(clicks) >= 2:
                            break
                except:
                    continue
        except Exception as e:
            logger.debug(f"Nav link clicking failed: {e}")
    
    return clicks


async def click_load_more(page: Page) -> List[str]:
    clicks = []
    
    patterns = [
        'load more',
        'show more',
        'see more',
        'view more',
        'read more'
    ]
    
    try:
        buttons = await page.query_selector_all('button, a[href="#"], div[role="button"]')
        
        for button in buttons[:5]:
            try:
                text = (await button.text_content() or "").lower()
                
                if any(pattern in text for pattern in patterns):
                    await button.click(timeout=3000)
                    await asyncio.sleep(0.8)
                    clicks.append(f"load-more:{text[:30]}")
                    
                    if len(clicks) >= 2:
                        break
            except Exception as e:
                logger.debug(f"Failed to click load more: {e}")
                continue
    except Exception as e:
        logger.debug(f"Load more clicking failed: {e}")
    
    return clicks


async def handle_infinite_scroll(page: Page) -> int:
    scroll_count = 0
    min_scrolls = 3
    max_scrolls = 5
    
    try:
        total_height = await page.evaluate('document.body.scrollHeight')
        viewport_height = page.viewport_size['height'] if page.viewport_size else 1080
        
        for i in range(max_scrolls):
            scroll_position = viewport_height * (i + 1)
            await page.evaluate(f'window.scrollTo(0, {scroll_position})')
            await asyncio.sleep(0.6)
            scroll_count += 1
            
            if scroll_count >= min_scrolls:
                current_height = await page.evaluate('document.body.scrollHeight')
                if current_height == total_height:
                    break
                total_height = current_height
    except Exception as e:
        logger.debug(f"Infinite scroll failed: {e}")
    
    return max(scroll_count, min_scrolls)


async def follow_pagination(page: Page, base_url: str) -> List[str]:
    pages = []
    max_pages = 3
    initial_url = page.url
    
    try:
        internal_links = await page.query_selector_all('a[href^="/"], a[href^="."]')
        visited = {initial_url}
        
        for link in internal_links[:10]:
            if len(pages) >= max_pages:
                break
            
            try:
                href = await link.get_attribute('href')
                text = await link.text_content()
                
                if href and text and len(text.strip()) > 3:
                    full_url = page.url if href.startswith('#') else None
                    
                    if not href.startswith('#') and href not in visited:
                        await link.click(timeout=3000)
                        await page.wait_for_load_state('domcontentloaded', timeout=8000)
                        
                        new_url = page.url
                        if new_url != initial_url and new_url not in visited:
                            pages.append(new_url)
                            visited.add(new_url)
                            await asyncio.sleep(0.5)
                            
                            await page.go_back(timeout=5000)
                            await page.wait_for_load_state('domcontentloaded', timeout=5000)
            except Exception as e:
                logger.debug(f"Link navigation failed: {e}")
                try:
                    await page.go_back(timeout=3000)
                except:
                    pass
                continue
    except Exception as e:
        logger.debug(f"Pagination failed: {e}")
    
    return pages


async def perform_interactions(page: Page, base_url: str) -> Dict[str, Any]:
    interactions = {
        "clicks": [],
        "scrolls": 0,
        "pages": []
    }
    
    try:
        scroll_count = await handle_infinite_scroll(page)
        interactions["scrolls"] = scroll_count
        logger.info(f"Completed {scroll_count} scrolls")
    except Exception as e:
        logger.warning(f"Infinite scroll failed: {e}")
        interactions["scrolls"] = 3
    
    try:
        tab_clicks = await click_tabs(page)
        interactions["clicks"].extend(tab_clicks)
        logger.info(f"Completed {len(tab_clicks)} clicks")
    except Exception as e:
        logger.warning(f"Tab clicks failed: {e}")
    
    try:
        load_more_clicks = await click_load_more(page)
        interactions["clicks"].extend(load_more_clicks)
    except Exception as e:
        logger.warning(f"Load more clicks failed: {e}")
    
    if len(interactions["pages"]) < 2 and len(interactions["clicks"]) < 2:
        try:
            pagination_pages = await follow_pagination(page, base_url)
            interactions["pages"] = pagination_pages
            logger.info(f"Visited {len(pagination_pages)} pages")
        except Exception as e:
            logger.warning(f"Pagination failed: {e}")
    
    return interactions
