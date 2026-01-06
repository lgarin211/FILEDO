from config import Config
import mysql.connector

def check_db():
    print(f"Config Host: {Config.MYSQL_HOST}")
    print(f"Config User: {Config.MYSQL_USER}")
    print(f"Config DB: {Config.MYSQL_DB}")
    
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        print("Connection Success!")
        conn.close()
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    check_db()
