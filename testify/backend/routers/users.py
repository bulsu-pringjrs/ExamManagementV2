import json
import logging
from typing import List, Optional


from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.users import UsersService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entities/users", tags=["users"])


# ---------- Pydantic Schemas ----------
class UsersData(BaseModel):
    """Entity data schema (for create/update)"""
    email: str
    password: str
    role: str
    full_name: str
    created_at: str = None


class UsersUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    full_name: Optional[str] = None
    created_at: Optional[str] = None


class UsersResponse(BaseModel):
    """Entity response schema"""
    id: int
    email: str
    password: str
    role: str
    full_name: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UsersListResponse(BaseModel):
    """List response schema"""
    items: List[UsersResponse]
    total: int
    skip: int
    limit: int


class UsersBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[UsersData]


class UsersBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: UsersUpdateData


class UsersBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[UsersBatchUpdateItem]


class UsersBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=UsersListResponse)
async def query_userss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query userss with filtering, sorting, and pagination"""
    logger.debug(f"Querying userss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = UsersService(db)
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
        logger.debug(f"Found {result['total']} userss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying userss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=UsersListResponse)
async def query_userss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query userss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying userss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = UsersService(db)
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
        logger.debug(f"Found {result['total']} userss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying userss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=UsersResponse)
async def get_users(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single users by ID"""
    logger.debug(f"Fetching users with id: {id}, fields={fields}")
    
    service = UsersService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Users with id {id} not found")
            raise HTTPException(status_code=404, detail="Users not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching users {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=UsersResponse, status_code=201)
async def create_users(
    data: UsersData,
    db: AsyncSession = Depends(get_db),
):
    """Create a new users"""
    logger.debug(f"Creating new users with data: {data}")
    
    service = UsersService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create users")
        
        logger.info(f"Users created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating users: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[UsersResponse], status_code=201)
async def create_userss_batch(
    request: UsersBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create multiple userss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} userss")
    
    service = UsersService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} userss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[UsersResponse])
async def update_userss_batch(
    request: UsersBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update multiple userss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} userss")
    
    service = UsersService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} userss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=UsersResponse)
async def update_users(
    id: int,
    data: UsersUpdateData,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing users"""
    logger.debug(f"Updating users {id} with data: {data}")

    service = UsersService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Users with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Users not found")
        
        logger.info(f"Users {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating users {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating users {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_userss_batch(
    request: UsersBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple userss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} userss")
    
    service = UsersService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} userss successfully")
        return {"message": f"Successfully deleted {deleted_count} userss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_users(
    id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a single users by ID"""
    logger.debug(f"Deleting users with id: {id}")
    
    service = UsersService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Users with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Users not found")
        
        logger.info(f"Users {id} deleted successfully")
        return {"message": "Users deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting users {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")