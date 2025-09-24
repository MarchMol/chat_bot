import json
import asyncio
import datetime
from pathlib import Path
from contextlib import AsyncExitStack
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from importlib import import_module
CONFIG_PATH = Path("./host_config.json")

class Logger():
    def __init__(self, path="logs/mcp-log.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
    def write(self, type, payload):
        log = {
            "time": str(datetime.datetime.now()),
            "type": type,
            "payload": payload
        }
        try:
            with self.path.open("r", encoding="utf-8") as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        logs.append(log)

        # rewrite with pretty formatting
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=True, indent=4)


class MCPHost():
    # Initializing MCP manager or host
    def __init__(self):
        self.logger = Logger()
        self.servers = {}
        self.sessions = {}
        self.contexts = {}
        self._connections = {}
        self.tools = []
        self.config = self.load_config()
        self._stack: AsyncExitStack | None = None

    
    def load_config(self):
        cnf = None
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            cnf = json.load(f)
        return cnf
    
    # Logging utility
    def log(self, type, msg):
        self.logger.write(type, msg)
        
    # MCP Tool management
    async def expose_tools(self):
        self.tools.clear()
        for name, session in self.sessions.items():
            try:
                tools_response = await session.list_tools()
                for tool in tools_response.tools:
                    
                    self.tools.append({
                        "name": tool.name,
                        "description": f"[{name}] {tool.description or ''}",
                        "input_schema": tool.inputSchema
                    })
                self.log("TOOLS", f"Loaded {len(tools_response.tools)} tools from [{name}]")

            except Exception as e:
                self.log("TOOLS", f"Failed to load tools from [{name}]")

    ## Tool calling
    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Call a tool by name with arguments"""
        # Find which server has this tool
        tool_server = None
        for name, session in self.sessions.items():
            try:
                tools_response = await session.list_tools()
                if any(tool.name == tool_name for tool in tools_response.tools):
                    tool_server = name
                    break
            except Exception:
                continue
        
        if not tool_server:
            raise ValueError(f"Tool '{tool_name}' not found in any server")
        
        try:
            session = self.sessions[tool_server]
            response = await session.call_tool(tool_name, arguments or {})
            self.log("TOOL", f"Called tool '{tool_name}' on server [{tool_server}]")
            return response.content
        except Exception as e:
            self.log("ERROR", f"Failed to call tool '{tool_name}': {e}")
            raise
    
    # Start/stop servers
    async def start_servers(self):
        self._stack = AsyncExitStack()
        for server in self.config.get("servers", []):
            if "command" in server and "args" in server:
                name, command, args = server["name"],server["command"], server["args"]
                
                
                # proc = await asyncio.create_subprocess_exec(
                #     command, *args,
                #     stdout=asyncio.subprocess.PIPE,
                #     stderr=asyncio.subprocess.PIPE
                # )

                # # Read first lines
                # out = await proc.stdout.readline()
                # err = await proc.stderr.readline()
                # print("STDOUT:", out.decode())
                # print("STDERR:", err.decode())
                
                
                
                print(name)
                self.log("DETECTED", f"Server [{name}] was detected")
                try:
                    server_params = StdioServerParameters(
                        command=command, args=args,
                        cwd="C:/Users/JM/Documents/Redes/chat_bot"
                    )
                    client_context = stdio_client(server_params)
                    streams = await self._stack.enter_async_context(client_context)
                    read, write, *rest = streams
                    session_cmgr = ClientSession(read, write)
                    session = await self._stack.enter_async_context(session_cmgr)
                    self.log("INIT", f"Server [{name}] client session set up, now waiting to initialize")

                    if hasattr(session, "initialize"):
                        await session.initialize()
                        
                    self.sessions[name] = session
                    self._connections[name] = session  # referencia útil
                    self.log("ONLINE", f"Server [{name}] is online and initialized!")
                                
                except Exception as e:
                    self.log("ERROR", f"Failed to start server [{name}]: {e}")
            else:
                self.log("Warning", f"Server [{name}] doesnt have command/args so it will be skipped")
    
    async def stop_servers(self):
        try:
            await self._stack.aclose() 
            self.log("CLOESD", f"closed stack successfully")
        except Exception as e:
            self.log("ERROR", f"Failed to close stack: {e}")



if __name__ == "__main__":
    try:
        mcph = MCPHost()
        mcph.start_servers()
        while(True):
            pass
    except KeyboardInterrupt:
        mcph.stop_servers()