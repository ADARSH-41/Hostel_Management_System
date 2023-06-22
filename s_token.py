import os
from itsdangerous import URLSafeTimedSerializer as s
from key import secret_key
'''secret_key = os.urandom(45)
serializer = s(secret_key)
token = serializer.dumps('nallaadarsh81199@gmail.com',salt='confirmation')
serializer.loads(token,salt='confirmation')

print(token)
print(serializer.loads(token,salt='confirmation',max_age=5))'''

def token(email,salt):
    serializer = s(secret_key)
    return serializer.dumps(email,salt=salt)