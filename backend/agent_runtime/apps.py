from django.apps import AppConfig


class AgentRuntimeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'agent_runtime'
    verbose_name = 'Autonomous Agent Runtime'

    def ready(self):
        # Register standard built-in tools and typed MCP tools on startup
        try:
            from .registry import register_builtin_tools
            register_builtin_tools()
            from .tools.registry import ToolRegistry as TypedRegistry
            TypedRegistry.ensure_initialized()
        except Exception:
            pass
