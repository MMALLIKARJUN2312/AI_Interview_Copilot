from __future__ import annotations

from typing import Generic, Type, TypeVar, Any

from sqlalchemy.orm import Session

from app.db.database import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """Generic repository providing reusable CRUD operations for SQLAlchemy models
    Transaction control intentionally remains in the service layer
    """
    
    def __init__(self, model : Type[ModelType]) -> None:
        self.model = model
        
    def create(self, db : Session, entity : ModelType) -> ModelType:
        db.add(entity)
        return entity
    
    def create_many(self, db : Session, entities : list[ModelType]) -> list[ModelType]:
        db.add_all(entities)
        return entities
    
    def get_by_id(self, db : Session, entity_id : int) -> ModelType | None:
        return (db.query(self.model).filter(self.model.id == entity_id).first())
        
    def get_all(self, db : Session) -> list[ModelType]:
        return (db.query(self.model).all())
    
    def exists(self, db : Session, **filters : any) -> bool: 
        return (db.query(self.model).filter_by(**filters).first() is not None)
        
    def count(self, db : Session) -> int:
        return (db.query(self.model).count())
    
    def update(self, db : Session, entity : ModelType) -> ModelType:
        db.add(entity)
        return entity
    
    def update_fields(self, entity : ModelType, **fields : Any) -> ModelType:
        for key, value in fields.items():
            setattr(entity, key, value)
        return entity    
    
    def delete(self, db : Session, entity : ModelType) -> ModelType:
        db.delete(entity)
        
    def delete_many(self, db : Session, entities : list[ModelType]) -> None:
        for entity in entities:
            db.delete(entity)
            
    def paginate(self, db : Session, *, page : int, page_size : int) -> list[ModelType]:
        return (db.query(self.model).offset((page - 1) * page_size).limit(page_size).all())
    
    def flush(self, db : Session) -> None:
        db.flush()
        
    def refresh(self, db : Session, entity : list[ModelType]) -> None:
        db.refresh(entity)
        
    def commit(self, db : Session) -> None:
        db.commit()
    
    def rollback(self, db : Session) -> None:
        db.rollback() 
        