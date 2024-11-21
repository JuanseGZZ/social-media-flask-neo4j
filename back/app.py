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
            # Get current user data
            current_user = session.run(
                """
                MATCH (u:Usuario {usuario: $user})
                RETURN u.nombre AS name, u.apellido AS surname, u.usuario AS username
                """, user=user
            ).single()

            if not current_user:
                return jsonify({"mensaje": "Usuario no encontrado"}), 404

            # Check if the user follows anyone
            follows_anyone = session.run(
                """
                MATCH (:Usuario {usuario: $user})-[:SIGUE]->(:Usuario)
                RETURN COUNT(*) > 0 AS follows
                """, user=user
            ).single()["follows"]

            if follows_anyone:
                # Get "friends of friends" recommendations
                recommendations = session.run(
                    """
                    MATCH (:Usuario {usuario: $user})-[:SIGUE]->(friend:Usuario)-[:SIGUE]->(fof:Usuario)
                    WHERE fof.usuario <> $user AND NOT EXISTS {
                        MATCH (:Usuario {usuario: $user})-[:SIGUE]->(fof)
                    }
                    RETURN DISTINCT fof.nombre AS name, fof.apellido AS surname, fof.usuario AS username
                    LIMIT 10
                    """, user=user
                ).values()
            else:
                # Get the first 20 users for new users
                recommendations = session.run(
                    """
                    MATCH (u:Usuario)
                    WHERE u.usuario <> $user
                    RETURN u.nombre AS name, u.apellido AS surname, u.usuario AS username
                    LIMIT 20
                    """, user=user
                ).values()

        # Format the recommendations
        formatted_recommendations = [
            {"name": rec[0], "surname": rec[1], "username": rec[2]} for rec in recommendations
        ]

        # Return user and recommendations
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
            # Obtener los posts del usuario
            user_posts = session.run(
                """
                MATCH (u:Usuario {usuario: $user})-[:POSTEO]->(p:Post)
                OPTIONAL MATCH (liker:Usuario)-[:LE_GUSTO]->(p)
                RETURN p.id AS id, p.contenido AS content, p.fecha AS date, 
                       u.nombre AS author_name, u.apellido AS author_surname, u.usuario AS author_username,
                       COUNT(liker) AS likes, EXISTS((u)-[:LE_GUSTO]->(p)) AS liked
                """,
                user=user
            ).values()

            # Obtener los posts de las personas que sigue
            followed_posts = session.run(
                """
                MATCH (:Usuario {usuario: $user})-[:SIGUE]->(followed:Usuario)-[:POSTEO]->(p:Post)
                OPTIONAL MATCH (liker:Usuario)-[:LE_GUSTO]->(p)
                RETURN p.id AS id, p.contenido AS content, p.fecha AS date, 
                       followed.nombre AS author_name, followed.apellido AS author_surname, followed.usuario AS author_username,
                       COUNT(liker) AS likes, EXISTS((:Usuario {usuario: $user})-[:LE_GUSTO]->(p)) AS liked
                """,
                user=user
            ).values()

        # Combinar y ordenar los posts
        all_posts = user_posts + followed_posts
        all_posts_sorted = sorted(
            all_posts,
            key=lambda post: post[2],  # Ordenar por fecha (índice 2: `p.fecha`)
            reverse=True  # Descendente
        )

        # Formatear los posts para enviarlos al frontend
        formatted_posts = [
            {
                "id": post[0],
                "content": post[1],
                "date": post[2].strftime("%Y-%m-%d %H:%M:%S") if post[2] else None,
                "author_name": post[3],
                "author_surname": post[4],
                "author_username": post[5],
                "likes": post[6],
                "liked": post[7],
            }
            for post in all_posts_sorted
        ]

        return jsonify(formatted_posts), 200

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


@app.route("/following", methods=["GET"])
def get_following():
    user = request.args.get("user")  # Usuario actual

    try:
        with driver.session() as session:
            # Obtener la lista de usuarios seguidos
            following = session.run(
                """
                MATCH (:Usuario {usuario: $user})-[:SIGUE]->(followed:Usuario)
                RETURN followed.nombre AS name, followed.apellido AS surname, followed.usuario AS username
                ORDER BY followed.nombre
                """,
                user=user
            ).values()

        # Formatear los resultados
        formatted_following = [
            {
                "name": f[0],
                "surname": f[1],
                "username": f[2]
            }
            for f in following
        ]

        return jsonify(formatted_following)

    except Exception as e:
        print("Error en /following:", e)
        return jsonify({"mensaje": "Error al cargar la lista de seguidos"}), 500


@app.route("/toggle-like", methods=["POST"])
def toggle_like():
    try:
        datos = request.get_json()
        user = datos["user"]
        post_id = datos["post_id"]

        with driver.session() as session:
            # Verificar si ya existe una relación "le_gusto"
            existing_relationship = session.run(
                """
                MATCH (:Usuario {usuario: $user})-[r:LE_GUSTO]->(:Post {id: $post_id})
                RETURN r
                """,
                user=user,
                post_id=post_id,
            ).single()

            if existing_relationship:
                # Si existe, eliminarla (unlike)
                session.run(
                    """
                    MATCH (:Usuario {usuario: $user})-[r:LE_GUSTO]->(:Post {id: $post_id})
                    DELETE r
                    """,
                    user=user,
                    post_id=post_id,
                )
                return jsonify({"message": "Post unliked"}), 200
            else:
                # Si no existe, crearla (like)
                session.run(
                    """
                    MATCH (u:Usuario {usuario: $user}), (p:Post {id: $post_id})
                    CREATE (u)-[:LE_GUSTO]->(p)
                    """,
                    user=user,
                    post_id=post_id,
                )
                return jsonify({"message": "Post liked"}), 200

    except Exception as e:
        print("Error en /toggle-like:", e)
        return jsonify({"message": "Error al cambiar el estado del like"}), 500


@app.route("/followers", methods=["GET"])
def get_followers():
    user = request.args.get("user")

    try:
        with driver.session() as session:
            # Obtener la lista de seguidores
            followers = session.run(
                """
                MATCH (follower:Usuario)-[:SIGUE]->(:Usuario {usuario: $user})
                RETURN follower.nombre AS name, follower.apellido AS surname, follower.usuario AS username
                ORDER BY follower.nombre
                """,
                user=user
            ).values()

        # Formatear los resultados
        formatted_followers = [
            {
                "name": f[0],
                "surname": f[1],
                "username": f[2]
            }
            for f in followers
        ]

        return jsonify(formatted_followers), 200

    except Exception as e:
        print("Error en /followers:", e)
        return jsonify({"mensaje": "Error al cargar la lista de seguidores"}), 500


@app.route("/comment", methods=["POST"])
def comment_post():
    data = request.get_json()
    user = data.get("user")
    post_id = data.get("post_id")
    comment_text = data.get("comment")

    try:
        with driver.session() as session:
            # Crear la relación COMENTO con el texto del comentario
            session.run(
                """
                MATCH (u:Usuario {usuario: $user}), (p:Post {id: $post_id})
                CREATE (u)-[:COMENTO {texto: $comment, fecha: datetime()}]->(p)
                """,
                user=user,
                post_id=post_id,
                comment=comment_text
            )
        return jsonify({"mensaje": "Comentario agregado exitosamente"}), 201
    except Exception as e:
        print("Error en /comment:", e)
        return jsonify({"mensaje": "Error al agregar el comentario"}), 500


@app.route("/comments", methods=["GET"])
def get_comments():
    post_id = request.args.get("post_id")

    try:
        with driver.session() as session:
            # Obtener todos los comentarios del post
            comments = session.run(
                """
                MATCH (u:Usuario)-[c:COMENTO]->(p:Post {id: $post_id})
                RETURN u.nombre AS author_name, u.apellido AS author_surname, u.usuario AS author_username, 
                       c.texto AS text, c.fecha AS date
                ORDER BY c.fecha ASC
                """,
                post_id=post_id
            ).values()

        # Formatear los comentarios
        formatted_comments = [
            {
                "author_name": comment[0],
                "author_surname": comment[1],
                "author_username": comment[2],
                "text": comment[3],
                "date": comment[4].strftime("%Y-%m-%d %H:%M:%S") if comment[4] else None
            }
            for comment in comments
        ]

        return jsonify(formatted_comments), 200
    except Exception as e:
        print("Error en /comments:", e)
        return jsonify({"mensaje": "Error al cargar los comentarios"}), 500



@app.route("/delete_comment", methods=["POST"])
def delete_comment():
    data = request.get_json()
    user = data.get("user")
    post_id = data.get("post_id")
    comment_text = data.get("comment_text")

    try:
        with driver.session() as session:
            # Eliminar la relación `COMENTO` basada en el usuario, post y texto del comentario
            session.run(
                """
                MATCH (:Usuario {usuario: $user})-[c:COMENTO {texto: $comment_text}]->(:Post {id: $post_id})
                DELETE c
                """,
                user=user,
                comment_text=comment_text,
                post_id=post_id
            )
        return jsonify({"mensaje": "Comentario eliminado exitosamente"}), 200
    except Exception as e:
        print("Error en /delete_comment:", e)
        return jsonify({"mensaje": "Error al eliminar el comentario"}), 500



@app.route("/search_users", methods=["GET"])
def search_users():
    user_input = request.args.get("query", "").lower()
    current_user = request.args.get("current_user")
    try:
        print(f"Endpoint /search_users llamado con query: {user_input}")
        with driver.session() as session:
            results = session.run(
                """
                MATCH (u:Usuario)
                WHERE toLower(u.usuario) CONTAINS toLower($input)
                OPTIONAL MATCH (:Usuario {usuario: $current_user})-[:SIGUE]->(u)
                RETURN u.nombre AS name, u.apellido AS surname, u.usuario AS username,
                       CASE WHEN EXISTS((:Usuario {usuario: $current_user})-[:SIGUE]->(u)) THEN true ELSE false END AS is_following
                LIMIT 5
                """,
                input=user_input,
                current_user=current_user
            ).values()

        print("Resultados crudos de la base de datos:", results)

        users = [
            {"name": result[0], "surname": result[1], "username": result[2], "is_following": result[3]}
            for result in results
        ]

        print("Resultados formateados para el frontend:", users)
        return jsonify(users), 200

    except Exception as e:
        print("Error en /search_users:", e)
        return jsonify({"mensaje": "Error al buscar usuarios"}), 500












if __name__ == "__main__":
    app.run(debug=True)