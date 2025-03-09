from datetime import datetime
import os
import json
from pydantic import BaseModel, Field
import uuid


class Product(BaseModel):
    uid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sku: str
    name: str
    price: float
    date: datetime = Field(default_factory=datetime.now)

    def model_dump_json(self) -> dict:
        return {
            "SKU": self.sku,
            "Product Name": self.name,
            "Price": f"${self.price}",
            "Date": self.date.strftime("%Y-%m-%d")
        }


class Shop(BaseModel):
    shop_name: str
    products: list[Product] = []

    def save_to_json_file(self):
        file_path = f'data/{self.shop_name}.json'
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json_data = [product.model_dump_json()
                         for product in self.products]
            json.dump(json_data, f)
