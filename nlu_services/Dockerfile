FROM python:3.9-slim-buster

WORKDIR /app

# Install Python dependencies
COPY nlu_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download SpaCy English model (needed for nlp = spacy.blank("en"))
# en_core_web_sm is a small, general-purpose English model
RUN python -m spacy download en_core_web_sm

# Copy trained NLU model from host to image
# This directory must exist and contain your trained SpaCy model on the host
COPY backend/trained_nlu_model/ /app/trained_nlu_model/

# Copy application code
COPY nlu_service/app/ .

CMD ["uvicorn", "nlu_api:app", "--host", "0.0.0.0", "--port", "8000"]
