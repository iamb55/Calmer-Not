from flaskext.mail import Mail, Message
from flask import Flask, request, session, render_template, redirect, url_for, flash
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
    return None if user is None or not user.check_password_hash(p) else user


@app.route('/register', methods=['POST'])
def register():
    error = None
    email = request.form.get('email')
    password = request.form.get('password')

    school = emailAuth(email)
    if not school:
        error = 'Invalid email address'

    user = User(school,email,password)
    db.session.add(user)
    db.session.commit()

    sendConfirmation(user.id,email)

    session['user_id'] = user.id

    return redirect(url_for('index'),error=error)

def sendConfirmation(id,email):
    confkey = generateUnique()

    link = '<p><a href=%s/confirm?confkey=%s' % (base_url,confkey)
    body = '<p>Please confirm your email address by clicking the link below:</p>' + link)
    subj = '5C Word Warp - Email Confirmation'

    r.set(confkey,id)

    msg = Message(html=body,subject=subj,recipients=[email])
    mail.send(msg)

@app.route('/confirm', methods=['GET'])
def confirm():
    error = None
    key = request.args.get('confkey')

    if key = None:
        error = 'Invalid confirmation key' 
    id = r.get(key)
    if id = None:
        error = 'No such user'

    user = User.query.get(id)
    user.verified = True
    flash('Your email address is confirmed! Thanks!')
    return redirect(url_for('index'),error=error)


def emailAuth(e):
    e = e.lower()
    school = None

    if e.endswith('pomona.edu'):
        school = 'po'
    elif e.endswith('hmc.edu'):
        school = 'hm'
    elif e.endwith('pitzer.edu'):
        school = 'pz'
    elif e.endswith('scrippscollege.edu'):
        school = 'sc'
    elif e.endswith('cmc.edu') or e.endswith ('claremontmckenna.edu'):
        school = 'cm'

    return school
