"""
Base repository pattern for database operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Any, Dict
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseModel
from .transactions import database_transaction

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T], ABC):
    """
    Base repository class providing common CRUD operations.
    
    This class provides a foundation for all repository classes,
    implementing common database operations with proper error handling
    and transaction management.
    """
    
    def __init__(self, model_class: type[T]):
        self.model_class = model_class
    
    async def get_by_id(
        self, 
        session: AsyncSession, 
        id: UUID,
        load_relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Get entity by ID with optional relationship loading.
        
        Args:
            session: Database session
            id: Entity ID
            load_relationships: List of relationship names to eagerly load
            
        Returns:
            Entity instance or None if not found
        """
        query = select(self.model_class).where(self.model_class.id == id)
        
        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                query = query.options(selectinload(getattr(self.model_class, relationship)))
        
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        session: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        load_relationships: Optional[List[str]] = None
    ) -> List[T]:
        """
        Get all entities with pagination and filtering.
        
        Args:
            session: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of field filters
            order_by: Field name to order by
            load_relationships: List of relationship names to eagerly load
            
        Returns:
            List of entity instances
        """
        query = select(self.model_class)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
        
        # Apply ordering
        if order_by and hasattr(self.model_class, order_by):
            query = query.order_by(getattr(self.model_class, order_by))
        
        # Add eager loading for relationships
        if load_relationships:
            for relationship in load_relationships:
                if hasattr(self.model_class, relationship):
                    query = query.options(selectinload(getattr(self.model_class, relationship)))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        session: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count entities with optional filtering.
        
        Args:
            session: Database session
            filters: Dictionary of field filters
            
        Returns:
            Count of matching entities
        """
        query = select(func.count(self.model_class.id))
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    query = query.where(getattr(self.model_class, field) == value)
        
        result = await session.execute(query)
        return result.scalar()
    
    async def create(
        self,
        session: AsyncSession,
        entity: T,
        commit: bool = True
    ) -> T:
        """
        Create new entity.
        
        Args:
            session: Database session
            entity: Entity instance to create
            commit: Whether to commit the transaction
            
        Returns:
            Created entity instance
        """
        session.add(entity)
        
        if commit:
            await session.commit()
            await session.refresh(entity)
        else:
            await session.flush()
        
        return entity
    
    async def update(
        self,
        session: AsyncSession,
        id: UUID,
        updates: Dict[str, Any],
        commit: bool = True
    ) -> Optional[T]:
        """
        Update entity by ID.
        
        Args:
            session: Database session
            id: Entity ID
            updates: Dictionary of field updates
            commit: Whether to commit the transaction
            
        Returns:
            Updated entity instance or None if not found
        """
        # First check if entity exists
        entity = await self.get_by_id(session, id)
        if not entity:
            return None
        
        # Apply updates
        query = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**updates)
        )
        
        await session.execute(query)
        
        if commit:
            await session.commit()
        else:
            await session.flush()
        
        # Return updated entity
        await session.refresh(entity)
        return entity
    
    async def delete(
        self,
        session: AsyncSession,
        id: UUID,
        commit: bool = True
    ) -> bool:
        """
        Delete entity by ID.
        
        Args:
            session: Database session
            id: Entity ID
            commit: Whether to commit the transaction
            
        Returns:
            True if entity was deleted, False if not found
        """
        # Check if entity exists
        entity = await self.get_by_id(session, id)
        if not entity:
            return False
        
        query = delete(self.model_class).where(self.model_class.id == id)
        result = await session.execute(query)
        
        if commit:
            await session.commit()
        
        return result.rowcount > 0
    
    async def exists(
        self,
        session: AsyncSession,
        id: UUID
    ) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            session: Database session
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        query = select(func.count(self.model_class.id)).where(self.model_class.id == id)
        result = await session.execute(query)
        return result.scalar() > 0
    
    async def bulk_create(
        self,
        session: AsyncSession,
        entities: List[T],
        commit: bool = True
    ) -> List[T]:
        """
        Create multiple entities in bulk.
        
        Args:
            session: Database session
            entities: List of entity instances to create
            commit: Whether to commit the transaction
            
        Returns:
            List of created entity instances
        """
        session.add_all(entities)
        
        if commit:
            await session.commit()
            for entity in entities:
                await session.refresh(entity)
        else:
            await session.flush()
        
        return entities
    
    @abstractmethod
    async def get_by_unique_field(
        self,
        session: AsyncSession,
        field_name: str,
        field_value: Any
    ) -> Optional[T]:
        """
        Get entity by unique field (to be implemented by subclasses).
        
        Args:
            session: Database session
            field_name: Name of the unique field
            field_value: Value to search for
            
        Returns:
            Entity instance or None if not found
        """
        pass