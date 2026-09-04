import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 302

def test_login_page():
    client = app.test_client()

    response = client.get("/login")

    assert response.status_code == 200
    assert b"Login" in response.data

def test_register_page():
    client = app.test_client()

    response = client.get("/register")

    assert response.status_code == 200
    assert b"Register" in response.data    

def test_tasks_requires_login():
    client = app.test_client()

    response = client.get("/tasks")

    assert response.status_code == 302
    assert "/login" in response.location

def test_404_page():
    client = app.test_client()

    response = client.get("/this-page-does-not-exist")

    assert response.status_code == 404    

def test_logout():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "testuser"

    response = client.get("/logout")

    assert response.status_code == 302
    assert "/login" in response.location

def test_register_short_password():
    client = app.test_client()

    response = client.post(
        "/register",
        data={
            "username": "pytest_user",
            "password": "123",
            "confirm_password": "123"
        }
    )

    assert response.status_code == 200
    assert b"at least 8 characters" in response.data
def test_invalid_login():
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "does_not_exist",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data  

def test_register_invalid_username():
    client = app.test_client()

    response = client.post(
        "/register",
        data={
            "username": "test@user!",
            "password": "password123",
            "confirm_password": "password123"
        }
    )

    assert response.status_code == 200
    assert b"Username can only contain letters, numbers, and underscores." in response.data

def test_valid_login():
    client = app.test_client()

    response = client.post(
        "/login",
        data={
            "username": "sanjay",
            "password": "12345678"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]  

def test_valid_login():
    client = app.test_client()

    client.post(
        "/register",
        data={
            "username": "login_test_user",
            "password": "password123",
            "confirm_password": "password123"
        }
    )

    response = client.post(
        "/login",
        data={
            "username": "login_test_user",
            "password": "password123"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]
def test_tasks_after_login():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.get("/tasks")

    assert response.status_code == 200
    assert b"My Tasks" in response.data     
def test_add_task():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/tasks",
        data={
            "task": "Test Task",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]    
def test_delete_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()

        assert user is not None

        task = Task(
            title="Task to Delete",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/delete/{task_id}",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]
def test_complete_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Task to Complete",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/complete/{task_id}",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]    
def test_complete_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Task to Complete",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

        assert task.completed is False

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/complete/{task_id}",
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task.completed is True    
def test_edit_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Original Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/edit/{task_id}",
        data={
            "task": "Updated Task",
            "subject": "MAD-1",
            "priority": "High",
            "due_date": "2026-09-15"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task.title == "Updated Task"
        assert task.subject == "MAD-1"
        assert task.priority == "High"
        assert task.due_date == "2026-09-15"        

def test_user_cannot_delete_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        assert user1 is not None

        user2 = User.query.filter_by(username="sanjay123").first()
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Private Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.post(
        f"/tasks/delete/{task_id}",
        follow_redirects=False
    )

    assert response.status_code == 404

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task is not None

def test_user_cannot_complete_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Protected Complete Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.post(
        f"/tasks/complete/{task_id}",
        follow_redirects=False
    )

    assert response.status_code == 404

    # Verify the task is still incomplete
    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task is not None
        assert task.completed is False
def test_user_cannot_edit_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Protected Edit Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.post(
        f"/tasks/edit/{task_id}",
        data={
            "task": "Hacked Task",
            "subject": "MAD-1",
            "priority": "High",
            "due_date": "2026-09-20"
        },
        follow_redirects=False
    )

    assert response.status_code == 404

    # Verify the original task was not modified
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Protected Edit Task"
        assert task.priority == "Low"        
def test_add_task_empty_title():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/tasks",
        data={
            "task": "",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]
def test_add_task_invalid_priority():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/tasks",
        data={
            "task": "Invalid Priority Task",
            "subject": "Python",
            "priority": "Critical",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]
def test_add_task_invalid_due_date():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/tasks",
        data={
            "task": "Invalid Date Task",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-99-99"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]  
def test_add_task_title_too_long():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    long_title = "A" * 201

    response = client.post(
        "/tasks",
        data={
            "task": long_title,
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]     
def test_add_task_subject_too_long():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    long_subject = "A" * 101

    response = client.post(
        "/tasks",
        data={
            "task": "Test Subject Length",
            "subject": long_subject,
            "priority": "High",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 302
    assert "/tasks" in response.headers["Location"]      
def test_edit_task_invalid_priority():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Edit Validation Task",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/edit/{task_id}",
        data={
            "task": "Edited Task",
            "subject": "Python",
            "priority": "Critical",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 200

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task is not None
        assert task.priority == "Medium"    
def test_edit_task_empty_title():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Original Edit Task",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        f"/tasks/edit/{task_id}",
        data={
            "task": "",
            "subject": "Python",
            "priority": "Medium",
            "due_date": "2026-09-10"
        },
        follow_redirects=False
    )

    assert response.status_code == 200

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Original Edit Task" 

def test_api_tasks_requires_login():
    client = app.test_client()

    response = client.get("/api/tasks")

    assert response.status_code == 401
    assert response.json["error"] == "Authentication required"    

def test_api_tasks_authenticated():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="API Test Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert isinstance(data, list)
    assert any(task["id"] == task_id for task in data)                       
def test_api_tasks_user_isolation():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        task = Task(
            title="Private API Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user1.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

        user2_username = user2.username

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    # User 2 must not see User 1's task
    assert all(task["id"] != task_id for task in data)   
def test_api_task_data():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="API Data Test",
            subject="MAD-1",
            priority="High",
            due_date="2026-09-20",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.get("/api/tasks")

    assert response.status_code == 200

    data = response.get_json()

    api_task = next(
        task for task in data
        if task["id"] == task_id
    )

    assert api_task["title"] == "API Data Test"
    assert api_task["subject"] == "MAD-1"
    assert api_task["priority"] == "High"
    assert api_task["due_date"] == "2026-09-20"
    assert api_task["completed"] is False   


def test_api_create_task_requires_login():
    client = app.test_client()

    response = client.post(
        "/api/tasks",
        json={
            "title": "Unauthorized API Task",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-10"
        }
    )

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()["error"] == "Authentication required" 

def test_api_create_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_username = user.username

    with client.session_transaction() as session:
        session["username"] = user_username

    response = client.post(
        "/api/tasks",
        json={
            "title": "API Created Task",
            "subject": "MAD-1",
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["message"] == "Task created successfully"

    created_task = data["task"]

    assert created_task["title"] == "API Created Task"
    assert created_task["subject"] == "MAD-1"
    assert created_task["priority"] == "High"
    assert created_task["due_date"] == "2026-09-20"
    assert created_task["completed"] is False

    with app.app_context():
        task = db.session.get(Task, created_task["id"])

        assert task is not None
        assert task.title == "API Created Task"
        assert task.user_id == user.id         
def test_api_create_task_empty_title():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "title": "",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Task title is required"     

def test_api_create_task_invalid_priority():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "title": "Invalid Priority API Task",
            "subject": "Python",
            "priority": "Critical",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Invalid priority"     

def test_api_create_task_invalid_due_date():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "title": "Invalid Date API Task",
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-99-99"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Invalid due date"    

def test_api_create_task_title_too_long():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    long_title = "A" * 201

    response = client.post(
        "/api/tasks",
        json={
            "title": long_title,
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Task title must be 200 characters or less"  

def test_api_create_task_subject_too_long():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    long_subject = "A" * 101

    response = client.post(
        "/api/tasks",
        json={
            "title": "API Subject Length Test",
            "subject": long_subject,
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Subject must be 100 characters or less"  

def test_api_create_task_missing_title():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "subject": "Python",
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Task title is required"  

def test_api_create_task_no_json():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post("/api/tasks")

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Task title is required"  

def test_api_create_task_default_priority():
    from app import Task, db

    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "title": "Default Priority API Task",
            "subject": "Python",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["task"]["priority"] == "Medium"
    assert data["task"]["completed"] is False

    with app.app_context():
        task = db.session.get(Task, data["task"]["id"])

        assert task is not None
        assert task.priority == "Medium"       

def test_api_create_task_without_due_date():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.post(
        "/api/tasks",
        json={
            "title": "No Deadline API Task",
            "subject": "Python",
            "priority": "Low"
        }
    )

    assert response.status_code == 201
    assert response.is_json

    data = response.get_json()

    assert data["task"]["title"] == "No Deadline API Task"
    assert data["task"]["due_date"] == ""
    assert data["task"]["completed"] is False       
def test_api_create_task_assigns_correct_user():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

    with client.session_transaction() as session:
        session["username"] = username

    response = client.post(
        "/api/tasks",
        json={
            "title": "User Ownership API Test",
            "subject": "Python",
            "priority": "Medium",
            "due_date": "2026-09-25"
        }
    )

    assert response.status_code == 201

    data = response.get_json()
    task_id = data["task"]["id"]

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.user_id == user_id   

def test_api_create_task_assigns_correct_user():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

    with client.session_transaction() as session:
        session["username"] = username

    response = client.post(
        "/api/tasks",
        json={
            "title": "User Ownership API Test",
            "subject": "Python",
            "priority": "Medium",
            "due_date": "2026-09-25"
        }
    )

    assert response.status_code == 201

    data = response.get_json()
    task_id = data["task"]["id"]

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.user_id == user_id   


def test_api_update_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="Original API Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Updated API Task",
            "subject": "MAD-1",
            "priority": "High",
            "due_date": "2026-09-20"
        }
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["message"] == "Task updated successfully"
    assert data["task"]["title"] == "Updated API Task"
    assert data["task"]["subject"] == "MAD-1"
    assert data["task"]["priority"] == "High"
    assert data["task"]["due_date"] == "2026-09-20"

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Updated API Task"
        assert task.subject == "MAD-1"
        assert task.priority == "High"
        assert task.due_date == "2026-09-20"


def test_api_update_task_requires_login():
    client = app.test_client()

    response = client.put(
        "/api/tasks/1",
        json={
            "title": "Unauthorized Update"
        }
    )

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()["error"] == "Authentication required"    

def test_api_user_cannot_update_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Protected API Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Unauthorized Update",
            "priority": "High"
        }
    )

    assert response.status_code == 404

    # Verify User 1's task was not changed
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Protected API Task"
        assert task.priority == "Low"
def test_api_delete_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="API Delete Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()["message"] == "Task deleted successfully"

    with app.app_context():
        task = db.session.get(Task, task_id)
        assert task is None        

def test_api_delete_task_requires_login():
    client = app.test_client()

    response = client.delete("/api/tasks/1")

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()["error"] == "Authentication required"  

def test_api_user_cannot_delete_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Protected API Delete Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.delete(f"/api/tasks/{task_id}")

    assert response.status_code == 404

    # Verify User 1's task still exists
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Protected API Delete Task" 

def test_api_complete_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="API Complete Task",
            subject="Python",
            priority="Medium",
            due_date="2026-09-20",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}/complete"
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["message"] == "Task status updated successfully"
    assert data["task"]["completed"] is True

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.completed is True 

def test_api_complete_task_requires_login():
    client = app.test_client()

    response = client.put("/api/tasks/1/complete")

    assert response.status_code == 401
    assert response.is_json
    assert response.get_json()["error"] == "Authentication required"  
def test_api_user_cannot_complete_other_users_task():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user1 = User.query.filter_by(username="sanjay").first()
        user2 = User.query.filter_by(username="sanjay123").first()

        assert user1 is not None
        assert user2 is not None

        user1_id = user1.id
        user2_username = user2.username

        task = Task(
            title="Protected API Complete Task",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user1_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    # Login as User 2
    with client.session_transaction() as session:
        session["username"] = user2_username

    response = client.put(
        f"/api/tasks/{task_id}/complete"
    )

    assert response.status_code == 404

    # Verify User 1's task is still incomplete
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.completed is False      

def test_api_update_nonexistent_task():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.put(
        "/api/tasks/999999",
        json={
            "title": "Nonexistent Task"
        }
    )

    assert response.status_code == 404         

def test_api_delete_nonexistent_task():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.delete("/api/tasks/999999")

    assert response.status_code == 404    

def test_api_complete_nonexistent_task():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.put("/api/tasks/999999/complete")

    assert response.status_code == 404  

def test_api_update_task_invalid_priority():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="API Update Validation",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "priority": "Critical"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Invalid priority"

    # Verify the original value was not changed
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.priority == "Medium"   

def test_api_update_task_invalid_due_date():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="API Date Validation",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "due_date": "2026-99-99"
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == "Invalid due date"

    # Verify original date was not changed
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.due_date == "2026-09-10" 

def test_api_update_task_title_too_long():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="Original API Title",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    long_title = "A" * 201

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": long_title
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == \
        "Task title must be 200 characters or less"

    # Verify the original title was not changed
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.title == "Original API Title"   
def test_api_update_task_subject_too_long():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="Original API Subject",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    long_subject = "A" * 101

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "subject": long_subject
        }
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["error"] == \
        "Subject must be 100 characters or less"

    # Verify the original subject was not changed
    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task is not None
        assert task.subject == "Python" 
def test_api_update_task_partial():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="Original Partial Task",
            subject="Python",
            priority="Low",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "title": "Updated Partial Task"
        }
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["task"]["title"] == "Updated Partial Task"
    assert data["task"]["subject"] == "Python"
    assert data["task"]["priority"] == "Low"
    assert data["task"]["due_date"] == "2026-09-10"

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task.title == "Updated Partial Task"
        assert task.subject == "Python"
        assert task.priority == "Low"
        assert task.due_date == "2026-09-10" 

def test_api_update_task_completed_only():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        user_id = user.id
        username = user.username

        task = Task(
            title="Completion API Test",
            subject="Python",
            priority="High",
            due_date="2026-09-10",
            user_id=user_id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={
            "completed": True
        }
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["task"]["completed"] is True
    assert data["task"]["title"] == "Completion API Test"
    assert data["task"]["priority"] == "High"

    with app.app_context():
        task = db.session.get(Task, task_id)

        assert task.completed is True
        assert task.title == "Completion API Test"
        assert task.priority == "High"

def test_api_update_task_empty_json():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="Empty JSON Update",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id
        username = user.username

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(
        f"/api/tasks/{task_id}",
        json={}
    )

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["task"]["title"] == "Empty JSON Update"
    assert data["task"]["subject"] == "Python"
    assert data["task"]["priority"] == "Medium"
    assert data["task"]["due_date"] == "2026-09-10" 

def test_api_update_task_no_json():
    from app import Task, User, db

    client = app.test_client()

    with app.app_context():
        user = User.query.filter_by(username="sanjay").first()
        assert user is not None

        task = Task(
            title="No JSON Update",
            subject="Python",
            priority="Medium",
            due_date="2026-09-10",
            user_id=user.id
        )

        db.session.add(task)
        db.session.commit()

        task_id = task.id
        username = user.username

    with client.session_transaction() as session:
        session["username"] = username

    response = client.put(f"/api/tasks/{task_id}")

    assert response.status_code == 200
    assert response.is_json

    data = response.get_json()

    assert data["task"]["title"] == "No JSON Update"
    assert data["task"]["subject"] == "Python"
    assert data["task"]["priority"] == "Medium"
    assert data["task"]["due_date"] == "2026-09-10"

def test_api_tasks_json_response():
    client = app.test_client()

    with client.session_transaction() as session:
        session["username"] = "sanjay"

    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.content_type.startswith("application/json")
    assert isinstance(response.get_json(), list)    
           
                                                                                                                       