from models.user import User
from bcrypt import checkpw

def authenticate(username, password):
    user = User.find_by_username(username)
    if user and checkpw(password.encode('utf8'), user.password.encode('utf8')):
        return user

def identity(payload):
    user_id = payload['identity']
    return User.find_by_id(user_id)
