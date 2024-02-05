from flask import Blueprint, render_template, g, request, abort, url_for, redirect, flash, make_response, send_file
import os
import sqlite3
import tempfile
import math
import io
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
from util.trace import get_trace
from util.db import update_all_cache, get_unclassified_condition, update_filter, update_unclassified_cache

bp = Blueprint('project', __name__, url_prefix='/project')

def show_list():
    g.site_info = g.db.execute('SELECT (SELECT COUNT(*) AS project_cnt FROM project), (SELECT COUNT(*) AS bug_cnt FROM bug), (SELECT COUNT(*) AS crash_cnt FROM crash)').fetchone()
    
    g.project_list = g.db.execute("SELECT id, name, TO_CHAR(create_time, 'YYYY-MM-DD') as create_time FROM project ORDER BY id DESC").fetchall()
    
    return render_template('project/list.html')


@bp.before_request
def get_project_info():
    pid = request.view_args.get('pid')

    if not pid:
        return

    pid = int(pid)
    g.project = g.db.execute('SELECT * FROM project WHERE id = %s', [pid]).fetchone()

    if not g.project:
        abort(404)

@bp.get('/add_project')
def add_project():
    g.db.execute("INSERT INTO project (name) VALUES ('new project')")
    return redirect(url_for('index'))

@bp.get('/<pid>')
def detail(pid):
    g.crash_cnt = g.db.execute('SELECT COUNT(*) AS cnt FROM crash WHERE project_id = %s', [pid]).fetchone()['cnt']
    g.unclassified_cnt = g.db.execute('SELECT cache_unclassified_cnt AS cnt FROM project WHERE id = %s', [pid]).fetchone()['cnt']
    g.bug_list = g.db.execute('SELECT * FROM bug WHERE project_id = %s ORDER BY priority DESC, id', [pid]).fetchall()
    
    return render_template('project/detail.html')

@bp.route('/<pid>/edit', methods=['GET', 'POST'])
def edit(pid):
    if request.method == 'GET':
        return render_template('project/edit.html')
    
    g.db.execute(
        'UPDATE project SET name = %s, cve_product = %s, cve_version = %s, cve_vendor = %s, cve_credit = %s, cve_reference = %s WHERE id = %s', 
        [
            request.form.get('name'), 
            request.form.get('product'), 
            request.form.get('version'), 
            request.form.get('vendor'), 
            request.form.get('credit'), 
            request.form.get('reference'), 
            pid
        ]
    )


    return redirect(url_for('project.detail', pid=pid))

@bp.route('/<pid>/all_crash', methods=['GET', 'POST'])
def all_crashes(pid):
    if request.method == 'GET':
        g.crash_list = g.db.execute('SELECT * FROM crash WHERE project_id = %s ORDER BY id LIMIT 100', [pid]).fetchall()
        return render_template('project/all_crashes.html')

    f = request.files.get('file')

    temp_path = os.path.join(tempfile.gettempdir(), 'citrus-crash-load.db')
    f.save(temp_path)

    crash_db = sqlite3.connect(temp_path)

    crashes = crash_db.execute('SELECT filename, data, asan_report FROM info').fetchall()

    g.db.execute('DELETE FROM crash WHERE project_id = %s', [pid])
    g.db.commit()

    for x in range(len(crashes)):
        crashes[x] = list(crashes[x])
        crashes[x][2] = crashes[x][2].replace('\x00', '')
        crashes[x].append(get_trace(crashes[x][2]))

    with g.db.cursor() as cursor:
        cursor.executemany('INSERT INTO crash(project_id, origin_filename, data, asan_report, trace) VALUES ({}, %s, %s, %s, %s)'.format(pid), crashes)
    
    g.db.commit()

    crash_db.close()
    os.unlink(temp_path)

    update_all_cache(pid)

    return redirect(url_for('project.all_crashes', pid=pid))

@bp.get('/<pid>/add_bug')
def add_bug(pid):
    g.db.execute("INSERT INTO bug (project_id, title, crash_filter) VALUES (%s, 'untitled bug', '1=0')", [pid])
    return redirect(url_for('project.detail', pid=pid))

@bp.get('/<pid>/unclassified')
def unclassified_crashes(pid):
    sql = get_unclassified_condition(pid)

    g.crash_list = g.db.execute(f'SELECT * FROM crash WHERE {sql} ORDER BY id LIMIT 100').fetchall()
    return render_template('project/unclassified_crashes.html')


@bp.get('/<pid>/auto_classify')
def auto_classify(pid):
    trace_list = g.db.execute('SELECT DISTINCT trace FROM crash WHERE project_id = %s', [pid]).fetchall()

    for row in trace_list:
        trace = row['trace']

        if not trace:
            continue

        sql_condition = f"trace = '{trace}'"

        bid = g.db.execute('INSERT INTO bug (project_id, title, crash_filter) VALUES (%s, %s, %s) RETURNING id', [pid, trace, '1=0']).fetchone()['id']

        update_filter(pid, bid, sql_condition)
    
    update_unclassified_cache(pid)

    return redirect(url_for('project.detail', pid=pid))

@bp.get('/<pid>/debug_filter')
def debug_filter(pid):
    crash_filter = request.args.get('crash_filter')

    if crash_filter:
        try:
            g.page = request.args.get('page', 1, int)
            g.crash_list = g.db.execute(f"SELECT * FROM crash WHERE project_id = {pid} AND ({crash_filter}) ORDER BY trace DESC, asan_report DESC, origin_filename LIMIT 100 OFFSET {(g.page - 1)*100}").fetchall()
            g.trace_list = g.db.execute(f"SELECT DISTINCT ON (trace) trace, origin_filename FROM crash WHERE project_id = {pid} AND ({crash_filter}) ORDER BY trace DESC").fetchall()
            g.crash_cnt = g.db.execute(f"SELECT COUNT(*) AS cnt FROM crash WHERE project_id = {pid} AND ({crash_filter})").fetchone()['cnt']
            g.total_page = math.ceil(g.crash_cnt / 100)
        except Exception as e:
            flash(repr(e))

    return render_template('project/debug_filter.html')


@bp.get('/<pid>/jaccard_analyze')
def jaccard_analyze(pid):
    bug_list = g.db.execute('SELECT * FROM bug WHERE project_id = %s ORDER BY id', [pid]).fetchall()

    a = np.zeros([len(bug_list), len(bug_list)])

    for p1, x in enumerate(bug_list):
        for p2, y in enumerate(bug_list):
            a[p1, p2] = float(g.db.execute(f'''
SELECT (
    (SELECT COUNT(*) FROM crash WHERE project_id = {pid} AND ({x['crash_filter']}) AND ({y['crash_filter']}))::real
    /
    (SELECT COUNT(*) FROM crash WHERE project_id = {pid} AND (({x['crash_filter']}) OR ({y['crash_filter']})))::real
) as num
''').fetchone()['num'])

    sns.heatmap(a, cmap="Greys_r")
    
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'image/png'
    
    return response


@bp.get('/<pid>/cve')
def gen_cve(pid):
    bug_list = g.db.execute('SELECT * FROM bug WHERE project_id = %s AND priority > 0 ORDER BY priority DESC', [pid]).fetchall()

    bug_text = []
    case_list = []

    for idx, bug in enumerate(bug_list):
        idx += 1

        buf = []

        buf.append(f"### Vulnerability {idx}")

        buf.append(f"Vulnerability Type: {bug['cve_vulnerability_type']}")
        buf.append(f"Vendor:             {g.project['cve_vendor']}")
        buf.append(f"Affected product:   {g.project['cve_product']} {g.project['cve_version']}")
        buf.append('')
        buf.append(f"Attack type:        {bug['cve_attack_type']}")
        buf.append(f"Impact:             {bug['cve_impact']}")
        buf.append(f"Affected component: {bug['cve_affected_component']}")
        buf.append(f"Attack vector:      {bug['cve_attack_vector']}")
        buf.append('')
        buf.append(f"Description:        {bug['cve_description']}")
        
        buf.append(f"Discoverer:         {g.project['cve_credit']}")
        buf.append(f"Reference:          {g.project['cve_reference'] or bug['cve_reference']}")
        buf.append(f"Additional info:    {bug['cve_additional']}")

        buf.append('')
        buf.append(f"Trace:")

        trace_list = g.db.execute(f"SELECT DISTINCT ON (trace) trace, origin_filename FROM crash WHERE project_id = {pid} AND ({bug['crash_filter']}) ORDER BY trace DESC, origin_filename").fetchall()
        
        for t in trace_list:
            buf.append(f"  {t['origin_filename']}: {t['trace']}")
            case_list.append(t['origin_filename'])

        bug_text.append('\n'.join(buf))


    bug_text = '\n\n\n'.join(bug_text)

    buffer = io.BytesIO()

    zip = zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED)

    zip.writestr('description.txt', bug_text)

    for filename in case_list:
        row = g.db.execute('SELECT data, asan_report FROM crash WHERE origin_filename = %s', [filename]).fetchone()
        zip.writestr(f'files/{filename}', row['data'])
        zip.writestr(f'files/{filename}.asan_report', row['asan_report'])

    zip.close()

    buffer.seek(0)
    
    return send_file(buffer, download_name='cve.zip', max_age=0, as_attachment=True)

