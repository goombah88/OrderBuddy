FROM python:3.9-slim-buster

WORKDIR /app

# Copy menu data to a temporary location for DB initialization
COPY menu_data/menu.json /tmp/menu.json

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Initialize SQLite DB during build process
# This creates menu.db inside the image, which will then be copied to the volume
COPY backend/app/menu_db.py /app/menu_db.py
RUN python /app/menu_db.py
# Move the initialized DB to the expected volume path for runtime persistence
RUN mv /app/menu.db /app/data/menu.db

# Copy trained NLU model from host to image
# This directory must exist and contain your trained SpaCy model on the host
COPY backend/trained_nlu_model/ /app/trained_nlu_model/

# Copy application code
COPY backend/app/ .

# Ensure the data directory exists for SQLite persistence
RUN mkdir -p /app/data

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
