import os
import bcrypt
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# --- CONFIGURACIÓN DE CONEXIÓN A LA BASE DE DATOS ---
DB_HOST = os.getenv("DB_HOST", "localhost")

if DB_HOST.startswith("postgresql://") or DB_HOST.startswith("postgres://"):
    DATABASE_URL = DB_HOST
else:
    DATABASE_URL = f"postgresql://postgres:password_seguro@{DB_HOST}:5432/guarderia_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- CAPA DE SEGURIDAD: Cifrado en Reposo con Fernet (AES-128) ---
# En producción, FERNET_KEY debe venir de una variable de entorno secreta.
# Para uso académico, si no existe la variable, se genera una clave en memoria.
_fernet_key = os.getenv("FERNET_KEY")
if _fernet_key:
    FERNET_KEY = _fernet_key.encode()
else:
    FERNET_KEY = Fernet.generate_key()

fernet = Fernet(FERNET_KEY)

def cifrar_dato(texto: str) -> str:
    """Cifra un texto plano usando Fernet (AES-128 CBC + HMAC). Retorna string."""
    if not texto:
        return ""
    return fernet.encrypt(texto.encode()).decode()

def descifrar_dato(texto_cifrado: str) -> str:
    """Descifra un texto previamente cifrado con Fernet. Retorna el texto original."""
    if not texto_cifrado:
        return ""
    try:
        return fernet.decrypt(texto_cifrado.encode()).decode()
    except Exception:
        return "[Error al descifrar]"

# --- CAPA DE AUTENTICACIÓN: Usuario y contraseña con bcrypt ---
# Credenciales del administrador del sistema.
# El hash se genera con bcrypt.hashpw() y nunca se guarda la contraseña en texto plano.
USUARIO_ADMIN = "boris"
PASSWORD_HASH = bcrypt.hashpw(b"admin123", bcrypt.gensalt())

def verificar_credenciales(usuario: str, password: str) -> bool:
    """
    Verifica si el usuario y contraseña son válidos.
    Usa bcrypt.checkpw para comparar contra el hash almacenado.
    Retorna True si las credenciales son correctas.
    """
    if usuario != USUARIO_ADMIN:
        return False
    return bcrypt.checkpw(password.encode(), PASSWORD_HASH)

# --- CAPA DE DATOS: Modelos Relacionales (ORM con SQLAlchemy) ---

class Dueno(Base):
    __tablename__ = 'duenos'
    id_dueno          = Column(Integer, primary_key=True, index=True)
    nombre            = Column(String(100), nullable=False)
    correo_cifrado    = Column(String, nullable=False)
    telefono_cifrado  = Column(String, nullable=False)

    mascotas = relationship("Mascota", back_populates="dueno", cascade="all, delete-orphan")


class Mascota(Base):
    __tablename__ = 'mascotas'
    id_mascota     = Column(Integer, primary_key=True, index=True)
    id_dueno       = Column(Integer, ForeignKey('duenos.id_dueno', ondelete='CASCADE'))
    nombre_mascota = Column(String(100), nullable=False)
    especie        = Column(String(100), nullable=False)

    dueno    = relationship("Dueno", back_populates="mascotas")
    reservas = relationship("Reserva", back_populates="mascota", cascade="all, delete-orphan")


class Reserva(Base):
    __tablename__ = 'reservas'
    id_reserva       = Column(Integer, primary_key=True)
    id_mascota       = Column(Integer, ForeignKey('mascotas.id_mascota', ondelete='CASCADE'))
    fecha_ingreso    = Column(Date, nullable=False)
    dieta_restriccion = Column(String, nullable=False)

    mascota = relationship("Mascota", back_populates="reservas")


def inicializar_base_de_datos():
    """Crea todas las tablas en la base de datos si no existen."""
    Base.metadata.create_all(bind=engine)
