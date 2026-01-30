import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import jwt
import json
from datetime import datetime

from core.database import get_db
from services.classes import ClassesService
from services.exams import ExamsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/custom/classes", tags=["custom_classes"])

SECRET_KEY = "testify-secret-key-change-in-production"
ALGORITHM = "HS256"

def verify_token(request: Request):
    """Verify JWT token and return user info"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

class CreateClassRequest(BaseModel):
    class_name: str
    subject: str

class EnrollStudentRequest(BaseModel):
    student_id: int

@router.post("")
async def create_class(
    data: CreateClassRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new class (Teacher only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Only teachers can create classes")
        
        service = ClassesService(db)
        new_class = await service.create({
            "class_name": data.class_name,
            "subject": data.subject,
            "teacher_id": int(user.get("sub")),
            "student_ids": "[]",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return {
            "id": new_class.id,
            "class_name": new_class.class_name,
            "subject": new_class.subject,
            "teacher_id": new_class.teacher_id,
            "student_ids": json.loads(new_class.student_ids),
            "created_at": new_class.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create class error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create class: {str(e)}")

@router.get("")
async def list_classes(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """List classes based on user role"""
    try:
        user = verify_token(request)
        service = ClassesService(db)
        
        if user.get("role") == "teacher":
            # Teachers see their own classes
            result = await service.get_list(
                query_dict={"teacher_id": int(user.get("sub"))},
                limit=100
            )
        elif user.get("role") == "student":
            # Students see classes they're enrolled in
            all_classes = await service.get_list(limit=100)
            student_id = int(user.get("sub"))
            result = {
                "items": [
                    cls for cls in all_classes["items"]
                    if student_id in json.loads(cls.student_ids)
                ],
                "total": 0
            }
            result["total"] = len(result["items"])
        elif user.get("role") == "super_admin":
            # Super admin sees all classes
            result = await service.get_list(limit=100)
        else:
            raise HTTPException(status_code=403, detail="Invalid role")
        
        classes_list = [
            {
                "id": cls.id,
                "class_name": cls.class_name,
                "subject": cls.subject,
                "teacher_id": cls.teacher_id,
                "student_ids": json.loads(cls.student_ids),
                "created_at": cls.created_at
            }
            for cls in result["items"]
        ]
        
        return {"classes": classes_list, "total": result["total"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List classes error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list classes: {str(e)}")

@router.get("/{class_id}")
async def get_class(
    class_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get class details"""
    try:
        user = verify_token(request)
        service = ClassesService(db)
        
        class_obj = await service.get_by_id(class_id)
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Check access permissions
        student_ids = json.loads(class_obj.student_ids)
        user_id = int(user.get("sub"))
        
        if user.get("role") == "teacher" and class_obj.teacher_id != user_id:
            raise HTTPException(status_code=403, detail="Not your class")
        elif user.get("role") == "student" and user_id not in student_ids:
            raise HTTPException(status_code=403, detail="Not enrolled in this class")
        
        return {
            "id": class_obj.id,
            "class_name": class_obj.class_name,
            "subject": class_obj.subject,
            "teacher_id": class_obj.teacher_id,
            "student_ids": student_ids,
            "created_at": class_obj.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get class error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get class: {str(e)}")

@router.post("/{class_id}/enroll")
async def enroll_student(
    class_id: int,
    data: EnrollStudentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Enroll a student in a class (Teacher or Super Admin only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") not in ["teacher", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only teachers and super admin can enroll students")
        
        service = ClassesService(db)
        class_obj = await service.get_by_id(class_id)
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        # Check if teacher owns the class
        if user.get("role") == "teacher" and class_obj.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=403, detail="Not your class")
        
        # Add student to class
        student_ids = json.loads(class_obj.student_ids)
        if data.student_id not in student_ids:
            student_ids.append(data.student_id)
            await service.update(class_id, {"student_ids": json.dumps(student_ids)})
        
        return {"message": "Student enrolled successfully", "student_ids": student_ids}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enroll student error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enroll student: {str(e)}")

@router.delete("/{class_id}/students/{student_id}")
async def remove_student(
    class_id: int,
    student_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Remove a student from a class (Teacher or Super Admin only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") not in ["teacher", "super_admin"]:
            raise HTTPException(status_code=403, detail="Only teachers and super admin can remove students")
        
        service = ClassesService(db)
        class_obj = await service.get_by_id(class_id)
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        if user.get("role") == "teacher" and class_obj.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=403, detail="Not your class")
        
        student_ids = json.loads(class_obj.student_ids)
        if student_id in student_ids:
            student_ids.remove(student_id)
            await service.update(class_id, {"student_ids": json.dumps(student_ids)})
        
        return {"message": "Student removed successfully", "student_ids": student_ids}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove student error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove student: {str(e)}")

@router.get("/{class_id}/exams")
async def get_class_exams(
    class_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all exams for a class"""
    try:
        user = verify_token(request)
        
        # Verify access to class
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(class_id)
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        student_ids = json.loads(class_obj.student_ids)
        user_id = int(user.get("sub"))
        
        if user.get("role") == "teacher" and class_obj.teacher_id != user_id:
            raise HTTPException(status_code=403, detail="Not your class")
        elif user.get("role") == "student" and user_id not in student_ids:
            raise HTTPException(status_code=403, detail="Not enrolled in this class")
        
        # Get exams
        exam_service = ExamsService(db)
        result = await exam_service.get_list(
            query_dict={"class_id": class_id},
            limit=100
        )
        
        exams_list = []
        for exam in result["items"]:
            # Students only see enabled exams
            if user.get("role") == "student" and exam.availability_status != "enabled":
                continue
            
            exams_list.append({
                "id": exam.id,
                "class_id": exam.class_id,
                "title": exam.title,
                "description": exam.description,
                "duration_minutes": exam.duration_minutes,
                "total_score": exam.total_score,
                "availability_status": exam.availability_status,
                "created_by": exam.created_by,
                "created_at": exam.created_at,
                "question_count": len(json.loads(exam.questions))
            })
        
        return {"exams": exams_list, "total": len(exams_list)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get class exams error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get exams: {str(e)}")