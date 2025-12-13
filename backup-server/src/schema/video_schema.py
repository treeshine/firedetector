from pydantic import BaseModel

class SingleVideoRead(BaseModel):
    file_path: str
    
    class Config:
        orm_mode = True

class SingleThumbRead(BaseModel):
    thumb_path: str
    
    class Config:
        orm_mode = True