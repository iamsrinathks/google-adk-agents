"""Defines root Agent for GCP Product Curation using multiple sub-agents and tools."""
import os
from google.adk.agents.llm_agent import Agent,LlmAgent
from typing import List, Dict, Any
#from .sub_agents.discovery.agent import discovery_root_agent
from . import prompt
from . import config
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_toolset import BaseToolset
from .tools.search_tools import SearchTool, ReadWebpageTool
# from .tools.guideline_tool import GuidelineConsultantTool
from .tools.my_agent_tools import MyAgentTools
from .sub_agents.discovery.agent import build_agents, debug_tools

# from google.adk.tools.tool_context import ToolContext



# # --- Define the root agent ---
orchestrator_agent, shared_tools = build_agents()


debug_tools(orchestrator_agent)

greeting_agent = LlmAgent(
    name="greeting_agent",
    model=config.MODEL_NAME,
    description="Greets the user and asks for the product name they want to curate.",
    instruction=prompt.GREETING_PROMPT,
    output_key="product_name",
)

root_agent = Agent(
    model=config.MODEL_NAME,
    name=config.AGENT_NAME,
    description=config.DESCRIPTION,
    instruction=prompt.ROOT_AGENT_PROMPT,
    sub_agents=[greeting_agent, orchestrator_agent],
    output_key="product_assessment_template"
    )