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

            # Obtener usuarios no seguidos
            recommendations = session.run(
                """
                MATCH (u:Usuario)
                WHERE u.usuario <> $user AND NOT EXISTS {
                    MATCH (:Usuario {usuario: $user})-[:SIGUE]->(u)
                }
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
    user = request.args.get("user")  # Usuario actual
    try:
        with driver.session() as session:
            # Consulta para obtener los posts del usuario logueado y los de los usuarios que sigue
            posts = session.run(
                """
                MATCH (u:Usuario {usuario: $user})-[:POSTEO]->(p:Post)
                RETURN p.id AS id, p.contenido AS content, p.fecha AS date,
                       u.nombre AS author_name, u.apellido AS author_surname, u.usuario AS author_username
                UNION
                MATCH (:Usuario {usuario: $user})-[:SIGUE]->(followed:Usuario)-[:POSTEO]->(p:Post)
                RETURN p.id AS id, p.contenido AS content, p.fecha AS date,
                       followed.nombre AS author_name, followed.apellido AS author_surname, followed.usuario AS author_username
                ORDER BY date DESC
                LIMIT 20
                """,
                user=user
            ).values()

        # Formatear los resultados para incluir el campo `id`
        formatted_posts = [
            {
                "id": post[0],  # El primer índice corresponde al campo `p.id`
                "content": post[1],
                "date": post[2].strftime("%Y-%m-%d %H:%M:%S") if post[2] else None,
                "author_name": post[3],
                "author_surname": post[4],
                "author_username": post[5]
            }
            for post in posts
        ]

        # Retornar los posts en formato JSON
        return jsonify(formatted_posts)

    except Exception as e:
        print("Error en /posts:", e)
        return jsonify({"mensaje": "Error al cargar los posts"}), 500



@app.route("/profile", methods=["GET"])
def profile():
    user = request.args.get("user")
    try:
        with driver.session() as session:
            user_data = session.run(
                """
                MATCH (u:Usuario {usuario: $user})
                RETURN u.nombre AS name, u.apellido AS surname, u.email AS email, u.edad AS age, u.fecha_creacion AS created_at
                """, user=user
            ).single()

        if not user_data:
            return jsonify({"mensaje": "Usuario no encontrado"}), 404

        # No aplicar strftime si el valor ya es un string
        return jsonify({
            "name": user_data["name"],
            "surname": user_data["surname"],
            "email": user_data["email"],
            "age": user_data["age"],
            "created_at": user_data["created_at"]  # Asume que es string
        })
    except Exception as e:
        print("Error en /profile:", e)
        return jsonify({"mensaje": "Error al cargar el perfil"}), 500


@app.route("/follow", methods=["POST"])
def follow():
    try:
        data = request.get_json()
        current_user = data["current_user"]
        user_to_follow = data["user_to_follow"]

        with driver.session() as session:
            session.run(
                """
                MATCH (u1:Usuario {usuario: $current_user}), (u2:Usuario {usuario: $user_to_follow})
                CREATE (u1)-[:SIGUE]->(u2)
                """, current_user=current_user, user_to_follow=user_to_follow
            )

        return jsonify({"mensaje": "Usuario seguido exitosamente"}), 200
    except Exception as e:
        print("Error en /follow:", e)
        return jsonify({"mensaje": "Error al seguir al usuario"}), 500


@app.route("/unfollow", methods=["POST"])
def unfollow():
    try:
        data = request.get_json()
        current_user = data["current_user"]
        user_to_unfollow = data["user_to_unfollow"]

        with driver.session() as session:
            session.run(
                """
                MATCH (:Usuario {usuario: $current_user})-[rel:SIGUE]->(:Usuario {usuario: $user_to_unfollow})
                DELETE rel
                """, current_user=current_user, user_to_unfollow=user_to_unfollow
            )

        return jsonify({"mensaje": "Usuario dejado de seguir exitosamente"}), 200
    except Exception as e:
        print("Error en /unfollow:", e)
        return jsonify({"mensaje": "Error al dejar de seguir al usuario"}), 500


@app.route("/delete_post", methods=["POST"])
def delete_post():
    try:
        data = request.get_json()
        post_id = data["post_id"]  # Asegúrate de que este campo coincide con el que envías desde el frontend.

        with driver.session() as session:
            session.run(
                """
                MATCH (p:Post {id: $post_id})
                DETACH DELETE p
                """,
                post_id=post_id
            )

        return jsonify({"mensaje": "Post eliminado correctamente"}), 200
    except Exception as e:
        print("Error en /delete_post:", e)
        return jsonify({"mensaje": "Error al eliminar el post"}), 500



if __name__ == "__main__":
    app.run(debug=True)