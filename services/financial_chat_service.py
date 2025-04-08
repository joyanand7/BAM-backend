from crewai import Agent, Task, Crew, Process, LLM
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from ..models.schemas import ChatResponse
from datetime import datetime
import json
import asyncio
from ..tools.search_query import CustomSearchTool
from crewai.tools import tool

# Load environment variables
load_dotenv()

# Initialize LLM
llm = LLM(
    model='gemini/gemini-2.0-flash',
    api_key=os.getenv("GEMINI_API_KEY")
)

# Define the financial research tool
@tool("financial_research")
def financial_research_tool(query: str) -> str:
    """
    Perform financial research using the custom search tool.
    Returns a JSON string with research findings specific to Indian financial markets.
    """
    try:
        # Initialize the search tool
        search_tool = CustomSearchTool()
        
        # Perform the search using the tool's _run method
        results = search_tool._run(
            query=query,
            limit=5,  # Get top 5 results
            lang="en",
            timeout=60000
        )
        
        # Process and format the results
        formatted_results = {
            "research": {
                "sources": [],
                "key_findings": [],
                "data_points": []
            }
        }
        
        if isinstance(results, list):
            for result in results:
                if isinstance(result, dict):
                    formatted_results["research"]["sources"].append(result.get("url", ""))
                    formatted_results["research"]["key_findings"].append(result.get("content", ""))
                    formatted_results["research"]["data_points"].append({
                        "url": result.get("url", ""),
                        "content": result.get("content", "")
                    })
        
        # Convert to JSON string
        return json.dumps(formatted_results)
    except Exception as e:
        return json.dumps({
            "research": {
                "sources": [],
                "key_findings": [],
                "data_points": []
            }
        })

# Create agents
researcher = Agent(
    role='Indian Financial Market Researcher',
    goal='Gather and analyze financial information specific to Indian markets',
    backstory="""You are an expert financial researcher specializing in Indian markets 
                with deep knowledge of SEBI regulations, Indian market dynamics, and 
                local financial terminology. You use various tools to collect and 
                verify financial information relevant to Indian investors.""",
    tools=[financial_research_tool],
    verbose=True,
    llm=llm
)

advisor = Agent(
    role='Indian Financial Advisor',
    goal='Provide accurate and helpful financial advice based on Indian market research',
    backstory="""You are a certified financial advisor with expertise in Indian 
                personal finance and investments. You understand SEBI regulations, 
                Indian tax laws, and local market conditions. You analyze research 
                data to provide clear, actionable advice suitable for Indian investors.""",
    verbose=True,
    llm=llm
)

# Create tasks
research_task = Task(
    description="""
        Research the financial query using available tools, focusing on Indian markets.
        
        Query: {query}
        
        Requirements:
        1. Use the financial research tool to find relevant Indian market information
        2. Gather data from Indian financial sources
        3. Verify the accuracy of information against Indian market data
        4. Organize findings by topic, considering Indian market context
        
        Return a JSON object with the following structure:
        {{
            "research": {{
                "sources": ["Source 1", "Source 2"],
                "key_findings": ["Finding 1", "Finding 2"],
                "data_points": ["Data 1", "Data 2"]
            }}
        }}
    """,
    expected_output="Research findings with sources and data points specific to Indian markets",
    agent=researcher
)

advice_task = Task(
    description="""
        Provide financial advice based on the research findings, focusing on Indian markets.
        
        Query: {query}
        
        Requirements:
        1. Analyze the research findings in Indian market context
        2. Provide clear, actionable advice suitable for Indian investors
        3. Support recommendations with Indian market data
        4. Consider Indian tax implications and regulations
        5. Format the response professionally
        
        Return a JSON object with the following structure:
        {{
            "advice": {{
                "analysis": "Detailed analysis of the situation in Indian context",
                "recommendations": ["Recommendation 1", "Recommendation 2"],
                "supporting_data": ["Data point 1", "Data point 2"],
                "sources": ["Source 1", "Source 2"]
            }}
        }}
    """,
    expected_output="Comprehensive financial advice with supporting data specific to Indian markets",
    agent=advisor,
    context=[research_task]
)

# Create crew
chat_crew = Crew(
    agents=[researcher, advisor],
    tasks=[research_task, advice_task],
    verbose=1,
    process=Process.sequential
)

async def get_financial_advice(query: str) -> ChatResponse:
    """Get personalized financial advice using AI agents and research"""
    try:
        # Create a new event loop for this call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the crew with the input query
        result = chat_crew.kickoff(
            inputs={
                'query': query
            }
        )
        
        # Extract the content from CrewOutput
        if hasattr(result, 'content'):
            result_content = result.content
        else:
            result_content = str(result)
        
        # Parse the JSON content
        try:
            # Remove the markdown code block if present
            if result_content.startswith('```json'):
                result_content = result_content[7:-3]  # Remove ```json and trailing ```
            
            response_data = json.loads(result_content)
            advice_data = response_data.get('advice', {})
            
            # Extract sources from the advice data
            sources = advice_data.get('sources', [])
            
            return ChatResponse(
                answer=advice_data.get('analysis', '') + '\n\n' + 
                      '\n'.join(f"- {rec}" for rec in advice_data.get('recommendations', [])),
                sources=sources,
                timestamp=datetime.now()
            )
        except json.JSONDecodeError:
            return ChatResponse(
                answer=result_content,
                sources=[],
                timestamp=datetime.now()
            )
    except Exception as e:
        print(f"Error processing financial advice: {str(e)}")
        return ChatResponse(
            answer=f"Error: {str(e)}",
            sources=[],
            timestamp=datetime.now()
        )
    finally:
        loop.close() 