from fastapi import FastAPI
from pydantic import BaseModel
import spacy
from pathlib import Path

app = FastAPI()

# Load the trained SpaCy model
nlp = None # Initialize as None
@app.on_event("startup")
async def load_model():
    global nlp
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
    # textcat is a single-label classifier, so max(doc.cats) is fine
    intent = max(doc.cats, key=doc.cats.get) if doc.cats else "unknown"
    # You might want a confidence threshold here, e.g., if doc.cats[intent] < 0.7: intent = "unknown"

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
