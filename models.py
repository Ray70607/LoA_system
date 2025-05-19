from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student', or 'parent'
    name = db.Column(db.String(100), nullable=False)

    # Relationships
    student_record = db.relationship('Student', backref='user', uselist=False, foreign_keys='Student.user_id')
    parent_of = db.relationship('Student', backref='parent', foreign_keys='Student.parent_id')
    classes = db.relationship('Class', backref='teacher', foreign_keys='Class.teacher_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    # Relationships
    absences = db.relationship('LeaveOfAbsence', backref='student', lazy=True)
    classes = db.relationship('Class', secondary='student_class', backref='students')

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule = db.Column(db.String(100), nullable=False)  # e.g., "Monday 9:00-10:00"

    # Relationships
    absences = db.relationship('LeaveOfAbsence', backref='class_record', lazy=True)

# Association table for Student-Class many-to-many relationship
student_class = db.Table('student_class',
    db.Column('student_id', db.Integer, db.ForeignKey('student.id'), primary_key=True),
    db.Column('class_id', db.Integer, db.ForeignKey('class.id'), primary_key=True)
)

class LeaveOfAbsence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_present = db.Column(db.Boolean, default=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    class_record = db.relationship('Class', backref='attendance_records')
    student = db.relationship('Student', backref='attendance_records')
    teacher = db.relationship('User', backref='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', 'date', name='unique_attendance'),
    ) 