import psycopg
from psycopg.rows import dict_row
from flask import g, flash
import dotenv
from os import getenv

dotenv.load_dotenv()

def get_db():
    conn = psycopg.connect(getenv('PGSQL_URI'), row_factory=dict_row)
    return conn

# 更新 filter，并更新这个 bug 的 cache_crash_cnt
def update_filter(pid, bid, sql):
    try:
        new_cnt = g.db.execute(f'SELECT COUNT(*) AS cnt FROM crash WHERE project_id = {pid} AND ({sql})').fetchone()['cnt']
        g.db.execute('UPDATE bug SET crash_filter = %s, cache_crash_cnt = %s WHERE id = %s', [sql, new_cnt, bid])
        return True
    except Exception as e:
        g.db.rollback()
        flash(repr(e))
        return False

def get_unclassified_condition(pid):
    filters = g.db.execute('SELECT crash_filter FROM bug WHERE project_id = %s', [pid]).fetchall()

    sql = ['1=1']

    for x in filters:
        sql.append(f"(NOT ({x['crash_filter']}))")
    
    sql = f'project_id = {pid} AND ' + ' AND '.join(sql)
    return sql

def update_unclassified_cache(pid):
    sql = get_unclassified_condition(pid)

    cnt = g.db.execute(f'SELECT COUNT(*) AS cnt FROM crash WHERE {sql}').fetchone()['cnt']
    g.db.execute('UPDATE project SET cache_unclassified_cnt = %s WHERE id = %s', [cnt, pid])


def update_all_cache(pid):
    bugs = g.db.execute('SELECT * FROM bug WHERE project_id = %s', [pid])

    for b in bugs:
        update_filter(pid, b['id'], b['crash_filter'])

    update_unclassified_cache(pid)