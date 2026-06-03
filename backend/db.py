import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "ah.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Products
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT,
        brand TEXT,
        url TEXT UNIQUE,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Product nutrients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS nutrition (
        product_id TEXT PRIMARY KEY,
        energy_kcal REAL,
        carbs_g REAL,
        protein_g REAL,
        fat_g REAL,
        salt_g REAL,
        raw_text TEXT,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(product_id) REFERENCES products(id)
    )
    """)

    # User Products
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_products (
        user_id TEXT NOT NULL,
        product_id TEXT NOT NULL,
        quantity REAL NOT NULL,
        PRIMARY KEY (user_id, product_id)
    )
    """)

    conn.commit()
    conn.close()


def save_product(product):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO products (id, name, brand, url, last_seen)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        product["id"],
        product.get("name"),
        product.get("brand"),
        product["url"]
    ))

    conn.commit()
    conn.close()


def save_nutrition(product_id, nutrition, raw_text):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR REPLACE INTO nutrition (
        product_id,
        energy_kcal,
        carbs_g,
        protein_g,
        fat_g,
        salt_g,
        raw_text,
        last_updated
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        product_id,
        nutrition.get("energy_kcal"),
        nutrition.get("carbs_g"),
        nutrition.get("protein_g"),
        nutrition.get("fat_g"),
        nutrition.get("salt_g"),
        raw_text
    ))

    conn.commit()
    conn.close()


def show_products(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, brand, url, last_seen
        FROM products
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    print("\n--- PRODUCTS ---")
    for r in rows:
        print(r)

    conn.close()


def show_nutrition(limit=10):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT product_id, energy_kcal, carbs_g, protein_g, fat_g, salt_g
        FROM nutrition
        LIMIT ?
    """, (limit,))

    rows = cur.fetchall()

    print("\n--- NUTRITION ---")
    for r in rows:
        print(r)

    conn.close()


def get_product_id(product_name):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM products
        WHERE name LIKE ?
        LIMIT 1
    """, (f"%{product_name}%",))

    product = cur.fetchone()
    conn.close()
    
    if not product:
        return None

    product_id, name = product

    return product_id


def get_product_std_nutrition(product_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT energy_kcal, carbs_g, protein_g, fat_g, salt_g
        FROM nutrition
        WHERE product_id = ?
    """, (product_id,))

    nutrition = cur.fetchone()
    conn.close()

    if not nutrition:
        return None

    return nutrition

# if __name__ == "__main__":
#     show_products()
#     show_nutrition()