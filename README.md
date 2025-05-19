 # Leave of Absence Tracking System

A web application for tracking student leave of absence requests and attendance, with separate portals for teachers, students, and parents.

## Features

- Teacher Portal
  - View class schedules
  - See excused students for each class
  - Manage attendance records
  - Automatically mark excused students as absent but excused
  - View attendance history

- Student Portal
  - View personal schedule
  - Check excused absences
  - View leave of absence status
  - View attendance history

- Parent Portal
  - File leave of absence requests
  - View child's schedule
  - Track request status
  - View child's attendance records

- Admin Portal
  - Manage users and roles
  - View attendance reports
  - Filter attendance by class and date range
  - Track leave of absence requests

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

4. Load demo data (optional):
```bash
python init_db.py
```

5. Run the application:
```bash
flask run
```

## Demo Accounts

- Teacher: teacher@demo.com / password123
- Student: student@demo.com / password123
- Parent: parent@demo.com / password123
- Admin: admin@school.com / admin123

## Recent Updates

- Added automatic excused absence handling in attendance system
- Improved attendance interface with separate sections for excused and present students
- Added attendance reporting and filtering capabilities
- Enhanced user management features
- Added grade-based class assignments
- Improved schedule management
