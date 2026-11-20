import pymysql


try:
    # Connection Parameters
    connection = pymysql.connect(
        host = 'localhost', user = 'root',
        password = '12345', database = 'sales_db'
    )
    print("DB CONNECTED SUCCESSFULLY!")
    cursor = connection.cursor()
    
    # FETCHING
    table_name = 'users'
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    print("Users in your DB:")
    for row in rows:
        print(row)

except Exception as e:
    print(f"ERROR: {e}")

finally:
    if 'connection' in locals():
        connection.close()
        print("Connection closed") 

