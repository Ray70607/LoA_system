from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_migrate import Migrate
import os

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
    
    # Get all classes for this student
    classes = student.classes
    
    return render_template('student_dashboard.html', 
                         absences=absences, 
                         classes=classes, 
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
        
        # Verify the class is scheduled for the selected date
        selected_class = Class.query.get(class_id)
        if not selected_class:
            flash('Invalid class selected')
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
    
    # Get date from query parameters or use today's date
    date_str = request.args.get('date')
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    else:
        date = datetime.now().date()
    
    # Parse the schedule to get the day of week
    schedule_parts = class_record.schedule.split()
    class_day = schedule_parts[0]  # e.g., "Monday"
    days_ahead = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 
        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    day_of_week = days_ahead[class_day]
    
    # Get next 5 class dates
    next_class_dates = []
    current_date = date
    while len(next_class_dates) < 5:
        if current_date.weekday() == day_of_week:
            next_class_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Get approved absences for the selected date and class
    absences = LeaveOfAbsence.query.filter(
        LeaveOfAbsence.class_id == class_id,
        LeaveOfAbsence.date == date,
        LeaveOfAbsence.status == 'approved'
    ).all()
    
    # Get list of student IDs with approved absences
    excused_student_ids = {absence.student_id for absence in absences}
    
    if request.method == 'POST':
        # Get existing attendance records for this date
        existing_records = {
            record.student_id: record 
            for record in Attendance.query.filter_by(
                class_id=class_id,
                date=date
            ).all()
        }
        
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
        for student in class_record.students:
            # Skip if student has an approved absence
            if student.id in excused_student_ids:
                continue
                
            is_present = request.form.get(f'present_{student.id}') == 'on'
            if student.id in existing_records:
                record = existing_records[student.id]
                record.is_present = is_present
                record.is_excused = False
            else:
                record = Attendance(
                    date=date,
                    class_id=class_id,
                    student_id=student.id,
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
    students_to_show = [student for student in class_record.students if student.id not in excused_student_ids]
    
    return render_template('record_attendance.html',
                         class_record=class_record,
                         date=date,
                         next_class_dates=next_class_dates,
                         absences=absences,
                         students_to_show=students_to_show)

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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 