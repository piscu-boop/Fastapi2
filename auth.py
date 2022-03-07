from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError

# la secret key puede ser cualquier cosa, es el Signature que va con el JWT token
SECRET_KEY = "qaz1wsx3edc4rfv6tgb"
ALGORITHM = "HS256"
# HS256 ( HMAC con SHA-256), por otro lado, implica una combinación de una función hash 
# y una clave (secreta) que se comparte entre las dos partes que se utilizan para generar
#  el hash que servirá como firma. Dado que se utiliza la misma clave tanto para generar 
# la firma como para validarla, se debe tener cuidado para garantizar que la clave no se vea comprometida.


class Create_User(BaseModel):
    username: str
    email: Optional[str]
    firstname: str
    lastname: str
    password: str

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# La siguiente linea creara la base de datos y la tabla con todo lo necesario en caso
# de por alguna razon se ejecute auth.py antes que main.py

models.Base.metadata.create_all(bind=engine)

# Con el BEARER que significa portador nosotros accedemos a la api de OAuth2,
# Es una cadenaque actua como la autenticacion de la solicitud API, enviada en un header de "Autorizacion" HTTP.
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_password_hash(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)
    # El .verify sirve para que el bcrypt context verifique si 
    # la plain password y la hashed password son las mismas

def authenticate_user(username: str, password: str, db):
    # En la siguiente instruccion buscamos a ver si existe algun 
    # registro que coincida con el usuario a buscar
    user = db.query(models.Users).filter(models.Users.username == username).first()
    # user = db.query(models.Users).filter(models.Users.user_name == username).first()

    # Le decimos que si no existe ningun usuario, devuelva falso.
    if not user:
        return False
    # En la siguiente instruccion le decimos que si no esta verificada la 
    # contraseña, que devuelva Falso para indicar que el usuario no es autentificado
    if not verify_password(password, user.hashed_password):
        return False
    return user
    

def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id}
    # Si el delta ya esta expirado, le decimos que expire sera igual a 
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
        # DatetimeUTCNow envia la fecha y hora de la zona horaria
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    # En el return estamos encriptando al header y al signature  

async def get_current_user(token: str = Depends(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Con decirle el .decode estamos diciendole que payload sera el token, la secret key y el alg decodificado
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        # con el payload.get estamos buscando en SUB que habiamos definido antes, que era el username del cliente
        # lo mismo con el ID...
        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail="Not Found")
        # SI existen quiero devolver un diccionario que indique el user id y el username
        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=404, detail="User Not Found")

@app.post("/create/user")
async def create_new_user(create_user: Create_User, db: Session = Depends(get_db)):
    create_user_models = models.Users()
    create_user_models.email = create_user.email
    create_user_models.username = create_user.username
    create_user_models.first_name = create_user.firstname
    create_user_models.last_name = create_user.lastname
    hash_password = get_password_hash(create_user.password)
    create_user_models.hashed_password = hash_password
    create_user_models.is_active = True

    db.add(create_user_models)
    db.commit()

@app.post("/token")
async def login_for_acces_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session= Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token_expires = timedelta(minutes=20)
    # Todos los token deben tener si o si ua fecha de expiracion 
    token = create_access_token(user.username, user.id, expires_delta=token_expires)
    return {"token": token} # Nos devuelve un token que podemos desencriptar en JWT.io

    # OAuth2PasswordRequestFormtiene atributos de uso común como 'nombre de usuario', 'contraseña' y 'alcance'.
    # Después de verificar en la base de datos que el usuario existe, se crea un token de acceso para el usuario. 
    # El token de acceso consta de datos que describen al usuario, sus límites de tiempo de acceso y los permisos 
    # de alcance que se le asignan y que se codifica en un objeto compacto de tipo cadena, que es el token.