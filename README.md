# Leave of Absence Tracking System

A web application for tracking student leave of absence requests, with separate portals for teachers, students, and parents.

## Features

- Teacher Portal
  - View class schedules
  - See excused students for each class
  - Manage attendance records

- Student Portal
  - View personal schedule
  - Check excused absences
  - View leave of absence status

- Parent Portal
  - File leave of absence requests
  - View child's schedule
  - Track request status

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

4. Run the application:
```bash
flask run
```

## Demo Accounts

- Teacher: teacher@demo.com / password123
- Student: student@demo.com / password123
- Parent: parent@demo.com / password123 