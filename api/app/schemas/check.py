from pydantic import BaseModel

class TextCheck(BaseModel):
    title: str = "Pasted text"
    text: str
