# Importing Libraries
from flask import Flask, render_template, jsonify, request
from flask  import redirect, url_for, session, flash
from functools import wraps
from passlib.hash import pbkdf2_sha256
from flask_pymongo import PyMongo
import urllib, jinja2, time
from datetime import datetime

# Globals
info = {
    'logged_in' : False,
    'user' : {},
    'tasks' : [],
    'status_login' : {
        'value' : '',
        'positive' : True
    },
    'status_register' : {
        'value' : '',
        'positive' : True
    },
    'status_task' : {
        'value' : '',
        'positive' : True
    }
}


def reset():
    '''
    function to reset the info object
    '''
    global info
    info['status_login'] = {
        'value' : '',
        'positive' : True
    }
    info['status_register'] = {
        'value' : '',
        'positive' : True
    }
    info['status_task'] = {
        'value' : '',
        'positive' : True
    }


# Creating an app
app = Flask(__name__)
app.secret_key = "TODO: Add your system generated scret key here"


# Setting Up Database Connection
collection = "TODO: Add your collection name here"
app.config['MONGO_URI'] = "TODO: Paste your MongoDB URI here"
mongo = PyMongo(app)


# Setting Up Route for Index Page
@app.route('/')
def index():
    '''
    function to render 'index' page, i.e main page of site
    '''
    return render_template('index.html')


# Decorator Function
def login_required(dashboard_access):
    '''
    params: dashboard_access: function through which dashboard access was requested
    decorator function to check if the user directly trying to access dashboard is logged in or not
    '''
    @wraps(dashboard_access)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return dashboard_access(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap


# Setting Up Route for Login Page
@app.route('/login/', methods=['POST', 'GET'])
def login():
    '''
    function to login and render dashboard for user
    '''
    global info
    global collection

    # Fetching Form Data
    user = {
        "username": request.form.get('username'),
        "password": request.form.get('password'),
    }

    # Checking the Credentials
    if user['username'] != None:
        if mongo.db.collection.find_one({"username": user["username"]}) and pbkdf2_sha256.verify(user['password'], mongo.db.collection.find_one({"username": user["username"]})['password']):
            det = mongo.db.collection.find_one({"username": user["username"]})     # Fetching Data and Storing
            name = det['name']
            user['name'] = name
            del user['password']
            session['logged_in'] = True
            session['user'] = user
            info['tasks'] = det['tasks']
            info['status_login']['value'] = ''
            info['status_login']['positive'] = True
            return redirect(url_for('dashboard'))                               # Sending all Data to Function
        else:
            info['status_login']['value'] = 'Username or Password Incorrect'
            info['status_login']['positive'] = False
            return redirect(url_for('login'))
    status_val_login = info['status_login']['value']
    positive_status_login = info['status_login']['positive']
    status_val_register = info['status_register']['value']
    positive_status_register = info['status_register']['positive']
    reset()
    return render_template('login.html', value_login = status_val_login, positive_login = positive_status_login, value_register = status_val_register, positive_register = positive_status_register)


# Setting Up Route for Register Page
@app.route('/register/', methods=['GET', 'POST'])
def register():
    '''
    function to register an account into the server and database
    '''
    global info
    global collection

    # Fetching Form Data
    user = {
        "name": request.form.get('name'),
        "email": request.form.get('email'),
        "username": request.form.get('username'),
        "password": request.form.get('password'),
        "tasks":[]
    }

    repassword = request.form.get('repassword')
    # Inserting data to Database Redirecting to Login Page after Successful Registration
    if user['name'] != None:
        if user['password'] == repassword:
            user['password'] = pbkdf2_sha256.encrypt(user['password'])
            if mongo.db.collection.find_one({"username": user["username"]}):
                info['status_register']['value'] = 'Username Already Taken'
                info['status_register']['positive'] = False
                return redirect(url_for('register'))
            else:
                mongo.db.collection.insert(user)
                info['status_register']['value'] = 'Registered Successfully'
                info['status_register']['positive'] = True
                return redirect(url_for('login'))
        else:
            info['status_register']['value'] = 'Both password fields should match'
            info['status_register']['positive'] = False
    status_val = info['status_register']['value']
    positive_status = info['status_register']['positive']
    reset()
    return render_template('register.html', value = status_val, positive = positive_status)


# Setting Up Route for Register Page
@app.route('/dashboard/', methods=['GET', 'POST'])
@login_required
def dashboard():
    '''
    function to render dashboard on successful login attempt
    '''
    global info
    info['logged_in'] = session['logged_in']
    info['user'] = session['user']

    # Generating and Gathering Data for Database Insertion
    tasks_titles = [list(task_det.keys())[0] for task_det in list(info['tasks'])]
    tasks_completion_times = []
    for task_title, idx in zip(tasks_titles, range(len(tasks_titles))):
        tasks_completion_times.append(str(list(info['tasks'])[idx][task_title]['completion_date']).split()[0])
    tasks_descriptions = []
    for task_title, idx in zip(tasks_titles, range(len(tasks_titles))):
        tasks_descriptions.append(list(info['tasks'])[idx][task_title]['description'])
    tasks_status = []
    for task_title, idx in zip(tasks_titles, range(len(tasks_titles))):
        tasks_status.append(list(info['tasks'])[idx][task_title]['completion_status'])
    tasks = [[title, date, desc, status] for title, date, desc, status in zip(tasks_titles, tasks_completion_times, tasks_descriptions, tasks_status)]
    
    def takeDate(elem):
        '''
        generator function to sort the tasks according to their completion times
        params: elem: object that is needed to be sort
        return: elem[1]: index through which the sorting will be initialized
        '''
        return elem[1]

    
    tasks.sort(key=takeDate)                # sorting tasks
    today_date = str(datetime.now()).split(' ')[0]
    user = info['user']
    status_login_val = info['status_login']['value']
    login_positive_status = info['status_login']['positive']
    status_task_val = info['status_task']['value']
    task_positive_status = info['status_task']['positive']
    reset()
    return render_template('dashboard.html', tasks=tasks, login_details=user, positive_login=login_positive_status, task_value=status_task_val, positive_task=task_positive_status, date=today_date)


@app.route('/logout/')
def logout():
    '''
    function to logout of account
    '''
    session.clear()                         # destroying session info
    return redirect(url_for('index'))


@app.route('/add_todo', methods=['GET', 'POST'])
def add_todo():
    '''
    function to add a todo
    '''
    global info
    global collection

    # Fetching Form Data
    task_title = request.form.get('add_task')
    completion_date = request.form.get('completion_date')
    task_description = request.form.get('description')

    # Validating Input Data
    date = datetime.strptime(f'{completion_date} 00:00:00', '%Y-%m-%d %H:%M:%S')
    date_today = datetime.strptime(f'{str(datetime.now()).split()[0]} 00:00:00', '%Y-%m-%d %H:%M:%S')
    if date < date_today:
        info['status_task']['value'] = 'Date of Completion must be greater than or equal to Today'
        info['status_task']['positive'] = False
    elif task_title in [list(i.keys())[0] for i in list(info['tasks'])]:
        info['status_task']['value'] = 'Task Already Exists'
        info['status_task']['positive'] = False
    elif len(task_title) > 30:
        info['status_task']['value'] = 'Task Title too long. Max 30 characters allowed.'
        info['status_task']['positive'] = False
    else:
        info['status_task']['positive'] = True

        # Filling Data into Database
        condition = {"username" : session['user']["username"]}
        update_value = {
            "$push" : {
                "tasks" : {
                    task_title : {
                        "completion_date" : date,
                        "description" : task_description,
                        "completion_status" : "Not Yet Completed"
                    }
                }
            }
        }
        mongo.db.collection.update(condition, update_value)
        det = mongo.db.collection.find_one({"username": session['user']["username"]})
        info['tasks'] = det['tasks']
    return redirect(url_for('dashboard'))


@app.route('/complete_todo/<title>')
def complete_todo(title):
    global collection
    condition = {
        "username" : session['user']["username"],
        f"tasks.{title}" : {
            "$exists" : True
        }
    }
    update_value = {
        "$set" : {
            f"tasks.$.{title}.completion_status" : str(datetime.now()).split(' ')[0]
        }
    }
    response = mongo.db.collection.update(condition, update_value)
    det = mongo.db.collection.find_one({"username": session['user']["username"]})
    info['tasks'] = det['tasks']
    return redirect(url_for('dashboard'))


@app.route('/delete_todo/<title>')
def delete_todo(title):
    global collection
    condition = {
        "username" : session['user']["username"],
    }
    update_value = {
        "$pull" : {
            "tasks" : {
                title : { 
                    "$exists" : True
                }
            }
        }
    }
    response = mongo.db.collection.update(condition, update_value)
    det = mongo.db.collection.find_one({"username": session['user']["username"]})
    info['tasks'] = det['tasks']
    return redirect(url_for('dashboard'))


# Driver Code
if __name__ == "__main__":
    app.run(debug=True)