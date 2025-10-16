from db_config import engine
from sqlalchemy import text

def get_application(tenant_id, job_code):
    
    tenant_id = int(tenant_id)

    sql = text("""
        SELECT 
          title
        FROM job
        WHERE job_code = :jid AND tenant_id = :tid
    """)
    
    with engine.begin() as conn:
        job_name = conn.execute(sql, {"tid": tenant_id, "jid": job_code}).mappings().all()
    
    print (job_name)

    return job_name