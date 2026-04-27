import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sharwari@1520",
        database="sahaara_db"
    )
