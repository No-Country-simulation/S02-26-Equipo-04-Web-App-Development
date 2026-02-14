from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils.exceptions import UserAlreadyExistsException, UserNotFoundException


class UserService:
    """Servicio de gestión de usuarios"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: UUID) -> User:
        """Obtiene usuario por ID o lanza UserNotFoundException"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundException()
        return user

    def update_user(self, user_id: UUID, update_data: UserUpdate) -> User:
        """Actualiza datos de usuario"""
        user = self.get_user_by_id(user_id)

        if update_data.email:
            existing = (
                self.db.query(User)
                .filter(User.email == update_data.email, User.id != user_id)
                .first()
            )
            if existing:
                raise UserAlreadyExistsException()
            user.email = update_data.email

        if update_data.full_name is not None:
            user.full_name = update_data.full_name

        if update_data.password:
            user.hashed_password = get_password_hash(update_data.password.get_secret_value())

        self.db.commit()
        self.db.refresh(user)
        return user
