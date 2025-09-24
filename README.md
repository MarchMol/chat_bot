# Emoji Usage Multi-Server Chatbot Platform

This project is a modular, multi-server chatbot platform focused on emoji usage analysis and interpretation. It leverages multiple microservices (MCP servers) to provide tools for querying emoji usage data, interpreting emoji context, and interacting with large language models (LLMs) such as Anthropic's Claude.

## Table of Contents

- Features
- Project Structure
- Installation
- Configuration
- Usage
- MCP Servers
- Development
- Logging
- License

---

## Features

- **Multi-server architecture:** Easily add or remove microservices for different NLP or data tasks.
- **Emoji usage analysis:** Query emoji context, platform, gender, and popularity from a dataset.
- **LLM integration:** Interact with Anthropic's Claude via the command line.
- **Extensible tools:** Expose and list available tools from all running servers.
- **Logging:** All server actions and logs are stored in JSONL format.

---

## Project Structure

```
.
├── chat_bot.py                # Main CLI chatbot interface
├── mcp_host.py                # MCPHost: manages server processes
├── host_config.json           # Configuration for MCP servers
├── mcp_servers/               # Directory for all MCP servers
│   └── emoji-use-mcp/         # Emoji usage analysis server
│       ├── server.py          # MCP server exposing emoji tools
│       ├── resources.py       # Data processing and analysis logic
│       ├── model.py           # Pydantic models for emoji usage
│       └── data/              # Emoji usage dataset (CSV)
├── logs/
│   └── mcp-log.jsonl          # Log file for server actions
├── README.md                  # This file
└── ...
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
   pip install -r requirements.txt
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
        "name": "emoji-use-mcp",
        "command": "python",
        "args": ["mcp_servers/emoji-use-mcp/server.py"]
      }
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
python chat_bot.py
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

### Emoji Usage MCP Server

Located at `mcp_servers/emoji-use-mcp/server.py`.

**Exposed Tools:**
- `get_describers`: List possible emoji describers.
- `get_possible_contexts`: List possible emoji contexts.
- `get_possible_platforms`: List possible platforms.
- `is_valid_emoji`: Validate if an emoji exists in the dataset.
- `get_context_from_emoji`: Get likely context for an emoji.
- `get_platform_from_emoji`: Get likely platform for an emoji.
- `get_gender_from_emoji`: Get likely gender for an emoji.
- `get_appropriate_emoji`: Suggest emojis for a given context.

**Data:**  
Uses a CSV dataset at `mcp_servers/emoji-use-mcp/data/emoji_usage_dataset.csv`.

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

---

## License

MIT License (or specify your license here)

---

**For more details, see the code in each module or contact the project maintainer.**