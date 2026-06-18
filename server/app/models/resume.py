from sqlalchemy import Column, Integer, String, Text, ForeignKey

from app.db.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=False)