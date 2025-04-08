import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin


class CustomSearchToolSchema(BaseModel):
    query: str = Field(description="Search query about Indian financial markets")
    limit: Optional[int] = Field(default=5, description="Number of search results to return")
    lang: Optional[str] = Field(default="en", description="Language code")
    timeout: Optional[int] = Field(default=60000, description="Timeout in milliseconds")


class CustomSearchTool(BaseTool):
    name: str = "Indian Financial Market Search Tool"
    description: str = "Performs a search using DuckDuckGo specifically for Indian financial market information and scrapes result pages"
    args_schema = CustomSearchToolSchema

    def _run(self, query: str, limit: int = 5, lang: str = "en", timeout: int = 60000) -> List[Dict[str, Any]]:
        # Add "India" to the query to focus on Indian markets
        india_query = f"{query} India financial markets"
        search_url = f"https://duckduckgo.com/html/?q={india_query}&kl={lang}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            response = requests.get(search_url, headers=headers, timeout=timeout / 1000)
            if response.status_code != 200:
                raise Exception(f"Error fetching search results. Status code: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract result links
            result_links = []
            for link in soup.find_all("a", class_="result__url"):
                href = link.get("href")
                if href and href.startswith("http"):
                    result_links.append(href)
                if len(result_links) >= limit:
                    break

            # Scrape each result page
            results = []
            for url in result_links:
                try:
                    content = self.scrape_page(url, timeout=timeout)
                    results.append({
                        "url": url,
                        "content": content
                    })
                except Exception as e:
                    results.append({
                        "url": url,
                        "error": str(e)
                    })

            return results
        except Exception as e:
            return []

    def scrape_page(self, url: str, timeout: int) -> str:
        """Scrapes the content of the page at the provided URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=timeout / 1000)
            if response.status_code != 200:
                raise Exception(f"Error fetching page. Status code: {response.status_code}")

            soup = BeautifulSoup(response.text, "html.parser")
            body = soup.find("body")
            if not body:
                return "No body content found"

            return " ".join(body.stripped_strings)
        except Exception as e:
            raise
