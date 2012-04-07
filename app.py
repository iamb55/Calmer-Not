from flask import Flask

app = Flask(__name__)
app.config.from_object('settings')

db = SQLAlchemy(app)

@app.route('/')
def index():

@app.route('/login', methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
    
