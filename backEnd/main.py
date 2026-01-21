from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import mysql.connector

app = FastAPI()

# 1. Database Connection (Update with your local MySQL credentials)
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",        # Change this to your MySQL username
        password="",        # Change this to your MySQL password
        database="habesha_bites" # Change this to your DB name
    )

# 2. Food Prices (Matches your @ethiopian-food Entity)
FOOD_PRICES = {
    "Doro Wat": 250.0,
    "Kitfo": 300.0,
    "Beyaynetu": 180.0,
    "Shiro Wat": 120.0,
    "Tibs": 280.0,
    "Gomen": 100.0,
    "Firfir": 150.0
}

# Global dictionary to track items during a session (Temporary storage)
# In production, you would store this in a 'pending_orders' DB table
inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from Dialogflow
    payload = await request.json()
    
    # Extract intent name and parameters
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    session_id = payload['session'].split('/')[-1]

    if intent == "order.add - context: ongoing-order":
        return add_to_order(parameters, session_id)
    
    elif intent == "order.remove - context: ongoing-order":
        return remove_from_order(parameters, session_id)
    
    elif intent == "order.complete - context: ongoing-order":
        return complete_order(session_id)

    elif intent == "track.order - context: ongoing-tracking":
        order_id = parameters.get("number")
        return track_order(order_id)

def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("food-item")
    quantities = parameters.get("number")

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't quite get that. Please specify a quantity for every food item."
    else:
        new_food_dict = dict(zip(food_items, quantities))
        
        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            for food, qty in new_food_dict.items():
                current_food_dict[food] = current_food_dict.get(food, 0) + qty
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = ", ".join([f"{int(qty)} {food}" for food, qty in inprogress_orders[session_id].items()])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={"fulfillmentText": "I couldn't find your order. Try saying 'New Order'."})
    
    food_items = parameters.get("food-item")
    current_order = inprogress_orders[session_id]
    
    removed_items = []
    for item in food_items:
        if item in current_order:
            del current_order[item]
            removed_items.append(item)
    
    if not removed_items:
        fulfillment_text = "None of those items were in your order."
    else:
        order_str = ", ".join([f"{int(qty)} {food}" for food, qty in current_order.items()])
        fulfillment_text = f"Removed {', '.join(removed_items)}. Your remaining order: {order_str or 'Empty'}."
    
    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def complete_order(session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id]:
        return JSONResponse(content={"fulfillmentText": "Your cart is empty!"})
    
    order_data = inprogress_orders[session_id]
    total_price = sum(FOOD_PRICES.get(food, 0) * qty for food, qty in order_data.items())
    
    # Save to MySQL
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Insert into orders table
        cursor.execute("INSERT INTO orders (total_price, status) VALUES (%s, %s)", (total_price, "In Progress"))
        order_id = cursor.lastrowid
        
        # 2. Insert into order_items table
        for food, qty in order_data.items():
            cursor.execute(
                "INSERT INTO order_items (order_id, food_item, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, food, qty, FOOD_PRICES[food])
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Clear the session
        del inprogress_orders[session_id]
        
        fulfillment_text = f"Awesome! Your order #{order_id} is placed. Total is {total_price} ETB. You can track it using your ID."
    except Exception as e:
        fulfillment_text = f"Error saving order: {str(e)}"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})

def track_order(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return JSONResponse(content={"fulfillmentText": f"Order #{int(order_id)} status: {result[0]}"})
        else:
            return JSONResponse(content={"fulfillmentText": "Order ID not found."})
    except:
        return JSONResponse(content={"fulfillmentText": "Database error while tracking."})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)