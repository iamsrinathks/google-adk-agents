# product_curation/config.py

import os

# # API endpoint for your custom MCP search tool
# MCP_CUSTOM_SEARCH_API_URL = os.getenv("MCP_CUSTOM_SEARCH_API_URL", "https://mcp.example.com/api/v1/search")
# MCP_API_KEY = os.getenv("MCP_API_KEY")

# # Confluence API details
# CONFLUENCE_API_URL = os.getenv("CONFLUENCE_API_URL")
# CONFLUENCE_API_KEY = os.getenv("CONFLUENCE_API_KEY")


# LLM Model to use
MODEL_NAME = "gemini-2.5-pro"
AGENT_NAME = "product_curation"
DESCRIPTION = "A helpful assistant for curating GCP products based on guidelines and user feedback."