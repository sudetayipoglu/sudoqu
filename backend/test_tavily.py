from tavily import TavilyClient
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("TAVILY_API_KEY")

client = TavilyClient(api_key=api_key)
response = client.search(query="2026 hackathon başvuruları Türkiye")

for result in response["results"]:
    print(result["title"])
    print(result["url"])
    print("---")
