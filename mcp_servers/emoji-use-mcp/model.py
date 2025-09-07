from pydantic import BaseModel
from typing import Optional, List, Union

class EmojiUsage(BaseModel):
    context : Optional[str] = None
    platform : Optional[str] = None
    age : Optional[int] = None
    gender : Optional[str] = None
    
class Interpretation(BaseModel):
    entries_amount : int = 0
    type : str = ""
    result : List[Union[str, float]] = []