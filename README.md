# Food Delivery Transaction System

外卖交易信息系统课程项目 / Course project for a food-delivery transaction information system.

## Overview

This project is a prototype of a food-delivery platform. The repository includes a Python FastAPI backend, SQLAlchemy data models, SQLite schema, a web client, and a lightweight app-client page.

当前仓库展示的是课程项目原型，不代表生产环境系统。部分功能需要在本地安装依赖并运行后进一步验证。

## Features in the codebase

- User authentication and role-based API routes
- Merchant, menu, and order-related endpoints
- SQLite / SQLAlchemy data model and schema
- Analytics endpoints for sales overview, cuisine distribution, rider performance, customer ordering patterns, hourly order distribution, payment methods, and rating distribution
- Experimental sales-prediction and menu-recommendation code
- Web client and app-client static pages

Feature availability and completeness should be verified by running the application; listed modules indicate code present in this repository, not independently validated production functionality.

## Tech stack

- Python
- FastAPI / Uvicorn
- SQLAlchemy
- SQLite
- scikit-learn / NumPy (experimental prediction module)
- HTML, CSS, JavaScript

## Project structure

```text
.
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── auth.py
│   ├── config.py
│   ├── seed_data.py
│   ├── routes/
│   └── services/
├── database/
│   └── schema.sql
├── web-client/
└── app-client/
```

## Run locally

Requires Python 3.10+ (recommended) and pip.

1. Create and activate a virtual environment.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install backend dependencies.

   ```bash
   pip install -r backend/requirements.txt
   ```

3. Start the API from the backend directory.

   ```bash
   cd backend
   export SECRET_KEY="replace-with-a-long-random-local-secret"
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. Open the API docs at `http://127.0.0.1:8000/docs`. If the static client mounts successfully, the web client is at `http://127.0.0.1:8000/web` and the app client at `http://127.0.0.1:8000/app`.

The application initializes database tables and inserts demo records on startup. A new local SQLite database will be created in the backend working directory.

## Data analysis modules

The analytics service contains aggregation logic for daily sales and order counts, average order value, cuisine distribution, rider performance, customer ordering patterns, hourly orders, payment methods, and ratings. Use the documented API endpoints and verify outputs against the local demo database before using them in a report.

## Important limitations and security notes

- This is an educational prototype, not a production-ready service.
- Do not deploy publicly without reviewing authentication, password-reset behavior, CORS policy, secrets, input validation, and authorization.
- Set `SECRET_KEY` through an environment variable; never use a development default for deployment.
- Demo seed accounts and data are for local testing only. Do not reuse demo credentials in a public deployment.
- The generated SQLite databases and serialized prediction model are intentionally excluded from this public-ready source package. Regenerate local demo data when running the project.
- The sales-prediction module is experimental. Validate feature consistency and evaluate on held-out data before claiming predictive accuracy.

## For portfolio use

Suggested focus: database modeling, API design, and SQL-backed business analytics. Describe only the features you personally implemented and tested. Do not claim business impact or model accuracy unless you have measured evidence.
