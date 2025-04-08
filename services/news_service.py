from crewai import Agent, Task, Crew, Process, LLM
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from ..models.schemas import NewsArticleSummary, NewsArticleCollection
from datetime import datetime, timedelta
from ..tools.news_fetcher import IndianFinanceNewsTools, fetch_indian_financial_news
import asyncio
from fastapi import BackgroundTasks
import json

# Load environment variables
load_dotenv()

# Initialize LLM
llm = LLM(
    model='gemini/gemini-2.0-flash',
    api_key=os.getenv("GEMINI_API_KEY", "AIzaSyAjt3CbwaMW_B7a-c-J6-PMKW-Pd5AC03Q")
)

# Cache for recent articles
recent_articles = []
last_update = None
CACHE_DURATION = timedelta(minutes=10)

# Create agents
news_fetcher = Agent(
    role='Financial News Fetcher',
    goal='Fetch relevant and high-quality Indian financial market news articles',
    backstory="""You are a professional financial news researcher specializing in 
                Indian markets. You understand market dynamics, financial terminology,
                and can identify important news that could impact investments and
                trading decisions. You focus on credible sources and filter out noise.
                Use the fetch_indian_news tool to get the latest news articles.""",
    tools=[fetch_indian_financial_news],
    verbose=True,
    llm=llm
)

news_summarizer = Agent(
    role='News Summarizer',
    goal='Create concise and accurate summaries of news articles',
    backstory="""You are an experienced journalist and editor who can quickly grasp 
                the key points of news articles and create accurate, concise summaries.
                You know how to identify the most important information and present it clearly.
                You will receive news articles from the news fetcher and create summaries.""",
    verbose=True,
    llm=llm
)

# Create tasks
fetch_news_task = Task(
    description="""
    Fetch the latest Indian financial market news using multiple sources.
    Use the fetch_indian_news tool to get the articles.
    Return the complete list of articles with their metadata.
    """,
    expected_output="A list of relevant Indian financial market news articles with their metadata",
    agent=news_fetcher
)

summarize_news_task = Task(
    description="""
    Create concise summaries of the provided news articles.
    For each article, create a 2-3 sentence summary that captures the key points.
    Format the output as a JSON with datetime, summary, and source URL.
    """,
    expected_output="A collection of article summaries in JSON format",
    agent=news_summarizer,
    context=[fetch_news_task]
)

# Create crew
news_crew = Crew(
    agents=[news_fetcher, news_summarizer],
    tasks=[fetch_news_task, summarize_news_task],
    verbose=1,
    process=Process.sequential
)

async def fetch_and_process_news() -> NewsArticleCollection:
    """Fetch and process news articles"""
    try:
        # Create a new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Initialize the news tools
        news_tools = IndianFinanceNewsTools()
        
        # Fetch news using the tool directly
        articles_data = await news_tools.combine_news_sources()
        
        # Process the articles
        summaries = NewsArticleCollection(
            articles=[
                NewsArticleSummary(
                    published_at=datetime.fromisoformat(str(article.get('publishedAt', '')).replace('Z', '+00:00')),
                    summary=str(article.get('summary', 'No summary available')),
                    source_url=str(article.get('url', ''))
                )
                for article in articles_data
                if isinstance(article, dict)
            ]
        )
        return summaries
    except Exception as e:
        print(f"Error processing results: {str(e)}")
        return NewsArticleCollection(articles=[])
    finally:
        loop.close()

async def update_news_cache():
    """Update the news cache"""
    global recent_articles, last_update
    try:
        summaries = await fetch_and_process_news()
        recent_articles = summaries.articles
        last_update = datetime.now()
        print(f"News cache updated at {last_update}")
    except Exception as e:
        print(f"Error updating news cache: {str(e)}")

def get_news_summaries(query: str = '', language: str = 'en') -> NewsArticleCollection:
    """Get summaries of latest news articles from cache"""
    global recent_articles, last_update
    
    # Check if cache needs updating
    if last_update is None or datetime.now() - last_update > CACHE_DURATION:
        # Schedule background update
        asyncio.create_task(update_news_cache())
    
    # Return cached articles
    return NewsArticleCollection(articles=recent_articles)

async def fetch_financial_news() -> str:
    """
    Fetch financial news and format it as a JSON string.
    """
    try:
        # Fetch news using the news fetcher tool
        news_data = await fetch_indian_financial_news()
        
        # Format the news data into a JSON string
        formatted_news = json.dumps({
            "articles": [
                {
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", datetime.now().isoformat()),
                    "source": article.get("source", "")
                }
                for article in news_data.get("articles", [])[:20]  # Limit to 20 articles
            ]
        })
        
        return formatted_news
    except Exception as e:
        print(f"Error fetching financial news: {str(e)}")
        return json.dumps({"articles": []}) 