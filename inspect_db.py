import mysql.connector

def inspect_db():
    try:
        # Connect to MySQL Server (no db selected yet)
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()
        
        # List all databases
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        print("Available Databases:", databases)
        
        # Look for likely candidates
        candidates = [db for db in databases if db not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
        
        for db in candidates:
            print(f"\n--- Inspecting Database: {db} ---")
            try:
                conn.database = db
                cursor.execute("SHOW TABLES")
                tables = [t[0] for t in cursor.fetchall()]
                print(f"Tables: {tables}")
                
                # If there's a table with 'surat' in the name, show its columns
                for table in tables:
                    if 'surat' in table.lower() or 'doc' in table.lower() or 'file' in table.lower():
                        print(f"  > Columns in '{table}':")
                        cursor.execute(f"DESCRIBE {table}")
                        columns = [f"{col[0]} ({col[1]})" for col in cursor.fetchall()]
                        print(f"    {columns}")
                        
                        # Peek at data
                        try:
                           cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                           rows = cursor.fetchall()
                           if rows:
                               print(f"    Sample Row: {rows[0]}")
                        except:
                            pass

            except Exception as e:
                print(f"Error inspecting {db}: {e}")

        conn.close()

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    inspect_db()
