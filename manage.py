from flaskext.script import Manager
from models import db, app

manager = Manager(app)

@manager.command
def createDbSchema():
    db.create_all()

if __name__ == "__main__":
    manager.run()
