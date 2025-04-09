# Regvana - Regulatory Compliance Platform

A comprehensive Django-based regulatory compliance management platform that helps organizations track, manage, and ensure compliance with various regulations.

## Features

- **User Management**: Role-based access control with multiple user types (Admin, Compliance Maker/Checker, Department Maker/Checker)
- **Department Organization**: Manage organizational structure and department-specific compliance
- **Regulation Management**: Create, update, and track regulations with detailed articles
- **Compliance Tracking**: Track compliance status for each department across all regulations
- **Audit Logging**: Comprehensive logging of all user actions for accountability
- **Notifications**: User notification system for important updates and compliance status changes

## Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install required packages: `pip install -r requirements.txt`
5. Apply migrations: `python manage.py migrate`
6. Create a superuser: `python manage.py createsuperuser`
7. Run the development server: `python manage.py runserver`

## Usage

Access the admin interface at http://localhost:8000/admin/ to manage:

- Users and departments
- Regulations and articles
- Compliance status tracking
- System settings and notifications

## License

[MIT License](LICENSE) 