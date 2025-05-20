import psycopg2
import psycopg2.extras
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DBUtils:
    """Utility class for direct SQL operations"""
    
    @staticmethod
    def get_connection():
        """Get database connection to Supabase PostgreSQL"""
        try:
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT']
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    @staticmethod
    def execute_query(query, params=None, fetch=True):
        """Execute raw SQL query and return results"""
        conn = None
        cursor = None
        try:
            conn = DBUtils.get_connection()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cursor.execute(query, params or ())
            
            if fetch:
                results = cursor.fetchall()
                # Convert to list of dictionaries
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in results]
            else:
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Query execution error: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()