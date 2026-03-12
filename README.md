# SAGA Golf API (SagaApi)

Backend API for the SAGA Golf non-profit organization, built with FastAPI and PostgreSQL.

## Prerequisites

- **Python:** 3.13+
- **Node.js:** 16+ (for the React frontend)
- **PostgreSQL:** 14+ (local install or cloud provider like Neon)

## Project Structure

```
SagaApi/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   ├── config.py         # Settings & environment config
│   │   ├── database.py       # SQLAlchemy engine & session
│   │   └── dependencies.py   # FastAPI dependency injection
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── routers/              # API endpoint routers
│   ├── services/             # Business logic layer
│   ├── repositories/         # Data access layer
│   └── controllers/          # Controller logic
├── tests/                    # Pytest test files
├── requirements.txt          # Python dependencies
├── pyproject.toml            # Project config & dev tooling
└── .env.example              # Environment variable template
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/saga_golf` |
| `SECRET_KEY` | JWT signing key (use a long random string) | `your-secret-key-here` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_EMAIL` | Gmail address for sending emails | — |
| `SMTP_PASSWORD` | Gmail app password | — |
| `NORTH_MID` | North payment gateway merchant ID | — |
| `NORTH_DEVELOPER_KEY` | North payment gateway API key | — |
| `NORTH_PASSWORD` | North payment gateway password | — |
| `NORTH_BASE_URL` | North gateway URL | Sandbox URL |
| `NORTH_GATEWAY_PUBLIC_KEY` | North gateway public key | — |
| `RECAPTCHA_SECRET_KEY` | Google reCAPTCHA secret key | — |

## Backend Setup (SagaApi)

1. **Install Python dependencies:**

   ```bash
   cd SagaApi
   pip install -r requirements.txt
   ```

   Or if using `uv` (recommended):

   ```bash
   uv sync
   ```

2. **Set up your `.env` file** (see Environment Variables above).


3. **Start the API server:**

   ```bash
   cd src
   fastapi dev main.py
   ```

   The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Frontend Setup (SagaFe)

1. **Install Node dependencies:**

   ```bash
   cd SagaFe/sagafe
   npm install
   ```

2. **Set up environment variables:**

   Create a `.env` file in `SagaFe/sagafe/`:

   ```
   REACT_APP_API_URL=http://localhost:8000
   REACT_APP_NORTH_MID=your-merchant-id
   REACT_APP_NORTH_GATEWAY_PUBLIC_KEY=your-public-key
   REACT_APP_RECAPTCHA_SITE_KEY=your-recaptcha-site-key
   ```

3. **Start the development server:**

   ```bash
   npm start
   ```

   The frontend will be available at `http://localhost:3000`.

## Running Both Services Locally

Open two terminal windows:

**Terminal 1 — Backend:**
```bash
cd SagaApi/src
fastapi dev main.py
```

**Terminal 2 — Frontend:**
```bash
cd SagaFe/sagafe
npm start
```

The frontend at `http://localhost:3000` will proxy API requests to the backend at `http://localhost:8000`.

## Running Tests

```bash
cd SagaApi
pytest
```

With coverage:

```bash
pytest --cov=src
```

## Linting

```bash
ruff check src/
ruff format src/
```
