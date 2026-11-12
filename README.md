# OrderBuddy

OrderBuddy is an experimental voice-driven restaurant ordering prototype. It
contains a browser interface, a FastAPI backend, and separate speech
recognition and natural-language processing services.

## Project status

This repository is a work in progress, not a production-ready ordering system.
The deployment configuration and service integration have not been validated
end to end. Do not expose the services to the public internet or use them to
process real customer orders without a separate security and reliability
review.

The sample menu in `menu-data/menu.json` is synthetic demonstration data.
Replace it only with menu content you have permission to use.

## Repository layout

- `frontend/` — browser interface
- `asr_service/` — speech-to-text API
- `nlu_services/` — natural-language processing API and training script
- `menu-data/backend/` — backend API, order management, and SQLite menu code
- `menu-data/menu.json` — synthetic sample menu
- `docker-compose.yml` — draft local service configuration
- `OVERVIEW.md` — current high-level architecture
- `DETAILED_IMPLEMENTATION.md` — older design notes; not authoritative setup
  instructions

## Public-repository hygiene

Local environment files, credentials, downloaded website assets, model files,
and database files are excluded by `.gitignore`. Before publishing, review
`git status --short` and inspect the full Git history for anything that should
not be public. Removing a file from the current checkout does not remove it
from earlier commits.

The frontend currently loads some styling and font resources from third-party
CDNs. These requests disclose normal connection metadata to those providers.
