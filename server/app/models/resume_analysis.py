from sqlalchemy import Column, Integer, String, Text, ForeignKey

from app.db.database import Base 

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    ats_score = Column(Integer)
    strengths = Column(Text) 
    weaknesses = Column(Text)
    suggestions = Column(Text)   