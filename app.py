from flask import Flask, request, jsonify # Importamos request y jsonify

print("DEBUG: Importando Flask y creando la app...")

app = Flask(__name__)

print("DEBUG: App de Flask creada.")

# Usuarios de prueba (simulando una base de datos muy simple)
# Más adelante, esto vendrá de una base de datos real.
# Y las contraseñas NUNCA deben guardarse así en texto plano en producción.
# Esto es SOLO para nuestra simulación inicial.
usuarios_de_prueba = {
    "adminAPR": {"contrasena": "admin123", "rol": "administrador"},
    "estudiante01": {"contrasena": "alumno123", "rol": "estudiante"},
    "profe01": {"contrasena": "profe123", "rol": "docente"}
}

@app.route('/')
def hola_mundo():
    print("DEBUG: Accediendo a la ruta /")
    return 'Servidor Flask para Plataforma de Notas APR funcionando!'

# NUEVA RUTA PARA EL LOGIN
@app.route('/api/login', methods=['POST']) # Aceptamos peticiones POST a esta ruta
def login():
    print("DEBUG: Accediendo a la ruta /api/login con método POST")
    
    # Obtener los datos JSON enviados desde el frontend
    # Asumiremos que el frontend enviará un JSON con "username" y "password"
    try:
        datos_recibidos = request.get_json()
        print(f"DEBUG: Datos JSON recibidos: {datos_recibidos}")

        if not datos_recibidos:
            return jsonify({"mensaje": "No se recibieron datos JSON"}), 400

        username_ingresado = datos_recibidos.get('username')
        password_ingresada = datos_recibidos.get('password')
        # tipo_usuario_ingresado = datos_recibidos.get('tipo_usuario') # Podríamos usar esto más adelante

        print(f"DEBUG: Usuario recibido: {username_ingresado}, Contraseña recibida: {password_ingresada}")

        if not username_ingresado or not password_ingresada:
            return jsonify({"mensaje": "Usuario o contraseña faltantes"}), 400

        # PASO 2 y 3 (Manejar datos y Verificar login - simulación)
        if username_ingresado in usuarios_de_prueba:
            usuario_en_db = usuarios_de_prueba[username_ingresado]
            if usuario_en_db["contrasena"] == password_ingresada:
                # ¡Login exitoso!
                mensaje_bienvenida = f"¡Bienvenido {username_ingresado}! Eres un {usuario_en_db['rol']}."
                print(f"DEBUG: Login exitoso para {username_ingresado}")
                # En una aplicación real, aquí crearíamos una sesión.
                # Por ahora, solo devolvemos un mensaje de éxito y el rol.
                return jsonify({
                    "mensaje": mensaje_bienvenida, 
                    "rol": usuario_en_db['rol'],
                    "usuario": username_ingresado
                }), 200
            else:
                # Contraseña incorrecta
                print(f"DEBUG: Contraseña incorrecta para {username_ingresado}")
                return jsonify({"mensaje": "Contraseña incorrecta"}), 401 # 401 Unauthorized
        else:
            # Usuario no encontrado
            print(f"DEBUG: Usuario no encontrado: {username_ingresado}")
            return jsonify({"mensaje": "Usuario no encontrado"}), 404 # 404 Not Found

    except Exception as e:
        print(f"DEBUG: Error al procesar la petición JSON: {e}")
        return jsonify({"mensaje": "Error en el formato de la petición. Se esperaba JSON."}), 400


print("DEBUG: Rutas definidas.")

if __name__ == '__main__':
    print("DEBUG: Entrando al bloque if __name__ == '__main__'")
    app.run(debug=True, host='0.0.0.0', port=5000)
    print("DEBUG: app.run() ha sido llamado.")
else:
    print(f"DEBUG: app.py importado como módulo. __name__ es {__name__}")

print("DEBUG: Fin del script app.py (si app.run no bloquea).")