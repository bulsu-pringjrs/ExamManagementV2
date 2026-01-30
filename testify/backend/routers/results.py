import json
import logging
from typing import List, Optional


from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.results import ResultsService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/entities/results", tags=["results"])


# ---------- Pydantic Schemas ----------
class ResultsData(BaseModel):
    """Entity data schema (for create/update)"""
    submission_id: int
    student_id: int
    exam_id: int
    score: float
    feedback: str = None
    graded_at: str = None


class ResultsUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    submission_id: Optional[int] = None
    student_id: Optional[int] = None
    exam_id: Optional[int] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    graded_at: Optional[str] = None


class ResultsResponse(BaseModel):
    """Entity response schema"""
    id: int
    submission_id: int
    student_id: int
    exam_id: int
    score: float
    feedback: Optional[str] = None
    graded_at: Optional[str] = None

    class Config:
        from_attributes = True


class ResultsListResponse(BaseModel):
    """List response schema"""
    items: List[ResultsResponse]
    total: int
    skip: int
    limit: int


class ResultsBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[ResultsData]


class ResultsBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: ResultsUpdateData


class ResultsBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[ResultsBatchUpdateItem]


class ResultsBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=ResultsListResponse)
async def query_resultss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query resultss with filtering, sorting, and pagination"""
    logger.debug(f"Querying resultss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = ResultsService(db)
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
        logger.debug(f"Found {result['total']} resultss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying resultss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=ResultsListResponse)
async def query_resultss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query resultss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying resultss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = ResultsService(db)
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
        logger.debug(f"Found {result['total']} resultss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying resultss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=ResultsResponse)
async def get_results(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single results by ID"""
    logger.debug(f"Fetching results with id: {id}, fields={fields}")
    
    service = ResultsService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Results with id {id} not found")
            raise HTTPException(status_code=404, detail="Results not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching results {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=ResultsResponse, status_code=201)
async def create_results(
    data: ResultsData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new results"""
    logger.debug(f"Creating new results with data: {data}")
    
    service = ResultsService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create results")
        
        logger.info(f"Results created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating results: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[ResultsResponse], status_code=201)
async def create_resultss_batch(
    request: ResultsBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple resultss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} resultss")
    
    service = ResultsService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} resultss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[ResultsResponse])
async def update_resultss_batch(
    request: ResultsBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple resultss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} resultss")
    
    service = ResultsService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} resultss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=ResultsResponse)
async def update_results(
    id: int,
    data: ResultsUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing results"""
    logger.debug(f"Updating results {id} with data: {data}")

    service = ResultsService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Results with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Results not found")
        
        logger.info(f"Results {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating results {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating results {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_resultss_batch(
    request: ResultsBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple resultss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} resultss")
    
    service = ResultsService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} resultss successfully")
        return {"message": f"Successfully deleted {deleted_count} resultss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_results(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single results by ID"""
    logger.debug(f"Deleting results with id: {id}")
    
    service = ResultsService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Results with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Results not found")
        
        logger.info(f"Results {id} deleted successfully")
        return {"message": "Results deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting results {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")