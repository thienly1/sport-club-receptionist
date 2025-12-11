# 🎾 Sport Club AI Receptionist

An AI-powered voice receptionist system for sport clubs. Built with FastAPI, this backend service integrates with VAPI for AI voice conversations, handles customer management, bookings, and notifications.

## 📋 Overview

Sport Club AI Receptionist automates phone-based customer service for sport clubs. The AI assistant can:

- Answer questions about membership, pricing, facilities, and policies
- Guide customers to book through Matchi (booking platform)
- Collect customer information for lead generation
- Handle phone bookings when necessary
- Send SMS notifications and confirmations
- Escalate complex questions to club managers

## 🏗️ Project Structure

```
SPORT_CLUB_RECEPTIONIST/
├── backend/
│   ├── alembic/                    # Database migrations
│   │   ├── versions/
│   │   │   ├── 001_initial.py
│   │   │   └── 002_add_users.py
│   │   └── env.py
│   ├── src/
│   │   ├── app/
│   │   │   ├── config.py           # Configuration & environment variables
│   │   │   ├── database.py         # Database connection & session management
│   │   │   ├── main.py             # FastAPI application entry point
│   │   │   ├── dependencies/       # Auth dependencies
│   │   │   │   └── auth.py
│   │   │   ├── models/             # SQLAlchemy models
│   │   │   │   ├── booking.py
│   │   │   │   ├── club.py
│   │   │   │   ├── conversation.py
│   │   │   │   ├── customer.py
│   │   │   │   ├── notification.py
│   │   │   │   └── user.py
│   │   │   ├── routes/             # API endpoints
│   │   │   │   ├── auth.py
│   │   │   │   ├── booking.py
│   │   │   │   ├── club.py
│   │   │   │   ├── conversation.py
│   │   │   │   ├── customer.py
│   │   │   │   ├── dashboard.py
│   │   │   │   ├── notification.py
│   │   │   │   └── vapi.py
│   │   │   ├── schemas/            # Pydantic schemas
│   │   │   │   ├── booking.py
│   │   │   │   ├── club.py
│   │   │   │   ├── conversation.py
│   │   │   │   ├── customer.py
│   │   │   │   ├── notification.py
│   │   │   │   └── user.py
│   │   │   ├── services/           # Business logic services
│   │   │   │   ├── knowledge_base.py
│   │   │   │   ├── matchi_service.py
│   │   │   │   ├── notification_service.py
│   │   │   │   └── vapi_service.py
│   │   │   └── utils/              # Utility functions
│   │   └── .env                    # Environment variables
│   ├── test/                       # Test suite
│   │   ├── conftest.py             # Pytest fixtures & configuration
│   │   ├── test_auth.py            # Authentication tests
│   │   ├── test_booking.py         # Booking model & routes tests
│   │   ├── test_conversation.py    # Conversation tests
│   │   ├── test_customer.py        # Customer management tests
│   │   ├── test_dashboard.py       # Dashboard & analytics tests
│   │   ├── test_external_services.py # External service integration tests
│   │   ├── test_integration.py     # End-to-end integration tests
│   │   ├── test_models_club.py     # Club model tests
│   │   ├── test_notification.py    # Notification system tests
│   │   ├── test_routes_club.py     # Club API routes tests
│   │   ├── test_schemas.py         # Pydantic schema validation tests
│   │   ├── test_services.py        # Business logic service tests
│   │   ├── test_utils.py           # Utility function tests
│   │   ├── test_vapi_webhook_handlers.py # VAPI webhook tests
│   │   └── test.yml                # Test configuration
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── requirements.txt
```

## 🚀 Features

| Feature                 | Description                                            |
| ----------------------- | ------------------------------------------------------ |
| **AI Voice Assistant**  | VAPI integration for natural phone conversations       |
| **Club Management**     | Multi-tenant support for multiple sport clubs          |
| **Customer Management** | Lead tracking, customer profiles, conversation history |
| **Booking System**      | Phone-based bookings with Matchi integration           |
| **Notifications**       | SMS notifications via Twilio                           |
| **Authentication**      | JWT-based auth with role-based access control          |
| **Dashboard**           | Analytics and insights for club managers               |

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Authentication**: JWT (PyJWT)
- **AI Voice**: VAPI
- **SMS**: Twilio
- **Booking Integration**: Matchi
- **Testing**: Pytest

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database (or Supabase account)
- VAPI account for AI voice
- Twilio account for SMS (optional)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd SPORT_CLUB_RECEPTIONIST/backend
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the `src/` directory:

   ```env
   # Application
   APP_NAME=Sport Club AI Receptionist
   ENVIRONMENT=development
   DEBUG=True
   SECRET_KEY=your-secret-key-here

   # Database (Supabase)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   DATABASE_URL=postgresql://user:password@host:port/database

   # JWT Authentication
   JWT_SECRET_KEY=your-jwt-secret-key

   # VAPI Configuration
   VAPI_API_KEY=your-vapi-api-key
   VAPI_ASSISTANT_ID=your-assistant-id
   VAPI_PHONE_NUMBER=+46xxxxxxxxx
   VAPI_BASE_URL=https://api.vapi.ai

   # Twilio (SMS)
   TWILIO_ACCOUNT_SID=your-account-sid
   TWILIO_AUTH_TOKEN=your-auth-token
   TWILIO_PHONE_NUMBER=+46xxxxxxxxx

   # Matchi Integration
   MATCHI_BASE_URL=https://matchi.se
   MATCHI_API_KEY=your-matchi-api-key

   # Manager Contact
   MANAGER_PHONE_NUMBER=+46xxxxxxxxx

   # CORS
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

5. **Run database migrations**

   ```bash
   alembic upgrade head
   ```

6. **Start the server**

   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Authentication

| Method | Endpoint                | Description           |
| ------ | ----------------------- | --------------------- |
| POST   | `/auth/register`        | Register new user     |
| POST   | `/auth/login`           | Login and get tokens  |
| POST   | `/auth/refresh`         | Refresh access token  |
| GET    | `/auth/me`              | Get current user info |
| PUT    | `/auth/me`              | Update current user   |
| POST   | `/auth/change-password` | Change password       |

### Clubs

| Method | Endpoint      | Description      |
| ------ | ------------- | ---------------- |
| GET    | `/clubs`      | List all clubs   |
| POST   | `/clubs`      | Create new club  |
| GET    | `/clubs/{id}` | Get club details |
| PUT    | `/clubs/{id}` | Update club      |
| DELETE | `/clubs/{id}` | Delete club      |

### Customers

| Method | Endpoint          | Description          |
| ------ | ----------------- | -------------------- |
| GET    | `/customers`      | List customers       |
| POST   | `/customers`      | Create customer      |
| GET    | `/customers/{id}` | Get customer details |
| PUT    | `/customers/{id}` | Update customer      |

### Bookings

| Method | Endpoint         | Description         |
| ------ | ---------------- | ------------------- |
| GET    | `/bookings`      | List bookings       |
| POST   | `/bookings`      | Create booking      |
| GET    | `/bookings/{id}` | Get booking details |
| PUT    | `/bookings/{id}` | Update booking      |
| DELETE | `/bookings/{id}` | Cancel booking      |

### Conversations

| Method | Endpoint              | Description              |
| ------ | --------------------- | ------------------------ |
| GET    | `/conversations`      | List conversations       |
| GET    | `/conversations/{id}` | Get conversation details |

### Notifications

| Method | Endpoint                         | Description                 |
| ------ | -------------------------------- | --------------------------- |
| GET    | `/notifications`                 | List notifications          |
| POST   | `/notifications`                 | Create notification         |
| POST   | `/notifications/send`            | Send notification           |
| POST   | `/notifications/bulk`            | Send bulk notifications     |
| GET    | `/notifications/{id}`            | Get notification details    |
| POST   | `/notifications/{id}/retry`      | Retry failed notification   |
| GET    | `/notifications/stats/{club_id}` | Get notification statistics |

### VAPI Webhook

| Method | Endpoint        | Description          |
| ------ | --------------- | -------------------- |
| POST   | `/vapi/webhook` | VAPI webhook handler |

### Dashboard

| Method | Endpoint           | Description              |
| ------ | ------------------ | ------------------------ |
| GET    | `/dashboard/stats` | Get dashboard statistics |

## 🧪 Testing

The project includes a comprehensive test suite using pytest. Tests are organized by feature/module with support for fixtures, mocking, and database isolation.

### Test Structure

```
test/
├── conftest.py                 # Shared fixtures and test configuration
├── test.yml                    # Test environment configuration
├── test_auth.py                # Authentication & authorization tests
├── test_booking.py             # Booking CRUD, validation, conflicts, statistics
├── test_conversation.py        # Conversation tracking tests
├── test_customer.py            # Customer management & status transitions
├── test_dashboard.py           # Dashboard analytics tests
├── test_external_services.py   # VAPI, Twilio, Matchi integration tests
├── test_integration.py         # End-to-end workflow tests
├── test_models_club.py         # Club model unit tests
├── test_notification.py        # Notification CRUD, delivery, batching tests
├── test_routes_club.py         # Club API endpoint tests
├── test_schemas.py             # Pydantic schema validation tests
├── test_services.py            # Business logic service tests
├── test_utils.py               # Utility function tests
└── test_vapi_webhook_handlers.py # VAPI webhook event handling tests
```

### Test Files Description

| File                            | Description                              | Key Test Areas                                                                  |
| ------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------- |
| `conftest.py`                   | Pytest configuration and shared fixtures | Database session, test client, auth headers, mock services                      |
| `test_auth.py`                  | Authentication system tests              | Registration, login, token refresh, password change, role-based access          |
| `test_booking.py`               | Booking system tests                     | CRUD operations, conflict detection, capacity limits, modifications, statistics |
| `test_conversation.py`          | Conversation tracking tests              | Call records, transcripts, customer linking                                     |
| `test_customer.py`              | Customer management tests                | CRUD, status transitions, follow-ups, search                                    |
| `test_dashboard.py`             | Analytics tests                          | Statistics aggregation, date filtering, metrics                                 |
| `test_external_services.py`     | External integration tests               | VAPI API, Twilio SMS, Matchi booking                                            |
| `test_integration.py`           | End-to-end tests                         | Complete booking flow, notification chains                                      |
| `test_models_club.py`           | Club model tests                         | Model creation, relationships, JSON fields                                      |
| `test_notification.py`          | Notification system tests                | CRUD, templates, delivery, retry, batching, access control                      |
| `test_routes_club.py`           | Club API tests                           | Endpoints, authorization, validation                                            |
| `test_schemas.py`               | Schema validation tests                  | Input validation, serialization, error handling                                 |
| `test_services.py`              | Service layer tests                      | Business logic, data transformations                                            |
| `test_utils.py`                 | Utility tests                            | Helper functions, formatters, validators                                        |
| `test_vapi_webhook_handlers.py` | VAPI webhook tests                       | Event handling, function calls, call lifecycle                                  |

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest test/test_auth.py

# Run specific test class
pytest test/test_booking.py::TestBookingModel

# Run specific test function
pytest test/test_booking.py::TestBookingModel::test_create_booking

# Run tests matching a pattern
pytest -k "booking"

# Run tests with print output
pytest -s

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run only failed tests from last run
pytest --lf

# Stop on first failure
pytest -x
```

### Test Fixtures

The `conftest.py` provides these key fixtures:

| Fixture                     | Scope    | Description                             |
| --------------------------- | -------- | --------------------------------------- |
| `db`                        | function | Database session with automatic cleanup |
| `client`                    | function | FastAPI TestClient instance             |
| `test_club`                 | function | Sample club for testing                 |
| `test_user`                 | function | Sample super admin user                 |
| `test_club_admin`           | function | Sample club admin user                  |
| `test_customer`             | function | Sample customer                         |
| `test_booking`              | function | Sample booking                          |
| `test_conversation`         | function | Sample conversation                     |
| `auth_headers`              | function | JWT authentication headers              |
| `mock_vapi_service`         | function | Mocked VAPI service                     |
| `mock_notification_service` | function | Mocked notification service             |
| `mock_matchi_service`       | function | Mocked Matchi service                   |

### Writing Tests

Example test structure:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

class TestBookingAPI:
    """Test booking API endpoints"""

    def test_create_booking_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_club: Club,
        test_customer: Customer
    ):
        """Test successful booking creation"""
        booking_data = {
            "club_id": str(test_club.id),
            "customer_id": str(test_customer.id),
            "booking_type": "court",
            "resource_name": "Court 1",
            # ... more fields
        }

        response = client.post(
            "/bookings/",
            headers=auth_headers,
            json=booking_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["resource_name"] == "Court 1"
```

### Test Configuration

Tests use the same database as development but clean up after each test. Configure test settings in `pytest.ini`:

```ini
[pytest]
testpaths = test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 🔐 User Roles

| Role          | Description         |
| ------------- | ------------------- |
| `super_admin` | Full system access  |
| `club_admin`  | Manage own club     |
| `club_staff`  | Limited club access |

## 📱 VAPI Integration

The AI assistant is configured to handle:

1. **Membership Inquiries** - Answer questions about membership types and pricing
2. **Availability Checks** - Check court/facility availability
3. **Booking Creation** - Create phone bookings
4. **Lead Capture** - Save customer information
5. **Manager Escalation** - Escalate complex questions via SMS

### Webhook Events

The `/vapi/webhook` endpoint handles:

- `call.started` - New call initiated
- `call.ended` - Call completed
- `function.called` - AI function execution
- `transcript.update` - Real-time transcription

## 🗄️ Database Models

### Club

Stores sport club information including:

- Basic info (name, contact, location)
- Membership types and pricing
- Facilities and opening hours
- AI assistant configuration

### Customer

Customer/lead information:

- Contact details
- Status (lead, member, etc.)
- Interaction history

### Booking

Phone-based bookings:

- Resource and timing
- Status tracking
- Matchi sync status

### Conversation

Call records:

- VAPI call data
- Transcripts
- Intent and sentiment analysis

### Notification

SMS/email notifications:

- Delivery status
- Retry handling

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Set `ENVIRONMENT=production`
- [ ] Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production database URL
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS
- [ ] Configure logging

### Docker (Example)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 License

[Add your license here]

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions or issues, please contact: thienlysph@gmail.com
