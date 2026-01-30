import logging
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.users import Users

logger = logging.getLogger(__name__)


# ------------------ Service Layer ------------------
class UsersService:
    """Service layer for Users operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: Dict[str, Any]) -> Optional[Users]:
        """Create a new users"""
        try:
            obj = Users(**data)
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Created users with id: {obj.id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating users: {str(e)}")
            raise

    async def get_by_id(self, obj_id: int) -> Optional[Users]:
        """Get users by ID"""
        try:
            query = select(Users).where(Users.id == obj_id)
            result = await self.db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching users {obj_id}: {str(e)}")
            raise

    async def get_list(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        query_dict: Optional[Dict[str, Any]] = None,
        sort: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of userss"""
        try:
            query = select(Users)
            count_query = select(func.count(Users.id))
            
            if query_dict:
                for field, value in query_dict.items():
                    if hasattr(Users, field):
                        query = query.where(getattr(Users, field) == value)
                        count_query = count_query.where(getattr(Users, field) == value)
            
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            if sort:
                if sort.startswith('-'):
                    field_name = sort[1:]
                    if hasattr(Users, field_name):
                        query = query.order_by(getattr(Users, field_name).desc())
                else:
                    if hasattr(Users, sort):
                        query = query.order_by(getattr(Users, sort))
            else:
                query = query.order_by(Users.id.desc())

            result = await self.db.execute(query.offset(skip).limit(limit))
            items = result.scalars().all()

            return {
                "items": items,
                "total": total,
                "skip": skip,
                "limit": limit,
            }
        except Exception as e:
            logger.error(f"Error fetching users list: {str(e)}")
            raise

    async def update(self, obj_id: int, update_data: Dict[str, Any]) -> Optional[Users]:
        """Update users"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Users {obj_id} not found for update")
                return None
            for key, value in update_data.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)

            await self.db.commit()
            await self.db.refresh(obj)
            logger.info(f"Updated users {obj_id}")
            return obj
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating users {obj_id}: {str(e)}")
            raise

    async def delete(self, obj_id: int) -> bool:
        """Delete users"""
        try:
            obj = await self.get_by_id(obj_id)
            if not obj:
                logger.warning(f"Users {obj_id} not found for deletion")
                return False
            await self.db.delete(obj)
            await self.db.commit()
            logger.info(f"Deleted users {obj_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting users {obj_id}: {str(e)}")
            raise

    async def get_by_field(self, field_name: str, field_value: Any) -> Optional[Users]:
        """Get users by any field"""
        try:
            if not hasattr(Users, field_name):
                raise ValueError(f"Field {field_name} does not exist on Users")
            result = await self.db.execute(
                select(Users).where(getattr(Users, field_name) == field_value)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching users by {field_name}: {str(e)}")
            raise

    async def list_by_field(
        self, field_name: str, field_value: Any, skip: int = 0, limit: int = 20
    ) -> List[Users]:
        """Get list of userss filtered by field"""
        try:
            if not hasattr(Users, field_name):
                raise ValueError(f"Field {field_name} does not exist on Users")
            result = await self.db.execute(
                select(Users)
                .where(getattr(Users, field_name) == field_value)
                .offset(skip)
                .limit(limit)
                .order_by(Users.id.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching userss by {field_name}: {str(e)}")
            raise