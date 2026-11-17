"""Consultas especializadas de grafo: traversals, caminos y vecindades."""
from db.connection import ejecutar

# Q1 ¿Qué puedo cursar? Materias cuyos prerrequisitos ya aprobé
QUERY_DISPONIBLES = """
MATCH (a:Alumno {matricula: $matricula}), (m:Materia)
WHERE NOT EXISTS { (a)-[:APROBO|CURSA]->(m) }
  AND NOT EXISTS {
        MATCH (m)-[:REQUIERE]->(req:Materia)
        WHERE NOT EXISTS { (a)-[:APROBO]->(req) }
      }
RETURN m.clave AS clave, m.nombre AS nombre, m.semestre AS semestre
ORDER BY semestre, nombre
"""

# Q2 Cadena completa de prerrequisitos (traversal de longitud variable)
QUERY_CADENA = """
MATCH (m:Materia {clave: $clave})-[:REQUIERE*1..]->(req:Materia)
RETURN DISTINCT req.clave AS clave, req.nombre AS nombre, req.semestre AS semestre
ORDER BY semestre
"""

# Q3 ¿Qué me falta para llegar a X?
QUERY_FALTANTES = """
MATCH (a:Alumno {matricula: $matricula}),
      (m:Materia {clave: $clave})-[:REQUIERE*1..]->(req:Materia)
WHERE NOT EXISTS { (a)-[:APROBO]->(req) }
RETURN DISTINCT req.clave AS clave, req.nombre AS nombre, req.semestre AS semestre
ORDER BY semestre
"""

# Q4 Materias que desbloquea X (traversal inverso)
QUERY_DESBLOQUEA = """
MATCH (m:Materia {clave: $clave})<-[:REQUIERE*1..]-(dep:Materia)
RETURN DISTINCT dep.clave AS clave, dep.nombre AS nombre, dep.semestre AS semestre
ORDER BY semestre
"""

# Q5 Ruta crítica: cadena más larga hasta una materia
QUERY_RUTA_CRITICA = """
MATCH ruta = (m:Materia {clave: $clave})-[:REQUIERE*0..]->(base:Materia)
WHERE NOT EXISTS { (base)-[:REQUIERE]->() }
RETURN [n IN nodes(ruta) | n.nombre] AS ruta, length(ruta) + 1 AS semestres_minimos
ORDER BY semestres_minimos DESC
LIMIT 1
"""

# Q6 Camino más corto entre dos materias
QUERY_CAMINO_CORTO = """
MATCH (x:Materia {clave: $origen}), (y:Materia {clave: $destino})
MATCH ruta = shortestPath((x)-[:REQUIERE*]-(y))
RETURN [n IN nodes(ruta) | n.nombre] AS ruta, length(ruta) AS saltos
"""

# Q7 Compañeros con materias en común (vecindad a 2 saltos)
QUERY_COMPANEROS = """
MATCH (a:Alumno {matricula: $matricula})-[:CURSA]->(m:Materia)<-[:CURSA]-(otro:Alumno)
RETURN otro.nombre AS companero, collect(m.nombre) AS materias_en_comun,
       count(m) AS total
ORDER BY total DESC
"""

# Q8 Materias cuello de botella
QUERY_CUELLOS = """
MATCH (m:Materia)
OPTIONAL MATCH (m)<-[:REQUIERE*1..]-(dep:Materia)
RETURN m.clave AS clave, m.nombre AS nombre, count(DISTINCT dep) AS bloquea
ORDER BY bloquea DESC
LIMIT 5
"""


def materias_disponibles(driver, matricula):
    """Q1: materias no cursadas cuyos prerrequisitos directos están todos aprobados."""
    return ejecutar(driver, QUERY_DISPONIBLES, matricula=matricula)


def cadena_prerrequisitos(driver, clave):
    """Q2: todos los prerrequisitos de una materia, a cualquier profundidad."""
    return ejecutar(driver, QUERY_CADENA, clave=clave)


def faltantes(driver, matricula, clave):
    """Q3: prerrequisitos transitivos que el alumno aún no aprueba."""
    return ejecutar(driver, QUERY_FALTANTES, matricula=matricula, clave=clave)


def desbloquea(driver, clave):
    """Q4: materias que dependen (directa o indirectamente) de esta."""
    return ejecutar(driver, QUERY_DESBLOQUEA, clave=clave)


def ruta_critica(driver, clave):
    """Q5: la cadena de prerrequisitos más larga (semestres mínimos)."""
    return ejecutar(driver, QUERY_RUTA_CRITICA, clave=clave)


def camino_corto(driver, origen, destino):
    """Q6: shortestPath entre dos materias ignorando la dirección."""
    return ejecutar(driver, QUERY_CAMINO_CORTO, origen=origen, destino=destino)


def companeros(driver, matricula):
    """Q7: alumnos que cursan las mismas materias (vecindad a 2 saltos)."""
    return ejecutar(driver, QUERY_COMPANEROS, matricula=matricula)


def cuellos_de_botella(driver):
    """Q8: materias que bloquean más materias posteriores."""
    return ejecutar(driver, QUERY_CUELLOS)
