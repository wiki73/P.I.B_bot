from contextlib import contextmanager
from sqlalchemy.orm import Session
from database.models import SessionLocal
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self._session = None
        
    @property
    def session(self) -> Session:
        if self._session is None:
            self._session = SessionLocal()
        return self._session
    
    def close(self):
        if self._session:
            self._session.close()
            self._session = None
            
    @contextmanager
    def transaction(self):
        try:
            yield
            self.session.commit()
        except Exception as e:
            logger.error(f"Database transaction error: {str(e)}")
            self.session.rollback()
            self.close()  
            raise
        
    def refresh_session(self):
        self.close()
        return self.session

db = Database() 