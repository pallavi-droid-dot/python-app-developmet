from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI(
    title="Item Management API",
    description="A fully documented REST API with SQLite storage & authentication.",
    version="1.0.0"
)

# API Key Security Setup
API_KEY = "mysecuretoken123"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# Database Setup
def init_db():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Pydantic Schemas for Validation
class ItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(None, max_length=300)

class ItemResponse(BaseModel):
    id: int
    title: str
    description: str

# Endpoints
@app.get("/", tags=["Health Check"])
def root():
    return {"status": "API is online and running"}

@app.post("/items", response_model=ItemResponse, tags=["Items"])
def create_item(item: ItemCreate, token: str = Depends(verify_api_key)):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (title, description) VALUES (?, ?)", (item.title, item.description))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, "title": item.title, "description": item.description}

@app.get("/items", tags=["Items"])
def get_items():
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM items")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "description": r[2]} for r in rows]

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def get_item(item_id: int):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": row[0], "title": row[1], "description": row[2]}

@app.delete("/items/{item_id}", tags=["Items"])
def delete_item(item_id: int, token: str = Depends(verify_api_key)):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": f"Item {item_id} deleted successfully"}
