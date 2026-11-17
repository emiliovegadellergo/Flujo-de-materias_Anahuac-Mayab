"""Pobla AuraDB con las constraints y los datos de ejemplo.

Uso:  python seed/seed.py
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.connection import contar, get_driver, ejecutar  # noqa: E402

CARPETA = Path(__file__).resolve().parent


def sentencias(archivo):
    """Lee un archivo .cypher, quita comentarios y lo separa por ';'."""
    texto = "\n".join(
        linea for linea in (CARPETA / archivo).read_text(encoding="utf-8").splitlines()
        if not linea.strip().startswith("//")
    )
    return [s.strip() for s in texto.split(";") if s.strip()]


def poblar(driver):
    """Ejecuta schema.cypher y seed.cypher en orden."""
    for archivo in ("schema.cypher", "seed.cypher"):
        for sentencia in sentencias(archivo):
            ejecutar(driver, sentencia)
    return contar(driver)


if __name__ == "__main__":
    driver = get_driver()
    try:
        totales = poblar(driver)
        print(f"Seed listo: {totales['nodos']} nodos y {totales['relaciones']} relaciones en AuraDB.")
    finally:
        driver.close()
