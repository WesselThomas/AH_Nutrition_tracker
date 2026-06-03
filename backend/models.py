from pydantic import BaseModel

class ProductIn(BaseModel):
    product_id: str
    quantity: float
    user_id: str = "default"