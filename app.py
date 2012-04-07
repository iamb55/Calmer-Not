from flaskext.mail import Mail, Message
from flask import request, session, render_template, redirect, url_for, flash, jsonify
from models import User, Game, app, db
from redis import Redis
import random
import os
import hashlib
import urlparse

mail = Mail(app)
if os.environ.has_key('REDISTOGO_URL'):
    url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
    app.config.setdefault('REDIS_HOST', url.hostname)
    app.config.setdefault('REDIS_PORT', url.port)
    app.config.setdefault('REDIS_PASSWORD', url.password)    

r = Redis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], db=0, password=app.config['REDIS_PASSWORD'])

base_url = 'http://warm-cloud-8555.herokuapp.com'

six = set()
words = set()

for line in open("six.txt"):
    six.add(line[:-1])

for line in open("words.txt"):
    words.add(line[:-1])

r.set('poscore', 0)
r.set('pzscore', 0)
r.set('hmscore', 0)
r.set('scscore', 0)
r.set('cmscore', 0)

@app.route('/')
def index():
    error = None
    if session.get("user_id") != None:     
        return redirect(url_for('stats'))
    if session.get('error'): 
        error = session.pop('error')
    return render_template('index.html', error=error)

@app.route('/stats')
def stats():
    if session.get("user_id") != None:     
        return render_template('stats.html')
    
@app.route('/logout')
def logout():
    try:
        session.pop('user_id')
    except KeyError:
        pass
    finally:
        return redirect(url_for('index'))

@app.route('/login', methods=["POST"])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = authenticate(email, password)
    # user exists and authed
    if user != None:
        session['user_id']  = user.id
        flash('You were successfully logged in.')
        return redirect(url_for('stats'))
    # invalid u or p
    else:
        session['error'] = 'Your email or password was wrong'
        return render_template(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    school = emailAuth(email)
    if not school:
        session['error'] = 'Invalid email address'
        return redirect(url_for('index'))

    user = User(school,email,password)
    db.session.add(user)
    db.session.commit()

    sendConfirmation(user.id,email)

    session['user_id'] = user.id
    return redirect(url_for('index'))

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
    key = request.args.get('confkey')

    if key == None:
        session['error'] = 'Invalid confirmation key' 
        return redirect(url_for('index'))
    id = r.get(key)
    if id == None:
        session['error'] = 'No such user'
        return redirect(url_for('index'))

    r.delete(key)
    user = User.query.get(id)
    user.verified = True
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    flash('Your email address is confirmed! Thanks!')
    return redirect(url_for('stats'))

@app.route('/newgame', methods=['GET'])        
def newGame():
    if session.get("user_id") == None:     
        return redirect(url_for("index"))
    currentUser = User.query.get(session.get("user_id"))
    next = nextGame(currentUser.school)
    if next == None:
        score = None
        word = random.sample(six, 1)[0]
        game = Game(word)
        db.session.add(game)
        db.session.commit()
    else:
        game = Game.query.get(next)
        word = game.letters
        score = game.score
    return render_template("game.html", word=word, score=score, game_id=game.id)

def authenticate(e, p):
    user = User.query.filter_by(email=e).first()
    # TODO: check if verified
    return None if user is None or not user.check_password(p) else user

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
    body = '<p>Please confirm your email address by clicking <a href="%s/confirm?confkey=%s">here</a></p>'  % (base_url, confkey)
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
    elif e.endswith('pitzer.edu'):
        school = 'pz'
    elif e.endswith('scrippscollege.edu'):
        school = 'sc'
    elif e.endswith('cmc.edu') or e.endswith ('claremontmckenna.edu'):
        school = 'cm'
    return school

def nextGame(mySchool):
    games = [r.lindex('po', 0), r.lindex('pz', 0), r.lindex('cm', 0), r.lindex('hm', 0), r.lindex('sc', 0)]
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
    games = map(int, filter(lambda x: x != None, games))
    return None if len(games) == 0 else min(games)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port);
