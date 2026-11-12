# Project overview

OrderBuddy is an experimental voice-ordering prototype, organized as a browser
frontend and three Python services:

- **Frontend:** static HTML, CSS, and JavaScript in `frontend/`.
- **Backend:** FastAPI endpoints, menu database access, and order logic in
  `menu-data/backend/`.
- **Speech recognition:** a Whisper-based API in `asr_service/`.
- **Natural-language processing:** a spaCy API and training script in
  `nlu_services/`.
- **Menu data:** a synthetic example menu in `menu-data/menu.json`.

The backend uses SQLite for menu data. Docker Compose is included as draft
configuration, but the service integration is not yet validated end to end.
This project is not ready for production use or exposure to the public
internet.

See [README.md](./README.md) for the project status and public-release notes.
