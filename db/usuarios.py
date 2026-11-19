"""Inicio de sesión: busca al usuario (alumno o coordinador) y valida su contraseña."""
from db.connection import ejecutar
from db.seguridad import verificar

# U1 Buscar usuario por nombre de usuario (en cualquiera de los dos roles)
QUERY_BUSCAR_USUARIO = """
MATCH (u)
WHERE (u:Alumno OR u:Coordinador) AND u.usuario = $usuario
RETURN u.usuario AS usuario, u.nombre AS nombre, u.matricula AS matricula,
       u.password_hash AS password_hash,
       CASE WHEN u:Coordinador THEN 'coordinador' ELSE 'alumno' END AS rol
"""


def autenticar(driver, usuario, password):
    """Regresa los datos del usuario si la contraseña es correcta; si no, None."""
    filas = ejecutar(driver, QUERY_BUSCAR_USUARIO, usuario=usuario.strip().lower())
    if not filas or not verificar(password, filas[0]["password_hash"]):
        return None
    datos = filas[0]
    datos.pop("password_hash")
    return datos
