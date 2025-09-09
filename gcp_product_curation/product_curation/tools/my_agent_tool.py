from typing import Optional, Dict
from google.adk.tools.base_toolset import BaseToolset
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.tools.base_tool import BaseTool
from .search_tools import SearchTool, ReadWebpageTool
# from .guideline_tool import GuidelineConsultantTool
# from .guideline_search_tool import guideline_search_tool

# --- Toolset Definition ---
class MyAgentTools(BaseToolset):
    """
    A Toolset that provides instances of SearchTool,
    and ReadWebpageTool to an ADK agent.
    """
    tool_name_prefix = ""

    def __init__(self):
        # Instantiate your tools
        # self.guideline_tool = GuidelineConsultantTool()
        self.search_tool = SearchTool()
        self.read_webpage_tool = ReadWebpageTool()

    async def get_tools(
        self, readonly_context: Optional[ReadonlyContext] = None
    ) -> list[BaseTool]:
        """Returns the list of tools available to the agent."""
        agent_name = getattr(readonly_context, "agent_name", None)
        print(f"get_tools called for {agent_name}")

        tools = [
            # self.guideline_tool,
            self.search_tool,
            self.read_webpage_tool,
        ]

        # --- Sanity check: ensure unique tool names ---
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), f"Duplicate tool names detected: {names}"

        print("Tools returned:", names)
        return tools