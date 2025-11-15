import aiohttp
import os
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
load_dotenv()

class SearchTool:
    def __init__(self):
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.tavily_url = "https://api.tavily.com/search"
    
    async def search_emerging_domains(self, query: str) -> List[Dict[str, Any]]:
        """Search for emerging scientific domains using Tavily API"""
        results = []
        
        # Search queries targeting different sources
        search_queries = [
            f"{query} breakthrough 2024 2025",
            f"{query} emerging research trends",
            f"latest {query} innovations",
        ]
        
        for search_query in search_queries:
            try:
                # Use Tavily if API key is available
                if self.tavily_api_key:
                    tavily_results = await self._search_tavily(search_query)
                    results.extend(tavily_results)
                else:
                    # Fallback to DuckDuckGo
                    ddg_results = await self._search_duckduckgo(search_query)
                    results.extend(ddg_results)
            except Exception as e:
                print(f"Search error for '{search_query}': {e}")
                continue
        
        # Search specific sources
        github_results = await self.search_github_trending(query)
        results.extend(github_results)
        
        arxiv_results = await self.search_arxiv(query, max_results=3)
        results.extend(arxiv_results)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_results = []
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results[:15]
    
    async def _search_tavily(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Tavily API"""
        results = []
        
        try:
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "advanced",  # or "basic" for faster results
                "max_results": max_results,
                "include_domains": [
                    "arxiv.org",
                    "github.com",
                    "nature.com",
                    "science.org",
                    "mit.edu",
                    "stanford.edu"
                ],
                "include_answer": True,
                "include_raw_content": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.tavily_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract results
                        for result in data.get('results', []):
                            results.append({
                                "title": result.get('title', ''),
                                "url": result.get('url', ''),
                                "snippet": result.get('content', '')[:500],
                                "score": result.get('score', 0),
                                "source": "tavily",
                                "published_date": result.get('published_date', '')
                            })
                        
                        # Also add the AI-generated answer if available
                        if data.get('answer'):
                            results.insert(0, {
                                "title": f"AI Summary: {query}",
                                "url": "",
                                "snippet": data.get('answer'),
                                "source": "tavily_answer",
                                "score": 1.0
                            })
                    else:
                        error_text = await response.text()
                        print(f"Tavily API error {response.status}: {error_text}")
        except Exception as e:
            print(f"Tavily search error: {e}")
        
        return results
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Fallback search using DuckDuckGo"""
        results = []
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://html.duckduckgo.com/html/?q={query}"
                async with session.get(
                    url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        for result in soup.find_all('div', class_='result')[:5]:
                            title_elem = result.find('a', class_='result__a')
                            snippet_elem = result.find('a', class_='result__snippet')
                            
                            if title_elem:
                                results.append({
                                    "title": title_elem.get_text(strip=True),
                                    "url": title_elem.get('href', ''),
                                    "snippet": snippet_elem.get_text(strip=True) if snippet_elem else '',
                                    "source": "duckduckgo",
                                    "score": 0.5
                                })
        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        
        return results
    
    async def search_github_trending(self, query: str) -> List[Dict[str, Any]]:
        """Search for trending GitHub repositories"""
        results = []
        
        try:
            # GitHub trending page
            topics = query.lower().replace(' ', '-')
            url = f"https://github.com/trending/{topics}?since=monthly"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find trending repos
                        repos = soup.find_all('article', class_='Box-row')[:5]
                        
                        for repo in repos:
                            h2 = repo.find('h2')
                            if h2:
                                link = h2.find('a')
                                if link:
                                    title = link.get_text(strip=True).replace('\n', ' ').replace('  ', ' ')
                                    url = f"https://github.com{link.get('href', '')}"
                                    
                                    # Get description
                                    desc_elem = repo.find('p', class_='col-9')
                                    description = desc_elem.get_text(strip=True) if desc_elem else ''
                                    
                                    # Get stars
                                    stars_elem = repo.find('span', class_='d-inline-block float-sm-right')
                                    stars = stars_elem.get_text(strip=True) if stars_elem else ''
                                    
                                    results.append({
                                        "title": f"GitHub Trending: {title}",
                                        "url": url,
                                        "snippet": f"{description} | Stars: {stars}",
                                        "source": "github_trending",
                                        "score": 0.9
                                    })
        except Exception as e:
            print(f"GitHub trending search error: {e}")
            
            # Fallback: Search GitHub API
            try:
                results.extend(await self._search_github_api(query))
            except Exception as api_error:
                print(f"GitHub API fallback error: {api_error}")
        
        return results
    
    async def _search_github_api(self, query: str) -> List[Dict[str, Any]]:
        """Search GitHub using their API"""
        results = []
        
        try:
            # GitHub search API (no auth needed for basic search)
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"{query} created:>2024-01-01",
                "sort": "stars",
                "order": "desc",
                "per_page": 5
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers={
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/vnd.github.v3+json'
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for repo in data.get('items', [])[:5]:
                            results.append({
                                "title": f"GitHub: {repo.get('full_name', '')}",
                                "url": repo.get('html_url', ''),
                                "snippet": f"{repo.get('description', '')} | ⭐ {repo.get('stargazers_count', 0)} | Language: {repo.get('language', 'N/A')}",
                                "source": "github_api",
                                "score": 0.85,
                                "stars": repo.get('stargazers_count', 0)
                            })
        except Exception as e:
            print(f"GitHub API search error: {e}")
        
        return results
    
    async def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search ArXiv for recent papers"""
        results = []
        
        try:
            # URL encode the query
            import urllib.parse
            encoded_query = urllib.parse.quote(query)
            url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        text = await response.text()
                        soup = BeautifulSoup(text, 'xml')
                        
                        for entry in soup.find_all('entry'):
                            title = entry.find('title').get_text(strip=True) if entry.find('title') else ''
                            summary = entry.find('summary').get_text(strip=True) if entry.find('summary') else ''
                            link = entry.find('id').get_text(strip=True) if entry.find('id') else ''
                            published = entry.find('published').get_text(strip=True) if entry.find('published') else ''
                            
                            # Get categories
                            categories = []
                            for cat in entry.find_all('category'):
                                term = cat.get('term', '')
                                if term:
                                    categories.append(term)
                            
                            results.append({
                                "title": f"ArXiv: {title[:100]}",
                                "summary": summary[:500],
                                "url": link,
                                "published": published,
                                "categories": categories,
                                "source": "arxiv",
                                "score": 0.8
                            })
        except Exception as e:
            print(f"ArXiv search error: {e}")
        
        return results
    
    async def search_patents(self, query: str) -> List[Dict[str, Any]]:
        """Search for recent patents (using Google Patents)"""
        results = []
        
        try:
            # Search Google Patents through web scraping
            import urllib.parse
            encoded_query = urllib.parse.quote(f"{query} after:20240101")
            url = f"https://patents.google.com/?q={encoded_query}&oq={encoded_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find patent results
                        patent_items = soup.find_all('article', class_='search-result-item')[:5]
                        
                        for item in patent_items:
                            title_elem = item.find('h4')
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                link_elem = title_elem.find('a')
                                url = f"https://patents.google.com{link_elem.get('href', '')}" if link_elem else ""
                                
                                abstract_elem = item.find('div', class_='abstract')
                                abstract = abstract_elem.get_text(strip=True) if abstract_elem else ''
                                
                                results.append({
                                    "title": f"Patent: {title}",
                                    "url": url,
                                    "snippet": abstract[:500],
                                    "source": "google_patents",
                                    "score": 0.75
                                })
        except Exception as e:
            print(f"Patent search error: {e}")
        
        return results
    
    async def search_twitter_scientific(self, query: str) -> List[Dict[str, Any]]:
        """Search for scientific discussions on X/Twitter"""
        results = []
        
        try:
            # Use Tavily to search Twitter if available
            if self.tavily_api_key:
                payload = {
                    "api_key": self.tavily_api_key,
                    "query": f"{query} site:twitter.com OR site:x.com scientific research",
                    "search_depth": "basic",
                    "max_results": 5
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.tavily_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for result in data.get('results', []):
                                if 'twitter.com' in result.get('url', '') or 'x.com' in result.get('url', ''):
                                    results.append({
                                        "title": f"X/Twitter: {result.get('title', '')}",
                                        "url": result.get('url', ''),
                                        "snippet": result.get('content', '')[:300],
                                        "source": "twitter",
                                        "score": 0.7
                                    })
        except Exception as e:
            print(f"Twitter search error: {e}")
        
        return results

# Global search tool instance
search_tool = SearchTool()