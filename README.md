# 🎓 Mapa de Materias — Grafo de prerrequisitos con Neo4j AuraDB

Aplicación web sencilla que modela el plan de estudios de una carrera como un **grafo**: cada materia es un nodo y cada prerrequisito es una relación. Con eso el alumno puede saber, en tiempo real y desde la nube:

- ¿Qué materias **puedo cursar ya** con lo que tengo aprobado?
- ¿Qué **cadena completa de prerrequisitos** necesito para llegar a una materia (p. ej. *Proyecto Terminal*)?
- ¿Qué materias **desbloqueo** si apruebo una materia?
- ¿Cuál es la **ruta crítica** (la cadena más larga) que define el mínimo de semestres?
- ¿Qué compañeros **cursan las mismas materias** que yo?

> Proyecto del Segundo Parcial — Bases de Datos Avanzadas, Universidad Anáhuac Mayab.
> Paradigma: **Red / Grafo**. Servicio: **Neo4j AuraDB Free** (DaaS). Lenguaje: **Python**.

---

## 🧱 Stack

| Capa | Tecnología |
|---|---|
| Base de datos | Neo4j AuraDB Free (nube, gestionada) |
| Lenguaje de consultas | Cypher |
| Driver | `neo4j` (driver oficial de Python, v5) |
| Interfaz | Streamlit |
| Credenciales | Variables de entorno con `python-dotenv` (`.env`) |

## 📁 Estructura

```
mapa-materias/
├── app.py                 # Interfaz Streamlit (pestañas: Materias, Alumnos, Consultas)
├── db/
│   ├── connection.py      # Crea el driver a partir de variables de entorno
│   ├── materias.py        # CRUD de materias y prerrequisitos
│   ├── alumnos.py         # CRUD de alumnos y materias aprobadas/cursando
│   └── consultas.py       # Consultas especializadas de grafo (traversals y caminos)
├── seed/
│   ├── schema.cypher      # Restricciones de unicidad (constraints)
│   ├── seed.cypher        # Datos iniciales: materias, prerrequisitos y alumnos
│   └── seed.py            # Ejecuta schema + seed contra AuraDB
├── docs/                  # PDF y diagramas
├── .env.example           # Plantilla de variables de entorno (sin secretos)
├── requirements.txt
└── README.md
```

## ✅ Requisitos

- Python 3.10 o superior
- Una cuenta gratuita en [Neo4j Aura](https://console.neo4j.io) con una instancia **AuraDB Free** creada
- Conexión a internet (la base **no** corre en localhost)

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone <URL-del-repo>
cd mapa-materias

# 2. Crear y activar un entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 🔐 Configurar credenciales

1. En la consola de Aura crea una instancia **AuraDB Free**. Al crearla se descarga un archivo `.txt` con las credenciales; **guárdalo**, la contraseña solo se muestra una vez.
2. Copia la plantilla y llénala con los datos de ese archivo:

```bash
cp .env.example .env
```

```dotenv
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=tu_contraseña
NEO4J_DATABASE=neo4j
```

> `.env` está en `.gitignore`: las credenciales **nunca** se suben al repositorio.

## 🌱 Poblar la base de datos (seeding)

```bash
python seed/seed.py
```

Crea las restricciones de unicidad, borra los datos anteriores y carga el plan de estudios de ejemplo con sus prerrequisitos y algunos alumnos con materias aprobadas. Se puede correr las veces que quieras (es idempotente).

## ▶️ Ejecutar la aplicación

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`. La **interfaz** corre local, pero **todos los datos se leen y escriben en AuraDB en la nube**: en la barra lateral se muestra el estado de conexión y la URI del servidor remoto.

## 🧪 Flujo de la demo (4 minutos)

1. Mostrar en la barra lateral que la app está conectada a `neo4j+s://...databases.neo4j.io`.
2. **Crear** una materia nueva y asignarle un prerrequisito.
3. **Leer**: buscarla en la tabla de materias.
4. **Actualizar** sus créditos o su nombre.
5. Elegir un alumno → **"¿Qué puedo cursar?"** → marcar una materia como aprobada → ver cómo aparecen materias nuevas desbloqueadas.
6. **Cadena de prerrequisitos** de *Proyecto Terminal* y **ruta crítica**.
7. **Eliminar** la materia creada en el paso 2.
8. Abrir Neo4j Browser / Explore en Aura y mostrar que los cambios persisten en la nube (y el grafo dibujado).

## 🗺️ Modelo de datos (resumen)

```
(:Alumno {matricula, nombre, carrera})
   ├─[:APROBO {calificacion, periodo}]──▶ (:Materia)
   └─[:CURSA {periodo}]───────────────▶ (:Materia)

(:Materia {clave, nombre, semestre, creditos, area})
   └─[:REQUIERE]──▶ (:Materia)      // "Estructuras de Datos REQUIERE Programación II"
```

El diseño completo y el catálogo de consultas Cypher están en `docs/`.

## 👤 Autor

Emilio — Bases de Datos Avanzadas, Universidad Anáhuac Mayab, 2026.
