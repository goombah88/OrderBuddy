Core Components & Technologies
Menu Data: SQLite (Python's built-in sqlite3 module) for simple, file-based database management.

Speech Recognition (ASR):

OpenAI Whisper: The leading open-source model for high-quality speech-to-text.

Implementation: Using the Hugging Face transformers library in Python for loading and inference. For highly optimized CPU inference, we can consider ctranslate2 or whisper.cpp (with a Python wrapper) as an advanced optimization.

Natural Language Understanding (NLU) / Menu Understanding Model:

SpaCy: A powerful and efficient library for NLP in Python. You'll train a custom SpaCy model for Named Entity Recognition (NER) and potentially Text Classification to understand intents and extract menu-specific entities (items, options, quantities, sides).

Alternatively (for more complex NLU): Fine-tune a smaller pre-trained language model (e.g., DistilBERT) using Hugging Face transformers for more nuanced understanding, especially if your menu has many complex variations or ambiguous phrasing. We'll start with SpaCy for its simplicity and efficiency.

Order Management Logic: Pure Python code, interacting with the SQLite database.

Backend API: FastAPI (Python) – fast, modern, and easy to build RESTful APIs.

Frontend (Android Tablet): A Web Application (HTML, CSS, JavaScript) accessed via the tablet's browser. This offers the best balance of performance and deployment ease for self-hosting.

Containerization: Docker and Docker Compose to package and run all services.


----------------------------
Project Structure & Workflow
----------------------------

OrderBuddy/
├── backend/
│   ├── Dockerfile
│   ├── app/
│   │   ├── main.py             # FastAPI app, orchestrates ASR/NLU/Order
│   │   ├── menu_db.py          # SQLite database interaction
│   │   ├── order_manager.py    # Logic for managing the current order
│   │   └── nlu_client.py       # Client to interact with NLU service
│   ├── requirements.txt
│   └── trained_nlu_model/      # Directory for trained SpaCy model
├── asr_service/
│   ├── Dockerfile
│   ├── app/
│   │   ├── asr_api.py          # FastAPI app for Whisper ASR
│   │   └── whisper_model.py    # Whisper model loading/inference
│   ├── requirements.txt
│   └── models/                 # Directory for Whisper model weights (downloaded)
├── nlu_service/
│   ├── Dockerfile
│   ├── app/
│   │   ├── nlu_api.py          # FastAPI app for NLU inference
│   │   └── nlu_model.py        # SpaCy model loading/inference
│   ├── requirements.txt
│   └── training_data/          # Your NLU training data (JSON/CSV)
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── Dockerfile              # Optional: For serving static frontend files
├── menu_data/
│   └── menu.json               # Your structured restaurant menu
└── docker-compose.yml          # Orchestrates all services
