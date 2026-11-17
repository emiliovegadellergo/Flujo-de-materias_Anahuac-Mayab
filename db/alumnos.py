"""CRUD de alumnos y de su historial (relaciones APROBO y CURSA)."""
from db.connection import ejecutar

# C8 Crear alumno
QUERY_CREAR_ALUMNO = """
CREATE (a:Alumno {matricula: $matricula, nombre: $nombre, carrera: $carrera})
RETURN a.matricula AS matricula
"""

# C9 Leer alumnos con su avance
QUERY_LISTAR_ALUMNOS = """
MATCH (a:Alumno)
OPTIONAL MATCH (a)-[ap:APROBO]->(m:Materia)
RETURN a.matricula AS matricula, a.nombre AS nombre, a.carrera AS carrera,
       count(m) AS aprobadas, sum(m.creditos) AS creditos,
       round(avg(ap.calificacion), 1) AS promedio
ORDER BY nombre
"""

# C10 Actualizar alumno
QUERY_ACTUALIZAR_ALUMNO = """
MATCH (a:Alumno {matricula: $matricula})
SET a.nombre = $nombre, a.carrera = $carrera
RETURN a {.*} AS alumno
"""

# C11 Eliminar alumno
QUERY_ELIMINAR_ALUMNO = """
MATCH (a:Alumno {matricula: $matricula})
DETACH DELETE a
"""

# C12 Inscribir a una materia
QUERY_INSCRIBIR = """
MATCH (a:Alumno {matricula: $matricula}), (m:Materia {clave: $clave})
MERGE (a)-[c:CURSA]->(m)
SET c.periodo = $periodo
"""

# C13 Aprobar materia (pasa de CURSA a APROBO)
QUERY_APROBAR = """
MATCH (a:Alumno {matricula: $matricula}), (m:Materia {clave: $clave})
MERGE (a)-[ap:APROBO]->(m)
SET ap.calificacion = $calificacion, ap.periodo = $periodo
WITH a, m
OPTIONAL MATCH (a)-[c:CURSA]->(m)
DELETE c
"""

# Historial del alumno (apoyo para la interfaz)
QUERY_HISTORIAL = """
MATCH (a:Alumno {matricula: $matricula})-[r:APROBO|CURSA]->(m:Materia)
RETURN m.clave AS clave, m.nombre AS nombre, type(r) AS estado,
       r.calificacion AS calificacion, r.periodo AS periodo
ORDER BY estado, m.semestre
"""


def crear_alumno(driver, matricula, nombre, carrera):
    """Crea un nodo :Alumno (la constraint impide matrículas repetidas)."""
    return ejecutar(driver, QUERY_CREAR_ALUMNO, matricula=matricula, nombre=nombre, carrera=carrera)


def listar_alumnos(driver):
    """Lista alumnos con materias aprobadas, créditos y promedio."""
    return ejecutar(driver, QUERY_LISTAR_ALUMNOS)


def actualizar_alumno(driver, matricula, nombre, carrera):
    """Actualiza nombre y carrera de un alumno."""
    return ejecutar(driver, QUERY_ACTUALIZAR_ALUMNO, matricula=matricula, nombre=nombre, carrera=carrera)


def eliminar_alumno(driver, matricula):
    """Borra al alumno y todo su historial (DETACH DELETE)."""
    ejecutar(driver, QUERY_ELIMINAR_ALUMNO, matricula=matricula)


def inscribir(driver, matricula, clave, periodo):
    """Crea la relación (alumno)-[:CURSA]->(materia)."""
    ejecutar(driver, QUERY_INSCRIBIR, matricula=matricula, clave=clave, periodo=periodo)


def aprobar(driver, matricula, clave, calificacion, periodo):
    """Crea (alumno)-[:APROBO]->(materia) con calificación y quita CURSA."""
    ejecutar(driver, QUERY_APROBAR, matricula=matricula, clave=clave,
             calificacion=calificacion, periodo=periodo)


def historial(driver, matricula):
    """Materias aprobadas y en curso de un alumno."""
    return ejecutar(driver, QUERY_HISTORIAL, matricula=matricula)
