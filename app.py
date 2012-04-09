from flaskext.mail import Mail, Message
from flask import request, session, render_template, redirect, url_for, flash, jsonify
from models import User, Game, app, db
from redis import Redis
from collections import defaultdict
from functools import wraps
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

def login_required(f):
    @wraps(f)
    def dec_fn(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return dec_fn

@app.route('/')
def index():
    error = None
    if session.get("user_id"):     
        return redirect(url_for('stats'))
    if session.get('error'): 
        error = session.pop('error')
    return render_template('index.html', error=error)

@app.route('/stats')
@login_required
def stats():
    user = User.query.get(session['user_id'])
    scores = map(float, [r.get(s) for s in ('poscore', 'pzscore', 'hmscore', 'scscore', 'cmscore')])
    total = sum(scores)
    total = 1.0 if total == 0 else total
    percents = map(lambda x: x / total, scores)
    gamesPlayed = float(1 if user.gamesPlayed == 0 else user.gamesPlayed)
    return render_template('stats.html', wins=user.score, 
                                         percent=(user.score/gamesPlayed), 
                                         games=user.gamesPlayed,
                                         po=percents[0], 
                                         pz=percents[1], 
                                         hm=percents[2], 
                                         sc=percents[3], 
                                         cm=percents[4])
    
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
    if user:
        session['user_id']  = user.id
        flash('You were successfully logged in.')
        return redirect(url_for('stats'))
    # invalid u or p
    else:
        session['error'] = 'Your email or password was wrong.'
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')

    school = emailAuth(email)
    if not school:
        session['error'] = 'Invalid email address.'
        return redirect(url_for('index'))

    user = User(school,email,password)
    db.session.add(user)
    db.session.commit()

    sendConfirmation(user.id, email)

    session['user_id'] = user.id
    return redirect(url_for('index'))

@app.route('/validate')
def validate():
    word = request.args.get('guess') 
    base = request.args.get('base')
    d = defaultdict(int)
    for c in base:
        d[c] += 1
    # are letters in word in base?
    for c in word:
        if d[c] <= 0:
            return jsonify(valid=False)
        d[c] -= 1
    # is word a valid english word?
    if word in words or word in six:
        return jsonify(valid=True)
    else:
        return jsonify(valid=False)

@app.route('/confirm', methods=['GET'])
def confirm():
    key = request.args.get('confkey')

    if key == None:
        session['error'] = 'Invalid confirmation key' 
        return redirect(url_for('index'))
    user_id = r.get(key)
    if id == None:
        session['error'] = 'No such user'
        return redirect(url_for('index'))

    r.delete(key)
    user = User.query.get(user_id)
    user.verified = True
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    flash('Your email address is confirmed! Thanks!')
    return redirect(url_for('stats'))

@app.route('/newgame', methods=['GET'])        
@login_required
def newGame():
    currentUser = User.query.get(session.get("user_id"))
    next = nextGame(currentUser.school)
    if not next:
        score = None
        w = random.sample(six, 1)[0]
        word = ''.join(random.sample(w,len(w)))
        game = Game(word)
        db.session.add(game)
        db.session.commit()
    else:
        game = Game.query.get(next)
        word = game.letters
        score = game.u1Score
    return render_template("game.html", word=word, score=score, game_id=game.id)

def authenticate(e, p):
    user = User.query.filter_by(email=e).first()
    # TODO: check if verified
    return None if user is None or not user.check_password(p) else user

@app.route("/finish", methods=['POST'])
def finish():
    gameID = request.form.get("gameID")
    score = int(request.form.get("score"))
    game = Game.query.get(gameID)
    # current player was first to play
    if game.u1 is None:
        game.u1 = session['user_id']
        user = User.query.get(session['user_id'])
        game.u1Score = score
        # put on queue
        r.rpush(user.school, game.id)
        db.session.add(game)
        db.session.commit()
        return jsonify(success=True, win=False, first=True)
    # current player was second to play
    # TODO: This is unnecessary. In fact, we don't even need to store any info about u2
    # in the db. Not fixing yet, since we should update DB schema.
    elif game.u2 is None:
        game.u2 = session['user_id']
        game.u2Score = score
        db.session.add(game)
        db.session.commit()
    # TODO: Handle ties correctly
    if game.u1Score >= score:
        won = False
        winner = User.query.get(game.u1)
        loser = User.query.get(game.u2)
    else:
        won = True
        winner = User.query.get(game.u2)
        loser = User.query.get(game.u1)
    # we don't care about keeping the actual game data around anymore, now that it's over
    db.session.delete(game)
    winner.score += 1
    winner.gamesPlayed += 1
    loser.gamesPlayed += 1
    db.session.add(winner)
    db.session.add(loser)
    db.session.commit()
    # this allows for arbitrary strings, but since we set school ourselves it should be fine
    r.incr('%sscore' % winner.school)
    return jsonify(success=True, win=won, first=False)

def sendConfirmation(user_id,email):
    confkey = generateUnique(32)
    body = '<p>Please confirm your email address by clicking <a href="%s/confirm?confkey=%s">here</a></p>'  % (base_url, confkey)
    subj = '5C Word Warp - Email Confirmation'
    r.set(confkey, user_id)
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
    other_schools = [x for x in ('po','pz','cm','hm','sc') if x != mySchool]
    games = []
    for school in other_schools:
        games.append((r.lindex(school, 0), school))
     
    games = filter(lambda (x,y) : x != None, games)
    if len(games) == 0:
        return None
    else:
        x, y = min(games)
        r.lpop(y)
        return int(x)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port);
