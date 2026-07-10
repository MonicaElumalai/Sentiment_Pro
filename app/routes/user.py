"""app/routes/user.py — User dashboard, analyze, history, analytics, export, bulk"""
import json, csv, io, re
from datetime import datetime, timedelta
from functools import wraps
from flask import (Blueprint, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
from app.models.database import get_db
from app.utils.sentiment_engine import analyze as run_analysis, sanitize_aspects, POS_WORDS, NEG_WORDS, STOPS

user_bp = Blueprint('user', __name__)


def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user_id' not in session:
            flash('Please sign in to continue.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*a, **kw)
    return dec


# ── Dashboard ──────────────────────────────────────────────────────────────
@user_bp.route('/dashboard')
@login_required
def dashboard():
    db   = get_db(); uid = session['user_id']
    rows = db.execute('SELECT overall_sentiment FROM reviews WHERE user_id=?', (uid,)).fetchall()
    total  = len(rows)
    counts = {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0}
    for r in rows:
        counts[r['overall_sentiment']] = counts.get(r['overall_sentiment'], 0) + 1
    recent = db.execute(
        'SELECT * FROM reviews WHERE user_id=? ORDER BY created_at DESC LIMIT 5', (uid,)
    ).fetchall()
    return render_template('user/dashboard.html', total=total, counts=counts, recent=recent)


# ── Analyze (AJAX POST) ────────────────────────────────────────────────────
@user_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get('text') or '').strip()
    if not text:          return jsonify({'error': 'No text provided.'}), 400
    if len(text) > 5000:  return jsonify({'error': 'Text too long (max 5000 chars).'}), 400

    res   = run_analysis(text)
    sent  = 'mixed' if res['is_mixed'] else res['overall_sentiment']
    clean = sanitize_aspects(res['aspects'])

    db = get_db()
    db.execute(
        '''INSERT INTO reviews
           (user_id, review_text, overall_sentiment, overall_confidence,
            aspect_data, is_mixed, source)
           VALUES (?,?,?,?,?,?,?)''',
        (session['user_id'], text, sent,
         float(res['overall_confidence']),
         json.dumps(clean), int(bool(res['is_mixed'])), 'manual')
    )
    db.commit()

    return jsonify({
        'overall_sentiment':  sent,
        'overall_confidence': float(res['overall_confidence']),
        'is_mixed':           bool(res['is_mixed']),
        'distribution':       res['distribution'],
        'aspects':            clean,
        'is_multi_aspect':    len(clean) > 1,
    })


# ── Bulk CSV upload ────────────────────────────────────────────────────────
@user_bp.route('/bulk', methods=['POST'])
@login_required
def bulk():
    f = request.files.get('csv_file')
    if not f or not f.filename.lower().endswith('.csv'):
        flash('Please upload a valid CSV file.', 'warning')
        return redirect(url_for('user.dashboard'))
    try:
        import pandas as pd
        df = pd.read_csv(f)

        # Find the text column flexibly
        col = None
        for c in df.columns:
            if any(k in c.lower() for k in ('review', 'text', 'comment', 'feedback', 'content')):
                col = c; break
        if col is None:
            col = df.columns[0]   # fall back to first column

        db    = get_db()
        count = 0
        errors = 0
        for raw_text in df[col].dropna():
            text = str(raw_text).strip()
            if not text or len(text) > 5000:
                continue
            try:
                res   = run_analysis(text)
                sent  = 'mixed' if res['is_mixed'] else res['overall_sentiment']
                clean = sanitize_aspects(res['aspects'])
                db.execute(
                    '''INSERT INTO reviews
                       (user_id, review_text, overall_sentiment, overall_confidence,
                        aspect_data, is_mixed, source)
                       VALUES (?,?,?,?,?,?,?)''',
                    (session['user_id'], text, sent,
                     float(res['overall_confidence']),
                     json.dumps(clean), int(bool(res['is_mixed'])), 'bulk')
                )
                count += 1
            except Exception as row_err:
                errors += 1
                print(f'[BULK] Row error: {row_err}')
        db.commit()
        msg = f'✅ Bulk complete — {count} reviews analysed.'
        if errors:
            msg += f' ({errors} rows skipped due to errors)'
        flash(msg, 'success')
    except Exception as e:
        flash(f'Error processing CSV: {e}', 'danger')
    return redirect(url_for('user.history'))


# ── History ────────────────────────────────────────────────────────────────
@user_bp.route('/history')
@login_required
def history():
    db     = get_db(); uid = session['user_id']
    page   = max(1, request.args.get('page', 1, type=int))
    per    = 10
    search = request.args.get('q', '').strip()
    filt   = request.args.get('f', '')
    sort   = request.args.get('s', 'newest')

    q      = 'SELECT * FROM reviews WHERE user_id=?'; params = [uid]
    if search:
        q += ' AND review_text LIKE ?'; params.append(f'%{search}%')
    if filt in ('positive', 'negative', 'neutral', 'mixed'):
        q += ' AND overall_sentiment=?'; params.append(filt)

    total = db.execute(q.replace('SELECT *', 'SELECT COUNT(*)'), params).fetchone()[0]
    q    += f' ORDER BY created_at {"DESC" if sort != "oldest" else "ASC"} LIMIT ? OFFSET ?'
    params += [per, (page - 1) * per]
    reviews     = db.execute(q, params).fetchall()
    total_pages = max(1, (total + per - 1) // per)
    return render_template('user/history.html', reviews=reviews, page=page,
                           total_pages=total_pages, total=total,
                           search=search, filt=filt, sort=sort)


# ── Delete review ──────────────────────────────────────────────────────────
@user_bp.route('/delete/<int:rid>')
@login_required
def delete_review(rid):
    db = get_db()
    db.execute('DELETE FROM reviews WHERE id=? AND user_id=?', (rid, session['user_id']))
    db.commit()
    flash('Review deleted.', 'info')
    return redirect(request.referrer or url_for('user.history'))


# ── Analytics ──────────────────────────────────────────────────────────────
@user_bp.route('/analytics')
@login_required
def analytics():
    db   = get_db(); uid = session['user_id']
    rows = db.execute('SELECT overall_sentiment FROM reviews WHERE user_id=?', (uid,)).fetchall()
    counts = {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0}
    for r in rows:
        counts[r['overall_sentiment']] = counts.get(r['overall_sentiment'], 0) + 1
    trend = []
    for i in range(13, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        c   = db.execute(
            "SELECT COUNT(*) FROM reviews WHERE user_id=? AND DATE(created_at)=?",
            (uid, day)
        ).fetchone()[0]
        trend.append({'date': day, 'count': c})
    return render_template('user/analytics.html', counts=counts,
                           trend=json.dumps(trend), total=sum(counts.values()))


# ── Word cloud data ────────────────────────────────────────────────────────
@user_bp.route('/wordcloud-data')
@login_required
def wordcloud_data():
    db   = get_db(); uid = session['user_id']
    rows = db.execute(
        'SELECT review_text, overall_sentiment FROM reviews WHERE user_id=?', (uid,)
    ).fetchall()
    fp = {}; fn = {}
    for r in rows:
        words  = re.sub(r'[^a-z\s]', '', r['review_text'].lower()).split()
        bucket = fp if r['overall_sentiment'] == 'positive' else \
                 fn if r['overall_sentiment'] == 'negative' else None
        if bucket is not None:
            for w in words:
                if w not in STOPS and len(w) > 2:
                    bucket[w] = bucket.get(w, 0) + 1
    tp = sorted(fp.items(), key=lambda x: -x[1])[:40]
    tn = sorted(fn.items(), key=lambda x: -x[1])[:40]
    return jsonify({
        'positive': [{'text': w, 'size': c} for w, c in tp],
        'negative': [{'text': w, 'size': c} for w, c in tn],
    })


# ── Export CSV ─────────────────────────────────────────────────────────────
@user_bp.route('/export')
@login_required
def export():
    db   = get_db(); uid = session['user_id']
    rows = db.execute(
        '''SELECT review_text, overall_sentiment, overall_confidence,
                  is_mixed, aspect_data, source, created_at
           FROM reviews WHERE user_id=? ORDER BY created_at DESC''',
        (uid,)
    ).fetchall()

    out = io.StringIO()
    w   = csv.writer(out)
    w.writerow(['#', 'Review Text', 'Overall Sentiment', 'Confidence (%)',
                'Mixed', 'Aspects', 'Source', 'Date'])
    for i, r in enumerate(rows, 1):
        # Build aspects summary string
        try:
            asp_list = json.loads(r['aspect_data'] or '[]')
            asp_str  = ' | '.join(
                f"{a['aspect'].upper()}:{a['sentiment']}"
                for a in asp_list
            )
        except Exception:
            asp_str = ''
        w.writerow([
            i, r['review_text'], r['overall_sentiment'],
            r['overall_confidence'], 'Yes' if r['is_mixed'] else 'No',
            asp_str, r['source'], r['created_at'][:16]
        ])
    out.seek(0)
    return send_file(
        io.BytesIO(out.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='sentimentpro_history.csv'
    )
