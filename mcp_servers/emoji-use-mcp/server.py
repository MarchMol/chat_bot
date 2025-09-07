from mcp.server.fastmcp import FastMCP
from model import EmojiUsage, Interpretation
import resources as res_tools
# Create an MCP server
mcp = FastMCP("EmojiUsage")

# ---- Exitence queries ---- #
@mcp.tool()
def get_describers():
    """
    Returns possible characteristics or describers that are associated to an emoji
    """
    return res_tools.get_describers()
    
@mcp.tool()
def get_possible_contexts():
    """
    Returns list of possible contexts or feelings associated to an emoji.
    """
    return res_tools.get_contexts()

@mcp.tool()
def get_possible_platforms():
    """
    Returns list of possible social media plaftorms where emoji usage is recognized.
    """
    return res_tools.get_platforms()

@mcp.tool()
def is_valid_emoji(emoji: str):
    """
    Validates wether a given emoji string exists within the emoji usage dataset.
    """
    return res_tools.is_valid_emoji(emoji)

# ---- Emoji interpretation ---- #
# Get possible sentiment given an emoji + info
@mcp.tool()
def get_context_from_emoji(emoji: str, info:dict):
    """ 
    Returns a list of the possible context or feeling associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    int_obj = res_tools.get_context_from_emoji(emoji, info)
    return int_obj

# Get possible platform given an emoji + info
@mcp.tool()
def get_platform_from_emoji(emoji: str, info:dict):
    """ 
    Returns a list of the possible social media platform associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    int_obj = res_tools.get_platform_from_emoji(emoji, info)
    return int_obj

# Get possible gender given an emoji + info
@mcp.tool()
def get_gender_from_emoji(emoji: str, info:dict):
    """ 
    Returns a list of the possible gender idetity associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    int_obj = res_tools.get_gender_from_emoji(emoji, info)
    return int_obj

# ---- Emoji Usage ---- #
@mcp.tool(name="get_appropriate_emoji")
def get_appropriate_emoji(query: EmojiUsage) -> list[str]:
    """
    Returns one or more emojis suitable for the given situation 
    or list of conditions, ordered by how frequently it appears 
    in the dataset for Emoji Usage
    """
    rslt = res_tools.predict_emoji(query)
    return rslt

# @mcp.resource()
# @mcp.prompt()
