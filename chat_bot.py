from dotenv import load_dotenv
import os
import requests
import anthropic
from mcp_host import MCPHost
# Loading .env
load_dotenv()
MODEL = os.getenv("ANTHROPIC_MODEL") if os.getenv("ANTHROPIC_MODEL") else None
API_KEY = os.getenv("ANTHROPIC_API_KEY") if os.getenv("ANTHROPIC_API_KEY") else None
MAX_TOKENS = 20

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
        self.tools = []
        self.expose_tools()
        # self.test_connection()
        
    def test_connection(self):
        try:
            _ = self.client.messages.create(
                model=MODEL,
                messages=[{"role": "user", "content": [{"type": "text", "text": "hola"}]}],
                max_tokens=1
            )
        except:
            raise("No se pudo establecer conexion con LLM!")
    
    def ask(self, msg):
        parsed_msg = [{"role": "user", "content": [{"type": "text", "text": msg}]}]
        try:
            resp = self.client.messages.create(
                model=MODEL,
                messages=parsed_msg,
                max_tokens=MAX_TOKENS
            )
            return resp.content
        except:
            raise("No se pudo establecer conexion con LLM!")


    def query_llm(self):
        
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
                    content = self.ask(prompt)
                    final_text = "".join([c.text for c in content if getattr(c, "type", "") == "text"])
                    print(f"ChatBot > {final_text}\n\n")
                else:
                    print("[COMMAND NOT RECOGNIZED] must start with at least one indicator, you can use \'-h\' to list them")

        except KeyboardInterrupt:
            print("Closed!")

    def expose_tools(self):
        for name, server in self.mcp_host.servers.items():
            if hasattr(server, "list_tools"):
                for tool_name, desc in server.list_tools().items():
                    self.tools.append({
                        "name": tool_name,
                        "description": desc,
                        "server": name
                    })
        print(self.tools)

if __name__ == "__main__":
    mcph = MCPHost()
    chatbot = Chat(mcph)
    
    
