from app import app, db, User, Student, Class, LeaveOfAbsence
from datetime import datetime, timedelta

def init_db():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        # Create demo users
        admin = User(
            email='admin@school.com',
            name='Admin User',
            role='admin'
        )
        admin.set_password('admin123')

        # Create teachers
        teachers = [
            User(
                email='smith@school.com',
                name='John Smith',
                role='teacher'
            ),
            User(
                email='jones@school.com',
                name='Sarah Jones',
                role='teacher'
            ),
            User(
                email='patel@school.com',
                name='Raj Patel',
                role='teacher'
            )
        ]
        for teacher in teachers:
            teacher.set_password('teacher123')

        # Create students and their parents
        students_data = [
            {
                'student': {'email': 'jane.doe@school.com', 'name': 'Jane Doe', 'grade': '10th Grade'},
                'parent': {'email': 'mary.doe@email.com', 'name': 'Mary Doe'}
            },
            {
                'student': {'email': 'john.smith@school.com', 'name': 'John Smith Jr.', 'grade': '9th Grade'},
                'parent': {'email': 'jane.smith@email.com', 'name': 'Jane Smith'}
            },
            {
                'student': {'email': 'emma.wilson@school.com', 'name': 'Emma Wilson', 'grade': '11th Grade'},
                'parent': {'email': 'david.wilson@email.com', 'name': 'David Wilson'}
            },
            {
                'student': {'email': 'michael.brown@school.com', 'name': 'Michael Brown', 'grade': '10th Grade'},
                'parent': {'email': 'lisa.brown@email.com', 'name': 'Lisa Brown'}
            }
        ]

        students = []
        parents = []
        for data in students_data:
            student = User(
                email=data['student']['email'],
                name=data['student']['name'],
                role='student'
            )
            student.set_password('student123')
            students.append(student)

            parent = User(
                email=data['parent']['email'],
                name=data['parent']['name'],
                role='parent'
            )
            parent.set_password('parent123')
            parents.append(parent)

        # Add all users to database
        db.session.add_all([admin] + teachers + students + parents)
        db.session.commit()

        # Create student records
        student_records = []
        for i, student in enumerate(students):
            student_record = Student(
                user_id=student.id,
                parent_id=parents[i].id,
                grade=students_data[i]['student']['grade']
            )
            student_records.append(student_record)
        db.session.add_all(student_records)
        db.session.commit()

        # Create classes with detailed schedules
        classes = [
            # Mathematics classes
            Class(name='Algebra I', teacher_id=teachers[0].id, schedule='Monday 8:00-9:00'),
            Class(name='Geometry', teacher_id=teachers[0].id, schedule='Monday 10:00-11:00'),
            Class(name='Calculus', teacher_id=teachers[0].id, schedule='Wednesday 8:00-9:00'),
            Class(name='Advanced Mathematics', teacher_id=teachers[0].id, schedule='Monday 18:30-20:00'),
            
            # Science classes
            Class(name='Biology', teacher_id=teachers[1].id, schedule='Tuesday 8:00-9:00'),
            Class(name='Chemistry', teacher_id=teachers[1].id, schedule='Tuesday 10:00-11:00'),
            Class(name='Physics', teacher_id=teachers[1].id, schedule='Thursday 8:00-9:00'),
            Class(name='Advanced Science', teacher_id=teachers[1].id, schedule='Tuesday 20:10-21:20'),
            
            # English classes
            Class(name='English Literature', teacher_id=teachers[2].id, schedule='Monday 9:00-10:00'),
            Class(name='Creative Writing', teacher_id=teachers[2].id, schedule='Wednesday 9:00-10:00'),
            Class(name='Public Speaking', teacher_id=teachers[2].id, schedule='Friday 9:00-10:00'),
            Class(name='Advanced English', teacher_id=teachers[2].id, schedule='Wednesday 21:40-22:20')
        ]
        db.session.add_all(classes)
        db.session.commit()

        # Assign students to classes
        for student_record in student_records:
            # Assign all students to core classes
            student_record.classes.extend([
                classes[0],  # Algebra I
                classes[3],  # Biology
                classes[6]   # English Literature
            ])
            
            # Assign additional classes based on grade
            if student_record.grade == '9th Grade':
                student_record.classes.extend([classes[1], classes[4]])  # Geometry, Chemistry
            elif student_record.grade == '10th Grade':
                student_record.classes.extend([classes[2], classes[5]])  # Calculus, Physics
            elif student_record.grade == '11th Grade':
                student_record.classes.extend([classes[7], classes[8]])  # Creative Writing, Public Speaking

        db.session.commit()

if __name__ == '__main__':
    init_db()
    print("Database initialized with demo data!") 