import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re

class ScraperTool:
    # backend/tools/scraper.py (ScraperTool.scrape_url)
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL. Always returns a dict with 'success' bool."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                async with session.get(url, headers=headers, timeout=30) as response:
                    status = response.status
                    ctype = response.headers.get('Content-Type', '').lower()

                    if status != 200:
                        return {"url": url, "success": False, "status": status, "error": f"HTTP {status}"}

                    # If response looks like PDF or other binary, return a safe message
                    if 'pdf' in ctype or 'application/octet-stream' in ctype or url.lower().endswith('.pdf'):
                        # read bytes, but do not attempt to decode as text
                        content_bytes = await response.read()
                        return {
                            "url": url,
                            "title": "",
                            "content": None,
                            "content_bytes_sample_len": len(content_bytes),
                            "success": False,
                            "error": "binary/pdf content (not parsed)."
                        }

                    # Otherwise treat as HTML/text
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    for script in soup(["script", "style"]):
                        script.decompose()

                    text = soup.get_text(separator=' ')
                    # Clean up whitespace
                    text = ' '.join(t.strip() for t in text.split())
                    title = soup.title.get_text(strip=True) if soup.title else ''

                    return {
                        "url": url,
                        "title": title,
                        "content": text[:10000],
                        "success": True
                    }
        except Exception as e:
            # Always return a dict on error
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }

    
    async def extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured data from text"""
        # Extract numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        
        # Extract potential data points
        data = {
            "numbers": [float(n) for n in numbers[:100]],  # Limit to 100 numbers
            "sentences": text.split('.')[:50],  # First 50 sentences
            "word_count": len(text.split()),
        }
        
        return data

# Global scraper instance
scraper_tool = ScraperTool()