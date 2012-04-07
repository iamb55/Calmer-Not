from flaskext.mail import Mail, Message
from flask import request, session, render_template, redirect, url_for, flash, jsonify
from models import User, Game, app, db
from redis import Redis
import random
import os
import hashlib

mail = Mail(app)
r = Redis()
six = set()
words = set()

for line in open("six.txt"):
    six.add(line[:-1])

for line in open("words.txt"):
    words.add(line[:-1])

r.set(poscore, 0)
r.set(pzscore, 0)
r.set(hmscore, 0)
r.set(scscore, 0)
r.set(cmscore, 0)

@app.route('/')
def index():
    if session.get("user_id") != None:     
        return redirect(url_for('stats'))
    return render_template('index.html')


@app.route('/stats')
def stats():
    if session.get("user_id") != None:     
        return render_template('stats.html')
    

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

@app.route('/validate')
def validate():
    word = request.args.get('guess') 
    base = request.args.get('base') 
    # are letters in word in base?
    in_base = reduce(lambda acc, c : (c in base) and acc, word, True)
    # is word a valid english word?
    if (word in words or words in six) and in_base:
        return jsonify(valid=True)
    else:
        return jsonify(valid=False)

@app.route('/confirm', methods=['GET'])
def confirm():
    error = None
    key = request.args.get('confkey')

    if key == None:
        error = 'Invalid confirmation key' 
    id = r.get(key)
    if id == None:
        error = 'No such user'

    user = User.query.get(id)
    user.verified = True
    session['user_id'] = user.id
    flash('Your email address is confirmed! Thanks!')
    return redirect(url_for('index'),error=error)

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
    return render_template("game.html", word=word, score=score, game_id=game.id)

def authenticate(e, p):
    user = User.query.filter_by(email=e).first()
    # TODO: check if verified
    return None if user is None or not user.check_password_hash(p) else user

@app.route("/finish", methods=['POST'])
def finish():
    gameID = request.form.get("gameID")
    firstWon = request.form.get("gameID")
    game = Game.query.get(gameID)
    if firstWon:
        winner = User.query.get(game.u1)
        loser = User.query.get(game.u2)
    else:
        winner = User.query.get(game.u2)
        loser = User.query.get(game.u1)
    winner.score += 1
    winner.gamesPlayed += 1
    loser.gamesPlayed += 1
    db.session.add(winner)
    db.session.add(loser)
    db.session.commit()
    if (school == "po"):
        r.incr(poscore)
    elif(school == "pz"):
        r.inc(pzscore)
    elif(school == "hm"):
        r.inc(hmscore)
    elif(school == "sc"):
        r.inc(scscore)
    elif(school == "cm"):
        r.inc(cmscore)
    return jsonify(success=True)

def sendConfirmation(id,email):
    confkey = generateUnique(32)

    link = '<p><a href=%s/confirm?confkey=%s' % (base_url,confkey)
    body = '<p>Please confirm your email address by clicking the link below:</p>' + link
    subj = '5C Word Warp - Email Confirmation'

    r.set(confkey,id)

    msg = Message(html=body,subject=subj,recipients=[email])
    mail.send(msg)

def generate(length):
    randomData = os.urandom(length)
    return hashlib.sha512(randomData).hexdigest()[:16] 

def generateUnique(length):
    key = generate(length)
    while not unique(key):
        key = generate(length)
    return key

def unique(key):
    return r.get(key) == None

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
