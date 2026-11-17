"""Conexión a Neo4j AuraDB usando el driver oficial y variables de entorno."""
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI", "")
USUARIO = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def get_driver():
    """Crea el driver una sola vez (pool de conexiones) y verifica que AuraDB responda."""
    if not URI or not PASSWORD:
        raise RuntimeError("Faltan NEO4J_URI o NEO4J_PASSWORD. Revisa tu archivo .env")
    driver = GraphDatabase.driver(URI, auth=(USUARIO, PASSWORD))
    driver.verify_connectivity()
    return driver


def ejecutar(driver, query, **parametros):
    """Ejecuta una consulta Cypher parametrizada y regresa una lista de diccionarios."""
    records, _, _ = driver.execute_query(query, parametros, database_=DATABASE)
    return [r.data() for r in records]


QUERY_CONTEO = """
MATCH (n)
WITH count(n) AS nodos
OPTIONAL MATCH ()-[r]->()
RETURN nodos, count(r) AS relaciones
"""


def contar(driver):
    """Cuenta nodos y relaciones para mostrar en la barra lateral."""
    return ejecutar(driver, QUERY_CONTEO)[0]
