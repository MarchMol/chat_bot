from dotenv import load_dotenv
import os
import requests
import anthropic
import json
from mcp_host import MCPHost
import asyncio
import time
# Loading .env
load_dotenv()
MODEL = os.getenv("ANTHROPIC_MODEL") if os.getenv("ANTHROPIC_MODEL") else None
API_KEY = os.getenv("ANTHROPIC_API_KEY") if os.getenv("ANTHROPIC_API_KEY") else None
MAX_TOKENS = 200

COMMANDS = ["-h", "-t"]

def handle_commands(cm):
    if cm == "-h":
        print("\n\t Esto se supone que te ayudara\n")
    if cm == "-t":
        print("\n\t Esto se supone que lista las tools disponibles\n")
# ---- Chat ----- #
class Chat():
    def __init__(self, mcp_host):
        self.client = anthropic.Anthropic(api_key=API_KEY)
        self.mcp_host = mcp_host
        self.messages = []
        self.tools = []
        self.system_propmpt = (
            "Eres un asistente conversacional llamado ChatBot.\n"
            "Tienes acceso a diferentes herramientas (tools) basadas en los servers que te mostraran mas adelante.\n"
            "Cuando el usuario te haga una pregunta o solicitud, primero decides si necesitas usar alguna herramienta para responder.\n"
            "Si decides usar una herramienta, debes especificar claramente el nombre de la herramienta y los argumentos necesarios en formato JSON.\n"
            "Si no necesitas usar una herramienta, simplemente responde la pregunta o solicitud del usuario.\n"
            "Busca contestar de manera concisa y usar apropiadamente las herramientas disponibles\n"
        )
        
    def test_connection(self):
        try:
            _ = self.client.messages.create(
                model=MODEL,
                messages=[{"role": "user", "content": [{"type": "text", "text": "hola"}]}],
                max_tokens=1
            )
        except:
            raise("No se pudo establecer conexion con LLM!")
    
    def parse_user_msg(self, msg):
        parsed_msg = {"role": "user", "content": [{"type": "text", "text": msg}]}
        return parsed_msg
    
    async def ask(self, msg):
        
        self.messages.append(self.parse_user_msg(msg))
        try:
            resp = self.client.messages.create(
                model=MODEL,
                system=self.system_propmpt,
                tools=self.mcp_host.tools,
                messages=self.messages,
                max_tokens=MAX_TOKENS,
            )
            self.messages.append({"role": "assistant", "content": resp.content})
            tool_uses = [c for c in resp.content if getattr(c, "type", "") == "tool_use"]
            if tool_uses:
                tool_results = {}
                for t in tool_uses: 
                    name = t.name
                    args = t.input or {}
                    self.mcp_host.log("llm.tool_use", f"name: {name}, args: {args}")
                    # Ejecutar herramienta en MCP
                    result = await self.mcp_host.call_tool(name, args)
                    # Devolvemos tool_result al LLM
                    
                    if isinstance(result, list):
                        result_text_blocks = []
                        for r in result:
                            if hasattr(r, "text"):
                                result_text_blocks.append({"type": "text", "text": r.text})
                    else:
                        result_text_blocks = [{"type": "text", "text": str(result)}]
                        
                    tool_results = {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": t.id,
                                "content": result_text_blocks
                            }
                        ]  
                    }
        

                self.messages.append(tool_results)
                resp2 = self.client.messages.create(
                    model=MODEL,
                    system=self.system_propmpt,
                    messages=self.messages,
                    max_tokens=MAX_TOKENS
                )
                
                self.messages.append({"role": "assistant", "content": resp2.content})
                
                final_text = "".join([c.text for c in resp2.content if getattr(c, "type", "") == "text"])
                return final_text
            else:
                final_text = "".join([c.text for c in resp.content if getattr(c, "type", "") == "text"])
                return final_text

        except Exception as e:
            print(f"connection error: {e}")

    async def query_llm(self):
        
        try:
            while(True):
                raw = input("> ") # Fetch input
                user_input = raw.strip() # Clean spaces
                if (user_input in COMMANDS):
                    handle_commands(user_input)
                    continue
                if (user_input.startswith("-q" )):
                    prompt = user_input[2:].strip()
                    print(f"Your prompt was: \'{prompt}\'")
                    # Prompt llm
                    content = await self.ask(prompt)
                    print(f"ChatBot > {content}\n\n")
                else:
                    print("[COMMAND NOT RECOGNIZED] must start with at least one indicator, you can use \'-h\' to list them")

        except KeyboardInterrupt:
            print("Closed!")



## Main
async def async_main():
    mcph = MCPHost()
    await mcph.start_servers()
    await mcph.expose_tools()
    # await mcph.stop_servers()
    chatbot = Chat(mcph)
    await chatbot.query_llm()
    # await chatbot.expose_tools()
    
if __name__ == "__main__":
    asyncio.run(async_main())

    
    
