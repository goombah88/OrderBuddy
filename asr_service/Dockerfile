FROM python:3.9-slim-buster

WORKDIR /app

# Install system dependencies for soundfile and ffmpeg (for audio processing)
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
# This will download to the HF_HOME path.
ENV HF_HOME /app/hf_cache
RUN mkdir -p $HF_HOME
RUN python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-tiny')"

CMD ["uvicorn", "asr_api:app", "--host", "0.0.0.0", "--port", "8000"]
