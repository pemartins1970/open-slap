import logging
import re
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, constr, validator

from ..auth import (
    create_user,
    authenticate_user,
    create_access_token,
    verify_token,
    get_current_user,
    create_password_reset,
    confirm_password_reset,
    auth_manager,
)
from ..db import get_user_auth_settings
from ..deps import security

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# --- Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email é obrigatório')
        return v.strip().lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            raise ValueError('Senha é obrigatória')
        if len(v.strip()) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v.strip()

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email é obrigatório')
        return v.strip().lower()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or not v.strip():
            raise ValueError('Senha é obrigatória')
        return v.strip()

class PasswordResetRequest(BaseModel):
    email: EmailStr
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email é obrigatório')
        return v.strip().lower()

class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str
    new_password: constr(min_length=8, max_length=128)
    
    @validator('email')
    def validate_email(cls, v):
        if not v or not v.strip():
            raise ValueError('Email é obrigatório')
        return v.strip().lower()
    
    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Código é obrigatório')
        return v.strip()
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not v or not v.strip():
            raise ValueError('Nova senha é obrigatória')
        if len(v.strip()) < 8:
            raise ValueError('Nova senha deve ter pelo menos 8 caracteres')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Nova senha deve conter pelo menos uma letra maiúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('Nova senha deve conter pelo menos uma letra minúscula')
        if not re.search(r'\d', v):
            raise ValueError('Nova senha deve conter pelo menos um número')
        return v.strip()

# --- Routes ---

@router.post("/register")
async def register(user: UserRegister):
    """Registra um novo usuário no sistema."""
    try:
        logger.info(f"Tentando criar usuário: {user.email}")
        created_user = create_user(user.email, user.password)
        logger.info(f"Usuário criado com sucesso: {created_user['id']}")
        return {
            "message": "Usuário criado com sucesso",
            "user": {"id": created_user["id"], "email": created_user["email"]},
        }
    except HTTPException as e:
        logger.warning(f"HTTPException no registro: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Erro inesperado no registro: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")

@router.post("/login")
async def login(user: UserLogin):
    """Autentica o usuário e retorna um token JWT."""
    authenticated_user = authenticate_user(user.email, user.password)

    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Buscar configurações de expiração customizadas
    expires_minutes = None
    try:
        stored = get_user_auth_settings(int(authenticated_user["id"])) or {}
        raw = stored.get("settings") if isinstance(stored.get("settings"), dict) else {}
        v = (raw or {}).get("jwt_expire_minutes", None)
        expires_minutes = int(v) if v is not None else None
    except Exception:
        expires_minutes = None

    token = create_access_token(
        data={"sub": str(authenticated_user["id"])},
        expires_minutes=expires_minutes,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": authenticated_user,
    }

@router.post("/password-reset/request")
async def password_reset_request(payload: PasswordResetRequest):
    """Gera um código de recuperação de senha."""
    code = create_password_reset(payload.email)
    response = {
        "message": "Se a conta existir, você receberá instruções para redefinir a senha."
    }
    if code:
        response["recovery_code"] = code
    return response

@router.post("/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirm):
    """Confirma a redefinição de senha usando o código enviado."""
    ok = confirm_password_reset(payload.email, payload.code, payload.new_password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível redefinir a senha",
        )
    return {"message": "Senha redefinida com sucesso"}

@router.get("/me")
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Retorna as informações do usuário autenticado atual."""
    user = get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return user
