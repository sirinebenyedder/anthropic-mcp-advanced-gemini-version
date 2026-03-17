import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from unittest import result
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import json
from pydantic import AnyUrl
#sampling & roots imports 
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    TextContent,
    Root, ListRootsResult
)
from mcp.shared.context import RequestContext
from pydantic import FileUrl
from pathlib import Path
class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
        llm_service: Any = None,
        roots: Optional[list[str]] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._llm_service = llm_service  #accepting the llm service as a parameter for sampling
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._roots = self._create_roots(roots) if roots else []

    def _create_roots(self, root_paths: list[str]) -> list[Root]:
        """Convert path strings to Root objects."""
        roots = []
        for path in root_paths:
            p = Path(path).resolve()
            file_url = FileUrl(f"file://{p}")
            roots.append(Root(uri=file_url, name=p.name or "Root"))
        return roots

    async def _handle_list_roots(self, context) -> ListRootsResult:
        """Callback when server requests roots."""
        return ListRootsResult(roots=self._roots)

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write,
                          #passing the callback when initializing the client session
                          logging_callback=self._logging_callback,
                          sampling_callback=self._sampling_callback,
                          list_roots_callback=self._handle_list_roots if self._roots else None, )
        )
        await self._session.initialize()

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input,
                                              #For the Logging and Notification
                                              progress_callback=self._progress_callback,)
    

    async def list_prompts(self) -> list[types.Prompt]:
        # TODO: Return a list of prompts defined by the MCP server
        result = await self.session().list_prompts()
        return result.prompts
      

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        # TODO: Get a particular prompt defined by the MCP server
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        # TODO: Read a resource, parse the contents and return it
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]
        
        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)
        
        return resource.text

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    #Sampling method
    async def _sampling_callback(
        self,  
        context: RequestContext,
        params: CreateMessageRequestParams
    ) -> CreateMessageResult:
        
        messages = [
            {"role": msg.role, "content": msg.content.text}
            for msg in params.messages
        ]
        
        result = self._llm_service.chat(
        messages=messages,
        system=params.systemPrompt 
        )
        #print(f"sampling response: {self._llm_service.text_from_message(result)}")
        return CreateMessageResult(
            role="assistant",
            model=self._llm_service.model,
            content=TextContent(
                type="text",
                text=self._llm_service.text_from_message(result)
            ),
        )

    #Logging and Notification callback
    async def _progress_callback(self, progress, total, message):
        if total:
            print(f"⏳ {progress}/{total} ({(progress/total)*100:.1f}%)")
        else:
            print(f"⏳ {progress}")
    async def _logging_callback(self, params):
        print(f"📋 LOG: {params.data}")


# For testing
async def main():
    async with MCPClient(
        # If using Python without UV, update command to 'python' and remove "run" from args.
        command="uv",
        args=["run", "mcp_server.py"],
    ) as _client:
        result = await _client.list_tools()
        print("Tools:", result)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
