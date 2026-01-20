# Habesha Bites: Ethiopian Food Ordering & Tracking Chatbot

## Project Overview
My 3rd project from future Interns 
Habesha Bites is an AI-powered Virtual Assistant designed to automate the food ordering process for an Ethiopian restaurant. The bot handles end-to-end customer interactions, 
from greeting users and taking orders for traditional dishes (like Doro Wat and Kitfo) to providing real-time order status tracking.

## Features
- [cite_start]**Intent Recognition:** Understands user goals such as "New Order," "Add Item," and "Track Order"[cite: 1, 15].
- [cite_start]**Custom Entities:** Specifically trained to recognize Ethiopian cuisine and quantities[cite: 6, 11].
- [cite_start]**Order Tracking:** Integrated with a backend database to provide live status updates using unique Order IDs[cite: 16, 17].
- [cite_start]**Error Handling:** Robust fallback intent to guide users back to the menu if they mention unavailable items[cite: 5].

## Tech Stack
- **Dialogflow:** NLP engine for intent classification and conversation flow.
- **Python (FastAPI/Flask):** Backend webhook for database interaction.
- **MySQL:** Relational database for storing menu items and order history.
- **Streamlit:** Interactive web interface for the chatbot UI.

## Database Schema
The project utilizes a relational schema including:
- `food_items`: Stores names and prices.
- `orders`: Stores order status (In Progress, Delivered, etc.).
- `order_details`: Links orders to specific items and quantities.
