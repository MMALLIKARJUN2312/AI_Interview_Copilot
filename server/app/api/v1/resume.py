from fastapi import (APIRouter, UploadFile, File, HTTPException)
from app.services.file_service import FileService
from app.services.resume_service import ResumeService
from app.core.constants import (MAX_RESUME_SIZE, ALLOWED_RESUME_TYPES)

router = APIRouter(
    prefix='/resume',
    tags=["Resume"]
)

@router.post('/analyze')
async def analyze_resume(file : UploadFile = File(...)):
    try : 
        if (file.content_type not in ALLOWED_RESUME_TYPES):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        contents = await file.read()
        
        max_size = (MAX_RESUME_SIZE * 1024 * 1024)
        
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail=
                    f"File exceeds "
                    f"{MAX_RESUME_SIZE} MB"
                  )
        
        await file.seek(0)
        
        file_path = await FileService.save_resume(file)
        extracted_text = ResumeService.extract_text(file_path)
        analysis = ResumeService.analyze_resume(extracted_text)
        
        return analysis
    
    except HTTPException:
        raise 
    except ValueError as error :
        raise HTTPException(status_code=400, detail=str(error))
    except Exception : 
        raise HTTPException(status_code=500, detail=("Resume analysis failed"))
        