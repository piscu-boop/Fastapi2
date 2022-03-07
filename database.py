from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# La ultima parte es ./ porque el archivo todos.db se ubicara en el mismo directorio del archivo
SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread":False}
)
# Esto es para evitar compartir accidentalmente la misma conexión para diferentes 
# cosas (para diferentes solicitudes). Pero en FastAPI, usando funciones ordinarias 
# (def), puede usar múltiples hilos para interactuar con la base de datos para la misma 
# solicitud, por lo que debemos informar a SQLite que debe permitir el uso 
# de connect_args = {"check_same_thread ": Falso}.
# Además, nos aseguraremos de que cada solicitud obtenga su propia sesión de conexión de 
# base de datos con una dependencia, por lo que este mecanismo predeterminado no es necesario.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()