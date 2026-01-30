import json
import logging
from typing import List, Optional


from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.classes import ClassesService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entities/classes", tags=["classes"])


# ---------- Pydantic Schemas ----------
class ClassesData(BaseModel):
    """Entity data schema (for create/update)"""
    class_name: str
    subject: str
    teacher_id: int
    student_ids: str = None
    created_at: str = None


class ClassesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    class_name: Optional[str] = None
    subject: Optional[str] = None
    teacher_id: Optional[int] = None
    student_ids: Optional[str] = None
    created_at: Optional[str] = None


class ClassesResponse(BaseModel):
    """Entity response schema"""
    id: int
    class_name: str
    subject: str
    teacher_id: int
    student_ids: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class ClassesListResponse(BaseModel):
    """List response schema"""
    items: List[ClassesResponse]
    total: int
    skip: int
    limit: int


class ClassesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[ClassesData]


class ClassesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: ClassesUpdateData


class ClassesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[ClassesBatchUpdateItem]


class ClassesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=ClassesListResponse)
async def query_classess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query classess with filtering, sorting, and pagination"""
    logger.debug(f"Querying classess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = ClassesService(db)
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
        logger.debug(f"Found {result['total']} classess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying classess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=ClassesListResponse)
async def query_classess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query classess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying classess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = ClassesService(db)
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
        logger.debug(f"Found {result['total']} classess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying classess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=ClassesResponse)
async def get_classes(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single classes by ID"""
    logger.debug(f"Fetching classes with id: {id}, fields={fields}")
    
    service = ClassesService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Classes with id {id} not found")
            raise HTTPException(status_code=404, detail="Classes not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching classes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=ClassesResponse, status_code=201)
async def create_classes(
    data: ClassesData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new classes"""
    logger.debug(f"Creating new classes with data: {data}")
    
    service = ClassesService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create classes")
        
        logger.info(f"Classes created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating classes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating classes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[ClassesResponse], status_code=201)
async def create_classess_batch(
    request: ClassesBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple classess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} classess")
    
    service = ClassesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} classess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[ClassesResponse])
async def update_classess_batch(
    request: ClassesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple classess in a single request"""
    logger.debug(f"Batch updating {len(request.items)} classess")
    
    service = ClassesService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} classess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=ClassesResponse)
async def update_classes(
    id: int,
    data: ClassesUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing classes"""
    logger.debug(f"Updating classes {id} with data: {data}")

    service = ClassesService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Classes with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Classes not found")
        
        logger.info(f"Classes {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating classes {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating classes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_classess_batch(
    request: ClassesBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple classess by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} classess")
    
    service = ClassesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} classess successfully")
        return {"message": f"Successfully deleted {deleted_count} classess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_classes(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single classes by ID"""
    logger.debug(f"Deleting classes with id: {id}")
    
    service = ClassesService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Classes with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Classes not found")
        
        logger.info(f"Classes {id} deleted successfully")
        return {"message": "Classes deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting classes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")