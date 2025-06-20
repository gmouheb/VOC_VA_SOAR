# Vulnerability Management System

This repository contains a Django-based Vulnerability Management System with Docker configuration for easy development and deployment.

## Project Architecture

### Overview
This is a web application built with Django that helps manage and analyze vulnerabilities in IT assets. It includes features for vulnerability tracking, asset management, analyst collaboration, and AI-powered CVE chat assistance.

### Components
The project consists of the following main components:

1. **Backend (Django)**
   - **Core Apps**:
     - `analysts`: Custom user model and authentication system
     - `analyst_file`: File management for analysts
     - `vulnerabilities`: Vulnerability tracking and management
     - `assets`: IT asset inventory and management
     - `cve_chat`: AI-powered chat interface for CVE information

   - **Technologies**:
     - Django 5.2.1
     - Django REST Framework for API endpoints
     - PostgreSQL for database
     - JWT and API Key authentication
     - Gemini integration for the CVE chat feature

2. **Frontend**
   - Built with HTML, CSS, and JavaScript
   - Uses Tailwind CSS for styling

3. **Infrastructure**
   - Docker containerization
   - Nginx for production deployment
   - Gunicorn as a WSGI server in production

### Data Flow
1. Analysts authenticate using JWT
2. Analysts can manage assets and vulnerabilities
3. The system tracks vulnerabilities associated with assets
4. The CVE chat feature allows querying information about vulnerabilities

## Installation and Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL
- Node.js and npm (for frontend assets)
- Git

### Option 1: Standard Installation (Without Docker)

#### 1. Clone the repository
```bash
git clone https://github.com/gmouheb/VOC_PFE.git
cd VOC_PFE
```

#### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 3. Install dependencies
```bash
pip install -r requirements.txt
npm install
```

#### 4. Set up environment variables
Create a `.env` file in the root directory with the following variables:
```
SALT=your-django-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pfe_voc
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
PORT=5432
AI_URL=your-ai-api-url
API_KEY=your-api-key
```

#### 5. Set up the database
```bash
# Create PostgreSQL database
createdb pfe_voc

# Run migrations
python manage.py migrate
```

#### 6. Create a superuser
```bash
python manage.py createsuperuser
```

#### 7. Collect static files
```bash
python manage.py collectstatic
```

### Option 2: Docker Installation

#### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### 2. Clone the repository
```bash
git clone <repository-url>
cd DjangoProject
```

#### 3. Environment Variables
Create a `.env` file in the root directory with the following variables:
```
SALT=your-django-secret-key
DB_ENGINE=django.db.backends.postgresql
DB_NAME=pfe_voc
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
PORT=5432
AI_URL=your-ai-api-url
API_KEY=your-api-key
```

## Running the Application

### Option 1: Standard Run (Without Docker)

#### Development server
```bash
python manage.py runserver
```
The application will be available at http://127.0.0.1:8000

### Option 2: Docker Run

#### Development environment
```bash
docker-compose up --build
```
This will:
- Build the Docker image for the Django application
- Start the PostgreSQL database
- Run database migrations
- Start the Django development server

The application will be available at http://localhost:8000

#### Stop the containers
```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

#### Production environment
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
This will:
1. Use Gunicorn instead of the Django development server
2. Set up Nginx as a reverse proxy
3. Configure proper volume mounts for security
4. Set the DJANGO_ENV to 'production'

The application will be available at http://localhost:80

## Development

### Running Commands

#### Without Docker
```bash
python manage.py <command>
```

#### With Docker
```bash
docker-compose exec web python manage.py <command>
```

For example, to create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

### Database Access

The PostgreSQL database is exposed on port 5432. You can connect to it using:

- Host: localhost (or db if using Docker)
- Port: 5432
- Database: pfe_voc
- Username: postgres
- Password: postgres

## Production Configuration

The production setup includes:

1. **Gunicorn**: A production-ready WSGI server for Django
2. **Nginx**: A reverse proxy that handles static files and forwards requests to Django
3. **Separate volumes**: Static and media files are mounted separately for better security

### SSL Configuration

For SSL in production, update the Nginx configuration in `nginx/nginx.conf` to include SSL certificates and redirect HTTP to HTTPS.

## API Documentation

The Vulnerability Management System provides a comprehensive REST API for integrating with other systems. The API is organized into several endpoints grouped by functionality.

### Authentication

The API supports two authentication methods:

1. **JWT Authentication**: Used for user sessions and browser-based interactions
   - Obtain a token by sending a POST request to `/api/analyst/login` with email and password
   - Include the token in the Authorization header: `Authorization: Bearer <token>`

2. **API Key Authentication**: Used for programmatic access
   - Generate an API key in the web interface under "API Keys" section
   - Include the API key in the Authorization header: `Authorization: ApiKey <key>`

### API Endpoints

#### Authentication API

- **Register a new analyst**
  - URL: `/api/analyst/register`
  - Method: POST
  - Parameters: 
    - `email`: Email address
    - `password`: Password
    - `first_name`: First name
    - `last_name`: Last name
  - Response: User data with 201 Created status

- **Login**
  - URL: `/api/analyst/login`
  - Method: POST
  - Parameters:
    - `email`: Email address
    - `password`: Password
  - Response: JWT token and user data

- **Logout**
  - URL: `/api/analyst/logout`
  - Method: POST
  - Authentication: JWT token required
  - Response: Success message

- **Get user profile**
  - URL: `/api/analyst/analyst`
  - Method: GET
  - Authentication: JWT token required
  - Response: User profile data

#### API Key Management

- **Generate API key**
  - URL: `/api/analyst/api-keys/generate`
  - Method: POST
  - Authentication: JWT token required
  - Parameters:
    - `name`: Name for the API key (optional)
  - Response: API key details

- **List API keys**
  - URL: `/api/analyst/api-keys/list`
  - Method: GET
  - Authentication: JWT token required
  - Response: List of API keys

- **Delete API key**
  - URL: `/api/analyst/api-keys/delete/<key_id>`
  - Method: DELETE
  - Authentication: JWT token required
  - Parameters:
    - `key_id`: ID of the API key to delete (in URL)
  - Response: Success message

#### File Management API

- **Upload file**
  - URL: `/api/file/upload/`
  - Method: POST
  - Authentication: JWT token required
  - Parameters:
    - `upload`: File to upload (multipart/form-data)
  - Response: File data with 201 Created status

- **List files**
  - URL: `/api/file/upload/`
  - Method: GET
  - Authentication: JWT token required
  - Response: List of user's files

#### Vulnerability Management API

- **List vulnerabilities**
  - URL: `/api/security/vulnerabilities/`
  - Method: GET
  - Authentication: JWT token required
  - Parameters (all optional query parameters):
    - `severity`: Filter by severity
    - `min_cvss`: Filter by minimum CVSS score
    - `max_cvss`: Filter by maximum CVSS score
    - `discovered_after`: Filter by discovery date (after)
    - `discovered_before`: Filter by discovery date (before)
    - `analyst`: Filter by analyst ID (staff only)
  - Response: List of vulnerabilities

- **Get vulnerability details**
  - URL: `/api/security/vulnerabilities/<id>/`
  - Method: GET
  - Authentication: JWT token required
  - Parameters:
    - `id`: Vulnerability ID (in URL)
  - Response: Vulnerability details

- **Create vulnerability**
  - URL: `/api/security/vulnerabilities/`
  - Method: POST
  - Authentication: JWT token required
  - Parameters: Vulnerability data (in request body)
  - Response: Created vulnerability data

- **Update vulnerability**
  - URL: `/api/security/vulnerabilities/<id>/`
  - Method: PUT/PATCH
  - Authentication: JWT token required
  - Parameters:
    - `id`: Vulnerability ID (in URL)
    - Vulnerability data (in request body)
  - Response: Updated vulnerability data

- **Delete vulnerability**
  - URL: `/api/security/vulnerabilities/<id>/`
  - Method: DELETE
  - Authentication: JWT token required
  - Parameters:
    - `id`: Vulnerability ID (in URL)
  - Response: 204 No Content

- **Import vulnerabilities**
  - URL: `/api/security/import`
  - Method: POST
  - Authentication: JWT token required
  - Parameters:
    - `file_id`: ID of the file to import (optional, in request body)
  - Response: Import results

- **Get vulnerabilities JSON**
  - URL: `/api/security/listvul`
  - Method: GET
  - Authentication: JWT token required
  - Parameters (all optional query parameters):
    - `severity`: Filter by severity
    - `min_cvss`: Filter by minimum CVSS score
    - `max_cvss`: Filter by maximum CVSS score
    - `discovered_after`: Filter by discovery date (after)
    - `discovered_before`: Filter by discovery date (before)
  - Response: List of vulnerabilities in JSON format

- **Get vulnerabilities API**
  - URL: `/api/security/api/vulnerabilities`
  - Method: GET
  - Authentication: JWT token required
  - Parameters (all optional query parameters):
    - `severity`: Filter by severity
    - `min_cvss`: Filter by minimum CVSS score
    - `max_cvss`: Filter by maximum CVSS score
    - `discovered_after`: Filter by discovery date (after)
    - `discovered_before`: Filter by discovery date (before)
  - Response: List of vulnerabilities with all columns except analyst, including true_risk_score

#### CVE Chat API

- **Send message**
  - URL: `/api/cve-chat/api/send-message/`
  - Method: POST
  - Authentication: JWT token required
  - Parameters:
    - `conversation_id`: ID of the conversation (optional)
    - `message`: Message content (required)
    - `vulnerability_id`: ID of the vulnerability (optional)
  - Response: AI-generated response

### Example API Usage

#### Authentication and getting vulnerabilities

```python
import requests
import json

# Login and get JWT token
login_url = "http://localhost:8000/api/analyst/login"
login_data = {
    "email": "user@example.com",
    "password": "your_password"
}
response = requests.post(login_url, json=login_data)
token = response.json()["jwt"]

# Use JWT token to get vulnerabilities
headers = {
    "Authorization": f"Bearer {token}"
}
vulnerabilities_url = "http://localhost:8000/api/security/vulnerabilities/"
response = requests.get(vulnerabilities_url, headers=headers)
vulnerabilities = response.json()
print(json.dumps(vulnerabilities, indent=2))
```

#### Using API Key for programmatic access

```python
import requests

# API Key authentication
api_key = "your_api_key"
headers = {
    "Authorization": f"ApiKey {api_key}"
}

# Get vulnerabilities with API Key
vulnerabilities_url = "http://localhost:8000/api/security/vulnerabilities/"
response = requests.get(vulnerabilities_url, headers=headers)
vulnerabilities = response.json()
```

## Troubleshooting

If you encounter any issues:

1. Check the logs:
   - Without Docker: Check the console output
   - With Docker: `docker-compose logs`
2. Ensure all required environment variables are set
3. Verify that ports 8000 and 5432 are not already in use
4. Check database connection settings
