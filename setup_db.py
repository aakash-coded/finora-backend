import sys
import pymysql

def setup_database():
    hosts = ["127.0.0.1", "localhost"]
    port = 3306
    user = "root"
    db_name = "finora_db"

    # Variations of user's provided input
    passwords_to_try = [
        "aakash123",
        "aakash123 ",
        " aakash123",
        "aakash123-root",
        "aakash123 -root"
    ]
    
    connection = None
    successful_host = None
    successful_password = None

    for host in hosts:
        for pwd in passwords_to_try:
            print(f"Trying host: '{host}', password: '{pwd}'")
            try:
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=pwd
                )
                successful_host = host
                successful_password = pwd
                print(f"Successfully connected to host '{host}' using password '{pwd}'!")
                break
            except Exception as e:
                # Print details if it's not a password mismatch (e.g. host unreachable)
                if hasattr(e, 'args') and len(e.args) > 0 and e.args[0] == 1045:
                    continue
                else:
                    print(f"Error on host '{host}': {e}")
                    break
        if connection:
            break

    if not connection:
        print("\nCould not connect to MySQL server with the provided password variations.")
        sys.exit(1)

    # Write the successful password to a .env file so the backend can use it
    try:
        with open("backend/.env", "w") as env_file:
            env_file.write(f"DB_HOST={successful_host}\n")
            env_file.write(f"DB_PORT={port}\n")
            env_file.write(f"DB_USER={user}\n")
            env_file.write(f"DB_PASSWORD={successful_password}\n")
            env_file.write(f"DB_NAME={db_name}\n")
            env_file.write(f"SECRET_KEY=django-insecure-key-finora-2026-prod\n")
            env_file.write(f"DEBUG=True\n")
        print("Wrote database configuration to backend/.env")
    except Exception as e:
        print("Warning: Failed to write to .env: {}".format(e))

    try:
        with connection.cursor() as cursor:
            print("Checking if database '{}' exists, creating if not...".format(db_name))
            cursor.execute("CREATE DATABASE IF NOT EXISTS {} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;".format(db_name))
            connection.commit()
            print("Database '{}' is ready!".format(db_name))
    except Exception as e:
        print("Failed to create database: {}".format(e))
        sys.exit(1)
    finally:
        connection.close()

if __name__ == "__main__":
    setup_database()
