"""Pobla AuraDB con el plan real, las electivas y los alumnos de ejemplo.

Lee data/plan_curricular.json y data/alumnos.json.
Las contraseñas de demo salen de la variable SEED_PASSWORD (por defecto 'anahuac2026')
y se guardan como hash, nunca en texto plano.

Uso:  python seed/seed.py
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.append(str(RAIZ))

from db.connection import contar, ejecutar, get_driver  # noqa: E402
from db.seguridad import hashear  # noqa: E402

QUERY_LIMPIAR = "MATCH (n) DETACH DELETE n"

QUERY_MATERIAS = """
UNWIND $materias AS m
CREATE (:Materia {clave: m.clave, nombre: m.nombre, semestre: m.semestre,
                  creditos: m.creditos, bloque: m.bloque, tipo: m.tipo})
"""

QUERY_REQUISITOS = """
UNWIND $requisitos AS r
MATCH (m:Materia {clave: r.materia}), (q:Materia {clave: r.requiere})
CREATE (m)-[:REQUIERE]->(q)
"""

QUERY_ALUMNOS = """
UNWIND $alumnos AS al
CREATE (:Alumno {matricula: al.matricula, nombre: al.nombre, carrera: al.carrera,
                 usuario: al.usuario, password_hash: al.password_hash})
"""

# CREATE (no MERGE) para permitir una electiva aprobada dos veces (ej. Fútbol Soccer)
QUERY_ESTADO = """
UNWIND $pares AS p
MATCH (a:Alumno {{matricula: p.matricula}}), (m:Materia {{clave: p.clave}})
CREATE (a)-[:{tipo}]->(m)
"""

QUERY_COORDINADOR = """
CREATE (:Coordinador {usuario: 'coordinador', nombre: 'Coordinación Académica',
                      password_hash: $password_hash})
"""


def cargar_json(nombre):
    return json.loads((RAIZ / "data" / nombre).read_text(encoding="utf-8"))


def esquema(driver):
    """Ejecuta las constraints de seed/schema.cypher."""
    texto = (RAIZ / "seed" / "schema.cypher").read_text(encoding="utf-8")
    lineas = [l for l in texto.splitlines() if not l.strip().startswith("//")]
    for sentencia in "\n".join(lineas).split(";"):
        if sentencia.strip():
            ejecutar(driver, sentencia)


def poblar(driver):
    """Borra todo y carga plan, electivas, seriaciones, alumnos y coordinador."""
    plan = cargar_json("plan_curricular.json")
    alumnos = cargar_json("alumnos.json")["alumnos"]
    password = os.getenv("SEED_PASSWORD", "anahuac2026")

    esquema(driver)
    ejecutar(driver, QUERY_LIMPIAR)

    materias = [{**m, "tipo": "obligatoria"} for m in plan["materias"]]
    materias += [{**e, "semestre": None, "tipo": "electiva"} for e in plan["catalogo_electivas"]]
    ejecutar(driver, QUERY_MATERIAS, materias=materias)
    ejecutar(driver, QUERY_REQUISITOS, requisitos=plan["requisitos"])

    ejecutar(driver, QUERY_ALUMNOS, alumnos=[
        {"matricula": a["matricula"], "nombre": a["nombre"], "carrera": a["carrera"],
         "usuario": a["usuario"], "password_hash": hashear(password)} for a in alumnos])

    for tipo, campo in (("APROBO", "aprobadas"), ("CURSA", "cursando"), ("PRECARGA", "precargadas")):
        pares = [{"matricula": a["matricula"], "clave": c} for a in alumnos for c in a[campo]]
        ejecutar(driver, QUERY_ESTADO.format(tipo=tipo), pares=pares)

    ejecutar(driver, QUERY_COORDINADOR, password_hash=hashear(password))
    return contar(driver)


if __name__ == "__main__":
    driver = get_driver()
    try:
        totales = poblar(driver)
        print(f"Seed listo: {totales['nodos']} nodos y {totales['relaciones']} relaciones en AuraDB.")
    finally:
        driver.close()
