# Student Study & Task Manager

A Flask-based web application for managing study tasks with authentication, task management, REST APIs, testing, and database support.

## Features

- User registration and login
- Password hashing
- Remember-me sessions
- Password change
- Password reset
- Task creation
- Task editing
- Task deletion
- Mark tasks as completed/pending
- Search and filtering
- Priority management
- Due-date tracking
- User-specific task isolation
- REST API
- Automated testing with pytest
- SQLite database
- Git/GitHub version control

## Technology Stack

- Python
- Flask
- SQLAlchemy
- SQLite
- HTML
- CSS
- JavaScript
- pytest
- Git
- GitHub

## REST API

### Authentication

The API requires the user to be logged in.

### Get Tasks

```text
GET /api/tasks