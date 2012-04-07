import os
DEBUG = True

MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = '5cwordwarp@gmail.com'
MAIL_PASSWORD = os.environ['MAIL_PASSWORD']
DEFAULT_MAIL_SENDER = '5cwordwarp@gmail.com'

SECRET_KEY = os.environ['SECRET_KEY']
