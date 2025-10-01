import uuid
from fastapi import FastAPI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import asyncio
import os
import uuid
from pydantic import BaseModel
from datetime import datetime, timezone
from pymongo.mongo_client import MongoClient
import ssl


app = FastAPI(title="FastAPI AI MCP Microservice",
    description="API Description:This API provides a unified interface for interacting with multiple MCP "
                "(Model Context Protocol) servers. It offers endpoints to send requests, retrieve responses, "
                "and manage server connections, streamlining integration across diverse MCP services. "
                "The Bright Data Web Scraper MCP is available now, with Playwright MCP support coming soon. "
                "The API is containerized with Docker and deployed on AWS ECS for scalability and reliability. "
                "***** FEEL FREE TO SCAPE ANY WEBSITE YOU LIKE USING BRIGHT-DATA POST*****",
    version="1.0.0")


class BrightDataOut(BaseModel):
    prompt: str
    results: str
    type: str
    guId: str
    time_stamp: str



@app.get("/bright-data/info",tags=["Bright Data AI MCP Server"])
def info():
    return("name: Fast Api AI microservice",
        "description: Scrape websites and generate responses using Databright MCP and Anthropics LLM")


@app.post("/bright-data/generate/",tags=["Bright Data AI MCP Server"])
def generate(web_scaper_prompt = "Navigate to Zillow and scrape all open houses this upcoming weekend located in 80111 zip code"):
    results = asyncio.run(chat_with_agent(web_scaper_prompt))

    guId = str(uuid.uuid4())
    bright_data_type = "BrightData"
    # Get the current UTC time as a timezone-aware datetime object
    current_utc_time = datetime.now(timezone.utc)
    zulu_time_string = str(current_utc_time.isoformat(timespec='milliseconds').replace('+00:00', 'Z'))

    db = connect_to_brightdata_mongodb()
    collection = db["brightdata_mcp_data_collection"]

    data_instance = BrightDataOut(prompt=web_scaper_prompt, results=results, type="BrightData", guId=guId,
                             time_stamp=zulu_time_string)
    data_dict = data_instance.model_dump()
    # Insert the document into the MongoDB collection
    collection.insert_one(data_dict)

    return {"prompt": web_scaper_prompt,
            "results": results,
            "type": data_instance.type,
            "guId": data_instance.guId,
            "ts": data_instance.time_stamp
            }

@app.get("/playwright/info",tags=["Playwright AI MCP Server (Coming Soon)"])


async def chat_with_agent(prompt):
    load_dotenv()
    model = ChatAnthropic(model_name="claude-3-5-sonnet-20240620")

    # tools used is bright data mcp, specify the commands to load mcp client within python script with our agent, similar to what was done in the claude desktop app
    server_params = StdioServerParameters(
        command="npx",
        env={
            "API_TOKEN": os.getenv("API_TOKEN"),
            "BROWSER_AUTH": os.getenv("BROWSER_AUTH"),
            "WEB_UNLOCKER_ZONE": os.getenv("WEB_UNLOCKER_ZONE"),
        },
        # make sure to update the full absolute path to your math_server.py file
        args=["@brightdata/mcp"],
    )
    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            agent = create_react_agent(model,tools)

            #start conversation history
            #encourages agent to use multiple of the tools
            messages = [
                {
                    "role": "system",
                    "content": "You can use multiple tools in sequence to answer complex questions. Think step by step."
                }
            ]


            user_input= "Description: " + prompt
            if user_input.strip().lower() in {"exit", "quit"}:
                print("Goodbye!")

            #add user history (adding more context)
            messages.append({"role": "user", "content": user_input})

            #call the agent
            agent_response = await agent.ainvoke({"messages": messages})

            #extract agents reply and add to history
            ai_message = agent_response["messages"][-1].content
            print(f"Agent: {ai_message}")
            return ai_message



def connect_to_brightdata_mongodb():

    mongo_uri = os.getenv("MONGO_URI")
    client = MongoClient(mongo_uri)
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)

    return client["brightdata_mcp_data"]
