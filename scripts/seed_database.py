#!/usr/bin/env python3
"""
Database seeding script for development and testing environments.
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.shared.config import get_settings
from src.shared.database.connection import DatabaseManager
from src.shared.database.base import Base

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Database seeding utility for development and testing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        logger.info("Creating database tables...")
        
        # Import all models to ensure they're registered
        # TODO: Import actual models when they're created
        # from src.services.auth.models import User
        # from src.services.campaigns.models import Campaign
        # etc.
        
        async with self.db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
    
    async def seed_development_data(self) -> None:
        """Seed database with development data."""
        logger.info("Seeding development data...")
        
        async with self.db_manager.get_session() as session:
            # TODO: Add development seed data
            # Example:
            # admin_user = User(
            #     email="admin@example.com",
            #     full_name="System Administrator",
            #     is_active=True
            # )
            # session.add(admin_user)
            pass
        
        logger.info("Development data seeded successfully")
    
    async def seed_test_data(self) -> None:
        """Seed database with test data."""
        logger.info("Seeding test data...")
        
        async with self.db_manager.get_session() as session:
            # TODO: Add test seed data
            # Example:
            # test_user = User(
            #     email="test@example.com",
            #     full_name="Test User",
            #     is_active=True
            # )
            # session.add(test_user)
            pass
        
        logger.info("Test data seeded successfully")
    
    async def clear_database(self) -> None:
        """Clear all data from database (for testing)."""
        logger.warning("Clearing all database data...")
        
        async with self.db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database cleared and recreated")
    
    async def run_health_check(self) -> bool:
        """Run database health check."""
        logger.info("Running database health check...")
        
        try:
            health_result = await self.db_manager.health_check()
            if health_result["status"] == "healthy":
                logger.info("Database health check passed")
                return True
            else:
                logger.error(f"Database health check failed: {health_result}")
                return False
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return False
    
    async def close(self) -> None:
        """Close database connections."""
        await self.db_manager.close()


async def main():
    """Main seeding function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database seeding utility")
    parser.add_argument(
        "--action",
        choices=["create", "seed-dev", "seed-test", "clear", "health"],
        default="seed-dev",
        help="Action to perform"
    )
    parser.add_argument(
        "--environment",
        choices=["development", "testing"],
        default="development",
        help="Environment to seed for"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    seeder = DatabaseSeeder()
    
    try:
        if args.action == "create":
            await seeder.create_tables()
        elif args.action == "seed-dev":
            await seeder.create_tables()
            await seeder.seed_development_data()
        elif args.action == "seed-test":
            await seeder.create_tables()
            await seeder.seed_test_data()
        elif args.action == "clear":
            await seeder.clear_database()
        elif args.action == "health":
            success = await seeder.run_health_check()
            sys.exit(0 if success else 1)
        
        logger.info(f"Database seeding completed successfully for action: {args.action}")
        
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        sys.exit(1)
    finally:
        await seeder.close()


if __name__ == "__main__":
    asyncio.run(main())