import mysql.connector

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '@Muhe0915',
    'database': 'habesha_bites'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def get_item_id_and_price(food_name):
    """Retrieves item_id and price for a specific food name."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT item_id, price FROM food_items WHERE name = %s"
        cursor.execute(query, (food_name,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result if result else (None, None)
    except Exception as e:
        print(f"Error in get_item_id_and_price: {e}")
        return None, None

def get_next_order_id():
    """Finds the highest order_id and returns the next one."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT MAX(order_id) FROM orders"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result[0] is not None:
            return result[0] + 1
        return 1000 # Start at 1000 if table is empty
    except Exception as e:
        print(f"Error in get_next_order_id: {e}")
        return 1000

def insert_order(order_id, status="in progress"):
    """Inserts a new order into the orders table."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO orders (order_id, status) VALUES (%s, %s)"
        cursor.execute(query, (order_id, status))
        connection.commit()
        cursor.close()
        connection.close()
        return order_id
    except Exception as e:
        print(f"Error in insert_order: {e}")
        return None

def insert_order_item(order_id, item_id, quantity, total_price):
    """Inserts an item into the order_details table."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "INSERT INTO order_details (order_id, item_id, quantity, total_price) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (order_id, item_id, quantity, total_price))
        connection.commit()
        cursor.close()
        connection.close()
    except Exception as e:
        print(f"Error in insert_order_item: {e}")

def get_order_status(order_id):
    """Fetches the status of an existing order."""
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = "SELECT status FROM orders WHERE order_id = %s"
        cursor.execute(query, (order_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Error in get_order_status: {e}")
        return None