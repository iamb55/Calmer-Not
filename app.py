from flaskext.mail import Mail
from flask import Flask, request, session, render_template, redirect, url_for, flash
from models import User, Game
from redis import Redis
import random

app = Flask(__name__)
app.config.from_object('settings')

db = SQLAlchemy(app)
mail = Mail(app)
r = Redis()
six = set()
words = set()

for line in open("six.txt"):
    six.add(line[:-1])

for line in open("words.txt"):
    words.add(line[:-1])

@app.route('/')
def index():
    if session.get("user_id") != None:     
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
    school = request.form.get('school')
    email = request.form.get('email')
    password = request.form.get('password')

    user = User(school,email,password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id

    return redirect(url_for('app.home'))

@app.route('/newgame', methods=['POST'])        
def newGame():
    if session.get("user_id") == None:     
        return redirect(url_for("index"))
    currentUser = User.query.get(session.get("user_id"))
    next = nextGame(currentUser.school)
    if next == None:
        score = None
        word = random.sample(six)[0]
    else:
        game = Game.query.get(next)
        word = game.letters
        score = game.score
    return render_template("game.html", word, score)


def nextGame(mySchool):
    games = [r.lindex(po, 0), r.lindex(pz, 0), r.lindex(cm, 0), r.lindex(hm, 0), r.lindex(sc, 0)]
    if (mySchool == "po"):
        del games[0]
    elif (mySchool == "pz"):
        del games[1]
    elif (mySchool == "cm"):
        del games[2]
    elif (mySchool == "hm"):
        del games[3]
    elif (mySchool == "sc"):
        del games[4]
    game = map (int, game)
    return min(game)
        
    
