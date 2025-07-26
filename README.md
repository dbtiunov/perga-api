# Perga API

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10-blue.svg)
![Build](https://github.com/dbtiunov/perga-api/actions/workflows/ci.yml/badge.svg)

Personal organizer that helps you plan and organize your days and months efficiently.

## Features

- Daily planner
- Monthly agenda and backlog
- RESTful API with FastAPI
- User authentication with JWT tokens
- Comprehensive documentation with Swagger UI

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **PostgreSQL**: Relational database
- **JWT**: JSON Web Tokens for authentication
- **Pydantic**: Data validation and settings management
- **Pytest**: Testing framework

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL 15+

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/dbtiunov/perga-api.git
   cd perga-api
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Update the `.env` file with your specific configuration:
   - Set a secure `SECRET_KEY`
   - Configure PostgreSQL connection details
   - Set `CORS_ORIGINS`

6. Run database migrations:
   ```bash
   alembic upgrade head
   ```

7. Start the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000 with the Swagger documentation at http://localhost:8000/docs.

## Docker Setup

You can also run the application using Docker:

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. The API will be available at http://localhost:8080

## API Documentation

Once the application is running, you can access the interactive API documentation:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/signup/`: Register a new user
- `POST /api/v1/auth/access_token/`: Get access token (form data)
- `POST /api/v1/auth/access_token_json/`: Get access token (JSON)
- `POST /api/v1/auth/refresh_token/`: Refresh access token
- `GET /api/v1/auth/user/`: Get current user information
- `PUT /api/v1/auth/user/`: Update user information

### Planner Days

- `GET /api/v1/planner/days/`: Get planner items for a specific day
- `POST /api/v1/planner/days/`: Add a new item for a specific day
- `PUT /api/v1/planner/days/{item_id}`: Update a planner day item
- `DELETE /api/v1/planner/days/{item_id}`: Delete a planner day item

### Monthly Agenda and Backlog

- `GET /api/v1/planner/agendas/`: Get agendas by specific day
- `GET /api/v1/planner/agendas/{agenda_id}/items`: Get items for a specific agenda
- `POST /api/v1/planner/agendas/{agenda_id}/items`: Create a new agenda item
- `PUT /api/v1/planner/agendas/items/{item_id}`: Update an agenda item
- `DELETE /api/v1/planner/agendas/items/{item_id}`: Delete an agenda item

## Development

### Project Structure

- `app/`: Main application package
  - `api/`: API endpoints and routers
  - `core/`: Core functionality (config, database)
  - `models/`: SQLAlchemy models
  - `schemas/`: Pydantic schemas for request/response validation
  - `services/`: Business logic
  - `tests/`: Test files

### Testing

Run tests with pytest:

```bash
python -m pytest
```

Run specific tests:

```bash
python -m pytest app/tests/test_services/test_user_service.py
```

### Database Migrations

Create a new migration:

```bash
./scripts/create_migration.sh <migration_name>
```

Apply migrations:

```bash
alembic upgrade head
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
