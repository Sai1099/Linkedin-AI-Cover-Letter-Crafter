import secrets

secret = secrets.token_urlsafe(128)  # 64-character secure key
print(secret)
