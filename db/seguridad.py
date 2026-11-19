"""Hash de contraseñas con PBKDF2-SHA256 (biblioteca estándar, sin dependencias)."""
import hashlib
import hmac
import os

ITERACIONES = 200_000


def hashear(password):
    """Regresa 'sal$hash' en hexadecimal. La contraseña nunca se guarda en texto plano."""
    sal = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), sal, ITERACIONES)
    return f"{sal.hex()}${digest.hex()}"


def verificar(password, guardado):
    """Compara la contraseña escrita contra el hash guardado en Neo4j."""
    if not guardado or "$" not in guardado:
        return False
    sal_hex, digest_hex = guardado.split("$", 1)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal_hex), ITERACIONES)
    return hmac.compare_digest(digest.hex(), digest_hex)
