from flask import Flask
from models import User
from flaskext.mail import Mail

app = Flask(__name__)
app.config.from_object('settings')

db = SQLAlchemy(app)
mail = Mail(app)

@app.route('/')
def index():
    print "hello"

@app.route('/login', methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
    

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
