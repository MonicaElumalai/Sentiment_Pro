"""app/routes/admin.py — Admin dashboard, users, reviews management"""
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify)
from app.models.database import get_db

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if not session.get('is_admin'):
            flash('Admin access required.','danger')
            return redirect(url_for('auth.admin_login'))
        return f(*a, **kw)
    return dec


@admin_bp.route('/admin')
@admin_required
def dashboard():
    db = get_db()
    total_users   = db.execute("SELECT COUNT(*) FROM users WHERE is_admin=0").fetchone()[0]
    total_reviews = db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    counts = {'positive':0,'negative':0,'neutral':0,'mixed':0}
    for r in db.execute("SELECT overall_sentiment,COUNT(*) c FROM reviews GROUP BY overall_sentiment").fetchall():
        counts[r['overall_sentiment']] = r['c']
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = db.execute("SELECT COUNT(*) FROM reviews WHERE DATE(created_at)=?",(today,)).fetchone()[0]
    recent_users = db.execute(
        "SELECT * FROM users WHERE is_admin=0 ORDER BY created_at DESC LIMIT 8").fetchall()
    recent_reviews = db.execute(
        "SELECT r.*,u.username,u.avatar_color FROM reviews r JOIN users u ON r.user_id=u.id ORDER BY r.created_at DESC LIMIT 10").fetchall()
    trend = []
    for i in range(13,-1,-1):
        day = (datetime.now()-timedelta(days=i)).strftime('%Y-%m-%d')
        c   = db.execute("SELECT COUNT(*) FROM reviews WHERE DATE(created_at)=?",(day,)).fetchone()[0]
        trend.append({'date':day,'count':c})
    return render_template('admin/dashboard.html', total_users=total_users,
        total_reviews=total_reviews, counts=counts, today_count=today_count,
        recent_users=recent_users, recent_reviews=recent_reviews,
        trend=json.dumps(trend))


@admin_bp.route('/admin/users')
@admin_required
def users():
    db     = get_db()
    search = request.args.get('q','').strip()
    page   = max(1,request.args.get('page',1,type=int)); per = 12
    q = "SELECT u.*,(SELECT COUNT(*) FROM reviews r WHERE r.user_id=u.id) review_count FROM users u WHERE u.is_admin=0"
    params = []
    if search:
        q += ' AND (u.username LIKE ? OR u.email LIKE ?)'; params += [f'%{search}%']*2
    all_rows    = db.execute(q, params).fetchall()
    total       = len(all_rows)
    total_pages = max(1,(total+per-1)//per)
    users_list  = all_rows[(page-1)*per : page*per]
    return render_template('admin/users.html', users=users_list, page=page,
                           total_pages=total_pages, total=total, search=search)


@admin_bp.route('/admin/reviews')
@admin_required
def reviews():
    db     = get_db()
    page   = max(1,request.args.get('page',1,type=int)); per = 15
    uid    = request.args.get('uid','')
    filt   = request.args.get('f','')
    search = request.args.get('q','').strip()
    q      = "SELECT r.*,u.username,u.avatar_color FROM reviews r JOIN users u ON r.user_id=u.id WHERE 1=1"
    params = []
    if uid:    q += ' AND r.user_id=?'; params.append(uid)
    if filt in ('positive','negative','neutral','mixed'):
        q += ' AND r.overall_sentiment=?'; params.append(filt)
    if search: q += ' AND r.review_text LIKE ?'; params.append(f'%{search}%')
    total = db.execute(q.replace('SELECT r.*,u.username,u.avatar_color','SELECT COUNT(*)'), params).fetchone()[0]
    q    += ' ORDER BY r.created_at DESC LIMIT ? OFFSET ?'; params += [per,(page-1)*per]
    reviews_list = db.execute(q, params).fetchall()
    total_pages  = max(1,(total+per-1)//per)
    all_users    = db.execute("SELECT id,username FROM users WHERE is_admin=0 ORDER BY username").fetchall()
    return render_template('admin/reviews.html', reviews=reviews_list, page=page,
                           total_pages=total_pages, total=total, uid=uid,
                           filt=filt, search=search, all_users=all_users)


@admin_bp.route('/admin/delete-review/<int:rid>')
@admin_required
def delete_review(rid):
    db = get_db(); db.execute('DELETE FROM reviews WHERE id=?',(rid,)); db.commit()
    flash('Review deleted.','info')
    return redirect(request.referrer or url_for('admin.reviews'))


@admin_bp.route('/admin/delete-user/<int:uid>')
@admin_required
def delete_user(uid):
    db = get_db()
    db.execute('DELETE FROM reviews WHERE user_id=?',(uid,))
    db.execute('DELETE FROM users WHERE id=? AND is_admin=0',(uid,))
    db.commit(); flash('User deleted.','info')
    return redirect(url_for('admin.users'))
