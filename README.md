# Vapi Voice Scheduler

A real-time voice scheduling assistant using Vapi and Google Calendar. The backend is a small FastAPI service that handles Vapi tool calls and Google OAuth, then creates calendar events.

## Deployed URL

- https://YOUR-RENDER-URL.onrender.com

## How to test the agent

1. Complete Google OAuth:
   - Open `https://YOUR-RENDER-URL.onrender.com/api/v1/auth/google/start`
   - Sign in and grant access
2. Configure your Vapi agent with the tool schema in `vapi_agent.json` and set:
   - `toolWebhookUrl` to `https://YOUR-RENDER-URL.onrender.com/api/v1/vapi/webhook`
3. Call the agent and provide name, date, time, timezone, and title.
4. The assistant will confirm details and create an event.

## Local run

1. Copy `.env.example` to `.env` and fill in values.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the server:
   - `uvicorn app.main:app --reload`
4. Start OAuth:
   - `http://localhost:8000/api/v1/auth/google/start`

## Google Calendar integration

- OAuth 2.0 uses the Google Calendar scope `https://www.googleapis.com/auth/calendar.events`.
- Tokens are stored in SQLite and refreshed automatically on use.
- The calendar client inserts events into the primary calendar.

## Evidence

- Add a screenshot of a created event or a short Loom link here.

## Files

- `app/` contains the FastAPI app and business logic.
- `vapi_agent.json` contains the tool schema and starter agent config.

## Render deployment

1. Create a new Web Service.
2. Set the build command:
   - `pip install -r requirements.txt`
3. Set the start command:
   - `uvicorn app.main:app --host 0.0.0.0 --port 10000`
4. Add environment variables from `.env.example`.

## Notes

- Replace `YOUR-RENDER-URL` with your actual Render service URL.
- If you want per-user calendars, use Vapi metadata to map to user IDs and store separate tokens.
