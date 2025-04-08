import aiohttp
import asyncio
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
from crewai.tools import tool

class IndianFinanceNewsTools:
    def __init__(self):
        self.ua = UserAgent()
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.sources = {
            'moneycontrol': {
                'url': 'https://www.moneycontrol.com/news/business/markets/',
                'pages': 2,  # Number of pages to scrape
                'article_selector': 'li.clearfix',
                'title_selector': 'h2 a',
                'summary_selector': 'p',
                'base_url': 'https://www.moneycontrol.com'
            }
        }

    async def fetch_page(self, session, url):
        """Async function to fetch a single page"""
        try:
            await asyncio.sleep(1)  # Rate limiting
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            return None

    def parse_article(self, article, source_config, source_name):
        """Parse a single article"""
        try:
            title_elem = article.select_one(source_config['title_selector'])
            if not title_elem:
                return None

            url = title_elem.get('href', '')
            if url:
                if not url.startswith('http'):
                    url = source_config['base_url'] + url
                if not url.startswith('http'):
                    url = 'https://' + url.lstrip('/')

            title = title_elem.text.strip()

            summary_elem = article.select_one(source_config['summary_selector'])
            summary = summary_elem.text.strip() if summary_elem else ''
            
            return {
                'title': title,
                'url': url,
                'publishedAt': datetime.now().isoformat(),
                'summary': summary,
                'source': source_name
            }
        except Exception as e:
            print(f"Error parsing article: {str(e)}")
            return None

    async def fetch_source_articles(self, source_name, config):
        """Fetch articles from a single source"""
        articles = []
        try:
            async with aiohttp.ClientSession() as session:
                for page in range(1, config['pages'] + 1):
                    page_url = f"{config['url']}/page-{page}" if page > 1 else config['url']
                    html = await self.fetch_page(session, page_url)
                    if html:
                        soup = BeautifulSoup(html, 'html.parser')
                        for article in soup.select(config['article_selector']):
                            article_data = self.parse_article(article, config, source_name)
                            if article_data:
                                articles.append(article_data)
        except Exception as e:
            print(f"Error fetching {source_name}: {str(e)}")
        return articles

    async def combine_news_sources(self) -> List[Dict]:
        """Combine news from multiple Indian financial sources"""
        all_articles = []
        
        # Run async fetching for all sources
        tasks = []
        for source_name, config in self.sources.items():
            tasks.append(self.fetch_source_articles(source_name, config))
        results = await asyncio.gather(*tasks)
        for articles in results:
            all_articles.extend(articles)
        
        # Sort by timestamp and remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        for article in sorted(all_articles, key=lambda x: x['publishedAt'], reverse=True):
            if article['title'] not in seen_titles:
                seen_titles.add(article['title'])
                unique_articles.append(article)
        
        return unique_articles[:20]  # Return top 20 most recent unique articles

@tool("fetch_indian_news")
async def fetch_indian_financial_news() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch Indian financial news from various sources.
    """
    try:
        # List of news sources to fetch from
        sources = [
            {
                "name": "Economic Times",
                "url": "https://economictimes.indiatimes.com/markets",
                "selector": ".eachStory"
            },
            {
                "name": "Money Control",
                "url": "https://www.moneycontrol.com/news/business/markets/",
                "selector": ".newslist"
            }
        ]

        articles = []
        ua = UserAgent()

        async with aiohttp.ClientSession() as session:
            for source in sources:
                try:
                    headers = {"User-Agent": ua.random}
                    async with session.get(source["url"], headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Extract articles based on the source's selector
                            news_items = soup.select(source["selector"])
                            
                            for item in news_items[:10]:  # Limit to 10 articles per source
                                try:
                                    title = item.select_one("h2, h3, .title").text.strip()
                                    link = item.select_one("a")["href"]
                                    if not link.startswith("http"):
                                        link = f"https://{source['url'].split('/')[2]}{link}"
                                    
                                    articles.append({
                                        "title": title,
                                        "url": link,
                                        "source": source["name"],
                                        "publishedAt": datetime.now().isoformat(),
                                        "summary": title  # Using title as summary for now
                                    })
                                except Exception as e:
                                    print(f"Error parsing article: {str(e)}")
                                    continue
                except Exception as e:
                    print(f"Error fetching from {source['name']}: {str(e)}")
                    continue

        return {"articles": articles}
    except Exception as e:
        print(f"Error in fetch_indian_financial_news: {str(e)}")
        return {"articles": []} 