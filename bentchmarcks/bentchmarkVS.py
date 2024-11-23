import cx_Oracle
from neo4j import GraphDatabase
from datetime import datetime

# Configuración de conexión para Oracle DB
dsn_oracle = cx_Oracle.makedsn("192.168.56.1", 1521, service_name="XE")
connection_oracle = cx_Oracle.connect(user="C##juan", password="1234", dsn=dsn_oracle)

# Configuración de conexión para Neo4j
class Neo4jConnection:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            return session.run(query, parameters)

connection_neo4j = Neo4jConnection(uri="bolt://192.168.1.34:7687", user="neo4j", password="touch-nice-joker-tape-junior-9975")

# Consulta en Oracle DB
def query_oracle():
    cursor = connection_oracle.cursor()
    start_time = datetime.now()

    query = """
        SELECT p.id_publicacion, COUNT(l.id_like) AS total_likes
        FROM Publicaciones p
        JOIN Likeo_Post l ON p.id_publicacion = l.id_publicacion
        GROUP BY p.id_publicacion
        HAVING COUNT(l.id_like) = 3
    """
    cursor.execute(query)
    resultado = cursor.fetchall()

    elapsed_time = datetime.now() - start_time
    cursor.close()

    return resultado, elapsed_time.total_seconds()

def query_neo4j():
    start_time = datetime.now()

    query = """
        MATCH (p:Post)<-[:LE_GUSTO]-(u:Usuario)
        WITH p, COUNT(u) AS total_likes
        WHERE total_likes = 3
        RETURN p.contenido AS publicacion, total_likes
    """
    # Ejecutar la consulta y procesar el resultado de forma segura
    with connection_neo4j.driver.session() as session:
        resultado = session.run(query)
        publicaciones = [{"publicacion": record["publicacion"], "likes": record["total_likes"]} for record in resultado]

    elapsed_time = datetime.now() - start_time

    return publicaciones, elapsed_time.total_seconds()



# Comparar resultados
def comparar_tiempos():
    print("Ejecutando consulta en Oracle DB...")
    oracle_resultado, oracle_tiempo = query_oracle()
    print(f"Oracle DB - Tiempo de ejecución: {oracle_tiempo:.6f} segundos")
    print(f"Resultados: {oracle_resultado}")

    print("\nEjecutando consulta en Neo4j...")
    neo4j_resultado, neo4j_tiempo = query_neo4j()
    print(f"Neo4j - Tiempo de ejecución: {neo4j_tiempo:.6f} segundos")
    print(f"Resultados: {neo4j_resultado}")

    # Comparar tiempos
    print("\nComparación de Tiempos:")
    print(f"- Oracle DB: {oracle_tiempo:.6f} segundos")
    print(f"- Neo4j: {neo4j_tiempo:.6f} segundos")

    if oracle_tiempo < neo4j_tiempo:
        print("Oracle DB fue más rápido.")
    elif oracle_tiempo > neo4j_tiempo:
        print("Neo4j fue más rápido.")
    else:
        print("Ambas bases de datos tardaron lo mismo.")

# Ejecutar la comparación
if __name__ == "__main__":
    try:
        comparar_tiempos()
    finally:
        # Cerrar conexiones
        connection_oracle.close()
        connection_neo4j.close()
