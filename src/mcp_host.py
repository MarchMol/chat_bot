import json
import asyncio
import datetime
from pathlib import Path
from contextlib import AsyncExitStack
import subprocess
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from importlib import import_module
import aiohttp
import sys
import traceback

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
        self.ssh_sessions = {}
        self.contexts = {}
        self._connections = {}
        self.tools = []
        self.config = self.load_config()
        self._stack: AsyncExitStack | None = None
        self._http_session: aiohttp.ClientSession | None = None
    
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
        print("Loading tools from server:")
        for name, session in self.sessions.items():
            
            try:
                # Check if this is a raw SSH session
                if isinstance(session, dict) and 'process' in session:
                    # Handle SSH session - send tools/list request
                    list_tools_msg = {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "resources/list",
                        "params": {"resource": "tools"}
                    }

                    session['message_id'] = 2
                    await self._send_message(session['process'], list_tools_msg)
                    response = await self._read_response(session['process'], name)
                    print(f"Resp: {response}")
                    if response and 'result' in response:
                        tools = response['result'].get('tools', [])
                        for tool in tools:
                            self.tools.append({
                                "name": tool['name'],
                                "description": f"[{name}] {tool.get('description', '')}",
                                "input_schema": tool.get('inputSchema', {})
                            })
                        self.log("TOOLS", f"Loaded {len(tools)} tools from SSH server [{name}]")
                    else:
                        self.log("TOOLS", f"Failed to get tools from SSH server [{name}]: {response}")
                        
                else:
                    # Handle regular MCP session (your existing code)
                    tools_response = await session.list_tools()
                    for tool in tools_response.tools:
                        self.tools.append({
                            "name": tool.name,
                            "description": f"[{name}] {tool.description or ''}",
                            "input_schema": tool.inputSchema
                        })
                    self.log("TOOLS", f"Loaded {len(tools_response.tools)} tools from MCP server [{name}]")

            except Exception as e:
                self.log("TOOLS", f"Failed to load tools from [{name}]: {type(e).__name__}: {e}")

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
            name = server.get("name", "unknown")
            server_type = server.get("transport", "stdio")
            command = server.get("command")
            if command == "ssh":
                self.log("DETECTED", f"Server [{name}] of transport type \'stdio\' with ssh command")
                await self.start_ssh_server(server)
            elif server_type == "stdio":
                self.log("DETECTED", f"Server [{name}] of transport type \'stdio\'")
                await self.start_stdio_servers(server)
            else: 
                self.log("ERROR", f"Unknown transport type '{server_type}' for server [{name}]")
                
                
    async def _send_message(self, process, message):
        """Helper to send JSON message to process"""
        import json
        message_str = json.dumps(message) + "\n"
        print(f"MSG: {message_str}")
        process.stdin.write(message_str.encode())
        await process.stdin.drain()

    async def _read_response(self, process, name):
        """Helper to read JSON response from process"""
        import json
        try:
            response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
            response_json = json.loads(response_line.decode())
            self.log("DEBUG", f"Server [{name}] response: {response_json}")
            return response_json
        except asyncio.TimeoutError:
            self.log("ERROR", f"Server [{name}] timeout reading response")
            return None
        except json.JSONDecodeError as e:
            self.log("ERROR", f"Server [{name}] invalid JSON: {e}")
            return None
                
                
    async def call_tool(self, tool_name: str, arguments: dict = None):
        """Call a tool by name with arguments"""
        # Find which server has this tool
        tool_server = None
        
        for name, session in self.sessions.items():
            # Check if this is a raw SSH session
            if isinstance(session, dict) and 'process' in session:
                # List tools from SSH session
                list_tools_msg = {
                    "jsonrpc": "2.0",
                    "id": session['message_id'],
                    "method": "tools/list",
                    "params": {}
                }
                session['message_id'] += 1
                
                await self._send_message(session['process'], list_tools_msg)
                response = await self._read_response(session['process'], name)
                
                if response and 'result' in response:
                    tools = response['result'].get('tools', [])
                    if any(tool['name'] == tool_name for tool in tools):
                        tool_server = name
                        break
            else:
                # Handle regular MCP sessions (your existing code)
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
            # Handle SSH session
            if isinstance(session, dict) and 'process' in session:
                call_tool_msg = {
                    "jsonrpc": "2.0",
                    "id": session['message_id'],
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments or {}
                    }
                }
                session['message_id'] += 1
                
                await self._send_message(session['process'], call_tool_msg)
                response = await self._read_response(session['process'], tool_server)
                
                if response and 'result' in response:
                    self.log("TOOL", f"Called tool '{tool_name}' on server [{tool_server}]")
                    return response['result'].get('content', [])
                else:
                    raise Exception(f"Tool call failed: {response}")
                    
            else:
                # Handle regular MCP session (your existing code)
                response = await session.call_tool(tool_name, arguments or {})
                self.log("TOOL", f"Called tool '{tool_name}' on server [{tool_server}]")
                return response.content
                
        except Exception as e:
            self.log("ERROR", f"Failed to call tool '{tool_name}': {e}")
            raise

    async def start_ssh_server(self, server_config):
        if "command" in server_config and "args" in server_config:
            name, command, args = server_config["name"], server_config["command"], server_config["args"]
            
            try:
                self.log("DEBUG", f"Server [{name}] creating raw subprocess...")
                
                # Create subprocess directly
                process = await asyncio.create_subprocess_exec(
                    *([command] + args),
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                self.log("DEBUG", f"Server [{name}] SSH process created, PID: {process.pid}")
                
                # Give it a moment to establish
                await asyncio.sleep(2.0)
                
                # Check if process is still alive
                if process.returncode is not None:
                    stderr_data = await process.stderr.read()
                    self.log("ERROR", f"Server [{name}] SSH process died immediately: {stderr_data.decode()}")
                    raise Exception(f"SSH process exited with code {process.returncode}")
                
                self.log("DEBUG", f"Server [{name}] SSH process is alive, testing communication...")
                
                # Send initialize message
                import json
                init_message = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "mcp-host", "version": "1.0.0"}
                    }
                }
                
                await self._send_message(process, init_message)
                response = await self._read_response(process, name)
                print(f"Resp: {response}")
                if not response:
                    raise Exception("Failed to initialize")
                
                self.log("DEBUG", f"Server [{name}] initialization successful")
                
                # Store the process and create a wrapper for easy communication
                ssh_session = {
                    'process': process,
                    'name': name,
                    'message_id': 2  # Start at 2 since we used 1 for initialize
                }
                
                self.sessions[name] = ssh_session
                self.log("ONLINE", f"Server [{name}] is online and ready for calls!")
                print(f"[{name}] - Online")
                
            except Exception as e:
                self.log("ERROR", f"Failed to start server [{name}]: {type(e).__name__}: {e}")
                print(f"[{name}] - Offline")


    async def start_stdio_servers(self, server_config):
        if "command" in server_config and "args" in server_config:
            name, command, args = server_config["name"], server_config["command"], server_config["args"]
            try:
                server_params = StdioServerParameters(
                    command=command, args=args,
                )
                client_context = stdio_client(server_params)
                # I/O streams
                streams = await self._stack.enter_async_context(client_context)
                read, write, *rest = streams
                
                session_cmgr = ClientSession(read, write)
                session = await self._stack.enter_async_context(session_cmgr)
                self.log("INIT", f"Server [{name}] client session set up, now waiting to initialize")
                await asyncio.sleep(1.0)
                if hasattr(session, "initialize"):
                    self.log("DEBUG", f"Server [{name}] starting initialization...")
                    await session.initialize()
                        
                self.sessions[name] = session
                self.log("ONLINE", f"Server [{name}] is online and initialized!")
                print(f"[{name}] - Online")
            except Exception as e:
                self.log("ERROR", f"Failed to start server [{name}]: {e}")
                print(f"[{name}] - Offline")
        else:
            self.log("WARNING", f"Server [{name}] doesnt have command/args so it will be skipped")
            print(f"[{name}] - Offline")


    async def stop_servers(self):
        try:
            await self._stack.aclose() 
            self.log("CLOESD", f"closed stack successfully")
        except Exception as e:
            self.log("ERROR", f"Failed to close stack: {e}")