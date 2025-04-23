from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.services.auth import AuthService
from app.api.dependencies.services import get_auth_service
from app.schemas.token import Token

router = APIRouter()

class LoginForm(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = await auth_service.authenticate_user(
        username=form_data.username, password=form_data.password
    )
    
    access_token = auth_service.create_access_token(subject=user.username)
    
    return {"access_token": access_token, "token_type": "bearer"} 