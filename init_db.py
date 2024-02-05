from util.db import get_db

with get_db() as db:
    db.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    db.execute('DROP TABLE IF EXISTS project')
    db.execute('DROP TABLE IF EXISTS bug')
    db.execute('DROP TABLE IF EXISTS crash')
    
    db.commit()

    db.execute('''
    CREATE TABLE project (
        id SERIAL,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name TEXT NOT NULL,
        
        cve_product TEXT DEFAULT '',
        cve_version TEXT DEFAULT '',
        cve_vendor TEXT DEFAULT '',
        cve_credit TEXT DEFAULT '',
        cve_reference TEXT DEFAULT '',
        
        cache_unclassified_cnt INTEGER NOT NULL DEFAULT 0
    )''')

    db.execute('''
    CREATE TABLE bug (
        id SERIAL,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        crash_filter TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 0,
        
        cve_vulnerability_type TEXT DEFAULT '',
        cve_attack_type TEXT DEFAULT '',
        cve_impact TEXT DEFAULT '',
        cve_affected_component TEXT DEFAULT '',
        cve_attack_vector TEXT DEFAULT '',
        cve_description TEXT DEFAULT '',
        cve_reference TEXT DEFAULT '',
        cve_additional TEXT DEFAULT '',
               
        cache_crash_cnt INTEGER NOT NULL DEFAULT 0
)''')

    db.execute('''
    CREATE TABLE crash (
        id SERIAL,
        project_id INTEGER NOT NULL,
        data BYTEA NOT NULL,
        asan_report TEXT NOT NULL,
        origin_filename TEXT NOT NULL,
        trace TEXT NOT NULL
    )''')
    db.execute('CREATE INDEX ON crash USING gin (asan_report gin_trgm_ops)')
    db.execute('CREATE INDEX ON crash USING gin (trace gin_trgm_ops)')


