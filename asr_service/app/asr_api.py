from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from transformers import pipeline
import torch
import os
import io
import soundfile as sf
import tempfile

app = FastAPI()

# Define model name
WHISPER_MODEL_NAME = "openai/whisper-tiny" # Or "base", "small" etc.

# Check for GPU
# device = 0 if torch.cuda.is_available() else -1 # Use this if you have GPU setup
device = -1 # Force CPU for broader compatibility in this example

# Load Whisper model
asr_pipeline = None # Initialize as None
@app.on_event("startup")
async def load_model():
    global asr_pipeline
    try:
        # The pipeline will download model to HF_HOME (set in Dockerfile)
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

        # Save to a temporary file for soundfile to read,
        # as soundfile.read might not directly support all in-memory blobs
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_audio_file:
            tmp_audio_file.write(audio_bytes)
            tmp_audio_path = tmp_audio_file.name

        # Transcribe using the temporary file path
        # The pipeline can handle various formats if ffmpeg is available
        transcription = asr_pipeline(tmp_audio_path)

        # Clean up the temporary file
        os.unlink(tmp_audio_path)

        return {"text": transcription["text"]}
    except Exception as e:
        print(f"Transcription error: {e}")
        # Clean up temp file if error occurs before unlink
        if 'tmp_audio_path' in locals() and os.path.exists(tmp_audio_path):
            os.unlink(tmp_audio_path)
        return JSONResponse(status_code=500, content={"message": f"Error during transcription: {e}"})

@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": asr_pipeline is not None}
