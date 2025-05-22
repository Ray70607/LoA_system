from app import app, db, User, Student, Class, Classroom, ClassStudent, LeaveOfAbsence, Attendance
from datetime import datetime, timedelta

def init_db():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            name='Admin User',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create teachers
        teachers = []
        for i in range(1, 4):
            teacher = User(
                name=f'Teacher {i}',
                email=f'teacher{i}@example.com',
                role='teacher'
            )
            teacher.set_password('teacher123')
            teachers.append(teacher)
            db.session.add(teacher)
        
        # Create parents
        parents = []
        for i in range(1, 6):
            parent = User(
                name=f'Parent {i}',
                email=f'parent{i}@example.com',
                role='parent'
            )
            parent.set_password('parent123')
            parents.append(parent)
            db.session.add(parent)
        
        # Create students
        students = []
        for i in range(1, 11):
            student = Student(
                user=User(
                    name=f'Student {i}',
                    email=f'student{i}@example.com',
                    role='student'
                ),
                parent=parents[(i-1) // 2],  # Assign 2 students per parent
                grade=f'Grade {(i-1) // 2 + 1}'  # Assign grades 1-5
            )
            student.user.set_password('student123')
            students.append(student)
            db.session.add(student)
        
        # Create classes
        classes = []
        schedules = [
            ('Monday 8:00-9:00', 'Room 101'),
            ('Monday 9:00-10:00', 'Room 102'),
            ('Tuesday 8:00-9:00', 'Room 103'),
            ('Tuesday 9:00-10:00', 'Room 104'),
            ('Wednesday 8:00-9:00', 'Room 105'),
            ('Wednesday 9:00-10:00', 'Room 106'),
            ('Thursday 8:00-9:00', 'Room 107'),
            ('Thursday 9:00-10:00', 'Room 108'),
            ('Friday 8:00-9:00', 'Room 109'),
            ('Friday 9:00-10:00', 'Room 110')
        ]
        
        for i, (schedule, room) in enumerate(schedules):
            class_obj = Class(
                name=f'Class {i+1}',
                teacher=teachers[i % len(teachers)],
                schedule=schedule
            )
            classes.append(class_obj)
            db.session.add(class_obj)
            
            # Create classroom for this class
            classroom = Classroom(
                name=room,
                class_obj=class_obj
            )
            db.session.add(classroom)
            
            # Add students to class with classroom assignment
            for student in students:
                enrollment = ClassStudent(
                    class_obj=class_obj,
                    student=student,
                    classroom=classroom
                )
                db.session.add(enrollment)
        
        # Create some sample leave requests
        for student in students[:5]:  # Only for first 5 students
            for class_obj in classes[:3]:  # Only for first 3 classes
                absence = LeaveOfAbsence(
                    student=student,
                    class_record=class_obj,
                    date=datetime.now().date() + timedelta(days=1),
                    reason='Sample absence reason',
                    status='pending'
                )
                db.session.add(absence)
        
        # Commit all changes
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!") 