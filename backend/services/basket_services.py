from backend.db import get_connection

def get_user_basket(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT up.user_id, up.product_id, p.name, up.quantity
    FROM user_products up
    LEFT JOIN products p ON up.product_id = p.id
    WHERE up.user_id = ?;
    """, (user_id,))

    basket = [dict(r) for r in cur.fetchall()]
    conn.close()

    return basket


def add_product(user_id, product_id, quantity):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT quantity FROM user_products
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    existing = cur.fetchone()

    if not existing:
        cur.execute("""
            INSERT INTO user_products (user_id, product_id, quantity)
            VALUES (?, ?, ?)
        """, (user_id, product_id, quantity))

    conn.commit()
    conn.close()

    
def update_quantity(user_id, product_id, quantity):
    quantity = max(0, quantity)
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE user_products
        SET quantity = ?
        WHERE user_id = ? AND product_id = ?
    """, (quantity, user_id, product_id))

    conn.commit()
    conn.close()


def delete_product(user_id, product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM user_products
        WHERE user_id = ? AND product_id = ?
    """, (user_id, product_id))

    conn.commit()
    conn.close()


def delete_all_products(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM user_products
        WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()