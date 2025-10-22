from db_config import engine
from sqlalchemy import text

def set_application(data):

    return True

    sql = text("""
        SELECT 
            title
        FROM job
        WHERE job_code = :jid AND tenant_id = :tid
    """)

    with engine.begin() as conn:
        result = conn.execute(
            sql, {"tid": tenant_id, "jid": job_code}
        ).mappings().first() 

    return result
