from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from neo4j import GraphDatabase
from datetime import datetime
import uuid

# Inicializamos Flask
app = Flask(__name__)
CORS(app)

# Configuración de Neo4j
uri = "bolt://192.168.1.34:7687"
username = "neo4j"
password = "touch-nice-joker-tape-junior-9975"
driver = GraphDatabase.driver(uri, auth=(username, password))


@app.route("/login", methods=["POST"])
def login():
    try:
        # Datos del login
        datos = request.get_json()
        usuario = datos["usuario"]
        contraseña = datos["contraseña"]

        # Verificar usuario en la base de datos
        with driver.session() as session:
            resultado = session.run(
                """
                MATCH (u:Usuario {usuario: $usuario, contraseña: $contraseña})
                RETURN u
                """,
                usuario=usuario,
                contraseña=contraseña
            )

            usuario_db = resultado.single()

        if usuario_db:
            # Generar cookie
            cookie = str(uuid.uuid4())
            fecha_login = datetime.now().isoformat()

            # Guardar cookie en la base de datos
            with driver.session() as session:
                session.run(
                    """
                    CREATE (c:Cookie {
                        cuenta: $usuario,
                        cookie: $cookie,
                        fecha_login: $fecha_login
                    })
                    """,
                    usuario=usuario,
                    cookie=cookie,
                    fecha_login=fecha_login
                )

            # Devolver cookie al frontend
            return jsonify({"cookie": cookie}), 200
        else:
            return jsonify({"mensaje": "Usuario o contraseña incorrectos"}), 401
    except Exception as e:
        print("Error:", e)
        return jsonify({"mensaje": "Error en el servidor"}), 500


@app.route("/verificar", methods=["POST"])
def verificar():
    try:
        # Validar la cookie enviada por el frontend
        datos = request.get_json()
        cookie = datos["cookie"]

        with driver.session() as session:
            resultado = session.run(
                """
                MATCH (c:Cookie {cookie: $cookie})
                RETURN c
                """,
                cookie=cookie
            )

            cookie_db = resultado.single()

        if cookie_db:
            return jsonify({"mensaje": "Sesión válida"}), 200
        else:
            return jsonify({"mensaje": "Sesión inválida"}), 401
    except Exception as e:
        print("Error:", e)
        return jsonify({"mensaje": "Error en el servidor"}), 500



@app.route("/logout", methods=["POST"])
def logout():
    try:
        # Recibimos la cookie desde el frontend
        datos = request.get_json()
        cookie = datos["cookie"]

        # Eliminamos la cookie de la base de datos
        with driver.session() as session:
            session.run(
                """
                MATCH (c:Cookie {cookie: $cookie})
                DELETE c
                """,
                cookie=cookie
            )

        return jsonify({"mensaje": "Sesión cerrada correctamente"}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"mensaje": "Error al cerrar la sesión"}), 500


@app.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return jsonify({"mensaje": "OK"}), 200 
    try:
        # Recibir datos JSON enviados por el frontend
        datos = request.get_json()
        print("Datos recibidos:", datos)

        nombre = datos["nombre"]
        apellido = datos["apellido"]
        usuario = datos["usuario"]
        email = datos["email"]
        contraseña = datos["contraseña"]
        edad = int(datos["edad"])
        fecha_creacion = datetime.now().isoformat()  # Fecha de creación

        # Generar un ID único en Python
        user_id = str(uuid.uuid4())

        # Guardar los datos en Neo4j
        with driver.session() as session:
            session.run(
                """
                CREATE (u:Usuario {
                    id: $user_id,
                    nombre: $nombre,
                    apellido: $apellido,
                    usuario: $usuario,
                    email: $email,
                    contraseña: $contraseña,
                    fecha_creacion: $fecha_creacion,
                    edad: $edad
                })
                """,
                user_id=user_id,
                nombre=nombre,
                apellido=apellido,
                usuario=usuario,
                email=email,
                contraseña=contraseña,
                fecha_creacion=fecha_creacion,
                edad=edad
            )

        # Respuesta exitosa
        return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201

    except Exception as e:
        # Manejo de errores
        print("Error en /register:", e)
        return jsonify({"mensaje": "Error al registrar usuario"}), 500


@app.route("/feed", methods=["GET"])
def feed():
    user = request.args.get("user")
    try:
        with driver.session() as session:
            # Obtener datos del usuario actual
            current_user = session.run(
                """
                MATCH (u:Usuario {usuario: $user})
                RETURN u.nombre AS name, u.apellido AS surname, u.usuario AS username
                """, user=user
            ).single()

            if not current_user:
                return jsonify({"mensaje": "Usuario no encontrado"}), 404

            # Obtener usuarios genéricos
            recommendations = session.run(
                """
                MATCH (u:Usuario)
                WHERE u.usuario <> $user
                RETURN u.nombre AS name, u.apellido AS surname, u.usuario AS username
                LIMIT 20
                """, user=user
            ).values()

        # Formatear las recomendaciones
        formatted_recommendations = [
            {"name": rec[0], "surname": rec[1], "username": rec[2]} for rec in recommendations
        ]

        return jsonify({
            "currentUser": {
                "name": current_user["name"],
                "surname": current_user["surname"],
                "username": current_user["username"]
            },
            "recommendations": formatted_recommendations
        })
    except Exception as e:
        print("Error en /feed:", e)
        return jsonify({"mensaje": "Error al cargar el feed"}), 500




from uuid import uuid4

@app.route("/post", methods=["POST"])
def post():
    try:
        datos = request.get_json()
        user = datos["user"]
        content = datos["content"]

        post_id = str(uuid4())  # Generar un ID único en Python

        with driver.session() as session:
            session.run(
                """
                MATCH (u:Usuario {usuario: $user})
                CREATE (p:Post {id: $post_id, contenido: $content, fecha: datetime()})
                CREATE (u)-[:POSTEO]->(p)
                """, user=user, content=content, post_id=post_id
            )

        return jsonify({"mensaje": "Post creado exitosamente"}), 201
    except Exception as e:
        print("Error en /post:", e)
        return jsonify({"mensaje": "Error al crear el post"}), 500


from datetime import datetime

@app.route("/posts", methods=["GET"])
def get_posts():
    user = request.args.get("user")
    try:
        with driver.session() as session:
            # Obtener posts genéricos
            posts = session.run(
                """
                MATCH (u:Usuario)-[:POSTEO]->(p:Post)
                RETURN p.contenido AS content, p.fecha AS date, u.nombre AS author_name, u.apellido AS author_surname, u.usuario AS author_username
                ORDER BY p.fecha DESC
                LIMIT 20
                """
            ).values()

        # Convertir datetime a string y formatear los datos
        formatted_posts = [
            {
                "content": post[0],
                "date": post[1].strftime("%Y-%m-%d %H:%M:%S") if post[1] else None,
                "author_name": post[2],
                "author_surname": post[3],
                "author_username": post[4]
            }
            for post in posts
        ]

        return jsonify(formatted_posts)
    except Exception as e:
        print("Error en /posts:", e)
        return jsonify({"mensaje": "Error al cargar los posts"}), 500






if __name__ == "__main__":
    app.run(debug=True)