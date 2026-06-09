from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.models import ProductIn
from backend.db import get_connection, init_db
import backend.services.basket_services as service

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/basket")
def get_list(user_id: str = "default"):
    return service.get_user_basket(user_id)


@app.post("/basket")
def add(item: ProductIn):
    service.add_product(
        item.user_id,
        item.product_id,
        item.quantity
    )
    return {"status": "ok"}


@app.put("/basket")
def update(item: ProductIn):
    service.update_quantity(item.user_id, item.product_id, item.quantity)
    return {"status": "updated"}


@app.delete("/basket")
def delete(user_id: str, product_id: str):
    service.delete_product(user_id, product_id)
    return {"status": "deleted"}


@app.delete("/basket/clear")
def clear_basket(user_id: str):
    service.delete_all_products(user_id)
    return {"status": "deleted"}


@app.get("/products/search")
def search_products(q: str):
    conn = get_connection()
    cur = conn.cursor()

    q = q.strip()

    if not q:
        return []

    cur.execute("""
        SELECT id, name, brand
        FROM products
        WHERE LOWER(name) LIKE LOWER(?)
        LIMIT 10
    """, (f"%{q}%",))

    rows = cur.fetchall()
    conn.close()

    return [dict(r) for r in rows]


@app.get("/totals")
def get_totals(user_id: str = "default"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            SUM(n.energy_kcal * up.quantity / 100.0) AS energy_kcal,
            SUM(n.protein_g   * up.quantity / 100.0) AS protein_g,
            SUM(n.carbs_g     * up.quantity / 100.0) AS carbs_g,
            SUM(n.fat_g       * up.quantity / 100.0) AS fat_g
        FROM user_products up
        JOIN nutrition n ON up.product_id = n.product_id
        WHERE up.user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if row["energy_kcal"] is None:
        return {
            "energy_kcal": 0,
            "protein_g": 0,
            "carbs_g": 0,
            "fat_g": 0
        }

    return dict(row)
  

@app.head("/")
def head():
    return {}

# uvicorn main:app --reload

