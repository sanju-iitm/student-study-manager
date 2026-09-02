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
        if task_title:
            new_task = Task(title=task_title)
            db.session.add(new_task)
            db.session.commit()
        return redirect("/tasks")    
    tasks_list = Task.query.all()    

    return render_template("tasks.html", tasks=tasks_list)


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