import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.exams import Exams

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class ExamsService:
    """Service layer for Exams operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Exams]:
        """Create a new exams"""
        try:
            obj = Exams(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created exams with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating exams: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Exams]:
        """Get exams by ID"""
        try:
            query = select(Exams).where(Exams.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching exams {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of examss"""
        try:
            query = select(Exams)
            count_query = select(func.count(Exams.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Exams, field):
                        query = query.where(getattr(Exams, field) == value)
                        count_query = count_query.where(getattr(Exams, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Exams, field_name):
                        query = query.order_by(getattr(Exams, field_name).desc())
                else:
                    if hasattr(Exams, sort):
                        query = query.order_by(getattr(Exams, sort))
            else:
                query = query.order_by(Exams.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching exams list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Exams]:
        """Update exams"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Exams {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated exams {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating exams {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete exams"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Exams {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted exams {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting exams {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Exams]:
        """Get exams by any field"""
        try:
            if not hasattr(Exams, field_name):
                raise ValueError(f"Field {field_name} does not exist on Exams")
            result = await self.db.execute(
                select(Exams).where(getattr(Exams, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching exams by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Exams]:
        """Get list of examss filtered by field"""
        try:
            if not hasattr(Exams, field_name):
                raise ValueError(f"Field {field_name} does not exist on Exams")
            result = await self.db.execute(
                select(Exams)
                .where(getattr(Exams, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Exams.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching examss by {field_name}: {str(e)}")
            raise