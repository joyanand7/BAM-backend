from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from typing import Dict, List, Any
import os
import json
import asyncio
from datetime import datetime
from ..models.schemas import (
    UserProfile, 
    RiskAnalysis, 
    InvestmentRecommendation,
    WealthManagementResponse,
    NewsArticleCollection,
    MarketAnalysis
)
from ..tools.news_fetcher import fetch_indian_financial_news
from dotenv import load_dotenv
import google.generativeai as genai
from app.services.news_service import fetch_financial_news

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

# Initialize LLM
llm = LLM(
    model='gemini/gemini-2.0-flash',
    api_key=os.environ["GEMINI_API_KEY"]
)

# Define the news fetching tool
@tool("Fetch Financial News")
def fetch_financial_news() -> str:
    """Fetches the latest Indian financial market news from cached data"""
    try:
        # Get the market news from the task context
        task_context = analyze_news_task.context
        market_news = json.loads(task_context.get('market_news', '{"articles": []}'))
        
        # Take up to 20 most recent articles
        articles = market_news.get('articles', [])[:20]
        
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
                for article in articles
            ]
        })
        
        return formatted_news
    except Exception as e:
        print(f"Error processing cached news data: {str(e)}")
        return json.dumps({"articles": []})

# Create agents
risk_analyzer = Agent(
    role='Risk Analysis Expert',
    goal='Analyze user risk profile and provide comprehensive risk assessment',
    backstory="""You are an experienced risk analyst with deep understanding of 
                Indian financial markets. You evaluate user profiles to determine 
                appropriate risk levels and investment capacity.""",
    verbose=True,
    llm=llm
)

news_fetcher = Agent(
    role='Financial News Analyst',
    goal='Analyze market news and identify relevant trends for investment decisions',
    backstory="""You are a financial news analyst specializing in Indian markets.
                You understand how market news impacts different investment strategies
                and can identify key trends that should influence investment decisions.""",
    tools=[fetch_financial_news],
    verbose=True,
    llm=llm
)

investment_advisor = Agent(
    role='Investment Advisor',
    goal='Provide personalized investment recommendations based on risk analysis and market conditions',
    backstory="""You are a certified financial advisor with expertise in Indian 
                markets. You create customized investment strategies considering 
                risk profiles, market conditions, and personal goals.""",
    verbose=True,
    llm=llm
)

# Create tasks
risk_analysis_task = Task(
    description="""
        Analyze the investor's risk profile comprehensively.
        
        User Profile:
        {user_data}
        
        Required Analysis:
        1. Calculate a risk score (0-100) considering:
           - Age factor: Younger investors can take more risks
           - Income stability: Higher stable income enables more risk
           - Dependencies: More dependents reduce risk capacity
           - Investment horizon: Longer horizon allows more risk
           - Current portfolio: Assess existing risk exposure
           - Stated preferences: Consider user's risk tolerance
        
        2. Determine risk category:
           - Conservative (0-30)
           - Moderate (31-70)
           - Aggressive (71-100)
        
        3. Identify key risk factors and their impact
        
        4. Provide risk management recommendations
        
        Return a JSON object with the following structure:
        {{
            "risk_analysis": {{
                "risk_score": 65.0,
                "risk_category": "Moderate",
                "key_factors": ["Age", "Income Stability", "Investment Horizon"],
                "recommendations": ["Diversify portfolio", "Consider tax-efficient investments"]
            }}
        }}
    """,
    expected_output="JSON formatted risk analysis with score, category, factors, and recommendations",
    agent=risk_analyzer
)

analyze_news_task = Task(
    description="""
        Analyze the provided market news and identify key trends and insights
        that could impact investment decisions.
        
        News Data:
        {market_news}
        
        Focus on:
        1. Market-moving news
        2. Sector-specific developments
        3. Economic indicators
        4. Policy changes
        5. Market sentiment
        
        Return a JSON object with the following structure:
        {{
            "market_analysis": {{
                "market_trends": ["Bullish market sentiment", "Tech sector growth"],
                "key_insights": ["Interest rates expected to rise", "Strong corporate earnings"],
                "impact_analysis": ["Positive for growth stocks", "Negative for bonds"]
            }}
        }}
    """,
    expected_output="JSON formatted market analysis with trends, insights, and impact analysis",
    agent=news_fetcher
)

recommend_investments_task = Task(
    description="""
        Based on the risk analysis and market news analysis, provide personalized
        investment recommendations. Consider:
        - Risk analysis results
        - Market trends and insights
        - User's financial goals
        - Tax saving requirements
        - Asset allocation strategy
        
        Return a JSON object with the following structure:
        {{
            "recommendations": {{
                "asset_allocation": {{
                    "equity": 60,
                    "debt": 30,
                    "gold": 5,
                    "real_estate": 5
                }},
                "specific_recommendations": [
                    {{
                        "type": "equity",
                        "instrument": "Index Fund",
                        "allocation": 30,
                        "reasoning": "Long-term growth potential"
                    }},
                    {{
                        "type": "debt",
                        "instrument": "Tax-saving Bonds",
                        "allocation": 20,
                        "reasoning": "Tax efficiency and stability"
                    }}
                ]
            }}
        }}
    """,
    expected_output="Detailed investment recommendations with asset allocation and specific suggestions",
    agent=investment_advisor,
    context=[risk_analysis_task, analyze_news_task]
)

# Create crew
wealth_crew = Crew(
    agents=[risk_analyzer, news_fetcher, investment_advisor],
    tasks=[risk_analysis_task, analyze_news_task, recommend_investments_task],
    verbose=1,
    process=Process.sequential
)

def _convert_datetime_to_str(obj: Any) -> Any:
    """Recursively convert datetime objects to ISO format strings"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _convert_datetime_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_datetime_to_str(item) for item in obj]
    return obj

async def get_wealth_management_advice(
    user_profile: UserProfile,
    market_news: NewsArticleCollection
) -> WealthManagementResponse:
    """Get personalized wealth management advice using AI agents"""
    try:
        # Convert market news to dict and ensure all datetime objects are strings
        market_news_dict = _convert_datetime_to_str(market_news.dict())
        user_data_dict = _convert_datetime_to_str(user_profile.dict())

        # Create a new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Run the crew with the input parameters
        result = wealth_crew.kickoff(
            inputs={
                'user_data': json.dumps(user_data_dict),
                'market_news': json.dumps(market_news_dict)
            }
        )

        # Extract the content from CrewOutput
        if hasattr(result, 'content'):
            result_content = result.content
        else:
            result_content = str(result)

        # Parse the JSON content
        try:
            recommendations_data = json.loads(result_content)
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the string
            import re
            json_match = re.search(r'\{.*\}', result_content, re.DOTALL)
            if json_match:
                recommendations_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse JSON from response")

        # Ensure we have the required structure with default values
        risk_analysis_data = recommendations_data.get('risk_analysis', {})
        if not risk_analysis_data:
            risk_analysis_data = {
                "risk_score": 50.0,
                "risk_category": "Moderate",
                "key_factors": ["Default risk factor"],
                "recommendations": ["Default recommendation"]
            }

        market_analysis_data = recommendations_data.get('market_analysis', {})
        if not market_analysis_data:
            market_analysis_data = {
                "market_trends": ["Default trend"],
                "key_insights": ["Default insight"],
                "impact_analysis": ["Default impact"]
            }

        recommendations_data = recommendations_data.get('recommendations', {})
        if not recommendations_data:
            recommendations_data = {
                "asset_allocation": {
                    "equity": 50,
                    "debt": 30,
                    "gold": 10,
                    "real_estate": 10
                },
                "specific_recommendations": [
                    {
                        "type": "equity",
                        "instrument": "Default Fund",
                        "allocation": 50,
                        "reasoning": "Default reasoning"
                    }
                ]
            }

        # Create the response without market news
        return WealthManagementResponse(
            risk_analysis=RiskAnalysis(**risk_analysis_data),
            market_analysis=MarketAnalysis(**market_analysis_data),
            recommendations=InvestmentRecommendation(
                asset_allocation=recommendations_data.get('asset_allocation', {}),
                specific_recommendations=recommendations_data.get('specific_recommendations', []),
                market_news=[]  # Empty list instead of market_news.articles
            )
        )
    except Exception as e:
        print(f"Error processing wealth management advice: {str(e)}")
        raise
    finally:
        loop.close()

def get_wealth_advice(
    age: int,
    income: float,
    dependents: int,
    investment_horizon: int,
    existing_investments: List[Dict[str, Any]],
    risk_tolerance: str,
    goals: List[Dict[str, Any]]
) -> str:
    """
    Get personalized wealth management advice using Gemini AI.
    """
    try:
        # Format the input data
        input_data = {
            "age": age,
            "income": income,
            "dependents": dependents,
            "investment_horizon": investment_horizon,
            "existing_investments": existing_investments,
            "risk_tolerance": risk_tolerance,
            "goals": goals
        }

        # Create the prompt
        prompt = f"""
        As a financial advisor, analyze this client's financial situation and provide personalized advice:
        
        Client Profile:
        - Age: {age}
        - Annual Income: ${income:,.2f}
        - Number of Dependents: {dependents}
        - Investment Horizon: {investment_horizon} years
        - Risk Tolerance: {risk_tolerance}
        
        Current Investments:
        {json.dumps(existing_investments, indent=2)}
        
        Financial Goals:
        {json.dumps(goals, indent=2)}
        
        Please provide:
        1. Risk assessment
        2. Investment recommendations
        3. Asset allocation strategy
        4. Specific action items
        5. Timeline for achieving goals
        
        Format the response as a JSON object with these sections.
        """

        # Generate the response
        response = model.generate_content(prompt)
        
        # Return the response text
        return response.text

    except Exception as e:
        return f"Error generating advice: {str(e)}" 