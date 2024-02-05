from flask import Blueprint, render_template, g, request, abort, url_for, redirect
from util.db import update_filter, update_unclassified_cache
import math

bp = Blueprint('bug', __name__, url_prefix='/bug')


@bp.before_request
def get_bug_info():
    bid = request.view_args.get('bid')

    if not bid:
        return

    bid = int(bid)
    g.bug = g.db.execute('SELECT * FROM bug WHERE id = %s', [bid]).fetchone()

    if not g.bug:
        abort(404)

    g.project = g.db.execute('SELECT * FROM project WHERE id = %s', [g.bug['project_id']]).fetchone()


@bp.route('/<bid>', methods=['GET', 'POST'])
def detail(bid):
    if request.method == 'GET':
        g.page = request.args.get('page', 1, int)
        g.crash_list = g.db.execute(f"SELECT * FROM crash WHERE project_id = {g.project['id']} AND ({g.bug['crash_filter']}) ORDER BY trace DESC, asan_report DESC, origin_filename LIMIT 100")
        g.trace_list = g.db.execute(f"SELECT DISTINCT ON (trace) trace, origin_filename FROM crash WHERE project_id = {g.project['id']} AND ({g.bug['crash_filter']}) ORDER BY trace DESC, origin_filename").fetchall()
        g.crash_cnt = g.db.execute(f"SELECT COUNT(*) AS cnt FROM crash WHERE project_id = {g.project['id']} AND ({g.bug['crash_filter']})").fetchone()['cnt']
        g.total_page = math.ceil(g.crash_cnt / 100)        
        
        return render_template('bug/detail.html')
    
    update_filter(g.project['id'], bid, request.form['crash_filter'])
    update_unclassified_cache(g.project['id'])

    g.db.execute(
        'UPDATE bug SET title = %s WHERE id = %s', 
        [
            request.form['title'],
            bid
        ]
    )

    return redirect(url_for('bug.detail', bid=bid))

@bp.route('/<bid>/edit_cve', methods=['GET', 'POST'])
def edit_cve(bid):
    if request.method == 'GET':
        return render_template('bug/edit_cve.html')
    
    g.db.execute(
        'UPDATE bug SET priority = %s, cve_vulnerability_type = %s, cve_attack_type = %s, cve_impact = %s, cve_affected_component = %s, cve_attack_vector = %s, cve_description = %s, cve_reference = %s, cve_additional = %s WHERE id = %s', 
        [
            request.form['priority'],
            
            request.form['cve_vulnerability_type'],
            request.form['cve_attack_type'],
            request.form['cve_impact'],
            request.form['cve_affected_component'],
            request.form['cve_attack_vector'],
            request.form['cve_description'],
            request.form['cve_reference'],
            request.form['cve_additional'],
            bid
        ]
    )

    return redirect(url_for('bug.detail', bid=bid))

@bp.get('/<bid>/delete')
def delete_bug(bid):
    g.db.execute('DELETE FROM bug WHERE id = %s', [bid])
    update_unclassified_cache(g.project['id'])

    return redirect(url_for('project.detail', pid=g.project['id']))