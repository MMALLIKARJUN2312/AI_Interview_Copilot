import uuid
from pathlib import Path
from fastapi import UploadFile

UPLOAD_DIR = Path("uploads/resumes")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class FileService:
    
    @staticmethod
    async def save_resume(file : UploadFile) -> str:
        
        extension = Path(file.filename).suffix
        unique_filename = (
            f"{uuid.uuid4()}"
            f"{extension}"
        )
        file_path = (
            UPLOAD_DIR/
            unique_filename
        )
        
        contents = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
            
        return str(file_path)