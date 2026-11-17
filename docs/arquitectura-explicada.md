# Cómo funciona el Mapa de Materias, de punta a punta

## 1. La idea en una frase

Tú abres una página web hecha con **Streamlit**. Cada botón llama a una función de Python, que manda una consulta **Cypher** por internet a tu base **Neo4j AuraDB** en la nube y te regresa el resultado en una tabla.

## 2. Diagrama de arquitectura (4 capas)

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1 · PRESENTACIÓN              (tu computadora)        │
│  Navegador  ⇄  app.py (Streamlit)                           │
│  Pestañas: Materias · Alumnos · Consultas de grafo          │
│  Solo dibuja la pantalla y recibe clics. NO tiene Cypher.   │
└───────────────────────────┬─────────────────────────────────┘
                            │ llama funciones de Python
┌───────────────────────────▼─────────────────────────────────┐
│  CAPA 2 · ACCESO A DATOS            (tu computadora)        │
│  db/materias.py   → CRUD de materias y prerrequisitos       │
│  db/alumnos.py    → CRUD de alumnos, inscribir, aprobar     │
│  db/consultas.py  → Q1–Q8 (traversals, caminos, vecindad)   │
│  Cada función = 1 consulta Cypher con parámetros ($clave).  │
└───────────────────────────┬─────────────────────────────────┘
                            │ driver.execute_query(...)
┌───────────────────────────▼─────────────────────────────────┐
│  CAPA 3 · CONEXIÓN (SDK)            (tu computadora)        │
│  db/connection.py + driver oficial `neo4j` para Python      │
│  Lee .env → NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD       │
│  Mantiene un pool de conexiones y reintenta si algo falla.  │
└───────────────────────────┬─────────────────────────────────┘
                            │ Protocolo Bolt cifrado (TLS)
                            │ neo4j+s://xxxx.databases.neo4j.io
                            │        ~~~ INTERNET ~~~
┌───────────────────────────▼─────────────────────────────────┐
│  CAPA 4 · BASE DE DATOS             (la nube de Neo4j)      │
│  Neo4j AuraDB Free: servicio gestionado (DaaS)              │
│  Nodos :Materia, :Alumno · Relaciones REQUIERE, APROBO,     │
│  CURSA · Constraints de unicidad · Datos persistentes       │
└─────────────────────────────────────────────────────────────┘

   seed/seed.py ──(usa la capa 3)──▶ borra y carga los datos de ejemplo
```

**Lo que pide el profe:** la base no puede estar en localhost. Aquí la base vive en la nube y solo la interfaz corre en tu compu. Eso cumple la regla. Si quieres ir más allá, la app se puede publicar gratis en Streamlit Community Cloud (ver pendientes).

## 3. Un clic, paso a paso

Ejemplo: eliges al alumno "Luis Pérez" y presionas **"¿Qué puedo cursar?"**

1. **app.py** detecta el clic y llama `consultas.materias_disponibles(driver, "A002")`.
2. **db/consultas.py** tiene guardada la consulta Q1 y la ejecuta con el parámetro `matricula = "A002"`.
3. **El driver** toma una conexión ya abierta del pool y manda la consulta cifrada a AuraDB.
4. **AuraDB** encuentra el nodo de Luis gracias al índice de la constraint. Recorre las materias que no ha aprobado y revisa si cada uno de sus prerrequisitos (`REQUIERE`) ya tiene una relación `APROBO`. Contesta con la lista.
5. **El driver** convierte la respuesta en objetos de Python (`records`) y la función los regresa como una lista de diccionarios.
6. **app.py** muestra la tabla con `st.dataframe(...)` y, debajo, el Cypher que se ejecutó (`st.code`). Así lo explicas en la defensa.

Una escritura funciona igual. Por ejemplo, al **aprobar una materia** (C13) se crea la relación `APROBO` y se borra `CURSA`. Si luego le das de nuevo a "¿Qué puedo cursar?", ya aparecen materias nuevas. Ese es el momento fuerte de la demo, porque se ve la persistencia en la nube.

## 4. Qué hace cada archivo

| Archivo | Para qué sirve | Qué dices en la defensa |
|---|---|---|
| `app.py` | Pantalla y botones | "Separé la interfaz de la lógica de datos." |
| `db/connection.py` | Crea el driver con las variables de entorno | "Las credenciales nunca están en el código; uso `neo4j+s` para cifrar." |
| `db/materias.py` | Crear, leer, editar y borrar materias; agregar y quitar prerrequisitos sin ciclos | "C6 valida que no se formen ciclos antes de crear la relación." |
| `db/alumnos.py` | CRUD de alumnos, inscribir y aprobar | "La calificación vive en la relación APROBO, no en el nodo." |
| `db/consultas.py` | Las 8 consultas de grafo | "Aquí está el valor del grafo: recorridos de profundidad variable." |
| `seed/schema.cypher` | Constraints de unicidad | "Evitan duplicados y crean índices." |
| `seed/seed.cypher` + `seed.py` | Cargan 22 materias y 4 alumnos | "Es idempotente: lo puedo correr las veces que quiera." |
| `.env` / `.env.example` | Credenciales reales y su plantilla | "`.env` está en `.gitignore`." |
| `requirements.txt` | Dependencias | — |

## 5. El modelo de datos (lo que vive en AuraDB)

```
            APROBO {calificacion, periodo}
 (Alumno) ───────────────────────────────▶ (Materia) ──REQUIERE──▶ (Materia)
     │                                         ▲
     └────────── CURSA {periodo} ──────────────┘
```

Ejemplo real del seed:
`(Proyecto Terminal)-[:REQUIERE]->(Cómputo en la Nube)-[:REQUIERE]->(Desarrollo Web)-[:REQUIERE]->(BD Avanzadas)-[:REQUIERE]->(Bases de Datos)-[:REQUIERE]->(POO)-[:REQUIERE]->(Fundamentos de Programación)`
Esa cadena de 7 materias es la **ruta crítica** (Q5): significa que se necesitan como mínimo 7 semestres para llegar a Proyecto Terminal.
