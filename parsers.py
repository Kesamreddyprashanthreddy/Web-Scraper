from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Any, Optional
import re


def remove_noise_elements(soup: BeautifulSoup) -> None:
    noise_selectors = [
        '[id*="cookie"]',
        '[class*="cookie"]',
        '[id*="consent"]',
        '[class*="consent"]',
        '[role="dialog"]',
        '[aria-modal="true"]',
        '.modal',
        '.popup',
        '[class*="ad-"]',
        '[id*="advertisement"]',
    ]
    
    for selector in noise_selectors:
        for element in soup.select(selector):
            element.decompose()
    
    for iframe in soup.find_all('iframe'):
        if iframe.get('src') and 'ads' in iframe['src']:
            iframe.decompose()


def extract_meta(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'lxml')
    
    meta = {
        "title": "",
        "description": "",
        "language": "en",
        "canonical": None
    }
    
    try:
        title_tag = soup.find('title')
        if title_tag and hasattr(title_tag, 'get_text'):
            meta["title"] = title_tag.get_text(strip=True)
    except:
        pass
    
    if not meta["title"]:
        try:
            og_title = soup.find('meta', property='og:title')
            if og_title and hasattr(og_title, 'get') and og_title.get('content'):
                meta["title"] = og_title['content']
        except:
            pass
    
    try:
        desc_tag = soup.find('meta', attrs={'name': 'description'})
        if desc_tag and hasattr(desc_tag, 'get') and desc_tag.get('content'):
            meta["description"] = desc_tag['content']
    except:
        pass
    
    if not meta["description"]:
        try:
            og_desc = soup.find('meta', property='og:description')
            if og_desc and hasattr(og_desc, 'get') and og_desc.get('content'):
                meta["description"] = og_desc['content']
        except:
            pass
    
    if not meta["description"]:
        try:
            main_content = soup.find(['main', 'article']) or soup.find('body')
            if main_content:
                paragraphs = main_content.find_all('p', limit=10)
                for p in paragraphs:
                    if p and hasattr(p, 'get_text'):
                        text = p.get_text(strip=True)
                        words = text.split()
                        if len(text) > 100 and len(words) > 15:
                            meta["description"] = text[:400]
                            break
        except:
            pass
    
    try:
        html_tag = soup.find('html')
        if html_tag and hasattr(html_tag, 'get') and html_tag.get('lang'):
            meta["language"] = html_tag['lang']
    except:
        pass
    
    try:
        canonical_tag = soup.find('link', rel='canonical')
        if canonical_tag and hasattr(canonical_tag, 'get') and canonical_tag.get('href'):
            meta["canonical"] = canonical_tag['href']
    except:
        pass
    
    return meta


def generate_section_label(element, section_type: str) -> str:
    boilerplate_phrases = [
        'skip to content', 'skip to', 'jump to', 'move to sidebar',
        'hide', 'main menu', 'toggle', 'navigation menu', 'search documentation',
        'getting started', 'contents', '[edit]', '(edit)', 'edit source',
        'menu', 'search', 'documentation'
    ]
    
    noise_patterns = [
        r'\[.*?\]',
        r'\(.*?\)',
    ]
    
    heading = element.find(['h1', 'h2', 'h3'])
    if heading:
        label = heading.get_text(strip=True)
        label_lower = label.lower()
        
        for phrase in boilerplate_phrases:
            label_lower = label_lower.replace(phrase, '')
        
        import re
        for pattern in noise_patterns:
            label_lower = re.sub(pattern, '', label_lower)
        
        words = label_lower.split()
        if len(words) > 0 and len(words) <= 8:
            label = ' '.join(words[:5])
            if len(label) > 2:
                return label.strip().capitalize()[:50]
    
    aria_label = element.get('aria-label')
    if aria_label:
        label = str(aria_label).strip()
        if len(label) > 2 and len(label) < 60:
            return label.capitalize()[:50]
    
    text = element.get_text(strip=True)
    clean_words = []
    
    for word in text.split():
        word_clean = word.strip()
        if len(word_clean) < 2:
            continue
        
        word_lower = word_clean.lower()
        if any(phrase in word_lower for phrase in boilerplate_phrases):
            continue
        
        if word_clean[0].isupper() or len(clean_words) == 0:
            clean_words.append(word_clean)
        
        if len(clean_words) >= 6:
            break
    
    if clean_words:
        label = ' '.join(clean_words)[:50]
        return label.strip()
    
    type_labels = {
        "nav": "Navigation Menu",
        "header": "Page Header",
        "footer": "Page Footer",
        "hero": "Hero Section",
        "aside": "Sidebar Content"
    }
    
    return type_labels.get(section_type, "Content Section")


def detect_section_type(element) -> str:
    tag_name = element.name.lower() if element.name else ""
    
    if tag_name == 'nav':
        return "nav"
    if tag_name == 'footer':
        return "footer"
    if tag_name == 'header':
        return "header"
    if tag_name == 'aside':
        return "aside"
    
    text = element.get_text(strip=True).lower()
    class_str = ' '.join(element.get('class', [])).lower()
    id_str = element.get('id', '').lower()
    
    if 'hero' in class_str or 'banner' in class_str:
        first_section = element.find_parent(['body', 'main'])
        if first_section:
            sections = first_section.find_all(['section', 'div'], recursive=False)
            if sections and sections[0] == element:
                return "hero"
    
    lists = element.find_all(['ul', 'ol'])
    if len(lists) > 2:
        return "list"
    
    if '$' in text or 'usd' in text or 'price' in text:
        if element.find_all(['table', 'div'], class_=re.compile(r'(price|pricing|plan)')):
            return "pricing"
    
    qa_patterns = ['?', 'q:', 'a:', 'question', 'answer']
    if sum(1 for p in qa_patterns if p in text) >= 2:
        return "faq"
    
    grid_like = element.find_all(['div', 'article'], recursive=False)
    if len(grid_like) >= 3:
        return "grid"
    
    return "section"


def extract_links(element, base_url: str) -> List[Dict[str, str]]:
    links = []
    for a in element.find_all('a', href=True):
        href = a['href']
        if href.startswith(('javascript:', 'mailto:', 'tel:')):
            continue
        
        absolute_url = urljoin(base_url, href)
        text = a.get_text(strip=True)
        links.append({"text": text, "href": absolute_url})
    
    return links


def extract_images(element, base_url: str) -> List[Dict[str, str]]:
    images = []
    for img in element.find_all('img'):
        src = img.get('src') or img.get('data-src')
        if src:
            absolute_url = urljoin(base_url, src)
            alt = img.get('alt', '')
            images.append({"src": absolute_url, "alt": alt})
    
    return images


def extract_lists(element) -> List[List[str]]:
    lists = []
    for ul_ol in element.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in ul_ol.find_all('li', recursive=False)]
        if items:
            lists.append(items)
    return lists


def extract_tables(element) -> List[List[List[str]]]:
    tables = []
    for table in element.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def extract_headings(element) -> List[str]:
    headings = []
    for tag in element.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        text = tag.get_text(strip=True)
        if text:
            headings.append(text)
    return headings


def parse_sections(html: str, base_url: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, 'lxml')
    
    remove_noise_elements(soup)
    
    sections = []
    section_id_counter = 0
    
    semantic_tags = soup.find_all(['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'])
    
    if not semantic_tags:
        body = soup.find('body')
        if body:
            semantic_tags = body.find_all(['div'], recursive=False)
    
    for element in semantic_tags:
        text = element.get_text(strip=True)
        if len(text) < 50:
            continue
        
        section_type = detect_section_type(element)
        label = generate_section_label(element, section_type)
        
        raw_html = str(element)
        truncated = False
        if len(raw_html) > 5000:
            raw_html = raw_html[:5000] + "..."
            truncated = True
        
        section_data = {
            "id": f"{section_type}-{section_id_counter}",
            "type": section_type,
            "label": label,
            "sourceUrl": base_url,
            "content": {
                "headings": extract_headings(element),
                "text": text[:2000],
                "links": extract_links(element, base_url),
                "images": extract_images(element, base_url),
                "lists": extract_lists(element),
                "tables": extract_tables(element)
            },
            "rawHtml": raw_html,
            "truncated": truncated
        }
        
        sections.append(section_data)
        section_id_counter += 1
    
    return sections


def should_use_js_fallback(html: str, sections: List[Dict[str, Any]]) -> bool:
    if len(sections) < 2:
        return True
    
    total_text = sum(len(s['content']['text']) for s in sections)
    if total_text < 200:
        return True
    
    spa_indicators = ['<div id="root"', '<div id="app"', 'ng-version=', 'data-reactroot']
    for indicator in spa_indicators:
        if indicator in html:
            return True
    
    return False
