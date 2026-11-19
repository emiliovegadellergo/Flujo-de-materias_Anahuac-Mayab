"""Consultas especializadas de grafo: traversals, caminos y vecindades.

Q1–Q9: vista del alumno.  Q10–Q13: vista del coordinador.
"""
from db.connection import ejecutar

# ---------------------------------------------------------------- Alumno

# Q1 ¿Qué puedo cargar? Materias cuyos prerrequisitos ya aprobé (o estoy cursando = condicionada)
QUERY_PUEDO_CARGAR = """
MATCH (a:Alumno {matricula: $matricula}), (m:Materia {tipo: 'obligatoria'})
WHERE NOT EXISTS { (a)-[:APROBO|CURSA|PRECARGA]->(m) }
  AND NOT EXISTS {
        MATCH (m)-[:REQUIERE]->(req:Materia)
        WHERE NOT EXISTS { (a)-[:APROBO|CURSA]->(req) }
      }
OPTIONAL MATCH (m)-[:REQUIERE]->(enCurso:Materia)<-[:CURSA]-(a)
RETURN m.clave AS clave, m.nombre AS nombre, m.semestre AS semestre,
       CASE WHEN count(enCurso) = 0 THEN 'Disponible'
            ELSE 'Condicionada: debes aprobar ' + head(collect(enCurso.nombre)) END AS situacion
ORDER BY semestre, nombre
"""

# Q2 Cadena completa de prerrequisitos (traversal de longitud variable)
QUERY_CADENA = """
MATCH (m:Materia {clave: $clave})-[:REQUIERE*1..]->(req:Materia)
RETURN DISTINCT req.clave AS clave, req.nombre AS nombre, req.semestre AS semestre
ORDER BY semestre
"""

# Q2b Aristas de la cadena (para dibujar el grafo en la app)
QUERY_CADENA_ARISTAS = """
MATCH ruta = (m:Materia {clave: $clave})-[:REQUIERE*1..]->(:Materia)
UNWIND relationships(ruta) AS r
RETURN DISTINCT startNode(r).clave AS desde, endNode(r).clave AS hacia
"""

# Q3 ¿Qué me falta para llegar a X? (prerrequisitos transitivos no aprobados)
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

# Q5 Ruta crítica: la cadena más larga hasta una materia
QUERY_RUTA_CRITICA = """
MATCH ruta = (m:Materia {clave: $clave})-[:REQUIERE*0..]->(base:Materia)
WHERE NOT EXISTS { (base)-[:REQUIERE]->() }
RETURN [n IN nodes(ruta) | n.nombre] AS ruta, length(ruta) + 1 AS materias_en_cadena
ORDER BY materias_en_cadena DESC
LIMIT 1
"""

# Q6 Camino más corto entre dos materias (búsqueda de caminos)
QUERY_CAMINO_CORTO = """
MATCH (x:Materia {clave: $origen}), (y:Materia {clave: $destino})
MATCH ruta = shortestPath((x)-[:REQUIERE*]-(y))
RETURN [n IN nodes(ruta) | n.nombre] AS ruta, length(ruta) AS saltos
"""

# Q7 ¿Con qué amigos puedo llevar la materia X el próximo semestre?
QUERY_AMIGOS_MATERIA = """
MATCH (yo:Alumno {matricula: $matricula}), (m:Materia {clave: $clave}), (otro:Alumno)
WHERE otro <> yo
  AND NOT EXISTS { (otro)-[:APROBO|CURSA]->(m) }
  AND NOT EXISTS {
        MATCH (m)-[:REQUIERE]->(req:Materia)
        WHERE NOT EXISTS { (otro)-[:APROBO|CURSA]->(req) }
      }
WITH otro, EXISTS { (otro)-[:PRECARGA]->(m) } AS precargada
RETURN otro.nombre AS amigo,
       CASE WHEN precargada THEN 'Ya la precargó' ELSE 'Puede cargarla' END AS situacion
ORDER BY precargada DESC, amigo
"""

# Q8 Mis precargas y quién más las precargó
QUERY_PRECARGAS_CON_AMIGOS = """
MATCH (yo:Alumno {matricula: $matricula})-[:PRECARGA]->(m:Materia)
OPTIONAL MATCH (m)<-[:PRECARGA]-(otro:Alumno)
WHERE otro <> yo
RETURN m.clave AS clave, m.nombre AS materia, count(otro) AS total,
       collect(otro.nombre) AS amigos
ORDER BY total DESC, materia
"""

# Q9 Compañeros con más materias en común (vecindad a 2 saltos, mismo tipo de relación)
QUERY_COMPANEROS = """
MATCH (yo:Alumno {matricula: $matricula})-[r1:CURSA|PRECARGA]->(m:Materia)<-[r2:CURSA|PRECARGA]-(otro:Alumno)
WHERE type(r1) = type(r2)
RETURN otro.nombre AS companero, count(DISTINCT m) AS en_comun,
       collect(DISTINCT m.nombre) AS materias
ORDER BY en_comun DESC
"""

# ---------------------------------------------------------------- Coordinador

# Q10 Demanda del próximo semestre: precargados + alumnos que podrían cargarla
QUERY_DEMANDA = """
MATCH (m:Materia {tipo: 'obligatoria'})
OPTIONAL MATCH (pre:Alumno)-[:PRECARGA]->(m)
WITH m, count(pre) AS precargados
OPTIONAL MATCH (pot:Alumno)
WHERE NOT EXISTS { (pot)-[:APROBO|CURSA|PRECARGA]->(m) }
  AND NOT EXISTS {
        MATCH (m)-[:REQUIERE]->(req:Materia)
        WHERE NOT EXISTS { (pot)-[:APROBO|CURSA]->(req) }
      }
WITH m, precargados, count(pot) AS podrian
WHERE precargados + podrian > 0
RETURN m.clave AS clave, m.nombre AS materia, m.semestre AS semestre,
       precargados, podrian, precargados + podrian AS demanda_maxima
ORDER BY demanda_maxima DESC, semestre
"""

# Q11 Alumnos rezagados: materias atrasadas respecto a su semestre actual y cuánto bloquean
QUERY_REZAGADOS = """
MATCH (a:Alumno)-[:CURSA]->(c:Materia {tipo: 'obligatoria'})
WITH a, max(c.semestre) AS semestre_actual
MATCH (m:Materia {tipo: 'obligatoria'})
WHERE m.semestre < semestre_actual AND NOT EXISTS { (a)-[:APROBO|CURSA]->(m) }
OPTIONAL MATCH (m)<-[:REQUIERE*1..]-(bloqueada:Materia)
RETURN a.nombre AS alumno, semestre_actual, m.nombre AS materia_atrasada,
       m.semestre AS semestre_materia, count(DISTINCT bloqueada) AS materias_que_bloquea
ORDER BY materias_que_bloquea DESC, alumno
"""

# Q12 Impacto de NO abrir una materia: alumnos afectados y materias que se retrasan
QUERY_IMPACTO = """
MATCH (m:Materia {clave: $clave})
OPTIONAL MATCH (a:Alumno)-[:PRECARGA]->(m)
WITH m, collect(a.nombre) AS alumnos_afectados
OPTIONAL MATCH (m)<-[:REQUIERE*1..]-(dep:Materia)
RETURN m.nombre AS materia, size(alumnos_afectados) AS total_alumnos, alumnos_afectados,
       count(DISTINCT dep) AS total_materias, collect(DISTINCT dep.nombre) AS materias_que_se_retrasan
"""

# Q13 Materias "cuello de botella" (las que más materias bloquean)
QUERY_CUELLOS = """
MATCH (m:Materia {tipo: 'obligatoria'})
OPTIONAL MATCH (m)<-[:REQUIERE*1..]-(dep:Materia)
RETURN m.clave AS clave, m.nombre AS materia, count(DISTINCT dep) AS bloquea
ORDER BY bloquea DESC
LIMIT 8
"""


def puedo_cargar(driver, matricula):
    """Q1: materias disponibles o condicionadas para el próximo semestre."""
    return ejecutar(driver, QUERY_PUEDO_CARGAR, matricula=matricula)


def cadena_prerrequisitos(driver, clave):
    """Q2: todos los prerrequisitos de una materia, a cualquier profundidad."""
    return ejecutar(driver, QUERY_CADENA, clave=clave)


def cadena_aristas(driver, clave):
    """Q2b: pares (desde, hacia) de la cadena, para dibujarla."""
    return ejecutar(driver, QUERY_CADENA_ARISTAS, clave=clave)


def faltantes(driver, matricula, clave):
    """Q3: prerrequisitos transitivos que el alumno aún no aprueba."""
    return ejecutar(driver, QUERY_FALTANTES, matricula=matricula, clave=clave)


def desbloquea(driver, clave):
    """Q4: materias que dependen (directa o indirectamente) de esta."""
    return ejecutar(driver, QUERY_DESBLOQUEA, clave=clave)


def ruta_critica(driver, clave):
    """Q5: la cadena de prerrequisitos más larga hasta la materia."""
    return ejecutar(driver, QUERY_RUTA_CRITICA, clave=clave)


def camino_corto(driver, origen, destino):
    """Q6: shortestPath entre dos materias ignorando la dirección."""
    return ejecutar(driver, QUERY_CAMINO_CORTO, origen=origen, destino=destino)


def amigos_para_materia(driver, matricula, clave):
    """Q7: compañeros que pueden llevar la misma materia el próximo semestre."""
    return ejecutar(driver, QUERY_AMIGOS_MATERIA, matricula=matricula, clave=clave)


def precargas_con_amigos(driver, matricula):
    """Q8: cada materia precargada y qué compañeros también la precargaron."""
    return ejecutar(driver, QUERY_PRECARGAS_CON_AMIGOS, matricula=matricula)


def companeros(driver, matricula):
    """Q9: compañeros con más materias en común (cursando o precargadas)."""
    return ejecutar(driver, QUERY_COMPANEROS, matricula=matricula)


def demanda(driver):
    """Q10: demanda estimada por materia para el próximo semestre."""
    return ejecutar(driver, QUERY_DEMANDA)


def rezagados(driver):
    """Q11: materias atrasadas por alumno y cuántas materias bloquean."""
    return ejecutar(driver, QUERY_REZAGADOS)


def impacto(driver, clave):
    """Q12: alumnos y materias afectados si no se abre la materia."""
    return ejecutar(driver, QUERY_IMPACTO, clave=clave)


def cuellos_de_botella(driver):
    """Q13: materias que bloquean más materias posteriores."""
    return ejecutar(driver, QUERY_CUELLOS)
