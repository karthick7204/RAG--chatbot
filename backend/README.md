# FastAPI Backend

This is a modern, modular FastAPI backend structure designed to integrate seamlessly with a Next.js frontend.

## Project Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── items.py          # CRUD route handlers
│   │   ├── __init__.py
│   │   └── router.py             # Main router aggregating all routes
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py             # Settings using Pydantic Settings
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── item.py               # Pydantic schemas for data validation
│   ├── __init__.py
│   └── main.py                   # FastAPI initialization & entry point
├── .gitignore
├── README.md
└── requirements.txt              # Project dependencies
```

## Setup & Running

### 1. Prerequisites
- Python 3.8+ installed on your system.

### 2. Install Dependencies
Navigate to the `backend` folder and run:
```bash
pip install -r requirements.txt
```

### 3. Run the Development Server
Run uvicorn to start the API:
```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`. You can access:
- **Interactive Documentation (Swagger UI)**: `http://127.0.0.1:8000/docs`
- **Alternative Documentation (ReDoc)**: `http://127.0.0.1:8000/redoc`
