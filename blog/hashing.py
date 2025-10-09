
from passlib.context import CryptContext
import hashlib

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

class Hash:
    @staticmethod
    def bcrypt(password: str):

        # Ensure password doesn't exceed bcrypt's 72-byte limit
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            # Pre-hash with SHA256 for passwords longer than 72 bytes
            password = hashlib.sha256(password_bytes).hexdigest()
        
        try:
            hashed_password = pwd_context.hash(password)
            return hashed_password
        except ValueError as e:
            if "password cannot be longer than 72 bytes" in str(e):
                # Fallback: use first 72 characters (not bytes) as a last resort
                password = password[:72]
                hashed_password = pwd_context.hash(password)
                return hashed_password
            else:
                raise e
    @staticmethod
    def verify(plain_password: str, hashed_password: str):
        # Handle bcrypt 72-byte limitation for verification
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            # Pre-hash with SHA256 for passwords longer than 72 bytes (same as in bcrypt method)
            plain_password = hashlib.sha256(password_bytes).hexdigest()
        
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except ValueError as e:
            if "password cannot be longer than 72 bytes" in str(e):
                # Fallback: use first 72 characters as a last resort
                plain_password = plain_password[:72]
                return pwd_context.verify(plain_password, hashed_password)
            else:
                raise e