from db_config import engine
from sqlalchemy import text

def get_application(tenant_id, job_code):
    
    sql = text("""
        SELECT 
          title
        FROM job
        WHERE job_code = :jid AND tenant_id = :tid
    """)
    
    with engine.begin() as conn:
        job_name = conn.execute(sql, {"tid": tenant_id, "jid": job_code}).mappings().all()
    
    return job_name