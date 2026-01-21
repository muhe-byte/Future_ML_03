from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper

app = FastAPI()

inprogress_orders = {}

@app.post("/")
async def handle_request(request: Request):
    payload = await request.json()
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    session_id = payload['session'].split('/')[-1]

    intent_handler_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)

def add_to_order(parameters: dict, session_id: str):
    food_items = parameters.get("Ethiopian-food", [])
    quantities = parameters.get("number", [])

    if len(food_items) > len(quantities):
        quantities.extend([1.0] * (len(food_items) - len(quantities)))

    new_items = dict(zip(food_items, quantities))

    if session_id in inprogress_orders:
        for f, q in new_items.items():
            inprogress_orders[session_id][f] = inprogress_orders[session_id].get(f, 0) + q
    else:
        inprogress_orders[session_id] = new_items

    order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
    return JSONResponse(content={"fulfillmentText": f"Added! Current cart: {order_str}. Anything else?"})

def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={"fulfillmentText": "Your cart is empty."})
    
    food_items = parameters.get("Ethiopian-food", [])
    current_order = inprogress_orders[session_id]
    removed_items = []

    for item in food_items:
        # Case-insensitive removal
        key_to_del = next((k for k in current_order.keys() if k.lower() == item.lower()), None)
        if key_to_del:
            del current_order[key_to_del]
            removed_items.append(key_to_del)

    order_str = generic_helper.get_str_from_food_dict(current_order)
    res_text = f"Removed {', '.join(removed_items)}." if removed_items else "I couldn't find those items in your cart."
    return JSONResponse(content={"fulfillmentText": f"{res_text} Current cart: {order_str if order_str else 'Empty'}."})

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders or not inprogress_orders[session_id]:
        return JSONResponse(content={"fulfillmentText": "Your cart is empty. What can I get for you?"})

    order_data = inprogress_orders[session_id]
    order_id = db_helper.get_next_order_id()
    
    if db_helper.insert_order(order_id):
        total_bill = 0
        for food, qty in order_data.items():
            item_id, price = db_helper.get_item_id_and_price(food)
            if item_id:
                item_total = price * qty
                total_bill += item_total
                db_helper.insert_order_item(order_id, item_id, int(qty), item_total)
        
        del inprogress_orders[session_id]
        return JSONResponse(content={
            "fulfillmentText": f"Thanks for choosing us! Your Order ID is #{order_id}. Your total is {total_bill} ETB."
        })
    
    return JSONResponse(content={"fulfillmentText": "I had trouble saving your order. Please try again."})

def track_order(parameters: dict, session_id: str):
    order_id_raw = parameters.get("number")
    if isinstance(order_id_raw, list): order_id_raw = order_id_raw[0]
    
    try:
        order_id = int(order_id_raw)
        status = db_helper.get_order_status(order_id)
        if status:
            return JSONResponse(content={"fulfillmentText": f"The status of order #{order_id} is: {status}"})
        return JSONResponse(content={"fulfillmentText": f"I couldn't find order #{order_id} in our records."})
    except:
        return JSONResponse(content={"fulfillmentText": "Please provide a valid numeric Order ID."})