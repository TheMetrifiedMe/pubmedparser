import psycopg2

# Database Credentials
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "pythonboy"
DB_PASS = "<placeholder>"

def database_credentials():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
