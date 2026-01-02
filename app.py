from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv
load_dotenv()

google_id = os.getenv("GOOGLE_CLIENT_ID")
google_secret = os.getenv("GOOGLE_CLIENT_SECRET")

app = Flask(__name__)

# This key secures your login sessions.
app.secret_key = "my_cloud_todo_secret_123"

# --- CLOUD DATABASE CONFIGURATION ---
MONGO_URI = MONGO_URI = "mongodb+srv://mahathishri1207_db_user:NenuNuvvudbMmM@cluster0.vrhdyri.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&connectTimeoutMS=30000"

# We define these outside the try block so 'users_col' is always defined
client = MongoClient(MONGO_URI)
db = client.todo_app        
users_col = db.users        
tasks_col = db.tasks        

try:
    # This line checks if the connection is actually working
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Error connecting to Cloud: {e}")

# --- ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Now users_col is guaranteed to be defined
        if users_col.find_one({"username": username}):
            return "Username already exists! Try another."
            
        users_col.insert_one({"username": username, "password": password})
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = users_col.find_one({"username": username, "password": password})
    
    if user:
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        return redirect(url_for('dashboard'))
    return "Invalid username or password. <a href='/'>Try again</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    # We fetch tasks and pass the username to the header
    user_tasks = list(tasks_col.find({"user_id": session['user_id']}))
    return render_template('dashboard.html', tasks=user_tasks, username=session.get('username', 'User'))

@app.route('/add', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('index'))
        
    new_task = {
        "user_id": session['user_id'],
        "description": request.form.get('description'),
        "deadline": request.form.get('deadline'),
        "priority": request.form.get('priority')
    }
    tasks_col.insert_one(new_task)
    return redirect(url_for('dashboard'))

@app.route('/delete/<id>')
def delete_task(id):
    if 'user_id' in session:
        tasks_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)