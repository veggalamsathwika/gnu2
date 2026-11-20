# Event API

A Flask API for listing events and managing event registrations with Supabase.

## Run locally

Python 3.10+ is required.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask --app app run --debug
```

Set `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `.env` (or the process environment). The Supabase project needs `users`, `events`, and `registrations` tables with the columns queried in `app.py` and policies that allow the intended operations.

## Deploy

### Render

This repository includes `render.yaml` for a Render Blueprint. Push the repository to GitHub, select **New > Blueprint** in Render, and connect the repository. During setup, provide `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` when prompted. Render builds with `pip install -r requirements.txt`, starts Gunicorn, and checks `/health`.

The Blueprint uses Render's free web service plan. Free instances can spin down when idle; choose a paid plan in `render.yaml` if the API needs continuous availability.

Use Python 3.10 or newer. Configure `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` as secrets/environment variables in your host. Start command:

```sh
gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
```

`/health` is a lightweight health check. Do not commit `.env` or use a Supabase service role key in a public deployment. Configure CORS to allow only your frontend's origin before exposing this API to browsers.

## Endpoints

- `GET /api/events`
- `GET /api/events/<event_id>`
- `POST /api/registrations` with JSON `{ "user_id": "...", "event_id": "..." }`
- `GET /api/me/registrations?user_id=...`
- `GET /api/events/<event_id>/registrations`
