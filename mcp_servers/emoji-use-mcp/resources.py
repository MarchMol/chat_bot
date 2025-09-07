import pandas as pd
from model import EmojiUsage, Interpretation
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder containing resources.py
CSV_PATH = os.path.join(BASE_DIR, "data", "emoji_usage_dataset.csv")

df = pd.read_csv(CSV_PATH)

# ---- Dataset description ---- #
def get_contexts():
    """
    Returns list of possible contexts or feelings associated to an emoji
    """
    return df["Context"].unique().tolist()
    
def get_platforms():
    """
    Returns list of possible sentiments in an emoji
    """
    return df["Platform"].unique().tolist()

def get_describers():
    """
    Returns possible characteristics or describers that are associated to an emoji
    """
    return df.columns.to_list()
    
def is_valid_emoji(emoji: str = ""):
    """
    Returns a boolean value if a given emoji exists in the dataest
    """
    return df["Emoji"].isin([emoji]).any()


# ---- Get emoji info ---- #
def apply_info(df, em_use: EmojiUsage, min_entries = 2):
    info = df.copy()
    # Apply use
    if em_use.age:
        filtered  = info[
            (info["User Age"] > em_use.age -1) & 
            (info["User Age"] < em_use.age +1)
        ]
        if (len(filtered)>min_entries):
            info = filtered
    # Context
    if em_use.context:
        filtered = info[
            (info["Context"] == em_use.context)
        ]
        if (len(filtered)>min_entries):
            info = filtered
    # Platform
    if em_use.platform:
        filtered = info[
            (info["Platform"] == em_use.platform)
        ]
        if (len(filtered)>min_entries):
            info = filtered
    # Gender
    if em_use.gender:
        filtered = info[
            (info["Gender"] == em_use.gender)
        ]
        if (len(filtered)>min_entries):
            info = filtered
    return info

def get_context_from_emoji(emoji: str, info : dict):
    """ 
    Returns a list of the possible context or feeling associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    # Parse
    emoji_usage = EmojiUsage(**info)
    # Search emoji
    df_applied = apply_info(df, emoji_usage)
    df_emoji = df_applied[df_applied["Emoji"] == emoji]
    # Get most likely context
    rslt = df_emoji["Context"].value_counts().head(2).index.tolist()
    
    # Interpretation
    int_dict = {
        "entries_amount": len(df_emoji),
        "type": "context",
        "result": rslt
    }
    interp = Interpretation(**int_dict)
    return interp
    
def get_platform_from_emoji(emoji: str, info : dict):
    """ 
    Returns a list of the possible social media platform associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    # Parse
    emoji_usage = EmojiUsage(**info)
    # Search emoji
    df_applied = apply_info(df, emoji_usage)
    df_emoji = df_applied[df_applied["Emoji"] == emoji]
    # Get most likely context
    rslt = df_emoji["Platform"].value_counts().head(2).index.tolist()
    
    # Interpretation
    int_dict = {
        "entries_amount": len(df_emoji),
        "type": "platform",
        "result": rslt
    }
    interp = Interpretation(**int_dict)
    return interp

def get_gender_from_emoji(emoji: str, info : dict):
    """ 
    Returns a list of the possible gender identity associated to a valid emoji usage
    including the use of optional describers for EmojiUsage.
    """
    # Parse
    emoji_usage = EmojiUsage(**info)
    # Search emoji
    df_applied = apply_info(df, emoji_usage)
    df_emoji = df_applied[df_applied["Emoji"] == emoji]
    # Get most likely context
    rslt = df_emoji["Gender"].value_counts().head(1).index.tolist()
    
    # Interpretation
    int_dict = {
        "entries_amount": len(df_emoji),
        "type": "gender",
        "result": rslt
    }
    interp = Interpretation(**int_dict)
    return interp

def get_popularity_from_emoji(emoji: str, info : dict):
    """ 
    Returns a list of the possible popularity given certain charactersitics,
    associated to a valid emoji usage, including the use of optional describers for EmojiUsage.
    """
    # Parse
    emoji_usage = EmojiUsage(**info)
    # Search emoji
    df_applied = apply_info(df, emoji_usage)
    df_emoji = df_applied[df_applied["Emoji"] == emoji]
    # Get most likely context
    rslt = len(df_emoji)/len(df_applied)
    
    # Interpretation
    int_dict = {
        "entries_amount": len(df_emoji),
        "type": "popularity",
        "result": rslt
    }
    interp = Interpretation(**int_dict)
    return interp


# ---- Get emoji info ---- #
def predict_emoji(info: EmojiUsage):
    df_applied = apply_info(df, info)
    emojis = df_applied["Emoji"].value_counts(normalize=True).index.tolist()
    return emojis[:5]
    
if __name__ == "__main__":
    predict_emoji(
        EmojiUsage(**{
            "context": "sad"
        })
    )