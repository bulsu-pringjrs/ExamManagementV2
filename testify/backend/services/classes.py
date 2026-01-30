import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.classes import Classes

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class ClassesService:
    """Service layer for Classes operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Classes]:
        """Create a new classes"""
        try:
            obj = Classes(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created classes with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating classes: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Classes]:
        """Get classes by ID"""
        try:
            query = select(Classes).where(Classes.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching classes {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of classess"""
        try:
            query = select(Classes)
            count_query = select(func.count(Classes.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Classes, field):
                        query = query.where(getattr(Classes, field) == value)
                        count_query = count_query.where(getattr(Classes, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Classes, field_name):
                        query = query.order_by(getattr(Classes, field_name).desc())
                else:
                    if hasattr(Classes, sort):
                        query = query.order_by(getattr(Classes, sort))
            else:
                query = query.order_by(Classes.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching classes list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Classes]:
        """Update classes"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Classes {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated classes {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating classes {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete classes"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Classes {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted classes {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting classes {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Classes]:
        """Get classes by any field"""
        try:
            if not hasattr(Classes, field_name):
                raise ValueError(f"Field {field_name} does not exist on Classes")
            result = await self.db.execute(
                select(Classes).where(getattr(Classes, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching classes by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Classes]:
        """Get list of classess filtered by field"""
        try:
            if not hasattr(Classes, field_name):
                raise ValueError(f"Field {field_name} does not exist on Classes")
            result = await self.db.execute(
                select(Classes)
                .where(getattr(Classes, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Classes.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching classess by {field_name}: {str(e)}")
            raise