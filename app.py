import hmac
import sqlite3
from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from datetime import timedelta


class UsersInfo(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def user_table():
    with sqlite3.connect('to_do_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users ("
                       "user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                       "full_name TEXT NOT NULL,"
                       "username TEXT NOT NULL,"
                       "password TEXT NOT NULL)")

        print("user table created successfully")


def tasks_table():
    with sqlite3.connect('to_do_list.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "user_id INTEGER,"
                     "category TEXT NOT NULL,"
                     "description TEXT NOT NULL,"
                     "FOREIGN KEY (user_id) REFERENCES users(user_id))")
    print("today table created successfully.")


user_table()
tasks_table()


def fetch_users():
    with sqlite3.connect('to_do_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        user_data = []
        for data in users:
            user_data.append(UsersInfo(data[0], data[2], data[3]))
    return user_data


users = fetch_users()
username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
CORS(app)
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=86400)
jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/registration/', methods=["POST"])
def registration():
    response = {}

    if request.method == "POST":

        full_name = request.json['full_name']
        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("to_do_list.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users ("
                           "full_name,"
                           "username,"
                           "password) VALUES(?, ?, ?)", (full_name, username, password))
            conn.commit()
            response["message"] = "success"
            response["status_code"] = 201
        return response


@app.route("/user_login/", methods=["POST"])
def user_login():
    response = {}

    if request.method == "POST":
        username = request.json['username']
        password = request.json['password']

        with sqlite3.connect("to_do_list.db") as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username,
                                                                                   password))
            user_info = cursor.fetchone()

            response["status_code"] = 200
            response["message"] = "User logged in successfully"
            response["user"] = user_info
        return response

    else:
        response["status_code"] = 404
        response["user"] = "user not found"
        response["message"] = "User logged in unsuccessfully"
    return response


@app.route('/add-task/', methods=["POST"])
# # @jwt_required()
def add_task():
    response = {}

    if request.method == "POST":
        category = request.json['category']
        description = request.json['description']

        with sqlite3.connect('to_do_list.db') as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks ("
                           "category,"
                           "description) VALUES (?,?)", (category, description))
            conn.commit()
            response["status_code"] = 201
            response['description'] = "task added successfully"
        return response


@app.route("/delete-task/<int:id>/")
# # @jwt_required()
def delete_task(id):
    response = {}
    with sqlite3.connect("to_do_list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=" + str(id))
        conn.commit()
        response['status_code'] = 200
        response['message'] = "task deleted successfully."
        
    return response


@app.route('/edit-task/<int:id>/', methods=["PUT"])
# @jwt_required()
def edit_task(id):
    response = {}

    if request.method == "PUT":
        with sqlite3.connect('to_do_list.db') as conn:
            incoming_data = dict(request.json)
            put_data = {}

            if incoming_data.get("category") is not None and incoming_data.get("description") is not None:
                put_data["category"] = incoming_data.get("category")
                put_data["description"] = incoming_data.get("description")
                with sqlite3.connect('to_do_list.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET category=? WHERE id=?", (put_data["category"],
                                                                              id))
                    conn.commit()

                    cursor.execute("UPDATE tasks SET description=? WHERE id=?", (put_data["description"],
                                                                                 id))
                    conn.commit()
                    response['message'] = "Updated successfully"
                    response['status_code'] = 200

            elif incoming_data.get("category") is not None:
                put_data["category"] = incoming_data.get("category")
                with sqlite3.connect('to_do_list.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET category =? WHERE id=?", (put_data["category"], id))
                    conn.commit()
                    response['message'] = "Updated successfully"
                    response['status_code'] = 200

            elif incoming_data.get("description") is not None:
                put_data["description"] = incoming_data.get("description")
                with sqlite3.connect('to_do_list.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET description =? WHERE id=?", (put_data["description"], id))
                    conn.commit()
                    response['message'] = "Updated successfully"
                    response['status_code'] = 200
    return response


@app.route('/view-tasks/', methods=["GET"])
def view_tasks():
    response = {}
    with sqlite3.connect("to_do_list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")

        tasks = cursor.fetchall()

    response['status_code'] = 200
    response['data'] = tasks
    return response


@app.route('/view-task/<int:id>/', methods=["GET"])
def view_task(id):
    response = {}
    with sqlite3.connect("to_do_list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id=?", str(id))

        tasks = cursor.fetchone()

    response['status_code'] = 200
    response['data'] = tasks
    return jsonify(response)


@app.route('/view-category/<category>/', methods=["GET"])
def view_category(category):
    response = {}
    with sqlite3.connect("to_do_list.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE category=?", [category])

        tasks = cursor.fetchone()

    response['status_code'] = 200
    response['data'] = tasks
    return response


if __name__ == '__main__':
    app.run()


