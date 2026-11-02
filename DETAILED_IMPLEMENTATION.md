Detailed Implementation Steps
Phase 1: Menu Data Management
Define Your Menu (menu_data/menu.json):
This is the source of truth for your system. Be meticulous.

JSON
￼
{
  "categories": [
    {
      "name": "Burgers",
      "items": [
        {
          "id": "classic_burger",
          "name": "Classic Burger",
          "price": 10.99,
          "description": "Beef patty, lettuce, tomato, onion, pickles.",
          "options": {
            "cheese": ["Cheddar", "Swiss", "Provolone"],
            "toppings": ["Bacon", "Mushrooms", "Jalapenos"],
            "bread": ["Brioche Bun", "Sesame Seed Bun", "Lettuce Wrap"]
          },
          "default_sides": ["Fries"],
          "available_sides": ["Fries", "Onion Rings", "Side Salad"]
        },
        {
          "id": "veggie_burger",
          "name": "Veggie Burger",
          "price": 9.99,
          "description": "Black bean patty, avocado, sprouts.",
          "options": {
            "cheese": ["Cheddar", "Vegan Cheese"],
            "bread": ["Brioche Bun", "Whole Wheat Bun"]
          },
          "default_sides": ["Side Salad"],
          "available_sides": ["Fries", "Onion Rings", "Side Salad"]
        }
      ]
    },
    {
      "name": "Drinks",
      "items": [
        {"id": "coke", "name": "Coke", "price": 2.50},
        {"id": "sprite", "name": "Sprite", "price": 2.50}
      ]
    }
  ]
}
SQLite Database (backend/app/menu_db.py):
A Python script to load menu.json into an SQLite database (e.g., menu.db). This makes querying efficient for the backend.

Python
￼
# backend/app/menu_db.py
import sqlite3
import json

DB_NAME = "menu.db"

def init_db(menu_data_path="menu_data/menu.json"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY,
            category_id INTEGER,
            name TEXT,
            price REAL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_options (
            item_id TEXT,
            option_type TEXT,
            option_value TEXT,
            PRIMARY KEY (item_id, option_type, option_value),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_sides (
            item_id TEXT,
            side_name TEXT,
            is_default INTEGER, -- 1 for default, 0 for available
            PRIMARY KEY (item_id, side_name),
            FOREIGN KEY (item_id) REFERENCES items(id)
        )
    ''')

    # Load data from JSON
    with open(menu_data_path, 'r') as f:
        menu = json.load(f)

    for category in menu['categories']:
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (category['name'],))
        category_id = cursor.execute("SELECT id FROM categories WHERE name = ?", (category['name'],)).fetchone()[0]

        for item in category['items']:
            cursor.execute("INSERT OR IGNORE INTO items (id, category_id, name, price, description) VALUES (?, ?, ?, ?, ?)",
                           (item['id'], category_id, item['name'], item['price'], item.get('description', '')))

            for option_type, values in item.get('options', {}).items():
                for value in values:
                    cursor.execute("INSERT OR IGNORE INTO item_options (item_id, option_type, option_value) VALUES (?, ?, ?)",
                                   (item['id'], option_type, value))

            for side in item.get('default_sides', []):
                cursor.execute("INSERT OR IGNORE INTO item_sides (item_id, side_name, is_default) VALUES (?, ?, ?)",
                               (item['id'], side, 1))
            for side in item.get('available_sides', []):
                cursor.execute("INSERT OR IGNORE INTO item_sides (item_id, side_name, is_default) VALUES (?, ?, ?)",
                               (item['id'], side, 0)) # Mark as available, not default

    conn.commit()
    conn.close()

def get_menu_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Return rows as dict-like objects
    cursor = conn.cursor()

    menu = {"categories": []}
    categories = cursor.execute("SELECT id, name FROM categories").fetchall()

    for cat_row in categories:
        category = {"name": cat_row['name'], "items": []}
        items = cursor.execute("SELECT id, name, price, description FROM items WHERE category_id = ?", (cat_row['id'],)).fetchall()

        for item_row in items:
            item = {
                "id": item_row['id'],
                "name": item_row['name'],
                "price": item_row['price'],
                "description": item_row['description'],
                "options": {},
                "default_sides": [],
                "available_sides": []
            }

            options = cursor.execute("SELECT option_type, option_value FROM item_options WHERE item_id = ?", (item_row['id'],)).fetchall()
            for opt_row in options:
                item['options'].setdefault(opt_row['option_type'], []).append(opt_row['option_value'])

            sides = cursor.execute("SELECT side_name, is_default FROM item_sides WHERE item_id = ?", (item_row['id'],)).fetchall()
            for side_row in sides:
                if side_row['is_default']:
                    item['default_sides'].append(side_row['side_name'])
                item['available_sides'].append(side_row['side_name'])

            category['items'].append(item)
        menu['categories'].append(category)

    conn.close()
    return menu

if __name__ == "__main__":
    # Run this once to initialize the database
    init_db()
    print("Database initialized with menu data.")
    # You can test by printing the retrieved menu
    # print(json.dumps(get_menu_data(), indent=2))
Phase 2: Natural Language Understanding (NLU) - SpaCy
This is the most critical AI component for understanding user intent.

Training Data (nlu_service/training_data/):
Create a JSON file (e.g., nlu_training_data.json) with examples. This is crucial for your model's accuracy.

JSON
￼
[
  {"text": "I want a classic burger", "entities": [{"start": 10, "end": 24, "label": "ITEM_NAME", "item_id": "classic_burger"}], "intent": "add_item"},
  {"text": "Can I get the veggie burger with Swiss cheese", "entities": [{"start": 13, "end": 26, "label": "ITEM_NAME", "item_id": "veggie_burger"}, {"start": 32, "end": 37, "label": "OPTION_TYPE", "value": "cheese"}, {"start": 38, "end": 43, "label": "OPTION_VALUE", "value": "Swiss"}], "intent": "add_item"},
  {"text": "Add bacon to my burger", "entities": [{"start": 4, "end": 9, "label": "TOPPING", "value": "Bacon"}, {"start": 16, "end": 22, "label": "ITEM_TYPE", "value": "burger"}], "intent": "add_topping"},
  {"text": "What sides come with the classic burger", "entities": [{"start": 23, "end": 37, "label": "ITEM_NAME", "item_id": "classic_burger"}], "intent": "query_sides"},
  {"text": "Change my burger to a lettuce wrap", "entities": [{"start": 10, "end": 16, "label": "ITEM_TYPE", "value": "burger"}, {"start": 23, "end": 34, "label": "BREAD", "value": "Lettuce Wrap"}], "intent": "modify_item"},
  {"text": "Remove the coke", "entities": [{"start": 11, "end": 15, "label": "ITEM_NAME", "item_id": "coke"}], "intent": "remove_item"},
  {"text": "I'm done ordering", "intent": "finalize_order"},
  {"text": "How much is a classic burger", "entities": [{"start": 14, "end": 28, "label": "ITEM_NAME", "item_id": "classic_burger"}], "intent": "query_price"},
  {"text": "I'll take two cokes", "entities": [{"start": 11, "end": 16, "label": "ITEM_NAME", "item_id": "coke"}, {"start": 7, "end": 10, "label": "QUANTITY", "value": "2"}], "intent": "add_item"}
]
Note: The item_id and value fields in entities are crucial for linking to your menu.json. This requires mapping spoken phrases (e.g., "classic burger") to their id in your menu data.

SpaCy Model Training Script (nlu_service/train_nlu.py):

Python
￼
# nlu_service/train_nlu.py
import spacy
import json
import random
from spacy.tokens import DocBin
from pathlib import Path

def train_spacy_model(training_data_path, model_output_path, n_iter=20):
    # Load blank English model
    nlp = spacy.blank("en")

    # Add a text categorizer for intent classification
    textcat = nlp.add_pipe("textcat_multilabel", last=True)
    textcat.add_label("add_item")
    textcat.add_label("modify_item")
    textcat.add_label("remove_item")
    textcat.add_label("query_sides")
    textcat.add_label("query_price")
    textcat.add_label("finalize_order")
    textcat.add_label("add_topping") # Add other intents as needed

    # Add a Named Entity Recognizer (NER)
    ner = nlp.add_pipe("ner", last=True)
    ner.add_label("ITEM_NAME")
    ner.add_label("ITEM_TYPE") # e.g., "burger" when specific item name isn't given
    ner.add_label("OPTION_TYPE")
    ner.add_label("OPTION_VALUE")
    ner.add_label("TOPPING")
    ner.add_label("BREAD") # Example of a specific option type
    ner.add_label("QUANTITY") # For "two cokes"

    # Load training data
    with open(training_data_path, 'r') as f:
        TRAIN_DATA = json.load(f)

    # Convert training data to SpaCy's DocBin format
    db = DocBin()
    for text_data in TRAIN_DATA:
        doc = nlp.make_doc(text_data["text"])
        # Add entities
        ents = []
        for ent in text_data.get("entities", []):
            span = doc.char_span(ent["start"], ent["end"], label=ent["label"])
            if span is not None:
                ents.append(span)
        doc.ents = ents

        # Add textcat labels
        cats = {label: 0.0 for label in textcat.labels}
        if "intent" in text_data:
            cats[text_data["intent"]] = 1.0
        doc.cats = cats
        db.add(doc)

    db.to_disk(f"{model_output_path}/train.spacy")

    # Train the model
    # You'd typically use `spacy train` CLI for this, which uses a config file.
    # For simplicity in this example, we'll show a basic in-script training loop.
    # For production, generate a config with `spacy init config` and use `spacy train`.

    # Disable other pipes for training NER and textcat
    pipe_exceptions = ["ner", "textcat_multilabel"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    with nlp.disable_pipes(*other_pipes):  # only train NER and textcat
        optimizer = nlp.begin_training()
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text_data in TRAIN_DATA:
                doc = nlp.make_doc(text_data["text"])
                example = spacy.training.Example(doc, nlp(text_data["text"])) # Create example
                # Ensure entities are correctly aligned
                example.reference.ents = [
                    doc.char_span(ent["start"], ent["end"], label=ent["label"])
                    for ent in text_data.get("entities", [])
                    if doc.char_span(ent["start"], ent["end"], label=ent["label"]) is not None
                ]
                # Ensure textcat labels are correctly set
                example.reference.cats = {label: (1.0 if text_data.get("intent") == label else 0.0) for label in textcat.labels}

                nlp.update([example], drop=0.5, losses=losses)
            print(f"Losses at iteration {itn}: {losses}")

    # Save the trained model
    nlp.to_disk(model_output_path)
    print(f"Trained SpaCy model saved to {model_output_path}")

if __name__ == "__main__":
    # Create output directory for the model
    output_dir = Path("trained_nlu_model")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy training data file for demonstration
    dummy_data_path = Path("training_data/nlu_training_data.json")
    dummy_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dummy_data_path, "w") as f:
        json.dump([
            {"text": "I want a classic burger", "entities": [{"start": 10, "end": 24, "label": "ITEM_NAME"}], "intent": "add_item"},
            {"text": "Add a coke", "entities": [{"start": 6, "end": 10, "label": "ITEM_NAME"}], "intent": "add_item"},
            {"text": "Veggie burger with cheddar", "entities": [{"start": 0, "end": 13, "label": "ITEM_NAME"}, {"start": 19, "end": 26, "label": "OPTION_VALUE"}], "intent": "add_item"},
            {"text": "Remove the sprite", "entities": [{"start": 11, "end": 17, "label": "ITEM_NAME"}], "intent": "remove_item"},
            {"text": "What sides for classic burger", "entities": [{"start": 16, "end": 30, "label": "ITEM_NAME"}], "intent": "query_sides"},
            {"text": "How much is the veggie burger", "entities": [{"start": 15, "end": 28, "label": "ITEM_NAME"}], "intent": "query_price"},
            {"text": "I'm done", "intent": "finalize_order"}
        ], f, indent=2)

    train_spacy_model(str(dummy_data_path), str(output_dir))
Note: For real-world training, you'd use spacy init config to generate a config.cfg file and then spacy train config.cfg --paths.train train.spacy --paths.dev dev.spacy for more robust training. The in-script training above is a simplified example.

NLU Inference API (nlu_service/app/nlu_api.py):

Python
￼
# nlu_service/app/nlu_api.py
from fastapi import FastAPI
from pydantic import BaseModel
import spacy
from pathlib import Path

app = FastAPI()

# Load the trained SpaCy model
try:
    nlu_model_path = Path("/app/trained_nlu_model") # Path inside Docker container
    nlp = spacy.load(nlu_model_path)
    print(f"SpaCy model loaded from {nlu_model_path}")
except Exception as e:
    print(f"Error loading SpaCy model: {e}")
    print("Ensure the model is trained and copied to /app/trained_nlu_model in the Docker image.")
    nlp = None # Handle case where model fails to load

class TextCommand(BaseModel):
    text: str

@app.post("/parse_command")
async def parse_command(command: TextCommand):
    if nlp is None:
        return {"error": "NLU model not loaded"}, 500

    doc = nlp(command.text)

    # Extract intent (from textcat)
    intent = max(doc.cats, key=doc.cats.get) if doc.cats else "unknown"
    # You might want a confidence threshold here

    # Extract entities (from NER)
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_})

    # For more advanced NLU, you'd map these entities to your menu IDs
    # This mapping logic would live in the backend/app/order_manager.py or similar.

    return {"text": command.text, "intent": intent, "entities": entities}

@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": nlp is not None}
Phase 3: Speech Recognition (ASR) - Whisper
ASR Inference API (asr_service/app/asr_api.py):

Python
￼
# asr_service/app/asr_api.py
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from transformers import pipeline
import torch
import os
import io
import soundfile as sf

app = FastAPI()

# Define model path within the Docker container
WHISPER_MODEL_NAME = "openai/whisper-tiny" # Or "base", "small" etc.
# Check for GPU
device = 0 if torch.cuda.is_available() else -1

# Load Whisper model
try:
    # Pipeline will download model to ~/.cache/huggingface/transformers by default
    # which will be persistent inside the Docker volume if configured.
    asr_pipeline = pipeline("automatic-speech-recognition", model=WHISPER_MODEL_NAME, device=device)
    print(f"Whisper model '{WHISPER_MODEL_NAME}' loaded on device: {'cuda' if device == 0 else 'cpu'}")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    asr_pipeline = None

@app.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    if asr_pipeline is None:
        return JSONResponse(status_code=500, content={"message": "ASR model not loaded"})

    try:
        # Read audio data from the uploaded file
        audio_bytes = await audio_file.read()

        # Convert to a format soundfile can read (e.g., WAV)
        # Assuming input is already compatible or can be easily converted client-side
        # For robust handling, you might need ffmpeg in the Docker image
        # and use pydub to convert to a common format.
        # For simplicity, let's assume WAV or a format soundfile directly supports.
        audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))

        # Transcribe
        # The pipeline expects a NumPy array or a path to an audio file
        transcription = asr_pipeline(audio_data)

        return {"text": transcription["text"]}
    except Exception as e:
        print(f"Transcription error: {e}")
        return JSONResponse(status_code=500, content={"message": f"Error during transcription: {e}"})

@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": asr_pipeline is not None}
Note on Whisper Model Download: The pipeline will download the model weights on first run. For Docker, you'll want to ensure these are downloaded during the Docker build or mounted via a volume to avoid re-downloading.

Phase 4: Backend API (FastAPI) - Orchestrator & Order Manager
This is the central hub.

Order Manager Logic (backend/app/order_manager.py):
This will manage the state of the current order.

Python
￼
# backend/app/order_manager.py
import sqlite3
import json
from backend.app.menu_db import DB_NAME, get_menu_data # Assuming menu_db is in the same folder

class OrderManager:
    def __init__(self):
        self.current_order = [] # List of dicts: {"item_id": "...", "quantity": 1, "options": {}, "sides": []}
        self.menu = get_menu_data() # Load menu from DB

    def _get_item_details(self, item_id):
        for category in self.menu['categories']:
            for item in category['items']:
                if item['id'] == item_id:
                    return item
        return None

    def add_item(self, item_id, quantity=1, options=None, sides=None):
        item_details = self._get_item_details(item_id)
        if not item_details:
            return False, "Item not found."

        new_item = {
            "item_id": item_id,
            "name": item_details['name'],
            "price": item_details['price'],
            "quantity": quantity,
            "options": options if options else {},
            "sides": sides if sides else item_details.get('default_sides', [])
        }
        self.current_order.append(new_item)
        return True, f"Added {quantity} {item_details['name']} to order."

    def remove_item(self, item_id):
        initial_len = len(self.current_order)
        self.current_order = [item for item in self.current_order if item["item_id"] != item_id]
        if len(self.current_order) < initial_len:
            return True, f"Removed {item_id} from order."
        return False, "Item not found in order."

    def get_order_summary(self):
        total_price = sum(item['price'] * item['quantity'] for item in self.current_order)
        return {
            "items": self.current_order,
            "total": round(total_price, 2)
        }

    def clear_order(self):
        self.current_order = []
        return True, "Order cleared."

    def finalize_order(self):
        if not self.current_order:
            return False, "Order is empty."
        # In a real system, this would save to a persistent order history,
        # send to kitchen, etc. For now, just clear.
        summary = self.get_order_summary()
        self.clear_order()
        return True, f"Order finalized. Total: ${summary['total']:.2f}. Thank you!"

Backend Main API (backend/app/main.py):

Python
￼
# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
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
    init_db(menu_data_path="/app/menu_data/menu.json") # Path inside Docker
    print("Backend: Database initialized.")

# CORS configuration (important for web app frontend)
origins = [
    "http://localhost",
    "http://localhost:8001", # Frontend port
    "http://YOUR_SERVER_IP", # Replace with your server's IP
    "http://YOUR_SERVER_IP:8001", # Replace with your server's IP and frontend port
    "http://192.168.1.X", # Example local network IP
    "http://192.168.1.X:8001",
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
order_manager = OrderManager()

# --- ASR & NLU Service URLs (if running as separate Docker containers) ---
ASR_SERVICE_URL = os.getenv("ASR_SERVICE_URL", "http://asr_service:8000")
NLU_SERVICE_URL = os.getenv("NLU_SERVICE_URL", "http://nlu_service:8000")

@app.get("/menu")
async def get_menu():
    return get_menu_data()

@app.post("/process_voice_command")
async def process_voice_command(audio_file: UploadFile = File(...)):
    try:
        # 1. Send audio to ASR service
        async with httpx.AsyncClient() as client:
            files = {'audio_file': (audio_file.filename, audio_file.file, audio_file.content_type)}
            asr_response = await client.post(f"{ASR_SERVICE_URL}/transcribe", files=files)
            asr_response.raise_for_status() # Raise an exception for 4xx/5xx responses
            transcribed_text = asr_response.json().get("text", "")
            print(f"Transcribed: {transcribed_text}")

        if not transcribed_text:
            return JSONResponse(status_code=200, content={"message": "Could not transcribe audio.", "order": order_manager.get_order_summary()})

        # 2. Send transcribed text to NLU service
        async with httpx.AsyncClient() as client:
            nlu_response = await client.post(f"{NLU_SERVICE_URL}/parse_command", json={"text": transcribed_text})
            nlu_response.raise_for_status()
            nlu_result = nlu_response.json()
            intent = nlu_result.get("intent")
            entities = nlu_result.get("entities", [])
            print(f"NLU Result: Intent={intent}, Entities={entities}")

        # 3. Process intent and entities with OrderManager
        feedback_message = "I didn't understand that command."
        if intent == "add_item":
            item_name_entity = next((e for e in entities if e['label'] == 'ITEM_NAME'), None)
            quantity_entity = next((e for e in entities if e['label'] == 'QUANTITY'), None)
            quantity = int(quantity_entity['text']) if quantity_entity and quantity_entity['text'].isdigit() else 1

            if item_name_entity:
                # In a real system, you'd map item_name_entity['text'] to actual item_id from your menu
                # For simplicity, let's assume item_name_entity['text'] is directly the item_id
                # You'd need a more robust mapping here (e.g., fuzzy matching, lookup table)
                item_id_from_nlu = item_name_entity['text'].lower().replace(" ", "_") # Simple mapping

                # Find the actual item ID from the menu data for validation
                actual_item_id = None
                for cat in order_manager.menu['categories']:
                    for item in cat['items']:
                        if item['id'] == item_id_from_nlu or item['name'].lower() == item_name_entity['text'].lower():
                            actual_item_id = item['id']
                            break
                    if actual_item_id: break

                if actual_item_id:
                    success, msg = order_manager.add_item(actual_item_id, quantity=quantity)
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
            # You might want to clear the order manager after finalization
            order_manager.clear_order()

        elif intent == "query_sides":
            item_name_entity = next((e for e in entities if e['label'] == 'ITEM_NAME'), None)
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


        # Add more intent handling here (e.g., modify_item, query_price, etc.)

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
Phase 5: Frontend Web App (HTML/CSS/JavaScript)
This will run in the Android tablet's browser.

HTML Structure (frontend/index.html):

HTML
￼
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voice Order System</title>
    <link rel="stylesheet" href="style.css">
    <!-- Tailwind CSS CDN for quick styling -->
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="container bg-white rounded-lg shadow-xl p-6 md:p-8 w-full max-w-4xl">
        <h1 class="text-3xl font-bold text-center text-gray-800 mb-6">Voice Order System</h1>

        <div class="flex flex-col md:flex-row gap-6">
            <!-- Menu Display -->
            <div class="md:w-1/2 bg-gray-50 p-4 rounded-md shadow-inner overflow-y-auto max-h-[60vh]">
                <h2 class="text-2xl font-semibold text-gray-700 mb-4">Menu</h2>
                <div id="menu-display" class="space-y-4">
                    <!-- Menu items will be loaded here by JavaScript -->
                    <p class="text-gray-500">Loading menu...</p>
                </div>
            </div>

            <!-- Order & Voice Control -->
            <div class="md:w-1/2 flex flex-col">
                <div class="bg-blue-50 p-4 rounded-md shadow-inner mb-6 flex-grow">
                    <h2 class="text-2xl font-semibold text-gray-700 mb-4">Current Order</h2>
                    <div id="order-display" class="space-y-2 text-gray-800">
                        <p>No items in order.</p>
                    </div>
                    <p class="text-xl font-bold text-gray-900 mt-4">Total: $<span id="order-total">0.00</span></p>
                </div>

                <div class="flex flex-col items-center p-4 bg-purple-50 rounded-md shadow-inner">
                    <button id="recordButton" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-8 rounded-full shadow-lg transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-blue-300 mb-4">
                        Start Recording
                    </button>
                    <p id="status" class="text-gray-700 text-lg mb-2">Press button to start.</p>
                    <p id="transcribedText" class="text-gray-600 italic text-center mb-4">Transcribed: ...</p>

                    <div class="flex space-x-4 w-full justify-center">
                        <button id="clearOrderButton" class="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg shadow-md transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-red-300">
                            Clear Order
                        </button>
                        <button id="finalizeOrderButton" class="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg shadow-md transition duration-300 ease-in-out transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-green-300">
                            Finalize Order
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>
CSS (Optional, using Tailwind mostly) (frontend/style.css):
You can add custom CSS here if Tailwind isn't enough, but for a quick prototype, Tailwind is very efficient.

CSS
￼
/* frontend/style.css */
/* Add any custom styles here if needed, otherwise Tailwind handles most of it */
.container {
    min-height: 80vh; /* Adjust as needed */
}
JavaScript Logic (frontend/script.js):

JavaScript
￼
// frontend/script.js

const recordButton = document.getElementById('recordButton');
const statusDisplay = document.getElementById('status');
const transcribedTextDisplay = document.getElementById('transcribedText');
const menuDisplay = document.getElementById('menu-display');
const orderDisplay = document.getElementById('order-display');
const orderTotalDisplay = document.getElementById('order-total');
const clearOrderButton = document.getElementById('clearOrderButton');
const finalizeOrderButton = document.getElementById('finalizeOrderButton');

let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// --- Configuration ---
const BACKEND_URL = 'http://YOUR_SERVER_IP:8000'; // <<< IMPORTANT: Replace with your server's IP and port

// --- UI Update Functions ---
async function updateMenuDisplay() {
    try {
        const response = await fetch(`${BACKEND_URL}/menu`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const menu = await response.json();

        menuDisplay.innerHTML = ''; // Clear previous menu
        menu.categories.forEach(category => {
            const categoryDiv = document.createElement('div');
            categoryDiv.className = 'mb-4';
            categoryDiv.innerHTML = `<h3 class="text-xl font-semibold text-blue-700">${category.name}</h3>`;
            const itemList = document.createElement('ul');
            itemList.className = 'list-disc list-inside ml-4';
            category.items.forEach(item => {
                const itemLi = document.createElement('li');
                itemLi.className = 'text-gray-700';
                let itemText = `${item.name} ($${item.price.toFixed(2)})`;
                if (item.description) itemText += `: ${item.description}`;
                if (Object.keys(item.options).length > 0) {
                    itemText += ` (Options: ${Object.keys(item.options).map(opt => `${opt}: ${item.options[opt].join(', ')}`).join('; ')})`;
                }
                if (item.available_sides && item.available_sides.length > 0) {
                    itemText += ` [Sides: ${item.available_sides.join(', ')}]`;
                }
                itemLi.textContent = itemText;
                itemList.appendChild(itemLi);
            });
            categoryDiv.appendChild(itemList);
            menuDisplay.appendChild(categoryDiv);
        });
    } catch (error) {
        console.error('Error fetching menu:', error);
        menuDisplay.innerHTML = '<p class="text-red-500">Failed to load menu. Please check server connection.</p>';
    }
}

function updateOrderDisplay(orderSummary) {
    if (!orderSummary || orderSummary.items.length === 0) {
        orderDisplay.innerHTML = '<p>No items in order.</p>';
        orderTotalDisplay.textContent = '0.00';
        return;
    }

    orderDisplay.innerHTML = '';
    orderSummary.items.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'flex justify-between items-center bg-gray-100 p-2 rounded-md';
        let itemDetails = `${item.quantity}x ${item.name}`;
        if (Object.keys(item.options).length > 0) {
            itemDetails += ` (${Object.keys(item.options).map(opt => `${opt}: ${item.options[opt]}`).join(', ')})`;
        }
        if (item.sides && item.sides.length > 0) {
            itemDetails += ` [${item.sides.join(', ')}]`;
        }
        itemDiv.innerHTML = `
            <span>${itemDetails}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
        `;
        orderDisplay.appendChild(itemDiv);
    });
    orderTotalDisplay.textContent = orderSummary.total.toFixed(2);
}

// --- Voice Recording Logic ---
recordButton.onclick = async () => {
    if (!isRecording) {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' }); // Use webm for broader browser support
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                statusDisplay.textContent = 'Sending to server...';
                transcribedTextDisplay.textContent = 'Transcribed: ...';
                recordButton.textContent = 'Start Recording';
                recordButton.classList.remove('bg-red-600', 'hover:bg-red-700');
                recordButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
                isRecording = false;

                try {
                    const formData = new FormData();
                    formData.append('audio_file', audioBlob, 'audio.webm');

                    const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
                        method: 'POST',
                        body: formData,
                    });

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(`Server error: ${response.status} - ${errorData.message || response.statusText}`);
                    }

                    const result = await response.json();
                    statusDisplay.textContent = result.message || 'Command processed.';
                    transcribedTextDisplay.textContent = `Transcribed: "${result.transcribed_text || 'N/A'}"`;
                    updateOrderDisplay(result.order);

                } catch (error) {
                    console.error('Error processing voice command:', error);
                    statusDisplay.textContent = `Error: ${error.message}`;
                    transcribedTextDisplay.textContent = 'Transcribed: (Error)';
                }
            };

            mediaRecorder.start();
            statusDisplay.textContent = 'Recording... Speak now!';
            recordButton.textContent = 'Stop Recording';
            recordButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
            recordButton.classList.add('bg-red-600', 'hover:bg-red-700');
            isRecording = true;

        } catch (err) {
            console.error('Error accessing microphone:', err);
            statusDisplay.textContent = 'Error: Microphone access denied or not available.';
        }
    } else {
        mediaRecorder.stop();
    }
};

// --- Button Actions ---
clearOrderButton.onclick = async () => {
    try {
        const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
            method: 'POST',
            body: new FormData(), // Send empty audio to trigger clear_order intent if NLU supports it
            headers: { 'X-Intent-Override': 'clear_order' } // Custom header for direct intent if needed
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();
        statusDisplay.textContent = result.message;
        updateOrderDisplay(result.order);
    } catch (error) {
        console.error('Error clearing order:', error);
        statusDisplay.textContent = `Error: ${error.message}`;
    }
};

finalizeOrderButton.onclick = async () => {
    try {
        const response = await fetch(`${BACKEND_URL}/process_voice_command`, {
            method: 'POST',
            body: new FormData(), // Send empty audio
            headers: { 'X-Intent-Override': 'finalize_order' } // Custom header for direct intent
        });
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const result = await response.json();
        statusDisplay.textContent = result.message;
        updateOrderDisplay(result.order); // Order should be cleared after finalization
    } catch (error) {
        console.error('Error finalizing order:', error);
        statusDisplay.textContent = `Error: ${error.message}`;
    }
};


// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    updateMenuDisplay();
    updateOrderDisplay({ items: [], total: 0 }); // Initialize empty order display
});
Note on X-Intent-Override: For clear_order and finalize_order buttons, I've added a custom header. You'd need to modify your FastAPI process_voice_command endpoint to check for this header and directly trigger the intent, bypassing ASR/NLU for these specific button actions. This makes the buttons reliable.

audio/webm: This is generally a good choice for MediaRecorder as it's widely supported and efficient. Ensure your ASR backend can handle it.

Phase 6: Dockerization & Orchestration
This is where Docker Compose brings it all together.

Backend Dockerfile (backend/Dockerfile):

Dockerfile
￼
# backend/Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

# Copy menu data
COPY menu_data/menu.json /app/menu_data/menu.json

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Initialize SQLite DB (run once during build)
COPY backend/app/menu_db.py /app/menu_db.py
RUN python /app/menu_db.py

# Copy trained NLU model
# This directory must exist and contain your trained SpaCy model
COPY backend/trained_nlu_model/ /app/trained_nlu_model/

# Copy application code
COPY backend/app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
backend/requirements.txt:

fastapi
uvicorn
python-multipart
httpx
# No spacy or transformers here, as they are separate services
ASR Service Dockerfile (asr_service/Dockerfile):

Dockerfile
￼
# asr_service/Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

# Install system dependencies for soundfile (if needed)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY asr_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY asr_service/app/ .

# Pre-download Whisper model during build (optional, but avoids runtime download)
# This will download to /root/.cache/huggingface/transformers
# You might want to mount a volume for models in production to persist them.
ENV HF_HOME /app/hf_cache
RUN mkdir -p $HF_HOME
RUN python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-tiny')"

CMD ["uvicorn", "asr_api:app", "--host", "0.0.0.0", "--port", "8000"]
asr_service/requirements.txt:

fastapi
uvicorn
transformers
torch # Or torch==<version>+cpu -f https://download.pytorch.org/whl/torch_stable.html
soundfile
# pydub # if you need robust audio format conversion
GPU Support: If you have a GPU, change FROM to a CUDA-enabled base image (e.g., nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04) and install pytorch with CUDA support.

NLU Service Dockerfile (nlu_service/Dockerfile):

Dockerfile
￼
# nlu_service/Dockerfile
FROM python:3.9-slim-buster

WORKDIR /app

# Install Python dependencies
COPY nlu_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy English model (needed for blank("en"))
RUN python -m spacy download en_core_web_sm # Or just "en" if blank is sufficient

# Copy trained NLU model
# This directory must exist and contain your trained SpaCy model
COPY backend/trained_nlu_model/ /app/trained_nlu_model/

# Copy application code
COPY nlu_service/app/ .

CMD ["uvicorn", "nlu_api:app", "--host", "0.0.0.0", "--port", "8000"]
nlu_service/requirements.txt:

fastapi
uvicorn
spacy
# If using transformers for NLU:
# transformers
# torch
# datasets
Frontend Dockerfile (Optional, but good for serving):

Dockerfile
￼
# frontend/Dockerfile
FROM nginx:alpine

COPY frontend/ /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
Docker Compose (docker-compose.yml):

YAML
￼
version: '3.8'

services:
  asr_service:
    build:
      context: .
      dockerfile: asr_service/Dockerfile
    ports:
      - "8002:8000" # Expose ASR service on port 8002 (or adjust as needed)
    environment:
      - HF_HOME=/app/hf_cache # Ensure model cache is within the container
    volumes:
      - ./asr_service/models:/app/hf_cache # Persist downloaded Whisper models
    deploy:
      resources:
        reservations:
          devices: # Example for GPU passthrough (NVIDIA)
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped

  nlu_service:
    build:
      context: .
      dockerfile: nlu_service/Dockerfile
    ports:
      - "8003:8000" # Expose NLU service on port 8003
    volumes:
      - ./backend/trained_nlu_model:/app/trained_nlu_model:ro # Mount trained model
    restart: unless-stopped

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000" # Main backend API on port 8000
    volumes:
      - ./menu_data:/app/menu_data:ro # Mount menu JSON
      - ./data:/app/data # For SQLite DB persistence (create a 'data' folder)
      - ./backend/trained_nlu_model:/app/trained_nlu_model:ro # Mount trained model
    environment:
      - ASR_SERVICE_URL=http://asr_service:8000 # Internal Docker network names
      - NLU_SERVICE_URL=http://nlu_service:8000
    depends_on:
      - asr_service
      - nlu_service
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile
    ports:
      - "8001:80" # Frontend web server on port 8001
    depends_on:
      - backend
    restart: unless-stopped
Volumes: Crucial for persisting data (SQLite DB, downloaded Whisper models) and mounting your trained NLU model. Create a data folder in your project root for the SQLite DB.

depends_on: Ensures services start in the correct order.

ports: Maps container ports to host ports. Adjust as needed.

Deployment & Usage
Prepare your environment:

Install Docker and Docker Compose on your Linux server.

Create the project directory structure.

Populate menu_data/menu.json with your actual menu.

Create your NLU training data (nlu_service/training_data/nlu_training_data.json).

Train your NLU model:

Bash
￼
cd nlu_service
python train_nlu.py
# This will create the 'trained_nlu_model' directory in your nlu_service folder.
# You then need to copy it to the backend folder as well for the backend service to access it.
# cp -r trained_nlu_model ../backend/
Self-correction: The trained_nlu_model should ideally be mounted to both NLU and Backend services if NLU is a separate service. If NLU is bundled into backend, then only backend needs it. For this microservice setup, NLU service loads it, and Backend service needs it for its own logic/validation. Let's adjust the Dockerfiles/compose to reflect this, having trained_nlu_model in the backend directory and mounted to nlu_service as well.

Build and Run with Docker Compose:
Navigate to the root of your restaurant-ordering-system project (where docker-compose.yml is).

Bash
￼
docker-compose build
docker-compose up -d
build: Builds the Docker images for each service. This will download Whisper models, install dependencies, and run the SpaCy training (if train_nlu.py is called in the NLU Dockerfile, or you do it manually beforehand and copy the model).

up -d: Starts all services in detached mode.

Access from Android Tablet:

Find your Linux server's IP address (e.g., ip a or hostname -I).

Open a web browser on your Android tablet.

Navigate to http://YOUR_SERVER_IP:8001 (replace YOUR_SERVER_IP with your server's actual IP).

Further Enhancements & Considerations:
Error Handling & User Feedback: Improve the message responses from the backend to be more user-friendly and actionable.

Context Management: The OrderManager is stateless between voice commands. For "add cheese to that burger" (referring to the last item added), you'd need to add session management and context tracking to the OrderManager.

Robust NLU Mapping: The simple item_name_entity['text'].lower().replace(" ", "_") mapping is fragile. For production, you'd use a more sophisticated lookup that matches entities from the NLU output to your actual menu.json IDs, potentially with fuzzy matching.

Quantity Parsing: Enhance NLU to parse quantities like "a couple," "a few," "one," "two," etc.

Advanced Options/Sides: Extend the NLU and order logic to handle complex option selections (e.g., "extra cheese," "no onions," "substitute fries for a salad").

Persistent Order History: Implement saving finalized orders to the SQLite DB or another database.

Kitchen Display System (KDS) Integration: For a real restaurant, you'd integrate with a KDS or printer.

Security: If exposing to the internet, implement HTTPS (e.g., with Nginx and Let's Encrypt), authentication, and restrict CORS origins.

GPU Acceleration: If your server has an NVIDIA GPU, configure Docker for GPU passthrough for the asr_service (and potentially nlu_service if using a larger LLM) to significantly speed up inference.

Audio Format Conversion: The ASR service might need ffmpeg and pydub to handle various audio formats uploaded from the browser more robustly.

This detailed plan provides a solid foundation for your self-hosted voice ordering system. It leverages Python's strengths for AI and backend, and Docker for efficient deployment.

￼
￼
￼
￼
￼
