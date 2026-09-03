from flask import Flask, render_template, request, redirect,url_for
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)

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
 #create the database tables
with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        task_title= request.form.get("task")
        priority = request.form.get("priority")
        due_date = request.form.get("due_date")
        subject = request.form.get("subject")

        if task_title:
            new_task = Task(title=task_title,
                            priority=priority, 
                            due_date=due_date, 
                            subject=subject)
            db.session.add(new_task)
            db.session.commit()
        return redirect("/tasks")    
    total_tasks = Task.query.count()
    completed_tasks = Task.query.filter_by(completed=True).count()
    pending_tasks = Task.query.filter_by(completed=False).count()
    high_priority_tasks = Task.query.filter_by(priority='High').count()
    search = request.args.get("search", "")
    subject = request.args.get("subject", "")
    priority = request.args.get("priority", "")
    status = request.args.get("status", "")

    query = Task.query

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

    tasks_list = query.all()

    return render_template("tasks.html",
                            tasks=tasks_list, 
                            total_tasks=total_tasks,
                            completed_tasks=completed_tasks, 
                            pending_tasks=pending_tasks, 
                            high_priority_tasks=high_priority_tasks,
                            search=search,
                            subject=subject,
                            priority=priority,
                            status=status)


@app.route("/tasks/delete/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("tasks"))


#update
@app.route("/tasks/edit/<int:task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        task.title = request.form.get("task")
        task.priority = request.form.get("priority")
        task.due_date = request.form.get("due_date")
        task.subject = request.form.get("subject")
        if task.title:
            db.session.commit()
            return redirect(url_for("tasks"))

    return render_template("edit_task.html", task=task)


@app.route("/tasks/complete/<int:task_id>", methods=["POST"])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    task.completed = not task.completed

    db.session.commit()

    return redirect(url_for("tasks"))


if __name__ == "__main__":
    app.run(debug=True)