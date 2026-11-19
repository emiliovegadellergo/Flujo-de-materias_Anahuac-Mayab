"""Flujo de Materias · Anáhuac Mayab: interfaz Streamlit conectada a Neo4j AuraDB.

Ejecutar:  streamlit run app.py
"""
import html

import pandas as pd
import streamlit as st
from neo4j.exceptions import AuthError, ConstraintError, ServiceUnavailable

from db import alumnos, consultas, materias, usuarios
from db.connection import URI, contar, get_driver
from seed.seed import poblar

st.set_page_config(page_title="Flujo de Materias", page_icon="🎓", layout="wide")

COLORES = {"APROBO": "#2e9e57", "CURSA": "#ef9b20", "PRECARGA": "#2b6cb0", "PENDIENTE": "#d3d7de"}
ETIQUETAS = {"APROBO": "Aprobada", "CURSA": "Cursando", "PRECARGA": "Precargada", "PENDIENTE": "Pendiente"}
BLOQUES = ["BPO", "BAO", "BIO", "REM", "BIET", "BIEA", "BAE"]
CARRERA = "Ingeniería en Tecnologías de la Información y Negocios Digitales"


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


def resultado(titulo, query, filas, vacio="Sin resultados."):
    """Tabla con el resultado y, debajo, el Cypher que la produjo (para la defensa)."""
    st.markdown(f"**{titulo}**")
    tabla(filas, vacio)
    with st.expander("Ver Cypher"):
        st.code(query.strip(), language="cypher")


# ------------------------------------------------------------------ Conexión
try:
    driver = conexion()
except (ServiceUnavailable, AuthError, RuntimeError, ValueError) as error:
    st.error(f"No se pudo conectar a Neo4j AuraDB: {error}")
    st.stop()

# ------------------------------------------------------------------ Login
if "usuario" not in st.session_state:
    st.title("🎓 Flujo de Materias")
    st.caption(f"{CARRERA} · Universidad Anáhuac Mayab")
    with st.form("login"):
        usuario = st.text_input("Usuario", placeholder="ej. evega")
        password = st.text_input("Contraseña", type="password")
        if st.form_submit_button("Entrar"):
            datos = usuarios.autenticar(driver, usuario, password)
            if datos:
                st.session_state.usuario = datos
                st.rerun()
            st.error("Usuario o contraseña incorrectos.")
    st.stop()

yo = st.session_state.usuario

# ------------------------------------------------------------------ Barra lateral
with st.sidebar:
    st.markdown(f"### 👤 {yo['nombre']}")
    st.caption(f"Rol: {yo['rol']} · usuario: {yo['usuario']}")
    st.success("Conectado a AuraDB")
    st.caption(URI)
    totales = contar(driver)
    c1, c2 = st.columns(2)
    c1.metric("Nodos", totales["nodos"])
    c2.metric("Relaciones", totales["relaciones"])
    if yo["rol"] == "coordinador" and st.button("🔄 Recargar datos iniciales"):
        poblar(driver)
        st.rerun()
    if st.button("Cerrar sesión"):
        del st.session_state.usuario
        st.rerun()

lista_materias = materias.listar_materias(driver)
nombres = {m["clave"]: f'{m["clave"]} · {m["nombre"]}' for m in lista_materias}
obligatorias = [m["clave"] for m in lista_materias if m["tipo"] == "obligatoria"]


# ------------------------------------------------------------------ Vistas del alumno
def flujograma(matricula):
    """Dibuja el mapa curricular: una fila por semestre, cada materia con el color de su estado."""
    filas = alumnos.mapa(driver, matricula)
    leyenda = " ".join(
        f'<span style="background:{COLORES[e]};color:{"#222" if e == "PENDIENTE" else "#fff"};'
        f'padding:2px 8px;border-radius:4px;margin-right:6px">{ETIQUETAS[e]}</span>' for e in COLORES)
    st.markdown(leyenda, unsafe_allow_html=True)
    for semestre in sorted({f["semestre"] for f in filas}):
        cajas = ""
        for f in (x for x in filas if x["semestre"] == semestre):
            texto = "#222" if f["estado"] == "PENDIENTE" else "#fff"
            cajas += (f'<div style="background:{COLORES[f["estado"]]};color:{texto};width:150px;'
                      f'min-height:70px;padding:6px;border-radius:6px;font-size:11px;">'
                      f'<b>{html.escape(f["nombre"])}</b><br>{f["clave"]} · {f["creditos"]} cr</div>')
        st.markdown(f'<div style="display:flex;gap:6px;align-items:center;margin-bottom:6px">'
                    f'<div style="width:28px;font-weight:bold">{semestre}</div>{cajas}</div>',
                    unsafe_allow_html=True)

    st.markdown("**Electivas**")
    tabla(alumnos.electivas(driver, matricula), "Sin electivas registradas.")
    creditos = alumnos.creditos_electivos(driver, matricula)
    for bloque, (llevo, requeridos) in creditos.items():
        nombre = "Anáhuac Electivo (BAE)" if bloque == "BAE" else "Interdisciplinario Electivo (BIEA + BIET)"
        st.progress(min(llevo / requeridos, 1.0), text=f"{nombre}: {llevo}/{requeridos} créditos")
    with st.expander("Ver Cypher"):
        st.code(alumnos.QUERY_MAPA.strip(), language="cypher")


def grafo_cadena(matricula, clave):
    """Dibuja con Graphviz la cadena de prerrequisitos, coloreada según el estado del alumno."""
    aristas = consultas.cadena_aristas(driver, clave)
    if not aristas:
        st.info("Esta materia no tiene prerrequisitos.")
        return
    estado = {f["clave"]: f["estado"] for f in alumnos.mapa(driver, matricula)}
    nodos = {a["desde"] for a in aristas} | {a["hacia"] for a in aristas}
    dot = ["digraph { rankdir=BT; node [shape=box style=\"rounded,filled\" fontname=Helvetica fontsize=10];"]
    for n in nodos:
        e = estado.get(n, "PENDIENTE")
        etiqueta = nombres.get(n, n).replace('"', "'")
        dot.append(f'"{n}" [label="{etiqueta}" fillcolor="{COLORES[e]}" '
                   f'fontcolor="{"black" if e == "PENDIENTE" else "white"}"];')
    for a in aristas:
        dot.append(f'"{a["hacia"]}" -> "{a["desde"]}";')
    dot.append("}")
    st.graphviz_chart("\n".join(dot))


def vista_alumno(matricula):
    """Pestañas que ve un alumno (y el coordinador al revisar a un alumno)."""
    t1, t2, t3, t4 = st.tabs(["🗺️ Flujograma", "📝 ¿Qué puedo cargar?", "👥 Amigos", "🔎 Explorar materia"])
    with t1:
        flujograma(matricula)
    with t2:
        resultado("Q1 · Materias que puedes cargar el próximo semestre", consultas.QUERY_PUEDO_CARGAR,
                  consultas.puedo_cargar(driver, matricula))
    with t3:
        resultado("Q8 · Tus precargas y quién más las precargó", consultas.QUERY_PRECARGAS_CON_AMIGOS,
                  consultas.precargas_con_amigos(driver, matricula), "No tienes materias precargadas.")
        opciones = [f["clave"] for f in consultas.puedo_cargar(driver, matricula)]
        opciones += [f["clave"] for f in alumnos.mapa(driver, matricula) if f["estado"] == "PRECARGA"]
        if opciones:
            clave = st.selectbox("¿Con quién puedo llevar…?", sorted(set(opciones)),
                                 format_func=nombres.get, key=f"amigos_{matricula}")
            resultado("Q7 · Compañeros que pueden llevarla contigo", consultas.QUERY_AMIGOS_MATERIA,
                      consultas.amigos_para_materia(driver, matricula, clave))
        resultado("Q9 · Compañeros con más materias en común", consultas.QUERY_COMPANEROS,
                  consultas.companeros(driver, matricula))
    with t4:
        clave = st.selectbox("Materia", obligatorias, index=len(obligatorias) - 1,
                             format_func=nombres.get, key=f"explorar_{matricula}")
        grafo_cadena(matricula, clave)
        c1, c2 = st.columns(2)
        with c1:
            resultado("Q3 · Lo que te falta aprobar para llegar", consultas.QUERY_FALTANTES,
                      consultas.faltantes(driver, matricula, clave), "¡Ya cumples todos los prerrequisitos!")
            resultado("Q5 · Ruta crítica (cadena más larga)", consultas.QUERY_RUTA_CRITICA,
                      consultas.ruta_critica(driver, clave))
        with c2:
            resultado("Q4 · Materias que desbloquea", consultas.QUERY_DESBLOQUEA,
                      consultas.desbloquea(driver, clave), "No desbloquea otras materias.")
            resultado("Q2 · Cadena completa de prerrequisitos", consultas.QUERY_CADENA,
                      consultas.cadena_prerrequisitos(driver, clave), "Sin prerrequisitos.")
        with st.expander("Q6 · Camino más corto entre dos materias"):
            destino = st.selectbox("Hasta", obligatorias, format_func=nombres.get, key=f"destino_{matricula}")
            if destino != clave:
                resultado("Camino", consultas.QUERY_CAMINO_CORTO, consultas.camino_corto(driver, clave, destino),
                          "No hay camino entre esas materias.")


# ------------------------------------------------------------------ Vistas del coordinador
def crud_materias():
    tabla(lista_materias)
    col1, col2 = st.columns(2)
    with col1, st.form("crear_materia", clear_on_submit=True):
        st.subheader("Crear materia")
        clave = st.text_input("Clave (ej. SIS5001)").strip().upper()
        nombre = st.text_input("Nombre")
        tipo = st.selectbox("Tipo", ["obligatoria", "electiva"])
        semestre = st.number_input("Semestre (solo obligatorias)", 1, 9, 1)
        creditos = st.number_input("Créditos", 0.0, 20.0, 6.0, 0.5)
        bloque = st.selectbox("Bloque", BLOQUES)
        if st.form_submit_button("Crear") and clave and nombre:
            try:
                materias.crear_materia(driver, clave, nombre, int(semestre) if tipo == "obligatoria" else None,
                                       float(creditos), bloque, tipo)
                st.rerun()
            except ConstraintError:
                st.error(f"Ya existe una materia con la clave {clave}.")
    with col2:
        st.subheader("Editar / eliminar")
        sel = st.selectbox("Materia", list(nombres), format_func=nombres.get, key="editar_materia")
        actual = materias.obtener_materia(driver, sel)
        with st.form("editar_materia_form"):
            nuevo_nombre = st.text_input("Nombre", actual["nombre"])
            nuevo_sem = st.number_input("Semestre", 1, 9, int(actual["semestre"] or 1))
            nuevos_cred = st.number_input("Créditos", 0.0, 20.0, float(actual["creditos"] or 0), 0.5)
            nuevo_bloque = st.selectbox("Bloque", BLOQUES, index=BLOQUES.index(actual["bloque"]) if actual["bloque"] in BLOQUES else 0)
            guardar, borrar = st.columns(2)
            if guardar.form_submit_button("Guardar cambios"):
                materias.actualizar_materia(driver, sel, nuevo_nombre,
                                            int(nuevo_sem) if actual["tipo"] == "obligatoria" else None,
                                            float(nuevos_cred), nuevo_bloque)
                st.rerun()
            if borrar.form_submit_button("🗑️ Eliminar"):
                materias.eliminar_materia(driver, sel)
                st.rerun()
    st.subheader("Prerrequisitos (seriación)")
    c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
    mat = c1.selectbox("Materia", obligatorias, format_func=nombres.get, key="req_materia")
    req = c2.selectbox("Requiere", obligatorias, format_func=nombres.get, key="req_requisito")
    if c3.button("➕ Agregar"):
        if materias.agregar_requisito(driver, mat, req):
            st.rerun()
        st.error("No se puede: es la misma materia o crearía un ciclo de prerrequisitos.")
    if c4.button("➖ Quitar"):
        materias.quitar_requisito(driver, mat, req)
        st.rerun()


def crud_alumnos(lista):
    tabla(lista)
    col1, col2 = st.columns(2)
    with col1, st.form("crear_alumno", clear_on_submit=True):
        st.subheader("Crear alumno")
        matricula = st.text_input("Matrícula (ej. A006)").strip().upper()
        nombre = st.text_input("Nombre completo")
        usuario = st.text_input("Usuario (inicial + apellido)").strip().lower()
        password = st.text_input("Contraseña inicial", type="password")
        if st.form_submit_button("Crear") and matricula and nombre and usuario and password:
            try:
                alumnos.crear_alumno(driver, matricula, nombre, CARRERA, usuario, password)
                st.rerun()
            except ConstraintError:
                st.error("Esa matrícula o ese usuario ya existen.")
    with col2:
        if lista:
            st.subheader("Editar / eliminar")
            sel = st.selectbox("Alumno", [a["matricula"] for a in lista],
                               format_func=lambda m: next(a["nombre"] for a in lista if a["matricula"] == m),
                               key="editar_alumno")
            actual = next(a for a in lista if a["matricula"] == sel)
            with st.form("editar_alumno_form"):
                nuevo_nombre = st.text_input("Nombre", actual["nombre"])
                guardar, borrar = st.columns(2)
                if guardar.form_submit_button("Guardar cambios"):
                    alumnos.actualizar_alumno(driver, sel, nuevo_nombre, actual["carrera"])
                    st.rerun()
                if borrar.form_submit_button("🗑️ Eliminar"):
                    alumnos.eliminar_alumno(driver, sel)
                    st.rerun()
    if lista:
        st.subheader("Cambiar estado de una materia")
        c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
        al = c1.selectbox("Alumno", [a["matricula"] for a in lista],
                          format_func=lambda m: next(a["nombre"] for a in lista if a["matricula"] == m),
                          key="estado_alumno")
        mat = c2.selectbox("Materia", list(nombres), format_func=nombres.get, key="estado_materia")
        estado = c3.selectbox("Nuevo estado", list(ETIQUETAS), format_func=ETIQUETAS.get)
        if c4.button("Aplicar"):
            alumnos.cambiar_estado(driver, al, mat, estado)
            st.rerun()


def vista_coordinador():
    lista = alumnos.listar_alumnos(driver)
    t1, t2, t3, t4 = st.tabs(["📊 Planeación", "👤 Ver alumno", "📚 Materias", "👥 Alumnos"])
    with t1:
        resultado("Q10 · Demanda estimada del próximo semestre", consultas.QUERY_DEMANDA, consultas.demanda(driver))
        resultado("Q11 · Alumnos rezagados", consultas.QUERY_REZAGADOS, consultas.rezagados(driver),
                  "Ningún alumno tiene materias atrasadas.")
        clave = st.selectbox("Si NO abro esta materia…", obligatorias, format_func=nombres.get, key="impacto")
        resultado("Q12 · Impacto de no abrirla", consultas.QUERY_IMPACTO, consultas.impacto(driver, clave))
        resultado("Q13 · Materias cuello de botella", consultas.QUERY_CUELLOS, consultas.cuellos_de_botella(driver))
    with t2:
        if lista:
            sel = st.selectbox("Alumno", [a["matricula"] for a in lista],
                               format_func=lambda m: next(a["nombre"] for a in lista if a["matricula"] == m),
                               key="ver_alumno")
            vista_alumno(sel)
    with t3:
        crud_materias()
    with t4:
        crud_alumnos(lista)


# ------------------------------------------------------------------ Página
st.title("🎓 Flujo de Materias")
st.caption(f"{CARRERA} · Plan de estudios como grafo en Neo4j AuraDB")
if yo["rol"] == "coordinador":
    vista_coordinador()
else:
    vista_alumno(yo["matricula"])
