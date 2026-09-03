import logging
from typing import Dict, Any, List, Optional, Type, Union
from .base import BaseTool, ToolExecutionContext, ToolResult
from .categories import ToolCategory
from .implementations import ALL_INITIAL_TOOLS

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for typed, composable Agent tools.
    Provides category filtering, MCP schema export, and guardrailed execution.
    """
    _tools: Dict[str, BaseTool] = {}
    _initialized: bool = False

    @classmethod
    def register(cls, tool: Union[BaseTool, Type[BaseTool]]) -> BaseTool:
        """Register a BaseTool instance or class."""
        instance = tool() if isinstance(tool, type) else tool
        cls._tools[instance.name] = instance
        return instance

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        cls.ensure_initialized()
        return cls._tools.get(name)

    @classmethod
    def list_tools(cls, category: Optional[ToolCategory] = None) -> List[BaseTool]:
        cls.ensure_initialized()
        tools = list(cls._tools.values())
        if category:
            cat_str = str(category).upper()
            tools = [t for t in tools if str(t.category).upper() == cat_str]
        return tools

    @classmethod
    def list_mcp_tools(cls, category: Optional[ToolCategory] = None) -> List[Dict[str, Any]]:
        """Exports all registered tools formatted according to the official MCP Protocol Schema."""
        return [tool.to_mcp_tool() for tool in cls.list_tools(category=category)]

    @classmethod
    def execute(cls, name: str, input_data: Dict[str, Any], context: Optional[ToolExecutionContext] = None) -> ToolResult:
        """
        Executes a tool with complete validation, idempotency, and guardrail enforcement.
        Never executes arbitrary unvetted code.
        """
        cls.ensure_initialized()
        tool = cls.get(name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{name}' is not registered in the ToolRegistry.",
            )

        context = context or ToolExecutionContext()
        return tool.run_with_guardrails(input_data, context)

    @classmethod
    def ensure_initialized(cls):
        """Initializes and registers all 19 standard tools if not already loaded."""
        if not cls._initialized:
            for tool_cls in ALL_INITIAL_TOOLS:
                cls.register(tool_cls)
            cls._initialized = True

    @classmethod
    def sync_to_db(cls):
        """Syncs all in-memory registered tools into the database AgentTool table."""
        from ..models import AgentTool
        cls.ensure_initialized()
        for tool in cls.list_tools():
            AgentTool.objects.update_or_create(
                name=tool.name,
                defaults={
                    "description": tool.description,
                    "category": str(tool.category).lower(),
                    "parameters_schema": tool.input_schema,
                    "risk_level": tool.risk_level,
                    "is_enabled": True,
                },
            )


# Initialize automatically upon module import
ToolRegistry.ensure_initialized()
