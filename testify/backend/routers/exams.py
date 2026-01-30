import json
import logging
from typing import List, Optional


from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.exams import ExamsService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entities/exams", tags=["exams"])


# ---------- Pydantic Schemas ----------
class ExamsData(BaseModel):
    """Entity data schema (for create/update)"""
    class_id: int
    title: str
    description: str = None
    duration_minutes: int
    total_score: int
    questions: str
    availability_status: str
    created_by: int
    created_at: str = None


class ExamsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    class_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_score: Optional[int] = None
    questions: Optional[str] = None
    availability_status: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


class ExamsResponse(BaseModel):
    """Entity response schema"""
    id: int
    class_id: int
    title: str
    description: Optional[str] = None
    duration_minutes: int
    total_score: int
    questions: str
    availability_status: str
    created_by: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ExamsListResponse(BaseModel):
    """List response schema"""
    items: List[ExamsResponse]
    total: int
    skip: int
    limit: int


class ExamsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[ExamsData]


class ExamsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: ExamsUpdateData


class ExamsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[ExamsBatchUpdateItem]


class ExamsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=ExamsListResponse)
async def query_examss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query examss with filtering, sorting, and pagination"""
    logger.debug(f"Querying examss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = ExamsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} examss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying examss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=ExamsListResponse)
async def query_examss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query examss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying examss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = ExamsService(db)
    try:
        # Parse query JSON if provided
        query_dict = None
        if query:
            try:
                query_dict = json.loads(query)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid query JSON format")

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} examss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying examss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=ExamsResponse)
async def get_exams(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single exams by ID"""
    logger.debug(f"Fetching exams with id: {id}, fields={fields}")
    
    service = ExamsService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Exams with id {id} not found")
            raise HTTPException(status_code=404, detail="Exams not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exams {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=ExamsResponse, status_code=201)
async def create_exams(
    data: ExamsData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new exams"""
    logger.debug(f"Creating new exams with data: {data}")
    
    service = ExamsService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create exams")
        
        logger.info(f"Exams created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating exams: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating exams: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[ExamsResponse], status_code=201)
async def create_examss_batch(
    request: ExamsBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple examss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} examss")
    
    service = ExamsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} examss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[ExamsResponse])
async def update_examss_batch(
    request: ExamsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple examss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} examss")
    
    service = ExamsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} examss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=ExamsResponse)
async def update_exams(
    id: int,
    data: ExamsUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing exams"""
    logger.debug(f"Updating exams {id} with data: {data}")

    service = ExamsService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Exams with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Exams not found")
        
        logger.info(f"Exams {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating exams {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating exams {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_examss_batch(
    request: ExamsBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple examss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} examss")
    
    service = ExamsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} examss successfully")
        return {"message": f"Successfully deleted {deleted_count} examss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_exams(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single exams by ID"""
    logger.debug(f"Deleting exams with id: {id}")
    
    service = ExamsService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Exams with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Exams not found")
        
        logger.info(f"Exams {id} deleted successfully")
        return {"message": "Exams deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exams {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")