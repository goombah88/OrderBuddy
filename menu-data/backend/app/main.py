import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx # For making HTTP requests to ASR/NLU services
import json
import io
import soundfile as sf

from backend.app.order_manager import OrderManager
from backend.app.menu_db import init_db, get_menu_data, DB_NAME

app = FastAPI()

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    # Ensure the data directory exists for SQLite DB
    os.makedirs("/app/data", exist_ok=True)
    # Initialize DB, it will create/update menu.db in /app/data
    init_db(menu_data_path="/app/menu_data/menu.json", db_path="/app/data/menu.db")
    print("Backend: Database initialized.")

# CORS configuration (important for web app frontend)
origins = [
    "http://localhost",
    "http://localhost:8001", # Frontend port
    # Replace with your server's actual IP and frontend port for Android tablet
    # "http://YOUR_SERVER_IP",
    # "http://YOUR_SERVER_IP:8001",
    # "http://192.168.1.X", # Example local network IP
    # "http://192.168.1.X:8001",
    "*" # For development, but restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instance of OrderManager
order_manager = OrderManager(db_path="/app/data/menu.db")

@app.get("/menu")
async def get_menu():
    return get_menu_data(db_path="/app/data/menu.db")

@app.post("/process_voice_command")
async def process_voice_command(request: Request, audio_file: UploadFile = File(None)):
    try:
        # Check for direct intent override from buttons
        intent_override = request.headers.get('X-Intent-Override')
        transcribed_text = ""
        nlu_result = {"intent": "unknown", "entities": []}

        if intent_override:
            nlu_result["intent"] = intent_override
            print(f"Direct intent override: {intent_override}")
        elif audio_file:
            # 1. Send audio to ASR service
            async with httpx.AsyncClient() as client:
                files = {'audio_file': (audio_file.filename, audio_file.file, audio_file.content_type)}
                asr_response = await client.post(f"{ASR_SERVICE_URL}/transcribe", files=files)
                asr_response.raise_for_status() # Raise an exception for 4xx/5xx responses
                transcribed_text = asr_response.json().get("text", "").strip()
                print(f"Transcribed: '{transcribed_text}'")

            if not transcribed_text:
                return JSONResponse(status_code=200, content={"message": "Could not transcribe audio.", "order": order_manager.get_order_summary(), "transcribed_text": ""})

            # 2. Send transcribed text to NLU service
            async with httpx.AsyncClient() as client:
                nlu_response = await client.post(f"{NLU_SERVICE_URL}/parse_command", json={"text": transcribed_text})
                nlu_response.raise_for_status()
                nlu_result = nlu_response.json()
                print(f"NLU Result: Intent={nlu_result.get('intent')}, Entities={nlu_result.get('entities', [])}")
        else:
            return JSONResponse(status_code=400, content={"message": "No audio file or intent override provided."})


        # 3. Process intent and entities with OrderManager
        feedback_message = "I didn't understand that command."
        intent = nlu_result.get("intent")
        entities = nlu_result.get("entities", [])

        if intent == "add_item":
            item_name_entity = next((e for e in entities if e['label'] == 'ITEM_NAME'), None)
            quantity_entity = next((e for e in entities if e['label'] == 'QUANTITY'), None)
            quantity = int(quantity_entity['text']) if quantity_entity and quantity_entity['text'].isdigit() else 1

            if item_name_entity:
                # Map NLU entity text to actual menu item ID
                item_name_lower = item_name_entity['text'].lower()
                actual_item_id = None
                for cat in order_manager.menu['categories']:
                    for item in cat['items']:
                        if item['id'] == item_name_lower.replace(" ", "_") or item['name'].lower() == item_name_lower:
                            actual_item_id = item['id']
                            break
                    if actual_item_id: break

                if actual_item_id:
                    # Extract options and sides from NLU entities
                    options = {}
                    sides = []
                    for entity in entities:
                        if entity['label'] == 'OPTION_TYPE' and 'value' in entity:
                            options[entity['text'].lower()] = entity['value']
                        elif entity['label'] == 'OPTION_VALUE' and 'option_type' in entity:
                            # This case is for when option_type is not separately labeled,
                            # but value is recognized. Requires more sophisticated NLU.
                            pass # For now, rely on OPTION_TYPE and its value
                        elif entity['label'] == 'SIDE':
                            sides.append(entity['text'])

                    success, msg = order_manager.add_item(actual_item_id, quantity=quantity, options=options, sides=sides)
                    feedback_message = msg
                else:
                    feedback_message = f"Sorry, I couldn't find '{item_name_entity['text']}' on the menu."
            else:
                feedback_message = "Please specify what item you'd like to add."

        elif intent == "remove_item":
            item_name_entity = next((e for e in entities if e['label'] == 'ITEM_NAME'), None)
            if item_name_entity:
                item_id_from_nlu = item_name_entity['text'].lower().replace(" ", "_")
                success, msg = order_manager.remove_item(item_id_from_nlu)
                feedback_message = msg
            else:
                feedback_message = "Please specify which item to remove."

        elif intent == "clear_order":
            success, msg = order_manager.clear_order()
            feedback_message = msg

        elif intent == "finalize_order":
            success, msg = order_manager.finalize_order()
            feedback_message = msg
            # After finalization, the order manager should clear itself
            order_manager.clear_order()

        elif intent == "query_sides":
            item_name_entity = next((e for e e in entities if e['label'] == 'ITEM_NAME'), None)
            if item_name_entity:
                item_id_from_nlu = item_name_entity['text'].lower().replace(" ", "_")
                item_details = order_manager._get_item_details(item_id_from_nlu)
                if item_details and item_details.get('available_sides'):
                    sides_list = ", ".join(item_details['available_sides'])
                    feedback_message = f"The {item_details['name']} comes with or can have sides like: {sides_list}."
                else:
                    feedback_message = f"I don't have information about sides for {item_name_entity['text']}."
            else:
                feedback_message = "Please specify an item to query sides for."

        elif intent == "query_price":
            item_name_entity = next((e for e in entities if e['label'] == 'ITEM_NAME'), None)
            if item_name_entity:
                item_id_from_nlu = item_name_entity['text'].lower().replace(" ", "_")
                item_details = order_manager._get_item_details(item_id_from_nlu)
                if item_details:
                    feedback_message = f"The {item_details['name']} costs ${item_details['price']:.2f}."
                else:
                    feedback_message = f"I couldn't find the price for {item_name_entity['text']}."
            else:
                feedback_message = "Please specify an item to query the price for."

        # Add more intent handling here (e.g., modify_item, add_topping etc.)

        return {"message": feedback_message, "order": order_manager.get_order_summary(), "transcribed_text": transcribed_text}

    except httpx.HTTPStatusError as e:
        print(f"HTTP error with ASR/NLU service: {e.response.status_code} - {e.response.text}")
        return JSONResponse(status_code=500, content={"message": f"Backend service error: {e.response.text}"})
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JSONResponse(status_code=500, content={"message": f"An internal server error occurred: {e}"})

@app.get("/health")
async def health_check():
    return {"status": "ok"}
