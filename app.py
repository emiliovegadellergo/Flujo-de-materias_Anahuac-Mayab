"""Mapa de Materias: interfaz Streamlit conectada a Neo4j AuraDB.

Ejecutar:  streamlit run app.py
"""
import pandas as pd
import streamlit as st
from neo4j.exceptions import AuthError, ConstraintError, ServiceUnavailable

from db import alumnos, consultas, materias
from db.connection import URI, contar, get_driver
from seed.seed import poblar

st.set_page_config(page_title="Mapa de Materias", page_icon="🎓", layout="wide")
AREAS = ["Matemáticas", "Programación", "Bases de Datos", "Redes", "Gestión", "Formación"]
PERIODO_ACTUAL = "2026-O"


@st.cache_resource
def conexion():
    """Un solo driver para toda la app (pool de conexiones)."""
    return get_driver()


def tabla(filas, vacio="Sin resultados."):
    """Muestra una lista de diccionarios como tabla."""
    if filas:
        st.dataframe(pd.DataFrame(filas), hide_index=True)
    else:
        st.info(vacio)


try:
    driver = conexion()
except (ServiceUnavailable, AuthError, RuntimeError, ValueError) as error:
    st.error(f"No se pudo conectar a Neo4j AuraDB: {error}")
    st.stop()

# ---------- Barra lateral ----------
with st.sidebar:
    st.success("Conectado a AuraDB")
    st.caption(URI)
    totales = contar(driver)
    st.metric("Nodos", totales["nodos"])
    st.metric("Relaciones", totales["relaciones"])
    if st.button("🔄 Recargar datos de ejemplo"):
        poblar(driver)
        st.rerun()

st.title("🎓 Mapa de Materias")
st.caption("Plan de estudios como grafo en Neo4j AuraDB")

lista_materias = materias.listar_materias(driver)
lista_alumnos = alumnos.listar_alumnos(driver)
claves = [m["clave"] for m in lista_materias]
nombres = {m["clave"]: f'{m["clave"]} · {m["nombre"]}' for m in lista_materias}
matriculas = [a["matricula"] for a in lista_alumnos]
nombres_alumnos = {a["matricula"]: f'{a["matricula"]} · {a["nombre"]}' for a in lista_alumnos}

tab_materias, tab_alumnos, tab_consultas = st.tabs(["📚 Materias", "👥 Alumnos", "🕸️ Consultas de grafo"])

# ---------- Materias ----------
with tab_materias:
    tabla(lista_materias, "No hay materias. Usa 'Recargar datos de ejemplo'.")
    col1, col2 = st.columns(2)

    with col1, st.form("crear_materia", clear_on_submit=True):
        st.subheader("Crear materia")
        clave = st.text_input("Clave (ej. BD501)").strip().upper()
        nombre = st.text_input("Nombre")
        semestre = st.number_input("Semestre", 1, 10, 1)
        creditos = st.number_input("Créditos", 1, 20, 8)
        area = st.selectbox("Área", AREAS)
        if st.form_submit_button("Crear") and clave and nombre:
            try:
                materias.crear_materia(driver, clave, nombre, int(semestre), int(creditos), area)
                st.rerun()
            except ConstraintError:
                st.error(f"Ya existe una materia con la clave {clave}.")

    with col2:
        st.subheader("Editar / eliminar")
        if claves:
            sel = st.selectbox("Materia", claves, format_func=nombres.get, key="editar_materia")
            actual = materias.obtener_materia(driver, sel)
            with st.form("editar_materia_form"):
                nuevo_nombre = st.text_input("Nombre", actual["nombre"])
                nuevo_sem = st.number_input("Semestre", 1, 10, int(actual["semestre"]))
                nuevos_cred = st.number_input("Créditos", 1, 20, int(actual["creditos"]))
                nueva_area = st.selectbox("Área", AREAS, index=AREAS.index(actual["area"]) if actual["area"] in AREAS else 0)
                guardar, borrar = st.columns(2)
                if guardar.form_submit_button("Guardar cambios"):
                    materias.actualizar_materia(driver, sel, nuevo_nombre, int(nuevo_sem), int(nuevos_cred), nueva_area)
                    st.rerun()
                if borrar.form_submit_button("🗑️ Eliminar"):
                    materias.eliminar_materia(driver, sel)
                    st.rerun()

    st.subheader("Prerrequisitos")
    if claves:
        c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
        mat = c1.selectbox("Materia", claves, format_func=nombres.get, key="req_materia")
        req = c2.selectbox("Requiere", claves, format_func=nombres.get, key="req_requisito")
        if c3.button("➕ Agregar"):
            if materias.agregar_requisito(driver, mat, req):
                st.rerun()
            else:
                st.error("No se puede: es la misma materia o crearía un ciclo de prerrequisitos.")
        if c4.button("➖ Quitar"):
            materias.quitar_requisito(driver, mat, req)
            st.rerun()

# ---------- Alumnos ----------
with tab_alumnos:
    tabla(lista_alumnos, "No hay alumnos.")
    col1, col2 = st.columns(2)

    with col1, st.form("crear_alumno", clear_on_submit=True):
        st.subheader("Crear alumno")
        matricula = st.text_input("Matrícula (ej. A005)").strip().upper()
        nombre = st.text_input("Nombre completo")
        carrera = st.text_input("Carrera", "Ingeniería en TI")
        if st.form_submit_button("Crear") and matricula and nombre:
            try:
                alumnos.crear_alumno(driver, matricula, nombre, carrera)
                st.rerun()
            except ConstraintError:
                st.error(f"Ya existe un alumno con la matrícula {matricula}.")

    with col2:
        st.subheader("Editar / eliminar")
        if matriculas:
            sel = st.selectbox("Alumno", matriculas, format_func=nombres_alumnos.get, key="editar_alumno")
            actual = next(a for a in lista_alumnos if a["matricula"] == sel)
            with st.form("editar_alumno_form"):
                nuevo_nombre = st.text_input("Nombre", actual["nombre"])
                nueva_carrera = st.text_input("Carrera", actual["carrera"])
                guardar, borrar = st.columns(2)
                if guardar.form_submit_button("Guardar cambios"):
                    alumnos.actualizar_alumno(driver, sel, nuevo_nombre, nueva_carrera)
                    st.rerun()
                if borrar.form_submit_button("🗑️ Eliminar"):
                    alumnos.eliminar_alumno(driver, sel)
                    st.rerun()

    if matriculas and claves:
        st.subheader("Historial: inscribir y aprobar")
        alumno = st.selectbox("Alumno", matriculas, format_func=nombres_alumnos.get, key="hist_alumno")
        tabla(alumnos.historial(driver, alumno), "Sin materias registradas.")
        c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
        mat = c1.selectbox("Materia", claves, format_func=nombres.get, key="hist_materia")
        calificacion = c2.number_input("Calificación", 6.0, 10.0, 9.0, 0.1)
        if c3.button("Inscribir"):
            alumnos.inscribir(driver, alumno, mat, PERIODO_ACTUAL)
            st.rerun()
        if c4.button("✅ Aprobar"):
            alumnos.aprobar(driver, alumno, mat, float(calificacion), PERIODO_ACTUAL)
            st.rerun()

# ---------- Consultas de grafo ----------
with tab_consultas:
    if not (matriculas and claves):
        st.info("Carga los datos de ejemplo para usar las consultas.")
        st.stop()

    c1, c2 = st.columns(2)
    alumno = c1.selectbox("Alumno", matriculas, format_func=nombres_alumnos.get, key="q_alumno")
    materia = c2.selectbox("Materia", claves, index=len(claves) - 1, format_func=nombres.get, key="q_materia")

    opciones = {
        "Q1 · ¿Qué puedo cursar?": (consultas.QUERY_DISPONIBLES, lambda: consultas.materias_disponibles(driver, alumno)),
        "Q2 · Cadena completa de prerrequisitos": (consultas.QUERY_CADENA, lambda: consultas.cadena_prerrequisitos(driver, materia)),
        "Q3 · ¿Qué me falta para llegar a la materia?": (consultas.QUERY_FALTANTES, lambda: consultas.faltantes(driver, alumno, materia)),
        "Q4 · ¿Qué materias desbloquea?": (consultas.QUERY_DESBLOQUEA, lambda: consultas.desbloquea(driver, materia)),
        "Q5 · Ruta crítica (semestres mínimos)": (consultas.QUERY_RUTA_CRITICA, lambda: consultas.ruta_critica(driver, materia)),
        "Q6 · Camino más corto entre dos materias": (consultas.QUERY_CAMINO_CORTO, None),
        "Q7 · Compañeros con materias en común": (consultas.QUERY_COMPANEROS, lambda: consultas.companeros(driver, alumno)),
        "Q8 · Materias cuello de botella": (consultas.QUERY_CUELLOS, lambda: consultas.cuellos_de_botella(driver)),
    }
    eleccion = st.radio("Consulta", list(opciones), horizontal=False)
    query, funcion = opciones[eleccion]

    if funcion is None:
        destino = st.selectbox("Materia destino", claves, format_func=nombres.get, key="q_destino")
        if destino == materia:
            st.warning("Elige una materia destino distinta a la de origen.")
            st.stop()
        funcion = lambda: consultas.camino_corto(driver, materia, destino)  # noqa: E731

    resultado, codigo = st.columns([3, 2])
    with resultado:
        st.subheader("Resultado")
        tabla(funcion())
    with codigo:
        st.subheader("Cypher ejecutado")
        st.code(query.strip(), language="cypher")
