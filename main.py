#!/usr/bin/env python3
"""
Ethiopian Food Chatbot - FastAPI Webhook Server
Backend server for Dialogflow and Telegram integration with MySQL
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import os
import db_helper
import generic_helper

# Initialize FastAPI app
app = FastAPI(
    title="Ethiopian Food Chatbot API",
    description="Backend webhook server for food ordering chatbot",
    version="1.0.0"
)

# In-memory storage for ongoing orders
inprogress_orders = {}

@app.post("/")
async def handle_webhook(request: Request):
    """Main webhook endpoint for Dialogflow requests"""
    try:
        payload = await request.json()
        intent = payload['queryResult']['intent']['displayName']
        parameters = payload['queryResult']['parameters']
        session_id = payload['session'].split('/')[-1]
        
        # Log the interaction
        print(f"📨 {intent} | Session: {session_id[:8]}...")
        
        # Route to appropriate handler
        intent_handlers = {
            'order.add - context: ongoing-order': add_to_order,
            'order.remove - context: ongoing-order': remove_from_order,
            'order.complete - context: ongoing-order': complete_order,
            'track.order - context: ongoing-tracking': track_order
        }
        
        handler = intent_handlers.get(intent)
        if handler:
            response = handler(parameters, session_id)
            print(f"✅ Response: {response['fulfillmentText'][:50]}...")
            return response
        else:
            return {"fulfillmentText": f"I didn't understand that intent: {intent}. Try saying 'new order' or 'track order'."}
            
    except Exception as e:
        print(f"❌ Error handling webhook: {e}")
        return {"fulfillmentText": f"Sorry, I encountered an error: {str(e)}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_connected = db_helper.test_connection()
        return {
            "status": "healthy" if db_connected else "unhealthy",
            "database": "connected" if db_connected else "disconnected",
            "active_sessions": len(inprogress_orders),
            "total_orders": db_helper.get_total_orders() if db_connected else 0,
            "menu_items": db_helper.get_menu_count() if db_connected else 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "Ethiopian Food Chatbot Webhook",
        "status": "active",
        "database": "mysql",
        "endpoints": {
            "webhook": "/",
            "health": "/health",
            "docs": "/docs"
        },
        "active_sessions": len(inprogress_orders)
    }

def add_to_order(parameters: dict, session_id: str):
    """Handle adding items to order"""
    food_items = parameters.get("Ethiopian-food", [])
    quantities = parameters.get("number", [])
    
    if not food_items:
        return {"fulfillmentText": "Please specify which food items you'd like to order from our menu: Doro Wat, Kitfo, Beyaynetu, Shiro Wat, Tibs, Gomen, or Firfir."}
    
    # Extend quantities if needed
    if len(food_items) > len(quantities):
        quantities.extend([1.0] * (len(food_items) - len(quantities)))
    
    new_items = dict(zip(food_items, quantities))
    
    # Add to existing order or create new one
    if session_id in inprogress_orders:
        for food, qty in new_items.items():
            inprogress_orders[session_id][food] = inprogress_orders[session_id].get(food, 0) + qty
    else:
        inprogress_orders[session_id] = new_items
    
    order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
    return {"fulfillmentText": f"Added to your cart! Current order: {order_str}. Would you like to add anything else or complete your order?"}

def remove_from_order(parameters: dict, session_id: str):
    """Handle removing items from order"""
    if session_id not in inprogress_orders:
        return {"fulfillmentText": "Your cart is empty. Say 'new order' to start ordering."}
    
    food_items = parameters.get("Ethiopian-food", [])
    if not food_items:
        return {"fulfillmentText": "Please specify which items you'd like to remove from your order."}
    
    current_order = inprogress_orders[session_id]
    removed_items = []
    
    # Remove items (case-insensitive)
    for item in food_items:
        key_to_del = next((k for k in current_order.keys() if k.lower() == item.lower()), None)
        if key_to_del:
            del current_order[key_to_del]
            removed_items.append(key_to_del)
    
    order_str = generic_helper.get_str_from_food_dict(current_order)
    if removed_items:
        res_text = f"Removed {', '.join(removed_items)} from your order."
    else:
        res_text = "I couldn't find those items in your cart."
    
    if order_str:
        return {"fulfillmentText": f"{res_text} Current order: {order_str}. Anything else?"}
    else:
        return {"fulfillmentText": f"{res_text} Your cart is now empty. Say 'new order' to start over."}

def complete_order(parameters: dict, session_id: str):
    """Handle completing an order"""
    if session_id not in inprogress_orders or not inprogress_orders[session_id]:
        return {"fulfillmentText": "Your cart is empty. Say 'new order' to start ordering delicious Ethiopian food!"}
    
    order_data = inprogress_orders[session_id]
    order_id = db_helper.get_next_order_id()
    
    # Save order to database
    if db_helper.insert_order(order_id):
        total_bill = 0
        for food, qty in order_data.items():
            item_id, price = db_helper.get_item_id_and_price(food)
            if item_id:
                item_total = price * qty
                total_bill += item_total
                db_helper.insert_order_item(order_id, item_id, int(qty), item_total)
        
        # Clear the order from memory
        del inprogress_orders[session_id]
        return {"fulfillmentText": f"Perfect! Your order has been placed. Order ID: #{order_id}. Total: {total_bill:.2f} ETB. We'll prepare your delicious Ethiopian food right away! You can track your order anytime by saying 'track order {order_id}'."}
    
    return {"fulfillmentText": "I'm sorry, there was an issue processing your order. Please try again or contact our support."}

def track_order(parameters: dict, session_id: str):
    """Handle order tracking"""
    order_id_raw = parameters.get("number")
    if isinstance(order_id_raw, list) and order_id_raw: 
        order_id_raw = order_id_raw[0]
    
    if not order_id_raw:
        return {"fulfillmentText": "Please provide your order ID number. For example, say 'track order 63321'."}
    
    try:
        order_id = int(order_id_raw)
        status = db_helper.get_order_status(order_id)
        if status:
            friendly_status = generic_helper.get_friendly_status(status)
            return {"fulfillmentText": f"Your order #{order_id} is currently {friendly_status}. Thank you for choosing our Ethiopian restaurant!"}
        return {"fulfillmentText": f"I couldn't find order #{order_id} in our system. Please check your order ID and try again."}
    except ValueError:
        return {"fulfillmentText": "Please provide a valid numeric order ID. For example, 'track order 63321'."}

def main():
    """Start the FastAPI server"""
    print("🍽️  Ethiopian Food Chatbot - FastAPI Backend Server")
    print("=" * 60)
    
    # Test database connection
    try:
        if db_helper.test_connection():
            print("✅ Database connection successful (MySQL)")
        else:
            print("❌ Database connection failed")
            return
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Check for ngrok.exe
    if os.path.exists('ngrok.exe'):
        print("✅ ngrok.exe found - ready for HTTPS tunneling")
        print(f"💡 To expose webhook publicly:")
        print(f"   1. Get free ngrok account: https://dashboard.ngrok.com/signup")
        print(f"   2. Run: .\\ngrok.exe config add-authtoken YOUR_TOKEN")
        print(f"   3. Run: .\\ngrok.exe http 8000")
        print(f"   4. Use the HTTPS URL for Dialogflow/Telegram webhook")
    else:
        print("⚠️  ngrok.exe not found - webhook will be local only")
    
    print(f"\n🚀 Starting FastAPI server...")
    print(f"📡 Webhook endpoint: http://localhost:8000")
    print(f"🔍 Health check: http://localhost:8000/health")
    print(f"📚 API docs: http://localhost:8000/docs")
    print(f"⏹️  Press Ctrl+C to stop the server")
    
    # Start FastAPI server with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()