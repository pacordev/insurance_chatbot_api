# Insurance Terminology Chatbot — API v1.0

A thin FastAPI wrapper around [`ins_chatbot`](https://github.com/pacordev/paco_insurance_chatbot), the insurance-terminology learning chatbot. This repo has no chatbot logic of its own — it depends on the core project as a normal pip package and exposes it over HTTP so it can be reached from a browser instead of only the command line.

## Endpoints

- `GET /health` — no auth, used by Render's health check.
- `POST /session` — `{"name": str, "is_newcomer": bool}` → `{"session_id": str, "welcome_message": str}`. Starts a new conversation.
- `POST /chat` — `{"session_id": str, "message": str}` → `{"reply": str}`. Continues an existing conversation.

`/session` and `/chat` both require an `X-API-Key` header matching the `API_KEY` environment variable. This isn't real access control — it's enough to keep out bots/crawlers/casual traffic and gives a clean revocation lever (rotate the env var, redeploy). See the core repo's `handoff.md` §2.56 for the full reasoning.

## Project structure

```
ins_chatbot_api/
├── app/
│   ├── __init__.py       # marks app/ as a package
│   ├── api_ins_chatbot.py # the FastAPI app: startup, endpoints, CORS, rate limiting
│   ├── models.py         # Pydantic request/response shapes
│   ├── auth.py           # X-API-Key check, used as a dependency on /session and /chat
│   └── sessions.py       # in-memory {session_id: ConversationState} store
├── requirements.txt      # pins fastapi/uvicorn/slowapi/pydantic + the ins_chatbot core as a git+https dependency
├── render.yaml           # Render Blueprint: service definition, build/start commands, env vars
├── README.md
```

**`app/api_ins_chatbot.py`** builds one `TermStore`/`Dispatcher` at startup (not per request) and defines the three endpoints described above. **`app/models.py`** is what gives FastAPI its automatic request validation and the `/docs` page. **`app/auth.py`** reads the expected key from `API_KEY` at request time, not at startup, so rotating it is just an env var change + redeploy. **`app/sessions.py`** is deliberately simple — see "Known limitations" below.

### Testing locally with Postman

Import `postman_collection.json` into Postman. It ships three collection variables (`base_url`, `api_key`, `session_id`) defaulting to `http://localhost:8000` / `local-test-key` — edit `api_key` if your local `.env` uses a different value. Requests, meant to be run in order:

1. **Health check** — `GET /health` sanity check.
2. **Start session** — has a test script attached that automatically saves the returned `session_id` into the collection variable, so nothing needs copy-pasting.
3. **Chat — what is ACV** / **Chat — give me an example** — both reference `{{session_id}}` already; the second one exercises multi-turn state (a follow-up that doesn't repeat the term name).
4. **Session — no API key (expect 401)** — sends no `X-API-Key` header on purpose, to confirm auth actually rejects it.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit API_KEY to a real local value
export $(cat .env | xargs)
uvicorn app.api_ins_chatbot:app --reload
```

## Deploying

This repo ships a `render.yaml` blueprint. In Render: New → Blueprint → connect this repo → Render reads `render.yaml` and proposes the service → set a real `API_KEY` value on the env-var screen (`openssl rand -hex 32` works well) → Apply.

## Known limitations

- Sessions live in an in-memory dict — lost on restart/redeploy, doesn't survive multiple instances. Fine for coworker testing, not a permanent design.
- `ALLOWED_ORIGINS` defaults to `*` until a frontend exists — lock it down to the real frontend origin once one is deployed.
- Depends on `ins_chatbot`'s `main` branch directly (`@main` in `requirements.txt`), not a pinned tag — worth pinning once this stabilizes.
