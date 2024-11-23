import uuid
from neo4j import GraphDatabase
from datetime import datetime

class RedSocialNeo4j:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def crear_estructura(self):
        with self.driver.session() as session:
            # Crear Usuarios
            usuarios = [
                {"id": 1, "nombre": "Juan", "apellido": "Pérez", "usuario": "juanperez", "email": "juan.perez@example.com", "edad": 30},
                {"id": 2, "nombre": "María", "apellido": "Gómez", "usuario": "mariagomez", "email": "maria.gomez@example.com", "edad": 28},
                {"id": 3, "nombre": "Luis", "apellido": "Martínez", "usuario": "luismartinez", "email": "luis.martinez@example.com", "edad": 35},
            ]
            for u in usuarios:
                session.run("""
                    CREATE (:Usuario {id: $id, nombre: $nombre, apellido: $apellido, usuario: $usuario, email: $email, edad: $edad, fecha_creacion: datetime()})
                """, u)

            # Crear publicaciones
            for i in range(10):
                for usuario_id in [1, 2, 3]:  # Usuario IDs 1, 2 y 3
                    contenido_publicacion = f"Publicación {i + 1} del usuario {usuario_id}"
                    publicacion_id = str(uuid.uuid4())  # Generar UUID desde Python
                    session.run("""
                        MATCH (u:Usuario {id: $usuario_id})
                        CREATE (u)-[:POSTEO]->(:Post {id: $post_id, contenido: $contenido, fecha_creacion: datetime()})
                    """, {"usuario_id": usuario_id, "post_id": publicacion_id, "contenido": contenido_publicacion})

    def agregar_likes(self):
        with self.driver.session() as session:
            # Obtener el último posteo
            resultado = session.run("""
                MATCH (p:Post)
                RETURN p.id AS post_id
                ORDER BY p.fecha_creacion DESC
                LIMIT 1
            """)
            ultimo_post_id = resultado.single()["post_id"]

            # Los tres usuarios le dan like
            for usuario_id in [1, 2, 3]:
                session.run("""
                    MATCH (u:Usuario {id: $usuario_id}), (p:Post {id: $post_id})
                    CREATE (u)-[:LE_GUSTO]->(p)
                """, {"usuario_id": usuario_id, "post_id": ultimo_post_id})

    def consultar_publicacion_con_3_likes(self):
        with self.driver.session() as session:
            start_time = datetime.now()

            resultado = session.run("""
                MATCH (p:Post)<-[:LE_GUSTO]-(u:Usuario)
                WITH p, COUNT(u) AS total_likes
                WHERE total_likes = 3
                RETURN p.contenido AS publicacion, total_likes
            """)
            publicaciones = [record["publicacion"] for record in resultado]

            elapsed_time = datetime.now() - start_time
            print(f"Tiempo para realizar la consulta: {elapsed_time.total_seconds():.6f} segundos")
            print("Publicaciones con 3 likes:", publicaciones)


# Ejecutar el script
if __name__ == "__main__":
    red_social = RedSocialNeo4j(uri="bolt://192.168.1.34:7687", user="neo4j", password="touch-nice-joker-tape-junior-9975")

    try:
        print("Creando estructura de la red social...")
        red_social.crear_estructura()
        print("Estructura creada con éxito.")

        print("Agregando likes a la última publicación...")
        red_social.agregar_likes()
        print("Likes agregados con éxito.")

        print("Consultando publicaciones con 3 likes...")
        red_social.consultar_publicacion_con_3_likes()

    finally:
        red_social.close()
