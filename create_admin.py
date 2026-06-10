import os
import secrets
import string
import psycopg2
import bcrypt
from dotenv import load_dotenv

load_dotenv()

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_secure_password(length=16):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_random_superuser():
    username = f"admin_{generate_random_string(6)}"
    password = generate_secure_password(16)
    
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    raw_db_url = os.getenv("DATABASE_URL")
    if not raw_db_url:
        print("Error: DATABASE_URL not found in .env file.")
        return

    try:
        url_without_protocol = raw_db_url.split("://", 1)[1]
        credentials, host_and_db = url_without_protocol.rsplit("@", 1)
        db_user, db_pass = credentials.split(":", 1)
        host_port, db_name = host_and_db.split("/", 1)
        
        db_host = host_port.split(":")[0] if ":" in host_port else host_port
        db_port = host_port.split(":")[1] if ":" in host_port else "5432"
    except Exception as e:
        print(f"Error parsing DATABASE_URL: {e}")
        return

    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_pass,
            host=db_host,
            port=db_port
        )
        cursor = conn.cursor()

        insert_query = """
        INSERT INTO admins (username, hashed_password, is_active, created_at)
        VALUES (%s, %s, True, NOW())
        """
        
        cursor.execute(insert_query, (username, hashed_password))
        conn.commit()

        print("\n=== SECURE ADMIN CREDENTIALS ===")
        print(f"Username : {username}")
        print(f"Password : {password}")
        print("================================")
        print("WARNING: Save these details immediately. They will not be shown again.\n")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] Database operation failed: {e}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    create_random_superuser()