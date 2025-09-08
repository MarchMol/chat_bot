import json
import datetime
from pathlib import Path
import subprocess
from mcp import ClientSession
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
    def __init__(self):
        self.logger = Logger()
        self.servers = {}

        self.config = self.load_config()
        
        self.start_servers()
                
                
    def load_config(self):
        cnf = None
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            cnf = json.load(f)
        return cnf
    
    def log(self, type, msg):
        self.logger.write(type, msg)
        
    def start_servers(self):
        for server in self.config.get("servers", []):
            if "command" in server and "args" in server:
                name, command, args = server["name"],server["command"], server["args"]
                proc = subprocess.Popen([command, *args])
                self.servers[name] = proc
                self.log("Online", f"Server [{name}] is online as Subprocces (pid={proc.pid})")
            else:
                self.log("Warning", f"Server [{name}] doesnt have command/args so it will be skipped")
    
    def stop_servers(self):
        for name, proc in self.servers.items():
            proc.terminate()
            self.log("")
            self.log("Stop", f"Server [{name}] has been stopped")

if __name__ == "__main__":
    try:
        mcph = MCPHost()
        mcph.start_servers()
        while(True):
            pass
    except KeyboardInterrupt:
        mcph.stop_servers()