from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
from user import UserManager

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'your_secret_key'
        self.user_manager = UserManager()

        self.app.route('/')(self.home)
        self.app.route('/login', methods=['GET', 'POST'])(self.login)
        self.app.route('/register', methods=['GET', 'POST'])(self.register)
        self.app.route('/dashboard')(self.dashboard)
        self.app.route('/logout')(self.logout)

    def run(self):
        self.app.run(debug=True, port=5003)

    def home(self):
        return render_template('index.html')

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.user_manager.verify_user(username, password):
                session['username'] = username
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials. Please try again.'
                return render_template('login.html', error=error)
        return render_template('login.html')

    def register(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.user_manager.is_username_taken(username):
                error = 'Username already taken. Please choose a different username.'
                return render_template('register.html', error=error)
            else:
                self.user_manager.add_user(username, password)
                return redirect(url_for('login'))
        return render_template('register.html')

    def dashboard(self):
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session['username']
        return render_template('dashboard.html', username=username)

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
