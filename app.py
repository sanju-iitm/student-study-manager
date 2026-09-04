from datetime import timedelta,datetime
import os
import re
import secrets
from flask import Flask, jsonify, render_template, request, redirect,url_for,session,flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case

app = Flask(__name__)

##secret key for session management
app.secret_key = os.environ.get("SECRET_KEY","sanjuiitm605") 

app.permanent_session_lifetime = timedelta(days=30)

#database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#task database model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100))
    priority = db.Column(db.String(20),default='Medium')
    due_date = db.Column(db.String(20))
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now())

#user database model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    tasks = db.relationship("Task", backref="user", lazy=True)

## registration route    
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            return render_template("register.html",error="Username can only contain letters, numbers, and underscores.")
        
        if password != confirm_password:
            return render_template("register.html",error="Passwords do not match. Please try again.")

        if len(password) < 8:
            return render_template("register.html",error="Password must be at least 8 characters long.")

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return  render_template("register.html",error="Username already exists. Please choose another.")

        password_hash = generate_password_hash(password)

        new_user = User(
            username=username,
            password_hash=password_hash
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

 #create the database tables
with app.app_context():
    db.create_all()


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("tasks"))
    return redirect(url_for("login"))


#login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user=User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["username"] = username
            if request.form.get("remember"):
                session.permanent = True
            else:
                session.permanent = False
            return redirect(url_for("tasks"))

        return render_template("login.html",error="Invalid username or password")

    return render_template("login.html")

#logout route
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()

    if request.method == "POST":
        task_title= request.form.get("task","").strip()
        priority = request.form.get("priority","Medium").strip()
        due_date = request.form.get("due_date","").strip()
        subject = request.form.get("subject","").strip()

        if len(subject) > 100:
            flash("Subject must be 100 characters or less.", "error")
            return redirect(url_for("tasks"))

        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                flash("Invalid due date.", "error")
                return redirect(url_for("tasks"))

        if priority not in ["Low", "Medium", "High"]:
            flash("Invalid priority selected.", "error")
            return redirect(url_for("tasks"))

        if task_title:
            if len(task_title) > 200:
                flash("Task title must be 200 characters or less.", "error")
                return redirect(url_for("tasks"))
            new_task = Task(title=task_title,
                            priority=priority, 
                            due_date=due_date, 
                            subject=subject,
                            user_id=user.id)
            db.session.add(new_task)
            db.session.commit()
            flash("Task added successfully!", "success")
        return redirect("/tasks")    
    ##statistics for tasks

    total_tasks = Task.query.filter_by(user_id=user.id).count()
    completed_tasks = Task.query.filter_by(user_id=user.id,completed=True).count()
    pending_tasks = Task.query.filter_by(user_id=user.id,completed=False).count()
    high_priority_tasks = Task.query.filter_by(user_id=user.id,priority="High").count() 

    #filtering and searching tasks
    search = request.args.get("search", "")
    subject = request.args.get("subject", "")
    priority = request.args.get("priority", "")
    status = request.args.get("status", "")
    sort = request.args.get("sort", "newest")
    today_filter = request.args.get("today", "")
    due_soon_filter = request.args.get("due_soon", "")
    overdue_filter = request.args.get("overdue", "")

    query = Task.query.filter_by(user_id=user.id)

    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    if subject:
        query = query.filter_by(subject=subject)

    if priority:
        query = query.filter_by(priority=priority)

    if status == "completed":
        query = query.filter_by(completed=True)
    elif status == "pending":
        query = query.filter_by(completed=False)
    if today_filter == "1":
        query = query.filter(Task.due_date == datetime.today().strftime("%Y-%m-%d"))  
    if due_soon_filter == "1":
        query = query.filter(
        Task.completed == False,
        Task.due_date >= today.strftime("%Y-%m-%d"),
        Task.due_date <= due_soon.strftime("%Y-%m-%d"))  
    if overdue_filter == "1":
        query = query.filter(
        Task.completed == False,
        Task.due_date < today.strftime("%Y-%m-%d"))            

    if sort == "due":
        tasks_list = query.order_by(
            case(
            (Task.due_date.is_(None), 1),
            (Task.due_date == "", 1),
            else_=0),
        Task.due_date.asc()).all()
    else:
        tasks_list = query.order_by(Task.created_at.desc()).all()
    today = datetime.today().date()
    due_soon = today + timedelta(days=3)
    due_soon_tasks = Task.query.filter(
        Task.user_id == user.id,
        Task.completed == False,
        Task.due_date != None,
        Task.due_date != "",
        Task.due_date >= today.strftime("%Y-%m-%d"),
        Task.due_date <= due_soon.strftime("%Y-%m-%d")).count()
    due_today_tasks = Task.query.filter(
        Task.user_id == user.id,
        Task.completed == False,
        Task.due_date == today.strftime("%Y-%m-%d")).count()
    overdue_tasks = Task.query.filter(
        Task.user_id == user.id,
        Task.completed == False,
        Task.due_date != None,
        Task.due_date != "",
        Task.due_date < today.strftime("%Y-%m-%d")).count()

    return render_template("tasks.html",
                            tasks=tasks_list, 
                            total_tasks=total_tasks,
                            completed_tasks=completed_tasks, 
                            pending_tasks=pending_tasks, 
                            high_priority_tasks=high_priority_tasks,
                            due_soon_tasks=due_soon_tasks,
                            search=search,
                            subject=subject,
                            priority=priority,
                            status=status,
                            sort=sort,
                            today=today,
                            due_soon=due_soon,
                            today_filter=today_filter,
                            due_today_tasks=due_today_tasks,
                            due_soon_filter=due_soon_filter,
                            overdue_filter=overdue_filter,
                            overdue_tasks=overdue_tasks)

##add api route
@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

    user = User.query.filter_by(username=session["username"]).first()

    tasks = Task.query.filter_by(user_id=user.id).order_by(
        Task.created_at.desc()
    ).all()

    return jsonify([
        {
            "id": task.id,
            "title": task.title,
            "subject": task.subject,
            "priority": task.priority,
            "due_date": task.due_date,
            "completed": task.completed
        }
        for task in tasks
    ])

@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip()
    subject = data.get("subject", "").strip()
    priority = data.get("priority", "Medium").strip()
    due_date = data.get("due_date", "").strip()

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    if len(title) > 200:
        return jsonify({"error": "Task title must be 200 characters or less"}), 400

    if len(subject) > 100:
        return jsonify({"error": "Subject must be 100 characters or less"}), 400

    if priority not in ["Low", "Medium", "High"]:
        return jsonify({"error": "Invalid priority"}), 400

    if due_date:
        try:
            datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({"error": "Invalid due date"}), 400

    user = User.query.filter_by(username=session["username"]).first()

    new_task = Task(
        title=title,
        subject=subject,
        priority=priority,
        due_date=due_date,
        user_id=user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "message": "Task created successfully",
        "task": {
            "id": new_task.id,
            "title": new_task.title,
            "subject": new_task.subject,
            "priority": new_task.priority,
            "due_date": new_task.due_date,
            "completed": new_task.completed
        }
    }), 201

@app.route("/api/tasks/<int:task_id>", methods=["PUT"])
def api_update_task(task_id):
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(data["title"]).strip()

        if not title:
            return jsonify({"error": "Task title is required"}), 400

        if len(title) > 200:
            return jsonify({
                "error": "Task title must be 200 characters or less"
            }), 400

        task.title = title

    if "subject" in data:
        subject = str(data["subject"]).strip()

        if len(subject) > 100:
            return jsonify({
                "error": "Subject must be 100 characters or less"
            }), 400

        task.subject = subject

    if "priority" in data:
        priority = str(data["priority"]).strip()

        if priority not in ["Low", "Medium", "High"]:
            return jsonify({"error": "Invalid priority"}), 400

        task.priority = priority

    if "due_date" in data:
        due_date = str(data["due_date"]).strip()

        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                return jsonify({"error": "Invalid due date"}), 400

        task.due_date = due_date

    if "completed" in data:
        task.completed = bool(data["completed"])

    db.session.commit()

    return jsonify({
        "message": "Task updated successfully",
        "task": {
            "id": task.id,
            "title": task.title,
            "subject": task.subject,
            "priority": task.priority,
            "due_date": task.due_date,
            "completed": task.completed
        }
    }), 200

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def api_delete_task(task_id):
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()

    return jsonify({
        "message": "Task deleted successfully"
    }), 200

@app.route("/api/tasks/<int:task_id>/complete", methods=["PUT"])
def api_complete_task(task_id):
    if "username" not in session:
        return jsonify({"error": "Authentication required"}), 401

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

    task.completed = not task.completed
    db.session.commit()

    return jsonify({
        "message": "Task status updated successfully",
        "task": {
            "id": task.id,
            "title": task.title,
            "completed": task.completed
        }
    }), 200


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

    db.session.delete(task)
    db.session.commit()
    flash("Task deleted successfully!", "success")

    return redirect(url_for("tasks"))


#update
@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):

    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

     
    if request.method == "POST":
        task.title = request.form.get("task", "").strip()
        task.subject = request.form.get("subject", "").strip()
        task.priority = request.form.get("priority", "Medium").strip()
        task.due_date = request.form.get("due_date", "").strip()

        if not task.title:
            flash("Task title cannot be empty.", "error")
            return render_template("edit_task.html", task=task)

        if len(task.title) > 200:
            flash("Task title must be 200 characters or less.", "error")
            return render_template("edit_task.html", task=task)

        if len(task.subject) > 100:
            flash("Subject must be 100 characters or less.", "error")
            return render_template("edit_task.html", task=task)

        if task.priority not in ["Low", "Medium", "High"]:
            flash("Invalid priority selected.", "error")
            return render_template("edit_task.html", task=task)

        if task.due_date:
            try:
                datetime.strptime(task.due_date, "%Y-%m-%d")
            except ValueError:
                flash("Invalid due date.", "error")
                return render_template("edit_task.html", task=task)
        if task.title:
            db.session.commit()
            flash("Task updated successfully!", "success")
            return redirect(url_for("tasks"))

    return render_template("edit_task.html", task=task)


@app.route("/tasks/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session["username"]).first()

    task = Task.query.filter_by(
        id=task_id,
        user_id=user.id
    ).first_or_404()

    task.completed = not task.completed
    db.session.commit()
    if task.completed:
        flash("Task marked as completed!", "success")
    else:
        flash("Task marked as pending.", "success")

    return redirect(url_for("tasks"))

##change password route
@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "username" not in session:
        return redirect(url_for("login"))

    user = User.query.filter_by(
        username=session["username"]
    ).first()
    if user is None:
       session.pop("username", None)
       return redirect(url_for("login"))

    if request.method == "POST":

        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not check_password_hash(
            user.password_hash,
            current_password
        ):
            return render_template(
                "change_password.html",
                error="Current password is incorrect."
            )

        if len(new_password) < 8:
            return render_template(
                "change_password.html",
                error="New password must be at least 8 characters long."
            )

        if new_password != confirm_password:
            return render_template(
                "change_password.html",
                error="New passwords do not match."
            )

        user.password_hash = generate_password_hash(new_password)

        db.session.commit()
        flash("Password changed successfully!", "success")


        return redirect(url_for("tasks"))

    return render_template("change_password.html")
##forgot password route
@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form.get("username", "").strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            return render_template(
                "forgot_password.html",
                message="If the account exists, a password reset link has been generated."
            )

        reset_token = secrets.token_urlsafe(32)

        user.reset_token = reset_token
        user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)

        db.session.commit()

        reset_link = url_for(
            "reset_password",
            token=reset_token,
            _external=True
        )

        return f"""
           <h2>Password Reset</h2>
           <p>If the account exists, a reset link has been generated.</p>
           <p><a href="{reset_link}">Open reset link</a></p>"""

    return render_template("forgot_password.html")
##reset password route

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return "Invalid or expired reset link."

    if not user.reset_token_expiry or user.reset_token_expiry < datetime.utcnow():
        return "Invalid or expired reset link."

    if request.method == "POST":

        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 8:
            return render_template(
                "reset_password.html",
                error="Password must be at least 8 characters long."
            )

        if password != confirm_password:
            return render_template(
                "reset_password.html",
                error="Passwords do not match."
            )

        user.password_hash = generate_password_hash(password)

        # Invalidate the reset token
        user.reset_token = None
        user.reset_token_expiry = None

        db.session.commit()

        return  render_template("reset_success.html")

    return render_template("reset_password.html")
##error handling
@app.errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)