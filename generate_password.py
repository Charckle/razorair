from passlib.hash import sha512_crypt
import getpass

# Ask for password input securely
password = getpass.getpass("Enter the password to hash: ")

password_hash = sha512_crypt.hash(password)

print("Generated password hash:", password_hash)