# 🎓 Flujo de Materias — Ingeniería en TI y Negocios Digitales (Anáhuac Mayab)

Aplicación que modela el **plan de estudios real** de la carrera como un **grafo** en **Neo4j AuraDB** (nube). Cada materia es un nodo, cada seriación es una relación `REQUIERE` y el avance de cada alumno se guarda como relaciones `APROBO`, `CURSA` y `PRECARGA`.

Tiene dos tipos de usuario:

- **Alumno:** ve su flujograma a colores, qué materias puede cargar el próximo semestre y **con qué amigos puede llevar cada materia**. También explora la cadena de prerrequisitos de cualquier materia, dibujada como grafo.
- **Coordinador:** ve la **demanda** de cada materia para el próximo semestre, los **alumnos rezagados**, el **impacto de no abrir una materia** y las materias "cuello de botella". Además administra materias, seriaciones, alumnos y estados (CRUD).

> Proyecto del Segundo Parcial — Bases de Datos Avanzadas, Universidad Anáhuac Mayab.
> Paradigma: **Red / Grafo** · Servicio: **Neo4j AuraDB Free** (DaaS) · Lenguaje: **Python**.

## 🧱 Stack

| Capa | Tecnología |
|---|---|
| Base de datos | Neo4j AuraDB Free (nube, gestionada) |
| Consultas | Cypher |
| Driver | `neo4j` (driver oficial de Python) |
| Interfaz | Streamlit (incluye grafos con Graphviz) |
| Credenciales | Variables de entorno (`.env` con `python-dotenv`) |
| Contraseñas | Hash PBKDF2-SHA256 con sal (biblioteca estándar) |

## 📁 Estructura

```
├── app.py                  # Interfaz: login, vista alumno y vista coordinador
├── db/
│   ├── connection.py       # Driver de Neo4j a partir de variables de entorno
│   ├── seguridad.py        # Hash y verificación de contraseñas
│   ├── usuarios.py         # Inicio de sesión (alumno / coordinador)
│   ├── materias.py         # CRUD de materias y seriaciones (C1–C7)
│   ├── alumnos.py          # CRUD de alumnos y estados de materias (C8–C13)
│   └── consultas.py        # Consultas de grafo (Q1–Q13)
├── data/
│   ├── plan_curricular.json  # 58 materias, 35 seriaciones, catálogo de electivas
│   └── alumnos.json          # 5 alumnos reales con su avance
├── seed/
│   ├── schema.cypher       # Constraints de unicidad
│   └── seed.py             # Carga data/*.json en AuraDB
├── docs/                   # PDF y diagramas
├── .env.example
└── requirements.txt
```

## ✅ Requisitos

- Python 3.10 o superior
- Instancia **AuraDB Free** creada en [console.neo4j.io](https://console.neo4j.io)

## ⚙️ Instalación y ejecución

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # y llénalo con el .txt que descarga Aura
python seed/seed.py                # carga plan, alumnos y usuarios en la nube
streamlit run app.py
```

> La interfaz corre en tu equipo, pero **todos los datos se leen y escriben en AuraDB en la nube**.

## 🔑 Usuarios de demo

Todos usan la contraseña definida en `SEED_PASSWORD` (por defecto `anahuac2026`).

| Usuario | Rol |
|---|---|
| `coordinador` | Coordinador |
| `evega`, `avieto`, `rvargas`, `ylanda`, `jzapata` | Alumnos |

## 🗺️ Modelo de datos

```
(:Alumno {matricula, nombre, usuario, password_hash})
   ├─[:APROBO]────▶ (:Materia)
   ├─[:CURSA]─────▶ (:Materia)
   └─[:PRECARGA]──▶ (:Materia)

(:Materia {clave, nombre, semestre, creditos, bloque, tipo})
   └─[:REQUIERE]──▶ (:Materia)        // seriación: hay que aprobar la de destino

(:Coordinador {usuario, nombre, password_hash})
```

## 🧪 Guion de la demo (4 min)

1. Entrar como `evega`: flujograma, "¿Qué puedo cargar?" y "¿Con quién puedo llevar…?".
2. "Explorar materia": grafo de la cadena hasta *Inteligencia de Negocios*.
3. Cerrar sesión y entrar como `coordinador`: demanda, rezagados e impacto de no abrir una materia.
4. CRUD: crear una materia, agregarle una seriación, aprobarle una materia a un alumno, y ver cómo cambia la demanda. Al final, eliminar la materia creada.
5. Abrir Neo4j Browser en Aura y mostrar que los cambios persisten en la nube.
