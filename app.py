from flask import Flask, render_template, redirect, url_for, flash, request, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_migrate import Migrate
import os
import csv
from io import StringIO, BytesIO
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loa.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import models
from models import User, Student, Class, LeaveOfAbsence, Attendance

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'teacher', 'student', or 'parent'
    name = db.Column(db.String(100), nullable=False)

    # Relationships
    student_record = db.relationship('Student', backref='user', uselist=False, foreign_keys='Student.user_id')
    parent_of = db.relationship('Student', backref='parent', foreign_keys='Student.parent_id')
    taught_classes = db.relationship('Class', backref='teacher', foreign_keys='Class.teacher_id')

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
    class_enrollments = db.relationship('ClassStudent', backref='student', lazy=True)

class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule = db.Column(db.String(100), nullable=False)

    # Relationships
    classrooms = db.relationship('Classroom', backref='class_obj', lazy=True)
    enrollments = db.relationship('ClassStudent', backref='class_obj', lazy=True)
    absences = db.relationship('LeaveOfAbsence', backref='class_record', lazy=True)

class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    enrollments = db.relationship('ClassStudent', backref='classroom', lazy=True)

class ClassStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classroom.id'), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', name='unique_class_student'),
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
    date = db.Column(db.Date, nullable=False)
    is_present = db.Column(db.Boolean, default=True)
    is_excused = db.Column(db.Boolean, default=False)  # New field for excused absences
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    class_record = db.relationship('Class', backref='attendance_records')
    student = db.relationship('Student', backref='attendance_records')
    teacher = db.relationship('User', backref='attendance_records')

    __table_args__ = (
        db.UniqueConstraint('class_id', 'student_id', 'date', name='unique_attendance'),
    )

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('parent_dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    
    # Get all classes taught by this teacher
    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    
    # Get all absences for these classes
    class_ids = [c.id for c in classes]
    absences = LeaveOfAbsence.query.filter(
        LeaveOfAbsence.class_id.in_(class_ids)
    ).order_by(LeaveOfAbsence.date.desc()).all()
    
    return render_template('teacher_dashboard.html', 
                         classes=classes, 
                         absences=absences)

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        return redirect(url_for('index'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    if not student:
        flash('Student record not found')
        return redirect(url_for('index'))
    
    # Get all absences for this student
    absences = LeaveOfAbsence.query.filter_by(student_id=student.id).order_by(LeaveOfAbsence.date.desc()).all()
    
    # Get all class enrollments for this student
    enrollments = ClassStudent.query.filter_by(student_id=student.id).all()
    
    return render_template('student_dashboard.html', 
                         absences=absences, 
                         enrollments=enrollments, 
                         today=datetime.now().date())

@app.route('/parent/dashboard')
@login_required
def parent_dashboard():
    if current_user.role != 'parent':
        return redirect(url_for('index'))
    
    # Get all students associated with this parent
    students = Student.query.filter_by(parent_id=current_user.id).all()
    if not students:
        flash('No students found under your account')
        return redirect(url_for('index'))
    
    # Get all absences for these students
    student_ids = [student.id for student in students]
    absences = LeaveOfAbsence.query.filter(
        LeaveOfAbsence.student_id.in_(student_ids)
    ).order_by(LeaveOfAbsence.date.desc()).all()
    
    return render_template('parent_dashboard.html', 
                         students=students, 
                         today=datetime.now().date(),
                         absences=absences,
                         timedelta=timedelta)

@app.route('/parent/request_absence', methods=['GET', 'POST'])
@login_required
def request_absence():
    if current_user.role != 'parent':
        return redirect(url_for('index'))
    
    # Get all students associated with this parent
    students = Student.query.filter_by(parent_id=current_user.id).all()
    if not students:
        flash('No students found under your account')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        class_id = request.form.get('class_id')
        date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        reason = request.form.get('reason')
        
        # Verify the student belongs to this parent
        student = Student.query.filter_by(id=student_id, parent_id=current_user.id).first()
        if not student:
            flash('Invalid student selected')
            return redirect(url_for('request_absence'))
        
        # Verify the student is enrolled in this class
        enrollment = ClassStudent.query.filter_by(
            student_id=student_id,
            class_id=class_id
        ).first()
        if not enrollment:
            flash('Student is not enrolled in this class')
            return redirect(url_for('request_absence'))
        
        # Check if there's already a pending or approved request for this student, class, and date
        existing_request = LeaveOfAbsence.query.filter_by(
            student_id=student_id,
            class_id=class_id,
            date=date
        ).first()
        
        if existing_request:
            flash('A leave request already exists for this class on the selected date')
            return redirect(url_for('request_absence'))
        
        absence = LeaveOfAbsence(
            student_id=student_id,
            class_id=class_id,
            date=date,
            reason=reason
        )
        db.session.add(absence)
        db.session.commit()
        flash('Leave of absence request submitted successfully')
        return redirect(url_for('parent_dashboard'))
    
    # Get all classes for the students
    all_classes = Class.query.all()
    
    return render_template('request_absence.html', 
                         students=students, 
                         classes=all_classes)

@app.route('/update_absence_status/<int:absence_id>', methods=['POST'])
@login_required
def update_absence_status(absence_id):
    if current_user.role != 'teacher':
        return redirect(url_for('index'))
    
    absence = LeaveOfAbsence.query.get_or_404(absence_id)
    
    # Verify the teacher teaches this class
    if absence.class_record.teacher_id != current_user.id:
        flash('You are not authorized to update this request')
        return redirect(url_for('teacher_dashboard'))
    
    status = request.form.get('status')
    
    if status in ['approved', 'rejected']:
        absence.status = status
        db.session.commit()
        flash(f'Leave request {status}')
    
    return redirect(url_for('teacher_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Get all pending leave requests
    pending_requests = LeaveOfAbsence.query.filter_by(status='pending').order_by(LeaveOfAbsence.created_at.desc()).all()
    
    # Get all approved/rejected requests from the last 30 days
    recent_requests = LeaveOfAbsence.query.filter(
        LeaveOfAbsence.status.in_(['approved', 'rejected']),
        LeaveOfAbsence.created_at >= datetime.now() - timedelta(days=30)
    ).order_by(LeaveOfAbsence.created_at.desc()).all()
    
    return render_template('admin_dashboard.html', 
                         pending_requests=pending_requests,
                         recent_requests=recent_requests)

@app.route('/admin/update_request/<int:request_id>', methods=['POST'])
@login_required
def admin_update_request(request_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    leave_request = LeaveOfAbsence.query.get_or_404(request_id)
    action = request.form.get('action')
    
    if action in ['approve', 'reject']:
        leave_request.status = 'approved' if action == 'approve' else 'rejected'
        db.session.commit()
        flash(f'Request {action}d successfully')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not all([name, email, role, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('add_user'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('add_user'))
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email address already in use.', 'danger')
            return redirect(url_for('add_user'))
        
        # Create new user
        new_user = User(
            name=name,
            email=email,
            role=role
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully.', 'success')
            return redirect(url_for('manage_users'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding user.', 'danger')
            print(f"Error: {str(e)}")
            return redirect(url_for('add_user'))
    
    return render_template('add_user.html')

@app.route('/admin/manage_users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        user = User.query.get_or_404(user_id)
        
        if action == 'delete':
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully.', 'success')
        elif action == 'update_role':
            new_role = request.form.get('role')
            if new_role in ['admin', 'teacher', 'student', 'parent']:
                user.role = new_role
                db.session.commit()
                flash('User role updated successfully.', 'success')
            else:
                flash('Invalid role selected.', 'danger')
        elif action == 'reset_password':
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if new_password != confirm_password:
                flash('Passwords do not match.', 'danger')
            else:
                user.set_password(new_password)
                db.session.commit()
                flash('Password reset successfully.', 'success')
    
    # Get all users
    users = User.query.all()
    return render_template('manage_users.html', users=users)

@app.route('/teacher/record-attendance/<int:class_id>', methods=['GET', 'POST'])
@login_required
def record_attendance(class_id):
    if current_user.role != 'teacher':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    class_record = Class.query.get_or_404(class_id)
    if class_record.teacher_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Parse the schedule to get the day of week
    schedule_parts = class_record.schedule.split()
    class_day = schedule_parts[0]  # e.g., "Monday"
    days_ahead = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 
        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    day_of_week = days_ahead[class_day]
    
    # Get date from query parameters or find next class date
    date_str = request.args.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        # Find the next class date
        today = datetime.now().date()
        days_until_next = (day_of_week - today.weekday()) % 7
        if days_until_next == 0 and datetime.now().time() >= datetime.strptime(schedule_parts[1].split('-')[0], '%H:%M').time():
            days_until_next = 7
        date = today + timedelta(days=days_until_next)
    
    # Get next 5 class dates
    next_class_dates = []
    current_date = date
    while len(next_class_dates) < 5:
        if current_date.weekday() == day_of_week:
            next_class_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Get all leave requests for this class and date
    leave_requests = LeaveOfAbsence.query.filter(
        LeaveOfAbsence.class_id == class_id,
        LeaveOfAbsence.date == date
    ).order_by(LeaveOfAbsence.date.desc()).all()
    
    # Get list of student IDs with approved absences
    excused_student_ids = {request.student_id for request in leave_requests if request.status == 'approved'}
    
    # Get existing attendance records for this date
    existing_records = {
        record.student_id: record 
        for record in Attendance.query.filter_by(
            class_id=class_id,
            date=date
        ).all()
    }
    
    if request.method == 'POST':
        # First, handle excused absences
        for student_id in excused_student_ids:
            if student_id in existing_records:
                record = existing_records[student_id]
                record.is_present = False
                record.is_excused = True
            else:
                record = Attendance(
                    date=date,
                    class_id=class_id,
                    student_id=student_id,
                    teacher_id=current_user.id,
                    is_present=False,
                    is_excused=True
                )
                db.session.add(record)
        
        # Then handle regular attendance for non-excused students
        for enrollment in class_record.enrollments:
            # Skip if student has an approved absence
            if enrollment.student_id in excused_student_ids:
                continue
                
            is_present = request.form.get(f'present_{enrollment.student_id}') == 'on'
            if enrollment.student_id in existing_records:
                record = existing_records[enrollment.student_id]
                record.is_present = is_present
                record.is_excused = False
            else:
                record = Attendance(
                    date=date,
                    class_id=class_id,
                    student_id=enrollment.student_id,
                    teacher_id=current_user.id,
                    is_present=is_present,
                    is_excused=False
                )
                db.session.add(record)
        
        try:
            db.session.commit()
            flash('Attendance recorded successfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error recording attendance.', 'danger')
            print(f"Error: {str(e)}")
        
        return redirect(url_for('record_attendance', class_id=class_id, date=date.strftime('%Y-%m-%d')))
    
    # Get list of students to show in attendance form (excluding excused students)
    students_to_show = [enrollment for enrollment in class_record.enrollments if enrollment.student_id not in excused_student_ids]
    
    # Get the approved absences for display
    approved_absences = [request for request in leave_requests]

    print("leave_requests are:", leave_requests)

    # absences = LeaveOfAbsence.query.filter(
    #     LeaveOfAbsence.class_id.in_(class_ids)
    # ).order_by(LeaveOfAbsence.date.desc()).all()


    return render_template('record_attendance.html',
                         class_record=class_record,
                         date=date,
                         next_class_dates=next_class_dates,
                         absences=approved_absences,
                         students_to_show=students_to_show,
                         existing_records=existing_records)

@app.route('/admin/attendance-reports')
@login_required
def attendance_reports():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Get filter parameters
    class_id = request.args.get('class_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query with explicit join conditions
    query = (Attendance.query
             .join(Class, Attendance.class_id == Class.id)
             .join(Student, Attendance.student_id == Student.id)
             .join(User, Student.user_id == User.id))
    
    # Apply filters
    if class_id:
        query = query.filter(Attendance.class_id == class_id)
    if start_date:
        query = query.filter(Attendance.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(Attendance.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    # Get all classes for filter dropdown
    classes = Class.query.all()
    
    # Get attendance records
    attendance_records = query.order_by(Attendance.date.desc()).all()

    
    
    return render_template('attendance_reports.html',
                         attendance_records=attendance_records,
                         classes=classes,
                         selected_class=class_id,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Verify current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('change_password'))
        
        # Verify new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('index'))
    
    return render_template('change_password.html')

@app.route('/admin/manage_schedules', methods=['GET'])
@login_required
def manage_schedules():
    if current_user.role != 'admin':
        abort(403)
    teachers = User.query.filter_by(role='teacher').all()
    all_students = Student.query.all()
    teacher_id = request.args.get('teacher_id', type=int)
    selected_teacher = User.query.get(teacher_id) if teacher_id else None
    teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all() if teacher_id else []
    
    # Get student enrollments for each class
    class_enrollments = {}
    for class_obj in teacher_classes:
        enrollments = ClassStudent.query.filter_by(class_id=class_obj.id).all()
        class_enrollments[class_obj.id] = enrollments
    
    return render_template('manage_schedules.html',
        teachers=teachers,
        selected_teacher=selected_teacher,
        selected_teacher_id=teacher_id,
        teacher_classes=teacher_classes,
        all_students=all_students,
        class_enrollments=class_enrollments)

@app.route('/admin/add_class/<int:teacher_id>', methods=['POST'])
@login_required
def add_class(teacher_id):
    if current_user.role != 'admin':
        abort(403)
    class_name = request.form.get('class_name')
    day = request.form.get('day')
    time = request.form.get('time')
    classroom_names = request.form.getlist('classroom_names[]')
    
    if not class_name or not day or not time or not classroom_names:
        flash('Class name, day, time, and at least one classroom are required.', 'danger')
        return redirect(url_for('manage_schedules', teacher_id=teacher_id))
    
    schedule = f"{day} {time}"
    new_class = Class(name=class_name, teacher_id=teacher_id, schedule=schedule)
    db.session.add(new_class)
    db.session.flush()  # Get the new class ID
    
    # Create classrooms
    for name in classroom_names:
        classroom = Classroom(name=name, class_id=new_class.id)
        db.session.add(classroom)
    
    db.session.commit()
    flash('Class and classrooms added successfully.', 'success')
    return redirect(url_for('manage_schedules', teacher_id=teacher_id))

@app.route('/admin/remove_class/<int:class_id>', methods=['POST'])
@login_required
def remove_class(class_id):
    if current_user.role != 'admin':
        abort(403)
    class_obj = Class.query.get_or_404(class_id)
    teacher_id = class_obj.teacher_id
    db.session.delete(class_obj)
    db.session.commit()
    flash('Class removed successfully.', 'success')
    return redirect(url_for('manage_schedules', teacher_id=teacher_id))

@app.route('/admin/add_student_to_class/<int:class_id>', methods=['POST'])
@login_required
def add_student_to_class(class_id):
    if current_user.role != 'admin':
        abort(403)
    student_id = request.form.get('student_id', type=int)
    classroom_id = request.form.get('classroom_id', type=int)
    class_obj = Class.query.get_or_404(class_id)
    student = Student.query.get_or_404(student_id)
    classroom = Classroom.query.get_or_404(classroom_id)
    
    # Safety check: prevent schedule conflict
    for other_class in student.class_enrollments:
        if other_class.class_obj.schedule == class_obj.schedule:
            flash(f'Student is already enrolled in another class ("{other_class.class_obj.name}") at the same time ("{other_class.class_obj.schedule}").', 'danger')
            return redirect(url_for('manage_schedules', teacher_id=class_obj.teacher_id))
    
    # Check if student is already in this class
    existing_enrollment = ClassStudent.query.filter_by(
        class_id=class_id,
        student_id=student_id
    ).first()
    
    if existing_enrollment:
        flash('Student already in class.', 'warning')
    else:
        # Create new enrollment with classroom
        enrollment = ClassStudent(
            class_id=class_id,
            student_id=student_id,
            classroom_id=classroom_id
        )
        db.session.add(enrollment)
        db.session.commit()
        flash('Student added to class.', 'success')
    
    return redirect(url_for('manage_schedules', teacher_id=class_obj.teacher_id))

@app.route('/admin/remove_student_from_class/<int:class_id>/<int:student_id>', methods=['POST'])
@login_required
def remove_student_from_class(class_id, student_id):
    if current_user.role != 'admin':
        abort(403)
    enrollment = ClassStudent.query.filter_by(
        class_id=class_id,
        student_id=student_id
    ).first_or_404()
    
    class_obj = Class.query.get(class_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash('Student removed from class.', 'success')
    return redirect(url_for('manage_schedules', teacher_id=class_obj.teacher_id))

@app.route('/admin/add_users_csv', methods=['GET', 'POST'])
@login_required
def add_users_csv():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)
        
        if not file.filename.endswith('.csv'):
            flash('Please upload a CSV file', 'danger')
            return redirect(request.url)
        
        try:
            # Read CSV file
            stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_data = csv.DictReader(stream)
            
            # Process each row
            success_count = 0
            error_count = 0
            for row in csv_data:
                try:
                    # Validate required fields
                    required_fields = ['name', 'email', 'role', 'password']
                    if not all(field in row for field in required_fields):
                        error_count += 1
                        continue
                    
                    # Check if email already exists
                    if User.query.filter_by(email=row['email']).first():
                        error_count += 1
                        continue
                    
                    # Create new user
                    new_user = User(
                        name=row['name'],
                        email=row['email'],
                        role=row['role']
                    )
                    new_user.set_password(row['password'])
                    
                    db.session.add(new_user)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {str(e)}")
                    continue
            
            db.session.commit()
            flash(f'Successfully added {success_count} users. {error_count} errors occurred.', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'danger')
        
        return redirect(url_for('add_users_csv'))
    
    return render_template('add_users_csv.html')

@app.route('/admin/download_sample_csv')
@login_required
def download_sample_csv():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Create sample CSV data
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['name', 'email', 'role', 'password'])
    
    # Write sample rows
    writer.writerow(['John Doe', 'john@example.com', 'teacher', 'password123'])
    writer.writerow(['Jane Smith', 'jane@example.com', 'student', 'password123'])
    writer.writerow(['Bob Wilson', 'bob@example.com', 'parent', 'password123'])
    
    # Convert to bytes
    output.seek(0)
    bytes_output = BytesIO()
    bytes_output.write(output.getvalue().encode('utf-8'))
    bytes_output.seek(0)
    
    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='sample_users.csv'
    )

@app.route('/copy_class/<int:class_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def copy_class(class_id):
    original_class = Class.query.get_or_404(class_id)
    
    if request.method == 'POST':
        new_teacher_id = request.form.get('teacher_id')
        new_day = request.form.get('day')
        new_time = request.form.get('time')
        new_name = request.form.get('name')
        
        # Combine day and time for schedule
        new_schedule = f"{new_day} {new_time}"
        
        # Create new class
        new_class = Class(
            name=new_name,
            teacher_id=new_teacher_id,
            schedule=new_schedule
        )
        db.session.add(new_class)
        db.session.flush()  # Get the new class ID
        
        # Get all enrollments from original class
        original_enrollments = ClassStudent.query.filter_by(class_id=class_id).all()
        
        # Track successful and failed enrollments
        successful_enrollments = []
        failed_enrollments = []
        
        for enrollment in original_enrollments:
            # Check for scheduling conflicts
            student_id = enrollment.student_id
            classroom_id = enrollment.classroom_id
            
            # Check if student has any classes at the same time
            conflicting_enrollments = ClassStudent.query.join(Class).filter(
                ClassStudent.student_id == student_id,
                Class.schedule == new_schedule
            ).all()
            
            if not conflicting_enrollments:
                # No conflicts, create new enrollment
                new_enrollment = ClassStudent(
                    student_id=student_id,
                    class_id=new_class.id,
                    classroom_id=classroom_id
                )
                db.session.add(new_enrollment)
                successful_enrollments.append(enrollment.student.user.name)
            else:
                failed_enrollments.append(enrollment.student.user.name)
        
        try:
            db.session.commit()
            flash(f'Class copied successfully! {len(successful_enrollments)} students enrolled, {len(failed_enrollments)} students omitted due to scheduling conflicts.', 'success')
            if failed_enrollments:
                flash(f'Students omitted due to conflicts: {", ".join(failed_enrollments)}', 'warning')
            return redirect(url_for('manage_schedules', teacher_id=new_teacher_id))
        except Exception as e:
            db.session.rollback()
            flash('Error copying class. Please try again.', 'error')
            return redirect(url_for('copy_class', class_id=class_id))
    
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('copy_class.html', 
                         original_class=original_class,
                         teachers=teachers)

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create admin user if it doesn't exist
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                name='Admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True) 