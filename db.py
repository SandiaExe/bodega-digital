import os
import base64
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Configuración de conexión dinámica para Docker
# Si corre dentro de Docker usará 'postgres_db', si lo pruebas suelto usará 'localhost'
DB_HOST = os.getenv("DB_HOST", "localhost")

if DB_HOST.startswith("postgresql://") or DB_HOST.startswith("postgres://"):
    DATABASE_URL = DB_HOST
else:
    DATABASE_URL = f"postgresql://postgres:password_seguro@{DB_HOST}:5432/guarderia_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- CAPA DE SEGURIDAD: Cifrado en Reposo (Datos de Contacto) ---
SECRET_KEY = 42  # Llave simétrica para la máscara XOR académica

def cifrar_dato(texto):
    if not texto: return ""
    cifrado = "".join(chr(ord(c) ^ SECRET_KEY) for c in texto)
    return base64.b64encode(cifrado.encode()).decode()

def descifrar_dato(texto_cifrado):
    if not texto_cifrado: return ""
    try:
        decoded = base64.b64decode(texto_cifrado.encode()).decode()
        return "".join(chr(ord(c) ^ SECRET_KEY) for c in decoded)
    except:
        return "[Error al descifrar]"

# --- CAPA DE DATOS: Modelos Relacionales (ORMs) ---
class Dueno(Base):
    __tablename__ = 'duenos'
    id_dueno = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    correo_cifrado = Column(String, nullable=False)
    telefono_cifrado = Column(String, nullable=False)
    
    mascotas = relationship("Mascota", back_populates="dueno", cascade="all, delete-orphan")

class Mascota(Base):
    __tablename__ = 'mascotas'
    id_mascota = Column(Integer, primary_key=True, index=True)
    id_dueno = Column(Integer, ForeignKey('duenos.id_dueno', ondelete='CASCADE'))
    nombre_mascota = Column(String(100), nullable=False)
    especie = Column(String(100), nullable=False)
    
    dueno = relationship("Dueno", back_populates="mascotas")
    reservas = relationship("Reserva", back_populates="mascota", cascade="all, delete-orphan")

class Reserva(Base):
    __tablename__ = 'reservas'
    id_reserva = Column(Integer, primary_key=True)  # ID Manual de la UI
    id_mascota = Column(Integer, ForeignKey('mascotas.id_mascota', ondelete='CASCADE'))
    fecha_ingreso = Column(Date, nullable=False)
    dieta_restriccion = Column(String, nullable=False)
    
    mascota = relationship("Mascota", back_populates="reservas")

def inicializar_base_de_datos():
    Base.metadata.create_all(bind=engine)
