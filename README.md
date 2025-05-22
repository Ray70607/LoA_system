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

### Admin
- Admin User (admin@example.com / admin123)

### Teachers
- Teacher 1 (teacher1@example.com / teacher123)
- Teacher 2 (teacher2@example.com / teacher123)
- Teacher 3 (teacher3@example.com / teacher123)

### Students
- Student 1 (student1@example.com / student123) - Grade 1
- Student 2 (student2@example.com / student123) - Grade 1
- Student 3 (student3@example.com / student123) - Grade 2
- Student 4 (student4@example.com / student123) - Grade 2
- Student 5 (student5@example.com / student123) - Grade 3
- Student 6 (student6@example.com / student123) - Grade 3
- Student 7 (student7@example.com / student123) - Grade 4
- Student 8 (student8@example.com / student123) - Grade 4
- Student 9 (student9@example.com / student123) - Grade 5
- Student 10 (student10@example.com / student123) - Grade 5

### Parents
- Parent 1 (parent1@example.com / parent123)
- Parent 2 (parent2@example.com / parent123)
- Parent 3 (parent3@example.com / parent123)
- Parent 4 (parent4@example.com / parent123)
- Parent 5 (parent5@example.com / parent123)

## Demo Classes

### Class Schedule
- Class 1 (Monday 8:00-9:00, Room 101)
- Class 2 (Monday 9:00-10:00, Room 102)
- Class 3 (Tuesday 8:00-9:00, Room 103)
- Class 4 (Tuesday 9:00-10:00, Room 104)
- Class 5 (Wednesday 8:00-9:00, Room 105)
- Class 6 (Wednesday 9:00-10:00, Room 106)
- Class 7 (Thursday 8:00-9:00, Room 107)
- Class 8 (Thursday 9:00-10:00, Room 108)
- Class 9 (Friday 8:00-9:00, Room 109)
- Class 10 (Friday 9:00-10:00, Room 110)

Note: Each class is assigned to one of the three teachers in rotation, and all students are enrolled in all classes.

## Recent Updates

- Added automatic excused absence handling in attendance system
- Improved attendance interface with separate sections for excused and present students
- Added attendance reporting and filtering capabilities
- Enhanced user management features
- Added grade-based class assignments
- Improved schedule management
- Added comprehensive demo data with realistic class schedules
- Implemented automatic attendance marking for excused students