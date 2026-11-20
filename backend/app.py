import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from postgrest import APIError
from supabase import Client, create_client

load_dotenv()

app = Flask(__name__)

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
supabase: Client | None = (
    create_client(supabase_url, supabase_key)
    if supabase_url and supabase_key
    else None
)


@app.after_request
def enable_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def database():
    if supabase is None:
        return None, (jsonify(error="Supabase is not configured"), 500)
    return supabase, None


def database_error(error: APIError):
    return jsonify(error="Database request failed", details=error.message), 500


@app.get("/")
def index():
    client, error = database()
    if error:
        return error
    try:
        response = client.table("users").select("id,email,role").execute()
        return jsonify(response.data)
    except APIError as exc:
        return database_error(exc)


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/api/events")
def list_events():
    client, error = database()
    if error:
        return error
    try:
        response = client.table("events").select("id,organizer_id,title,capacity,status").execute()
        return jsonify(response.data)
    except APIError as exc:
        return database_error(exc)


@app.get("/api/events/<event_id>")
def get_event(event_id):
    client, error = database()
    if error:
        return error
    try:
        response = (
            client.table("events")
            .select("id,organizer_id,title,capacity,status")
            .eq("id", event_id)
            .limit(1)
            .execute()
        )
        if not response.data:
            return jsonify(error="Event not found"), 404
        return jsonify(response.data[0])
    except APIError as exc:
        return database_error(exc)


@app.post("/api/registrations")
def create_registration():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    event_id = body.get("event_id")
    if not user_id or not event_id:
        return jsonify(error="user_id and event_id are required"), 400

    client, error = database()
    if error:
        return error
    try:
        existing = (
            client.table("registrations")
            .select("id")
            .eq("user_id", user_id)
            .eq("event_id", event_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return jsonify(error="User is already registered for this event"), 409

        event_response = (
            client.table("events")
            .select("id,capacity,status")
            .eq("id", event_id)
            .limit(1)
            .execute()
        )
        if not event_response.data:
            return jsonify(error="Event not found"), 404
        event = event_response.data[0]
        registrations = (
            client.table("registrations")
            .select("id")
            .eq("event_id", event_id)
            .execute()
        )
        capacity = event.get("capacity")
        if capacity is not None and len(registrations.data) >= capacity:
            return jsonify(error="Event is at capacity"), 409

        inserted = (
            client.table("registrations")
            .insert({"user_id": user_id, "event_id": event_id})
            .execute()
        )
        return jsonify(inserted.data[0]), 201
    except APIError as exc:
        if getattr(exc, "code", None) == "23505":
            return jsonify(error="User is already registered for this event"), 409
        return database_error(exc)


@app.get("/api/me/registrations")
def my_registrations():
    # There is no authentication by design, so the caller must identify a user explicitly.
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify(error="user_id query parameter is required"), 400
    client, error = database()
    if error:
        return error
    try:
        response = (
            client.table("registrations")
            .select("id,user_id,event_id,created_at,events(id,title,capacity,status)")
            .eq("user_id", user_id)
            .execute()
        )
        return jsonify(response.data)
    except APIError as exc:
        return database_error(exc)


@app.get("/api/events/<event_id>/registrations")
def event_registrations(event_id):
    # This endpoint is public because the requested API has no authentication.
    client, error = database()
    if error:
        return error
    try:
        event = (
            client.table("events")
            .select("id")
            .eq("id", event_id)
            .limit(1)
            .execute()
        )
        if not event.data:
            return jsonify(error="Event not found"), 404
        response = (
            client.table("registrations")
            .select("id,user_id,event_id,created_at")
            .eq("event_id", event_id)
            .execute()
        )
        return jsonify(response.data)
    except APIError as exc:
        return database_error(exc)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
