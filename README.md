# Leave of Absence Tracking System

A web application for tracking student leave of absence requests and attendance, with separate portals for teachers, students, and parents.

## Features

- Teacher Portal
  - View class schedules
  - See excused students for each class
  - Manage attendance records
  - Automatically mark excused students as absent but excused
  - View attendance history
  - Approve/reject leave of absence requests

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
  - Manage user accounts

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

4. Load demo data:
```bash
python init_db.py
```

5. Run the application:
```bash
flask run
```

## Demo Accounts

### Teachers
- John Smith (smith@school.com / teacher123)
- Sarah Jones (jones@school.com / teacher123)
- Raj Patel (patel@school.com / teacher123)

### Students
- Jane Doe (jane.doe@school.com / student123) - 10th Grade
- John Smith Jr. (john.smith@school.com / student123) - 9th Grade
- Emma Wilson (emma.wilson@school.com / student123) - 11th Grade
- Michael Brown (michael.brown@school.com / student123) - 10th Grade

### Parents
- Mary Doe (mary.doe@email.com / parent123)
- Jane Smith (jane.smith@email.com / parent123)
- David Wilson (david.wilson@email.com / parent123)
- Lisa Brown (lisa.brown@email.com / parent123)

### Admin
- Admin User (admin@school.com / admin123)

## Demo Classes

### Mathematics (John Smith)
- Algebra I (Monday 8:00-9:00)
- Geometry (Monday 10:00-11:00)
- Calculus (Wednesday 8:00-9:00)

### Science (Sarah Jones)
- Biology (Tuesday 8:00-9:00)
- Chemistry (Tuesday 10:00-11:00)
- Physics (Thursday 8:00-9:00)

### English (Raj Patel)
- English Literature (Monday 9:00-10:00)
- Creative Writing (Wednesday 9:00-10:00)
- Public Speaking (Friday 9:00-10:00)

## Recent Updates

- Added automatic excused absence handling in attendance system
- Improved attendance interface with separate sections for excused and present students
- Added attendance reporting and filtering capabilities
- Enhanced user management features
- Added grade-based class assignments
- Improved schedule management
- Added comprehensive demo data with realistic class schedules
- Implemented automatic attendance marking for excused students
