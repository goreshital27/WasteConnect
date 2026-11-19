from typing import Annotated, Any

from app.core.database import get_db
from app.core.permissions.auth import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

router = APIRouter(tags=["Auth"])


@router.post(
    "/auth/register",
    status_code=status.HTTP_201_CREATED,
    response_model=dict[str, Any],
)
def register(
    req: UserRegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user, token = AuthService.register_user(db, req)
    return {
        "code": "SUCCESS",
        "data": TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        ).model_dump(mode="json"),
    }


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def login(
    req: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, Any]:
    user, token = AuthService.authenticate_user(db, req)
    return {
        "code": "SUCCESS",
        "data": TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        ).model_dump(mode="json"),
    }


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    return {
        "code": "SUCCESS",
        "data": UserResponse.model_validate(current_user).model_dump(mode="json"),
    }
