from uuid import UUID

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import UserLoginRequest, UserRegisterRequest
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


class AuthService:
    @staticmethod
    def register_user(db: Session, req: UserRegisterRequest) -> tuple[User, str]:
        existing = db.scalar(select(User).where(User.email == req.email.lower()))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_ALREADY_EXISTS",
                    "detail": "User with this email already exists",
                },
            )

        user = User(
            name=req.name.strip(),
            email=req.email.lower().strip(),
            phone=req.phone.strip(),
            password_hash=hash_password(req.password),
            role=req.role,
            area=req.area.strip(),
            pincode=req.pincode.strip(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
        return user, token

    @staticmethod
    def authenticate_user(db: Session, req: UserLoginRequest) -> tuple[User, str]:
        user = db.scalar(select(User).where(User.email == req.email.lower().strip()))
        if not user or not verify_password(req.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_CREDENTIALS", "detail": "Invalid email or password"},
            )

        token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
        return user, token

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> User | None:
        return db.scalar(select(User).where(User.id == user_id))
