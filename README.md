# Multi-Server Chatbot Platform

This project is a modular, multi-server chatbot platform designed for the implementation of local and remote Model Context Protocol servers in tandem with a Claude LLM to provide a natural language ChatBot with access to predefined tools.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [MCP Servers](#mcp-servers)
- [Development](#development)
- [Logging](#logging)
- [License](#license)

---

## Features

- **Multi-server architecture:** Easily add or remove MCP for different data tasks.
- **Emoji usage analysis:** Custom made MCP server to analyze and predict emoji usage patterns.
- **LLM integration:** Interact with Anthropic's Claude via the command line.
- **Extensible tools:** Expose and list available tools from all running servers.
- **Logging:** All server actions and logs are stored in JSONL format.

---

## Project Structure

```
.
├── src
│   ├── chat_bot.py # Main CLI chatbot  
│   └── mcp_host.py # MCP server manager
├── mcp_servers
│   ├── emoji-use-mcp
│   ├── filesystem
│   ├── github
│   └── (Other mcp)
├── host_config.json # MCP server configurations
└── README.md

```

---

## Installation

1. **Clone the repository:**
   ```sh
   git clone <repo-url>
   cd <repo-directory>
   ```

2. **Install Python dependencies:**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate # Linux/Mac
   .venv\Scripts\activate # Windows
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your Anthropic API key and model name.
---

## Configuration

- **host_config.json:**  
  Defines which MCP servers to launch and how. Example:
  ```json
  {
    "servers": [
      {
        "name": <name>,
        "command": <command>,
        "args": [<arg1>, <arg2>, ...],
        "transport": "stdio"
      },
      ...
    ]
  }
  ```

- **.env:**  
  Set your Anthropic API key and model:
  ```
  ANTHROPIC_API_KEY=your_key_here
  ANTHROPIC_MODEL=claude-3-opus-20240229
  ```

---

## Usage

### Start the Host and Servers

```sh
python src/chat_bot.py
```

This will:
- Start the MCPHost, which launches all servers defined in `host_config.json`.
- Start the CLI chatbot interface.

### Chatbot Commands

- `-h` : Show help.
- `-t` : List available tools from all servers.
- `-q <prompt>` : Send a prompt to the LLM.

Example:
```
> -q What is the most common context for 😂?
ChatBot > The most common context for 😂 is "funny" or "laughter".
```

---

## MCP Servers
- **emoji-use-mcp:** Analyzes emoji usage patterns.
- **filesystem:** Interact with the local filesystem.
- **github:** Interact with GitHub repositories.
- **(Other MCP servers):** Add your own MCP servers as needed.
---

## Development

- **Add a new MCP server:**  
  1. Create a new folder in `mcp_servers`.
  2. Implement a `server.py` exposing tools via the MCP protocol.
  3. Add the server to `host_config.json`.

- **Add a new tool:**  
  Define a new function in the server and decorate it with `@mcp.tool()`.

---

## Logging

All server actions and logs are written to `logs/mcp-log.jsonl` in JSON format, including timestamps and message types.