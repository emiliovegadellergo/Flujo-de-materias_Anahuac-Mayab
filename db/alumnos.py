"""CRUD de alumnos y del estado de cada materia (APROBO, CURSA, PRECARGA)."""
from db.connection import ejecutar
from db.seguridad import hashear

ESTADOS = ["APROBO", "CURSA", "PRECARGA"]
CREDITOS_ELECTIVOS = {"BAE": 12, "BIE": 27}  # BIE = BIEA + BIET

# C8 Crear alumno (con contraseña hasheada)
QUERY_CREAR_ALUMNO = """
CREATE (a:Alumno {matricula: $matricula, nombre: $nombre, carrera: $carrera,
                  usuario: $usuario, password_hash: $password_hash})
RETURN a.matricula AS matricula
"""

# C9 Leer alumnos con su avance
QUERY_LISTAR_ALUMNOS = """
MATCH (a:Alumno)
OPTIONAL MATCH (a)-[r:APROBO|CURSA|PRECARGA]->(m:Materia)
RETURN a.matricula AS matricula, a.nombre AS nombre, a.usuario AS usuario,
       a.carrera AS carrera,
       sum(CASE WHEN type(r) = 'APROBO' THEN 1 ELSE 0 END) AS aprobadas,
       sum(CASE WHEN type(r) = 'CURSA' THEN 1 ELSE 0 END) AS cursando,
       sum(CASE WHEN type(r) = 'PRECARGA' THEN 1 ELSE 0 END) AS precargadas,
       sum(CASE WHEN type(r) = 'APROBO' THEN m.creditos ELSE 0 END) AS creditos_aprobados
ORDER BY nombre
"""

# C10 Actualizar alumno
QUERY_ACTUALIZAR_ALUMNO = """
MATCH (a:Alumno {matricula: $matricula})
SET a.nombre = $nombre, a.carrera = $carrera
RETURN a.matricula AS matricula
"""

# C11 Eliminar alumno y todo su historial
QUERY_ELIMINAR_ALUMNO = """
MATCH (a:Alumno {matricula: $matricula})
DETACH DELETE a
"""

# C12 Quitar el estado actual de una materia (la deja como pendiente)
QUERY_LIMPIAR_ESTADO = """
MATCH (a:Alumno {matricula: $matricula})-[r:APROBO|CURSA|PRECARGA]->(m:Materia {clave: $clave})
DELETE r
"""

# C13 Asignar estado: una consulta por tipo de relación (Cypher no permite tipos como parámetro)
QUERY_ASIGNAR_ESTADO = {
    tipo: f"""
MATCH (a:Alumno {{matricula: $matricula}}), (m:Materia {{clave: $clave}})
MERGE (a)-[:{tipo}]->(m)
"""
    for tipo in ESTADOS
}

# Mapa del alumno: todas las materias obligatorias con su estado
QUERY_MAPA = """
MATCH (a:Alumno {matricula: $matricula}), (m:Materia {tipo: 'obligatoria'})
OPTIONAL MATCH (a)-[r:APROBO|CURSA|PRECARGA]->(m)
RETURN m.clave AS clave, m.nombre AS nombre, m.semestre AS semestre,
       m.creditos AS creditos, m.bloque AS bloque,
       coalesce(type(r), 'PENDIENTE') AS estado
ORDER BY semestre, clave
"""

# Electivas del alumno
QUERY_ELECTIVAS = """
MATCH (a:Alumno {matricula: $matricula})-[r:APROBO|CURSA|PRECARGA]->(m:Materia {tipo: 'electiva'})
RETURN m.clave AS clave, m.nombre AS nombre, m.bloque AS bloque,
       m.creditos AS creditos, type(r) AS estado
ORDER BY bloque, nombre
"""

# Créditos de electivas aprobados por bloque
QUERY_CREDITOS_ELECTIVOS = """
MATCH (a:Alumno {matricula: $matricula})
OPTIONAL MATCH (a)-[:APROBO]->(m:Materia {tipo: 'electiva'})
RETURN sum(CASE WHEN m.bloque = 'BAE' THEN m.creditos ELSE 0 END) AS bae,
       sum(CASE WHEN m.bloque IN ['BIEA', 'BIET'] THEN m.creditos ELSE 0 END) AS bie
"""


def crear_alumno(driver, matricula, nombre, carrera, usuario, password):
    """Crea un nodo :Alumno; la contraseña se guarda como hash."""
    return ejecutar(driver, QUERY_CREAR_ALUMNO, matricula=matricula, nombre=nombre, carrera=carrera,
                    usuario=usuario.lower(), password_hash=hashear(password))


def listar_alumnos(driver):
    """Lista alumnos con cuántas materias aprobó, cursa y precargó."""
    return ejecutar(driver, QUERY_LISTAR_ALUMNOS)


def actualizar_alumno(driver, matricula, nombre, carrera):
    """Actualiza nombre y carrera de un alumno."""
    return ejecutar(driver, QUERY_ACTUALIZAR_ALUMNO, matricula=matricula, nombre=nombre, carrera=carrera)


def eliminar_alumno(driver, matricula):
    """Borra al alumno y todo su historial (DETACH DELETE)."""
    ejecutar(driver, QUERY_ELIMINAR_ALUMNO, matricula=matricula)


def cambiar_estado(driver, matricula, clave, estado):
    """Cambia el estado de una materia: APROBO, CURSA, PRECARGA o PENDIENTE (sin relación)."""
    ejecutar(driver, QUERY_LIMPIAR_ESTADO, matricula=matricula, clave=clave)
    if estado in QUERY_ASIGNAR_ESTADO:
        ejecutar(driver, QUERY_ASIGNAR_ESTADO[estado], matricula=matricula, clave=clave)


def mapa(driver, matricula):
    """Todas las materias obligatorias con el estado del alumno (para el flujograma)."""
    return ejecutar(driver, QUERY_MAPA, matricula=matricula)


def electivas(driver, matricula):
    """Electivas que el alumno aprobó, cursa o precargó."""
    return ejecutar(driver, QUERY_ELECTIVAS, matricula=matricula)


def creditos_electivos(driver, matricula):
    """Créditos de electivas aprobados contra los requeridos (BAE 12, BIEA+BIET 27)."""
    fila = ejecutar(driver, QUERY_CREDITOS_ELECTIVOS, matricula=matricula)[0]
    return {"BAE": (fila["bae"], CREDITOS_ELECTIVOS["BAE"]), "BIE": (fila["bie"], CREDITOS_ELECTIVOS["BIE"])}
