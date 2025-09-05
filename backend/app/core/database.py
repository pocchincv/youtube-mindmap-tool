"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from app.core.config import settings


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        """Initialize database manager"""
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize SQLAlchemy engine"""
        connect_args = {}
        
        # SQLite specific configurations
        if "sqlite" in settings.database_url.lower():
            connect_args = {
                "check_same_thread": False,
                "timeout": 20
            }
        
        self.engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            poolclass=StaticPool if "sqlite" in settings.database_url.lower() else None,
            echo=settings.DEBUG,  # Log SQL queries in debug mode
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def get_db_session(self) -> Generator[Session, None, None]:
        """
        Database session dependency for FastAPI
        
        Yields:
            Session: SQLAlchemy database session
        """
        db = self.SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    
    def create_all_tables(self):
        """Create all database tables"""
        from app.models import Base
        Base.metadata.create_all(bind=self.engine)
    
    def drop_all_tables(self):
        """Drop all database tables (use with caution!)"""
        from app.models import Base
        Base.metadata.drop_all(bind=self.engine)


# Global database manager instance
db_manager = DatabaseManager()

# Database session dependency for FastAPI
get_db = db_manager.get_db_session


def init_db():
    """
    Initialize database tables and default data
    """
    # Create all tables
    db_manager.create_all_tables()
    
    # Add default data
    _create_default_data()


def _create_default_data():
    """Create default system data"""
    from app.models import Playlist, User
    
    db = next(db_manager.get_db_session())
    try:
        # Check if default playlists already exist
        existing_system_playlists = db.query(Playlist).filter(
            Playlist.is_system_playlist == True
        ).count()
        
        if existing_system_playlists == 0:
            # Create a default user for system playlists
            default_user = User(
                email="system@youtube-mindmap.local",
                display_name="System User",
                preferences={"is_system": True}
            )
            db.add(default_user)
            db.flush()  # Get the user ID
            
            # Create default system playlists
            default_playlists = [
                Playlist(
                    user_id=default_user.id,
                    name="Uncategorized",
                    description="Default playlist for uncategorized videos",
                    is_system_playlist=True,
                    display_order=0
                ),
                Playlist(
                    user_id=default_user.id,
                    name="Smart Search Result",
                    description="Results from intelligent search queries",
                    is_system_playlist=True,
                    display_order=1
                )
            ]
            
            for playlist in default_playlists:
                db.add(playlist)
            
            db.commit()
            print("✅ Created default system playlists")
        else:
            print("✅ Default system playlists already exist")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating default data: {e}")
        raise
    finally:
        db.close()


# Health check function
def check_database_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        bool: True if connection is successful
    """
    try:
        db = next(db_manager.get_db_session())
        # Try a simple query
        db.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
    finally:
        try:
            db.close()
        except:
            pass