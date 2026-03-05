"""Authentication utilities for PASSA."""
import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Request, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.models import Usuario

SECRET_KEY = os.environ.get("SECRET_KEY", "passa-secret-key-change-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
COOKIE_NAME = "access_token"


def hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def criar_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _extract_token(request: Request) -> Optional[str]:
    """Extract token from cookie (web) or Authorization header (mobile)."""
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def get_current_user(
    request: Request, db: Session = Depends(get_db)
) -> Usuario:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Token invalido")
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Token invalido")

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")
    return usuario


def get_admin_user(
    request: Request, db: Session = Depends(get_db)
) -> Usuario:
    usuario = get_current_user(request, db)
    if not usuario.is_admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return usuario


def get_optional_user(
    request: Request, db: Session = Depends(get_db)
) -> Optional[Usuario]:
    token = _extract_token(request)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        return None

    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario or not usuario.ativo:
        return None
    return usuario
