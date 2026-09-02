from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Student Study & Task Manager"


if __name__ == "__main__":
    app.run(debug=True)