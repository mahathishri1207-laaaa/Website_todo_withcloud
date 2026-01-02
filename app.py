import os
from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth

# 1. Load hidden keys from .env file
load_dotenv()

# 2. Initialize Flask App
app = Flask(__name__)
app.secret_key = "my_cloud_todo_secret_123"

# 3. Setup Google OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

# 4. Cloud Database Configuration
MONGO_URI = "mongodb+srv://mahathishri1207_db_user:NenuNuvvudbMmM@cluster0.vrhdyri.mongodb.net/?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true&connectTimeoutMS=30000"

client = MongoClient(MONGO_URI)
db = client.todo_app        
users_col = db.users        
tasks_col = db.tasks        

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas")
except Exception as e:
    print(f"Error connecting to Cloud: {e}")

# --- GOOGLE AUTH ROUTES ---

@app.route('/login/google')
def google_login():
    # This sends the user to Google's login page
    redirect_uri = url_for('google_auth', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def google_auth():
    # Google sends the user back here
    token = google.authorize_access_token()
    user_info = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    
    # Check if this Google user exists in our DB
    user = users_col.find_one({"email": user_info['email']})
    
    if not user:
        # Create new user if they don't exist
        new_user = {
            "username": user_info['name'],
            "email": user_info['email'],
            "google_id": user_info['sub']
        }
        user_id = users_col.insert_one(new_user).inserted_id
    else:
        user_id = user['_id']

    # Set session data
    session['user_id'] = str(user_id)
    session['username'] = user_info['name']
    return redirect(url_for('dashboard'))

# --- STANDARD ROUTES ---

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
        session['username'] = user.get('username', 'User')
        return redirect(url_for('dashboard'))
    return "Invalid credentials. <a href='/'>Try again</a>"

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
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
    