# Vapi Voice Scheduler

A real-time voice scheduling assistant using Vapi, OpenAI, and Google Calendar. The backend is a robust FastAPI service designed with Clean Code principles, handling Vapi tool calls and Google OAuth to create calendar events seamlessly.

## Demo & Explanation

**Watch the code walkthrough and demo here:** [Loom Video](https://www.loom.com/share/0c576178d97840e7805cc5baa954614f)

## Deployed Application

**Live URL:** [https://voice-scheduling-agent-qg9u.onrender.com/](https://voice-scheduling-agent-qg9u.onrender.com/)

**App URL:** [https://voice-scheduling-agent-qg9u.onrender.com/api/v1/auth/google/start](https://voice-scheduling-agent-qg9u.onrender.com/api/v1/auth/google/start)

### Important: Google Cloud Development Mode
The Google Cloud Project for this application is currently in **Testing/Development mode**.
 **You cannot simply log in.** To test the Google Calendar integration, **you must provide your email address to the developer** to be manually added to the list of authorized testers.

## Tech Stack & Architecture

This project is built using entirely **Free Tier** services to demonstrate a cost-effective, production-ready architecture.

- **Vapi**: Used as the Voice AI orchestration layer. It handles speech-to-text, text-to-speech, and conversation flow. **Note:** For Vapi to access the backend tools, the application **must be deployed to a public URL** (like Render) or exposed via a tunnel (like ngrok) during development.
- **LLM Provider**: Configured to use **gpt-4.1-mini** via Vapi. This choice, combined with a highly optimized system prompt including `{{customer_id}}` injection, ensures minimal latency and operational costs while maintaining high intelligence.
- **FastAPI**: Powering the backend with a focus on speed, standard compliance, and async capabilities.
- **SQLite**: A lightweight, file-based database used to securely store Google OAuth tokens and authentication state.
- **Testing**: The project includes a comprehensive test suite. All Pydantic schemas, domain models, and core services are fully tested to ensure stability.
- **Render**: A unified cloud platform to build and run apps. This project is hosted on Render's free tier, utilizing seamless GitHub integration for continuous deployment.
- **Clean Code**: The codebase strictly adheres to Clean Code principles (SOLID, DRY, Single Responsibility), ensuring that the software is maintainable, readable, and scalable.

## How it Works

1.  **Voice Interaction**: The user talks to the Vapi agent.
2.  **Intent Recognition**: The agent identifies the user's intent to schedule a meeting.
3.  **Tool Call**: The agent triggers the `create_calendar_event` tool.
    *   **Crucial Step**: The system prompt instructs the LLM to inject the `customer_id` from the context (`{{customer_id}}`) into the tool parameters. This ensures the backend knows *exactly* which user's calendar to update without asking the user for their ID.
4.  **Backend Processing**:
    *   The FastAPI webhook receives the tool call.
    *   It validates the request and the `customer_id`.
    *   It retrieves the user's stored Google OAuth tokens from the SQLite database.
    *   It constructs a Google Calendar API request.
5.  **Calendar Event**: The event is created in the user's primary calendar, and the agent confirms the action verbally.

## How to Test

1.  **Authorize Google Calendar** (requires tester access):
    *   Navigate to `https://voice-scheduling-agent-qg9u.onrender.com/api/v1/auth/google/start`.
    *   Complete the Google sign-in flow.
2.  **Access Dashboard**:
    *   You will be redirected to the dashboard with your unique `customer_id`.
3.  **Start Scheduling**:
    *   Click "Start voice assistant".
    *   Say: "Schedule a meeting with [Name] on [Date] at [Time] for [Title]".
    *   The assistant will use the injected `customer_id` to book the slot on your calendar.

## Local Development

1.  **Clone & Setup**:
    ```bash
    git clone <repo-url>
    cd voice-scheduling-agent
    python -m venv .venv
    .venv\Scripts\activate  # or source .venv/bin/activate on Mac/Linux
    pip install -r requirements.txt
    ```
2.  **Environment Variables**:
    Copy `.env.example` to `.env` and configure:
    *   `GOOGLE_CLIENT_ID` / `SECRET`
    *   `VAPI_PUBLIC_KEY` / `ASSISTANT_ID` / `SIGNATURE_SECRET`
3.  **Run Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

## Project Structure

- `app/`: Core application logic (FastAPI).
    - `api/`: Route handlers and dependencies.
    - `core/`: Configuration and security.
    - `domain/`: Pydantic models and schemas.
    - `services/`: Business logic (Calendar, User).
    - `infrastructure/`: External integrations (Database, Google API).
- `vapi_agent.json`: Vapi tool configuration and system prompt.

---
*Created using Free Tier technologies.*
