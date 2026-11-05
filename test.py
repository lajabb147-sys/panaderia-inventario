import mysql.connector

try:
    conexion = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Laja123*",
        database="panaderia"
    )
    
    if conexion.is_connected():
        print("¡Conexión exitosa a MySQL y a la base de datos panaderia!")
        conexion.close()

except Exception as e:
    print(f"Error al conectar: {e}")