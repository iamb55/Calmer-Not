from flaskext.mail import Mail
from flask import Flask, request, session, render_template, redirect, url_for, flash, jsonify
from models import User

app = Flask(__name__)
app.config.from_object('settings')

db = SQLAlchemy(app)
mail = Mail(app)

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
    # TODO: check if verified
    return None if user is None or not user.check_password_hash(p) else user

@app.route('/register', methods=['POST'])
def register():
    school = request.form.get('school')
    email = request.form.get('email')
    password = request.form.get('password')

    user = User(school,email,password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id

    return redirect(url_for('app.home'))

@app.route('/validate')
def validate():
    word = request.args.get('word') 
    base = request.args.get('base') 
    # are letters in word in base?
    in_base = reduce(lambda acc, c : (c in base) and acc, word, True)
    # is word a valid english word?
    if (word in words or words in six) and in_base:
        return jsonify(valid=True)
    else:
        return jsonify(valid=False)

