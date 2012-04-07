from flask import Flask, request, session, render_template, redirect, url_for, flash
from models import User

app = Flask(__name__)
app.config.from_object('settings')

db = SQLAlchemy(app)

@app.route('/')
def index():
    pass

@app.route('/login', methods=["POST"])
def login():
    error = None
    email = request.form.get('username')
    password = request.form.get('password')
    user = authenticate(email, password)
    # user exists and authed
    if user != None:
        session['user_id']  = user.id
        flash('You were successfully logged in')
        return redirect(url_for('index'))
    # invalid u or p
    else:
        error = 'Your email or password was wrong'
    return render_template(url_for('index'), error=error)

def authenticate(e, p):
    user = User.query.filter_by(email=e).first()
    return None if user is None or not user.check_password_hash(p) else user




            

    
