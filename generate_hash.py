import bcrypt

password = "Admin@123"  # Choose a strong password
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print("Hashed password:\n", hashed.decode())
