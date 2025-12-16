from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from typing import Optional
import logging

from scraper import scrape_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Universal Website Scraper")

templates = Jinja2Templates(directory="templates")


class ScrapeRequest(BaseModel):
    url: HttpUrl


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/favicon.ico")
async def favicon():
    return {"status": "no favicon"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/scrape")
async def scrape(payload: ScrapeRequest):
    url = str(payload.url)
    
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=400,
            detail="Invalid URL. Only http and https protocols are supported."
        )
    
    try:
        result = await scrape_url(url)
        return {"result": result}
    except Exception as e:
        logger.error(f"Scraping failed for {url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )
