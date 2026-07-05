from app.db.database import Base
from app.db.mixins import (PrimaryKeyMixin, TimestampMixin)
from sqlalchemy.orm import Mapped, mapped_column

class User(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    
    full_name : Mapped[str] = mapped_column(nullable=False)
    email : Mapped[str] = mapped_column(unique=True ,nullable=False)
    hashed_password : Mapped[str] = mapped_column(nullable=False)
    role : Mapped[str] = mapped_column(default="candidate")
    
    
    