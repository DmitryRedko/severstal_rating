from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from user import UserManager,AdminManager
from config import dictionary, db_settings
from database import DataBase

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your_secret_key'
        self.user_manager = UserManager()
        self.admin_manager = AdminManager(dictionary)

        self.app.route('/')(self.home)
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/admin', methods=['GET', 'POST'])(self.admin)
        self.app.route('/dashboard', methods=['GET', 'POST'])(self.dashboard)
        self.app.route('/logout')(self.logout)

    def run(self):
        self.app.run(debug=True, port=5000)

    def home(self):
        return render_template('index.html')

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.user_manager.verify_user(username, password):
                session['username'] = username
                session['password'] = password  # Сохраняем пароль в сеансе
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('login.html', error=error)
        return render_template('login.html')

    def admin(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            print(username,password)
            if self.admin_manager.verify_admin(username, password):
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('admin.html', error=error)
        return render_template('admin.html')

    def dashboard(self, password = None):
        if password is None:
             password = session.get('password')
        
        db = DataBase(db_settings)
        colleagues = db.get_colleagues(password,0)
        
        username = db.get_head_service_name(password)
        
        print(username)

        return render_template('dashboard.html', username=username, colleagues_list=colleagues)

    def logout(self):
        session.pop('username', None)
        return redirect(url_for('home'))

    @staticmethod
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'username' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
