# search_tools.py
import os
import json
import httpx
from bs4 import BeautifulSoup
from google.adk.tools.base_tool import BaseTool
from google.genai import types
from typing import Any
from google.adk.tools.tool_context import ToolContext

API_KEY = os.environ.get("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.environ.get("GOOGLE_SEARCH_ENGINE_ID")


if not API_KEY:
    print("Warning: GOOGLE_API_KEY not set.")
if not SEARCH_ENGINE_ID:
    print("Warning: GOOGLE_SEARCH_ENGINE_ID not set.")

def _text_content_block(obj):
    return {"type": "text", "text": json.dumps(obj, indent=2, ensure_ascii=False)}



class SearchTool(BaseTool):
    """Reusable tool to perform a Google Custom Search query."""
    name = "search"
    description = "Perform a web search query."

    def __init__(self):
        super().__init__(name=self.name, description=self.description)

    def _get_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="Search query text"),
                    "num": types.Schema(type=types.Type.INTEGER, description="Number of results to return")
                },
                required=["query"]
            )
        )

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
        return await self.execute(**args)

    async def execute(self, query: str, num: int = 5) -> dict:
        if not query:
            return {"content": [{"type": "text", "text": "Invalid query"}], "isError": True}
        try:
            results = await self._call_google_search(query, num)
            return {"content": [_text_content_block(results)]}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Search API error: {e}"}], "isError": True}

    async def _call_google_search(self, query: str, num: int = 5) -> list[dict]:
        if not API_KEY or not SEARCH_ENGINE_ID:
            raise RuntimeError("Google API Key or Search Engine ID not configured.")
        params = {
            "key": API_KEY,
            "cx": SEARCH_ENGINE_ID,
            "q": query,
            "num": max(1, min(int(num), 10)),
            "fields": "items(title,link,snippet)",
        }
        url = "https://www.googleapis.com/customsearch/v1"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": it.get("title"), "link": it.get("link"), "snippet": it.get("snippet")}
                for it in data.get("items", [])
            ]
class ReadWebpageTool(BaseTool):
    """Reusable tool to fetch and extract text content from a webpage."""
    name = "read_webpage"
    description = "Fetch and extract text content from a webpage."

    def __init__(self):
        super().__init__(name=self.name, description=self.description)

    def _get_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "url": types.Schema(type=types.Type.STRING, description="The URL of the webpage to fetch")
                },
                required=["url"]
            )
        )

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
        return await self.execute(**args)

    async def execute(self, url: str) -> dict:
        if not url:
            return {"content": [{"type": "text", "text": "Invalid URL"}], "isError": True}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Webpage fetch error: {e}"}], "isError": True}

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else ""
        body_text = " ".join(soup.get_text(separator=" ", strip=True).split())
        content = {"title": title, "text": body_text, "url": url}
        return {"content": [_text_content_block(content)]}