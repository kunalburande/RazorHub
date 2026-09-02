import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class RazorpayMCPClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=["backend/razorpay_mcp_server.py"]
        )
        self.session = None
        self._ctx = None

    async def connect(self):
        self._ctx = stdio_client(self.server_params)
        read, write = await self._ctx.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        await self.session.initialize()

    async def disconnect(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._ctx:
            await self._ctx.__aexit__(None, None, None)

    async def get_tools(self):
        tools = await self.session.list_tools()
        return tools.tools

    async def call_tool(self, name: str, arguments: dict):
        result = await self.session.call_tool(name, arguments)
        # Returns a list of Content (TextContent usually)
        return [c.text for c in result.content if hasattr(c, 'text')]
