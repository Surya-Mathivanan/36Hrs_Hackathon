import mysql.connector
from dotenv import load_dotenv
import os
import hashlib

# Load environment variables
load_dotenv()

# Connect to database
conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = conn.cursor()

# Check existing users
cursor.execute('SELECT username FROM users')
print('Existing users:')
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# Add user 'surya' with password 'surya123'
username = 'surya'
password = 'surya123'
hashed_password = hashlib.sha256(password.encode()).hexdigest()

try:
    cursor.execute(
        'INSERT INTO users (username, password) VALUES (%s, %s)',
        (username, hashed_password)
    )
    conn.commit()
    print(f"\n✅ User '{username}' added successfully!")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
except mysql.connector.IntegrityError:
    print(f"\n⚠️ User '{username}' already exists!")

conn.close()
