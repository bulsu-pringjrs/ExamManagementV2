import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Any
import jwt
import json
from datetime import datetime

from core.database import get_db
from services.exams import ExamsService
from services.classes import ClassesService
from services.submissions import SubmissionsService
from services.results import ResultsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/custom/exams", tags=["custom_exams"])

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

class CreateExamRequest(BaseModel):
    class_id: int
    title: str
    description: str
    duration_minutes: int
    total_score: int
    questions: List[dict]

class ToggleAvailabilityRequest(BaseModel):
    availability_status: str

class SubmitExamRequest(BaseModel):
    answers: List[dict]

@router.post("")
async def create_exam(
    data: CreateExamRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Create a new exam (Teacher only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Only teachers can create exams")
        
        # Verify teacher owns the class
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(data.class_id)
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        if class_obj.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=403, detail="Not your class")
        
        # Create exam
        exam_service = ExamsService(db)
        new_exam = await exam_service.create({
            "class_id": data.class_id,
            "title": data.title,
            "description": data.description,
            "duration_minutes": data.duration_minutes,
            "total_score": data.total_score,
            "questions": json.dumps(data.questions),
            "availability_status": "disabled",
            "created_by": int(user.get("sub")),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        return {
            "id": new_exam.id,
            "class_id": new_exam.class_id,
            "title": new_exam.title,
            "description": new_exam.description,
            "duration_minutes": new_exam.duration_minutes,
            "total_score": new_exam.total_score,
            "questions": json.loads(new_exam.questions),
            "availability_status": new_exam.availability_status,
            "created_by": new_exam.created_by,
            "created_at": new_exam.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create exam error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create exam: {str(e)}")

@router.get("/{exam_id}")
async def get_exam(
    exam_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get exam details"""
    try:
        user = verify_token(request)
        
        exam_service = ExamsService(db)
        exam = await exam_service.get_by_id(exam_id)
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Verify access
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(exam.class_id)
        
        if not class_obj:
            raise HTTPException(status_code=404, detail="Class not found")
        
        user_id = int(user.get("sub"))
        student_ids = json.loads(class_obj.student_ids)
        
        # Students can only access enabled exams in their classes
        if user.get("role") == "student":
            if user_id not in student_ids:
                raise HTTPException(status_code=403, detail="Not enrolled in this class")
            if exam.availability_status != "enabled":
                raise HTTPException(status_code=403, detail="Exam is not available")
        elif user.get("role") == "teacher" and class_obj.teacher_id != user_id:
            raise HTTPException(status_code=403, detail="Not your class")
        
        return {
            "id": exam.id,
            "class_id": exam.class_id,
            "title": exam.title,
            "description": exam.description,
            "duration_minutes": exam.duration_minutes,
            "total_score": exam.total_score,
            "questions": json.loads(exam.questions),
            "availability_status": exam.availability_status,
            "created_by": exam.created_by,
            "created_at": exam.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get exam error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get exam: {str(e)}")

@router.patch("/{exam_id}/toggle-availability")
async def toggle_exam_availability(
    exam_id: int,
    data: ToggleAvailabilityRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Toggle exam availability (Teacher only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Only teachers can toggle exam availability")
        
        exam_service = ExamsService(db)
        exam = await exam_service.get_by_id(exam_id)
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Verify teacher owns the class
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(exam.class_id)
        
        if class_obj.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=403, detail="Not your exam")
        
        # Update availability
        await exam_service.update(exam_id, {
            "availability_status": data.availability_status
        })
        
        return {
            "message": "Exam availability updated",
            "availability_status": data.availability_status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Toggle availability error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle availability: {str(e)}")

@router.post("/{exam_id}/submit")
async def submit_exam(
    exam_id: int,
    data: SubmitExamRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Submit exam answers (Student only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") != "student":
            raise HTTPException(status_code=403, detail="Only students can submit exams")
        
        exam_service = ExamsService(db)
        exam = await exam_service.get_by_id(exam_id)
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Verify exam is enabled
        if exam.availability_status != "enabled":
            raise HTTPException(status_code=403, detail="Exam is not available")
        
        # Verify student is enrolled
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(exam.class_id)
        student_ids = json.loads(class_obj.student_ids)
        user_id = int(user.get("sub"))
        
        if user_id not in student_ids:
            raise HTTPException(status_code=403, detail="Not enrolled in this class")
        
        # Auto-grade objective questions
        questions = json.loads(exam.questions)
        total_score = 0
        graded = True
        
        for i, answer in enumerate(data.answers):
            question = questions[i]
            
            if question["type"] == "multiple_choice":
                if answer.get("answer") == question.get("correct_answer"):
                    answer["score"] = question["points"]
                    total_score += question["points"]
                else:
                    answer["score"] = 0
            elif question["type"] == "enumeration":
                # Simple exact match for enumeration
                student_answers = [a.strip().lower() for a in answer.get("answer", [])]
                correct_answers = [a.strip().lower() for a in question.get("correct_answers", [])]
                if set(student_answers) == set(correct_answers):
                    answer["score"] = question["points"]
                    total_score += question["points"]
                else:
                    answer["score"] = 0
            else:
                # Essay, coding, listening, viewing need manual grading
                answer["score"] = None
                graded = False
        
        # Create submission
        submission_service = SubmissionsService(db)
        submission = await submission_service.create({
            "exam_id": exam_id,
            "student_id": user_id,
            "answers": json.dumps(data.answers),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "score": total_score if graded else 0,
            "graded": graded
        })
        
        # Create result if fully graded
        if graded:
            result_service = ResultsService(db)
            await result_service.create({
                "submission_id": submission.id,
                "student_id": user_id,
                "exam_id": exam_id,
                "score": total_score,
                "feedback": "Auto-graded",
                "graded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return {
            "submission_id": submission.id,
            "score": total_score,
            "graded": graded,
            "message": "Exam submitted successfully" if graded else "Exam submitted, awaiting manual grading"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit exam error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit exam: {str(e)}")

@router.get("/{exam_id}/submissions")
async def get_exam_submissions(
    exam_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get all submissions for an exam (Teacher only)"""
    try:
        user = verify_token(request)
        
        if user.get("role") != "teacher":
            raise HTTPException(status_code=403, detail="Only teachers can view submissions")
        
        exam_service = ExamsService(db)
        exam = await exam_service.get_by_id(exam_id)
        
        if not exam:
            raise HTTPException(status_code=404, detail="Exam not found")
        
        # Verify teacher owns the class
        class_service = ClassesService(db)
        class_obj = await class_service.get_by_id(exam.class_id)
        
        if class_obj.teacher_id != int(user.get("sub")):
            raise HTTPException(status_code=403, detail="Not your exam")
        
        # Get submissions
        submission_service = SubmissionsService(db)
        result = await submission_service.get_list(
            query_dict={"exam_id": exam_id},
            limit=100
        )
        
        submissions_list = [
            {
                "id": sub.id,
                "exam_id": sub.exam_id,
                "student_id": sub.student_id,
                "answers": json.loads(sub.answers),
                "submitted_at": sub.submitted_at,
                "score": sub.score,
                "graded": sub.graded
            }
            for sub in result["items"]
        ]
        
        return {"submissions": submissions_list, "total": result["total"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get submissions error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get submissions: {str(e)}")