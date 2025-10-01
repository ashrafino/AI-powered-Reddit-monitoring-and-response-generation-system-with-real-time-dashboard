from pydantic import BaseModel

class ClientBase(BaseModel):
    name: str

class ClientCreate(ClientBase):
    pass

class ClientOut(ClientBase):
    id: int
    slug: str

    class Config:
        from_attributes = True



