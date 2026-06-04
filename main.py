import json
import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mock Inventory API")

DATA_FILE = "inventory.json"
API_KEY = os.getenv("INVENTORY_API_KEY", "demo-inventory-key")


class Item(BaseModel):
    itemId: str
    name: str
    category: str
    unit: str
    cost: float


class StockUpdate(BaseModel):
    itemId: str
    locationId: str
    quantity: int


def check_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def load_data():
    with open(DATA_FILE, "r") as file:
        return json.load(file)


def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=2)


@app.get("/")
def home():
    return {"status": "Mock Inventory API is running"}


@app.get("/inventory/items")
def get_items(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return load_data()["items"]


@app.post("/inventory/items")
def create_item(item: Item, x_api_key: str = Header(None)):
    check_api_key(x_api_key)

    data = load_data()

    for existing_item in data["items"]:
        if existing_item["itemId"] == item.itemId:
            raise HTTPException(status_code=400, detail="Item already exists")

    data["items"].append(item.dict())
    save_data(data)

    return item


@app.get("/inventory/stock")
def get_stock(x_api_key: str = Header(None)):
    check_api_key(x_api_key)
    return load_data()["stock"]


@app.post("/inventory/receipts")
def receive_stock(receipt: StockUpdate, x_api_key: str = Header(None)):
    check_api_key(x_api_key)

    data = load_data()

    for stock in data["stock"]:
        if stock["itemId"] == receipt.itemId and stock["locationId"] == receipt.locationId:
            stock["onHand"] += receipt.quantity
            save_data(data)
            return stock

    new_stock = {
        "itemId": receipt.itemId,
        "locationId": receipt.locationId,
        "onHand": receipt.quantity,
        "parLevel": 0,
        "reorderPoint": 0
    }

    data["stock"].append(new_stock)
    save_data(data)

    return new_stock


@app.get("/inventory/alerts")
def get_alerts(x_api_key: str = Header(None)):
    check_api_key(x_api_key)

    data = load_data()
    alerts = []

    for stock in data["stock"]:
        if stock["onHand"] <= stock["reorderPoint"]:
            alerts.append({
                "severity": "high",
                "itemId": stock["itemId"],
                "locationId": stock["locationId"],
                "message": "Item is at or below reorder point"
            })

    return alerts