"""CRUD de materias (obligatorias y electivas) y de sus prerrequisitos (REQUIERE)."""
from db.connection import ejecutar

# C1 Crear materia
QUERY_CREAR_MATERIA = """
CREATE (m:Materia {clave: $clave, nombre: $nombre, semestre: $semestre,
                   creditos: $creditos, bloque: $bloque, tipo: $tipo})
RETURN m.clave AS clave
"""

# C2 Leer todas las materias con sus prerrequisitos directos
QUERY_LISTAR_MATERIAS = """
MATCH (m:Materia)
OPTIONAL MATCH (m)-[:REQUIERE]->(r:Materia)
RETURN m.clave AS clave, m.nombre AS nombre, m.semestre AS semestre,
       m.creditos AS creditos, m.bloque AS bloque, m.tipo AS tipo,
       collect(r.clave) AS requisitos
ORDER BY tipo, semestre, clave
"""

# C3 Leer una materia
QUERY_OBTENER_MATERIA = """
MATCH (m:Materia {clave: $clave})
RETURN m {.*} AS materia
"""

# C4 Actualizar materia
QUERY_ACTUALIZAR_MATERIA = """
MATCH (m:Materia {clave: $clave})
SET m.nombre = $nombre, m.semestre = $semestre, m.creditos = $creditos, m.bloque = $bloque
RETURN m {.*} AS materia
"""

# C5 Eliminar materia y todas sus relaciones
QUERY_ELIMINAR_MATERIA = """
MATCH (m:Materia {clave: $clave})
DETACH DELETE m
"""

# C6 Agregar prerrequisito evitando ciclos
QUERY_AGREGAR_REQUISITO = """
MATCH (m:Materia {clave: $clave}), (r:Materia {clave: $requisito})
WHERE m <> r AND NOT EXISTS { (r)-[:REQUIERE*]->(m) }
MERGE (m)-[:REQUIERE]->(r)
RETURN m.clave AS materia, r.clave AS requisito
"""

# C7 Quitar prerrequisito
QUERY_QUITAR_REQUISITO = """
MATCH (:Materia {clave: $clave})-[rel:REQUIERE]->(:Materia {clave: $requisito})
DELETE rel
"""


def crear_materia(driver, clave, nombre, semestre, creditos, bloque, tipo="obligatoria"):
    """Crea un nodo :Materia (la constraint impide claves repetidas)."""
    return ejecutar(driver, QUERY_CREAR_MATERIA, clave=clave, nombre=nombre, semestre=semestre,
                    creditos=creditos, bloque=bloque, tipo=tipo)


def listar_materias(driver):
    """Lista las materias con sus prerrequisitos directos (vecinos REQUIERE)."""
    return ejecutar(driver, QUERY_LISTAR_MATERIAS)


def obtener_materia(driver, clave):
    """Regresa las propiedades de una materia o None si no existe."""
    filas = ejecutar(driver, QUERY_OBTENER_MATERIA, clave=clave)
    return filas[0]["materia"] if filas else None


def actualizar_materia(driver, clave, nombre, semestre, creditos, bloque):
    """Actualiza las propiedades de una materia."""
    return ejecutar(driver, QUERY_ACTUALIZAR_MATERIA, clave=clave, nombre=nombre,
                    semestre=semestre, creditos=creditos, bloque=bloque)


def eliminar_materia(driver, clave):
    """Borra la materia y todas sus relaciones (DETACH DELETE)."""
    ejecutar(driver, QUERY_ELIMINAR_MATERIA, clave=clave)


def agregar_requisito(driver, clave, requisito):
    """Crea (materia)-[:REQUIERE]->(requisito). Regresa False si formaría un ciclo."""
    return len(ejecutar(driver, QUERY_AGREGAR_REQUISITO, clave=clave, requisito=requisito)) > 0


def quitar_requisito(driver, clave, requisito):
    """Elimina la relación REQUIERE entre dos materias."""
    ejecutar(driver, QUERY_QUITAR_REQUISITO, clave=clave, requisito=requisito)
