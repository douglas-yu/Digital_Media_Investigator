#!/usr/bin/env python3
"""
PixelForce Analyze v3.0 — Griffeye-inspired digital media analysis platform
"""

import sys, os, json, csv, hashlib, datetime, threading, sqlite3
from typing import Optional, List

import cv2
import imagehash
import exifread
from PIL import Image as PILImage

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QProgressBar, QStatusBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QCheckBox,
    QFileDialog, QMessageBox, QDialog, QTextEdit,
    QGroupBox, QGridLayout, QFrame, QAbstractItemView, QMenu, QToolBar,
    QSpinBox, QFormLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QImage, QIcon, QColor, QFont, QPainter, QPen

# ─── Palette ─────────────────────────────────────────────────────────────────
BG0  = "#0b0f14"
BG1  = "#0d1117"
BG2  = "#161b22"
BG3  = "#21262d"
BRD  = "#30363d"
FG0  = "#c9d1d9"
FG1  = "#c9d1d9" #"#8b949e"
ACC  = "#1f6feb"
ACC2 = "#388bfd"
WARN = "#e3b341"
ERR  = "#f85149"
OK   = "#3fb950"
SEARCH_BG   = "#0e1620"
SEARCH_BORD = "#1c3a5e"

APP_NAME    = "PixelForce Analyze"
APP_VERSION = "3.0.0"
DB_PATH     = os.path.expanduser("~/.pixelforce/evidence.db")
SUPPORTED_EXT = {'.jpg','.jpeg','.png','.bmp','.gif','.tiff','.tif','.webp','.heic','.raw','.cr2','.nef'}

CATEGORY_COLORS = {
    "Uncategorized":      "#607D8B",
    "Evidence":           "#F44336",
    "Flagged":            "#FF9800",
    "Reviewed":           "#4CAF50",
    "Irrelevant":         "#9E9E9E",
    "CSAM Hit":           "#B71C1C",
    "Hash Match":         "#880E4F",
    "Person of Interest": "#1565C0",
}

DARK_STYLE = f"""
* {{ font-size: 12px; font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }}
QMainWindow, QDialog {{ background:{BG1}; color:{FG0}; }}
QWidget {{ background:{BG1}; color:{FG0}; }}
QMenuBar {{ background:{BG2}; color:{FG0}; border-bottom:1px solid {BRD}; font-size:12px; }}
QMenuBar::item:selected {{ background:{ACC}; }}
QMenu {{ background:{BG2}; color:{FG0}; border:1px solid {BRD}; font-size:12px; }}
QMenu::item {{ padding:6px 20px; }}
QMenu::item:selected {{ background:{ACC}; }}
QMenu::separator {{ height:1px; background:{BRD}; margin:4px 0; }}
QToolBar {{ background:{BG2}; border-bottom:2px solid {BRD}; spacing:3px; padding:3px 6px; }}
QToolBar QPushButton {{ background:transparent; border:1px solid transparent; border-radius:5px; padding:5px 12px; color:{FG0}; font-size:12px; }}
QToolBar QPushButton:hover {{ background:{BG3}; border-color:{BRD}; }}
QToolBar QPushButton:pressed {{ background:{ACC}; }}
QWidget#searchPanel {{ background:{SEARCH_BG}; border-bottom:2px solid {SEARCH_BORD}; min-height:100px; max-height:100px; }}
QWidget#searchPanel QLabel {{ color:{FG1}; font-size:12px; font-weight:bold; letter-spacing:1px; }}
QWidget#searchPanel QLineEdit {{ background:#0d1a2a; border:1px solid {SEARCH_BORD}; border-radius:6px; padding:6px 12px; color:{FG0}; font-size:13px; min-height:28px; }}
QWidget#searchPanel QLineEdit:focus {{ border-color:{ACC}; }}
QWidget#searchPanel QComboBox {{ background:#0d1a2a; border:1px solid {SEARCH_BORD}; border-radius:6px; padding:5px 10px; color:{FG0}; font-size:13px; min-height:28px; }}
QWidget#searchPanel QPushButton {{ background:{ACC}; border:none; border-radius:5px; padding:5px 14px; color:white; font-size:12px; font-weight:bold; }}
QWidget#searchPanel QPushButton:hover {{ background:{ACC2}; }}
QWidget#searchPanel QPushButton#btnSearchFace {{ background:#5a1f6f; border:1px solid #7b3fa0; }}
QWidget#searchPanel QPushButton#btnSearchFace:hover {{ background:#7b3fa0; }}
QWidget#searchPanel QCheckBox {{ color:{FG0}; font-size:12px; spacing:6px; }}
QSplitter::handle {{ background:{BRD}; }}
QSplitter::handle:horizontal {{ width:1px; }}
QSplitter::handle:vertical {{ height:1px; }}
QTreeWidget {{ background:{BG2}; border:none; color:{FG0}; outline:none; font-size:14px; }}
QTreeWidget::item {{ padding:3px 6px; border-radius:3px; margin:0px 2px; font-size:14px; }}
QTreeWidget::item:selected {{ background:{ACC}; color:white; }}
QTreeWidget::item:hover:!selected {{ background:{BG3}; }}
QTreeWidget::branch {{ background:{BG2}; }}
QListWidget {{ background:{BG1}; border:none; color:{FG0}; font-size:12px; }}
QListWidget::item {{ padding:4px; border-radius:4px; font-size:11px; }}
QListWidget::item:selected {{ background:{ACC}; }}
QListWidget::item:hover {{ background:{BG3}; }}
QTableWidget {{ background:{BG1}; border:none; color:{FG0}; gridline-color:{BG3}; alternate-background-color:{BG2}; font-size:12px; }}
QTableWidget::item {{ padding:5px 8px; font-size:12px; }}
QTableWidget::item:selected {{ background:{ACC}; }}
QHeaderView::section {{ background:{BG2}; color:{FG0}; padding:6px 10px; border:none; border-right:1px solid {BRD}; border-bottom:2px solid {BRD}; font-weight:bold; font-size:11px; letter-spacing:1px; }}
QPushButton {{ background:{BG3}; color:{FG0}; border:1px solid {BRD}; border-radius:6px; padding:6px 16px; font-size:12px; }}
QPushButton:hover {{ background:{BRD}; border-color:{FG0}; }}
QPushButton:pressed {{ background:{ACC}; border-color:{ACC}; }}
QPushButton#btnPrimary {{ background:{ACC}; border-color:{ACC}; color:white; font-weight:bold; }}
QPushButton#btnPrimary:hover {{ background:{ACC2}; }}
QPushButton#btnSuccess {{ background:#1a4731; border-color:{OK}; color:{OK}; }}
QPushButton#btnSuccess:hover {{ background:#2a6a47; }}
QPushButton#btnDanger {{ background:#3d1212; border-color:#da3633; color:{ERR}; }}
QPushButton#btnDanger:hover {{ background:#5a1a1a; }}
QPushButton#btnWarning {{ background:#3d2800; border-color:{WARN}; color:{WARN}; }}
QLineEdit, QSpinBox {{ background:{BG0}; border:1px solid {BRD}; border-radius:6px; padding:5px 10px; color:{FG0}; font-size:12px; selection-background-color:{ACC}; }}
QLineEdit:focus, QSpinBox:focus {{ border-color:{ACC}; }}
QComboBox {{ background:{BG0}; border:1px solid {BRD}; border-radius:6px; padding:5px 10px; color:{FG0}; font-size:12px; min-height:28px; }}
QComboBox:focus {{ border-color:{ACC}; }}
QComboBox::drop-down {{ border:none; width:20px; }}
QComboBox::down-arrow {{ border-left:4px solid transparent; border-right:4px solid transparent; border-top:6px solid {FG1}; margin-right:6px; }}
QComboBox QAbstractItemView {{ background:{BG2}; border:1px solid {BRD}; selection-background-color:{ACC}; font-size:12px; }}
QTabWidget::pane {{ border:1px solid {BRD}; background:{BG1}; }}
QTabBar::tab {{ background:{BG2}; color:{FG1}; padding:8px 18px; border:1px solid {BRD}; border-bottom:none; margin-right:2px; font-size:12px; }}
QTabBar::tab:selected {{ background:{BG1}; color:{FG0}; border-bottom:2px solid {ACC}; }}
QTabBar::tab:hover:!selected {{ background:{BG3}; color:{FG0}; }}
QProgressBar {{ background:{BG3}; border:none; border-radius:4px; height:8px; color:transparent; }}
QProgressBar::chunk {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {ACC},stop:1 {ACC2}); border-radius:4px; }}
QStatusBar {{ background:{BG2}; color:{FG1}; border-top:1px solid {BRD}; font-size:11px; }}
QGroupBox {{ border:1px solid {BRD}; border-radius:6px; margin-top:18px; padding-top:10px; color:{FG1}; font-size:11px; letter-spacing:1px; font-weight:bold; }}
QGroupBox::title {{ subcontrol-origin:margin; subcontrol-position:top left; left:10px; top:12px; padding:0 6px; background:{BG1}; }}
QScrollBar:vertical {{ background:{BG1}; width:8px; border:none; }}
QScrollBar::handle:vertical {{ background:{BRD}; border-radius:4px; min-height:20px; }}
QScrollBar::handle:vertical:hover {{ background:{FG1}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{BG1}; height:8px; border:none; }}
QScrollBar::handle:horizontal {{ background:{BRD}; border-radius:4px; min-width:20px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}
QTextEdit {{ background:{BG0}; border:1px solid {BRD}; color:{FG0}; font-family:'Courier New',monospace; font-size:11px; }}
QCheckBox {{ spacing:8px; color:{FG0}; font-size:12px; }}
QCheckBox::indicator {{ width:14px; height:14px; border:1px solid {BRD}; border-radius:3px; background:{BG0}; }}
QCheckBox::indicator:checked {{ background:{ACC}; border-color:{ACC}; }}
QLabel {{ color:{FG0}; font-size:12px; }}
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color:{BRD}; }}
"""

# ─── Database ────────────────────────────────────────────────────────────────
class Database:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self._init()

    def _init(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT DEFAULT '',
                    investigator TEXT DEFAULT '',
                    case_number TEXT DEFAULT '',
                    created_at TEXT,
                    status TEXT DEFAULT 'active'
                );
                CREATE TABLE IF NOT EXISTS media (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER DEFAULT 1,
                    filepath TEXT UNIQUE NOT NULL,
                    filename TEXT, size INTEGER,
                    width INTEGER, height INTEGER,
                    md5 TEXT, sha256 TEXT, phash TEXT, dhash TEXT, whash TEXT,
                    mime_type TEXT, category TEXT DEFAULT 'Uncategorized',
                    face_count INTEGER DEFAULT 0,
                    object_tags TEXT DEFAULT '[]', custom_tags TEXT DEFAULT '[]',
                    csam_flag INTEGER DEFAULT 0, hash_match TEXT DEFAULT NULL,
                    notes TEXT DEFAULT '', imported_at TEXT, exif_data TEXT DEFAULT '{}',
                    FOREIGN KEY(case_id) REFERENCES cases(id)
                );
                CREATE TABLE IF NOT EXISTS reference_db (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    db_name TEXT NOT NULL, hash_value TEXT NOT NULL,
                    hash_type TEXT NOT NULL, label TEXT DEFAULT '',
                    severity TEXT DEFAULT 'medium', added_at TEXT,
                    UNIQUE(db_name, hash_value)
                );
                CREATE INDEX IF NOT EXISTS idx_md5    ON media(md5);
                CREATE INDEX IF NOT EXISTS idx_sha256 ON media(sha256);
                CREATE INDEX IF NOT EXISTS idx_phash  ON media(phash);
                CREATE INDEX IF NOT EXISTS idx_cat    ON media(category);
                CREATE INDEX IF NOT EXISTS idx_case   ON media(case_id);
                CREATE INDEX IF NOT EXISTS idx_refhsh ON reference_db(hash_value);
            """)
            self.conn.execute(
                "INSERT OR IGNORE INTO cases (id,name,created_at,status) VALUES (1,'Default Case',?,'active')",
                (datetime.datetime.now().isoformat(),))
            self.conn.commit()

    # Cases
    def get_cases(self):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT id,name,description,investigator,case_number,created_at,status FROM cases ORDER BY id")
            cols = [d[0] for d in c.description]
            return [dict(zip(cols,r)) for r in c.fetchall()]

    def create_case(self, name, desc="", investigator="", case_number=""):
        with self.lock:
            c = self.conn.cursor()
            c.execute("INSERT INTO cases (name,description,investigator,case_number,created_at) VALUES (?,?,?,?,?)",
                      (name,desc,investigator,case_number,datetime.datetime.now().isoformat()))
            self.conn.commit(); return c.lastrowid

    def delete_case(self, cid):
        with self.lock:
            self.conn.execute("DELETE FROM media WHERE case_id=?",(cid,))
            self.conn.execute("DELETE FROM cases WHERE id=?",(cid,))
            self.conn.commit()

    # Media
    def insert_media(self, data):
        with self.lock:
            cols = ','.join(data.keys()); ph = ','.join(['?']*len(data))
            c = self.conn.cursor()
            c.execute(f"INSERT OR REPLACE INTO media ({cols}) VALUES ({ph})", list(data.values()))
            self.conn.commit(); return c.lastrowid

    def update_media(self, mid, data):
        with self.lock:
            sc = ','.join([f"{k}=?" for k in data])
            self.conn.execute(f"UPDATE media SET {sc} WHERE id=?", list(data.values())+[mid])
            self.conn.commit()

    def get_all_media(self, filters=None):
        with self.lock:
            q = "SELECT * FROM media"; params = []
            if filters:
                conds = []
                if filters.get('case_id'): conds.append("case_id=?"); params.append(filters['case_id'])
                if filters.get('category') and filters['category']!='All':
                    conds.append("category=?"); params.append(filters['category'])
                if filters.get('search'):
                    conds.append("(filename LIKE ? OR notes LIKE ? OR object_tags LIKE ? OR custom_tags LIKE ?)")
                    s=f"%{filters['search']}%"; params.extend([s,s,s,s])
                if filters.get('face_only'): conds.append("face_count>0")
                if filters.get('flagged_only'): conds.append("(csam_flag=1 OR hash_match IS NOT NULL)")
                if filters.get('custom_tag'):
                    conds.append("custom_tags LIKE ?")
                    params.append(f'%"{filters["custom_tag"]}"%')
                if filters.get('tagged_any'):
                    conds.append("custom_tags != '[]' AND custom_tags IS NOT NULL")
                if conds: q += " WHERE " + " AND ".join(conds)
            q += " ORDER BY imported_at DESC"
            c = self.conn.cursor(); c.execute(q,params)
            cols = [d[0] for d in c.description]
            return [dict(zip(cols,r)) for r in c.fetchall()]

    def get_media_by_id(self, mid):
        with self.lock:
            c = self.conn.cursor(); c.execute("SELECT * FROM media WHERE id=?",(mid,))
            row = c.fetchone()
            if row:
                cols = [d[0] for d in c.description]; return dict(zip(cols,row))

    def delete_media(self, mid):
        with self.lock:
            self.conn.execute("DELETE FROM media WHERE id=?",(mid,)); self.conn.commit()

    def get_selected_media(self, ids):
        with self.lock:
            ph = ','.join(['?']*len(ids)); c = self.conn.cursor()
            c.execute(f"SELECT * FROM media WHERE id IN ({ph})", ids)
            cols = [d[0] for d in c.description]
            return [dict(zip(cols,r)) for r in c.fetchall()]

    def get_all_custom_tags(self, case_id=None):
        """Return list of (tag, count) sorted by frequency for all tags in case."""
        with self.lock:
            c = self.conn.cursor()
            if case_id:
                c.execute("SELECT custom_tags FROM media WHERE case_id=? AND custom_tags != '[]'", (case_id,))
            else:
                c.execute("SELECT custom_tags FROM media WHERE custom_tags != '[]'")
            counts = {}
            for (raw,) in c.fetchall():
                try:
                    for t in json.loads(raw):
                        counts[t] = counts.get(t, 0) + 1
                except: pass
            return sorted(counts.items(), key=lambda x: (-x[1], x[0]))

    # Reference DB
    def add_ref_hash(self, db_name, hval, htype, label="", severity="medium"):
        with self.lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO reference_db (db_name,hash_value,hash_type,label,severity,added_at) VALUES (?,?,?,?,?,?)",
                (db_name,hval,htype,label,severity,datetime.datetime.now().isoformat()))
            self.conn.commit()

    def check_ref(self, hval, htype):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT * FROM reference_db WHERE hash_value=? AND hash_type=?",(hval,htype))
            row = c.fetchone()
            if row:
                cols = [d[0] for d in c.description]; return dict(zip(cols,row))

    def get_ref_dbs(self):
        with self.lock:
            c = self.conn.cursor()
            c.execute("SELECT db_name, COUNT(*) as count, MIN(added_at) as added FROM reference_db GROUP BY db_name")
            cols = [d[0] for d in c.description]
            return [dict(zip(cols,r)) for r in c.fetchall()]

    def create_hash_db_from_ids(self, ids, db_name, htype="md5"):
        rows = self.get_selected_media(ids); count = 0
        for m in rows:
            hv = m.get(htype)
            if hv: self.add_ref_hash(db_name, hv, htype, m['filename'], "custom"); count+=1
        return count

    def get_stats(self, case_id=None):
        with self.lock:
            c = self.conn.cursor()
            w = "WHERE case_id=?" if case_id else ""; a = (case_id,) if case_id else ()
            def q(sql, args=()): c.execute(sql,args); return c.fetchone()[0]
            aw = lambda extra: f"{w}{' AND ' if w else 'WHERE '}{extra}"
            return {
                'total':      q(f"SELECT COUNT(*) FROM media {w}", a),
                'flagged':    q(f"SELECT COUNT(*) FROM media {aw('(csam_flag=1 OR hash_match IS NOT NULL)')}", a),
                'with_faces': q(f"SELECT COUNT(*) FROM media {aw('face_count>0')}", a),
                'ref_hashes': q("SELECT COUNT(*) FROM reference_db"),
                'cases':      q("SELECT COUNT(*) FROM cases"),
                'by_category': dict(c.execute(f"SELECT category,COUNT(*) FROM media {w} GROUP BY category", a).fetchall()),
            }

    def export_csv(self, filepath, filters=None):
        rows = self.get_all_media(filters)
        if not rows: return 0
        with open(filepath,'w',newline='',encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
        return len(rows)

    def export_html(self, filepath, case, filters=None):
        rows = self.get_all_media(filters)
        stats = self.get_stats(filters.get('case_id') if filters else None)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trs = ""
        for r in rows[:500]:
            bg = "#2a0808" if r.get('csam_flag') else ("#1a0e1a" if r.get('hash_match') else "")
            col = CATEGORY_COLORS.get(r.get('category',''),'#607D8B')
            tags = ', '.join(json.loads(r.get('object_tags') or '[]'))
            ctags = ', '.join(json.loads(r.get('custom_tags') or '[]'))
            trs += f'<tr style="background:{bg}"><td>{r["filename"]}</td><td style="color:{col}">{r.get("category","")}</td><td>{r.get("face_count",0)}</td><td>{tags}</td><td>{ctags}</td><td style="color:{"#f85149" if r.get("hash_match") else "#8b949e"}">{r.get("hash_match") or "—"}</td><td>{"⚠ YES" if r.get("csam_flag") else "No"}</td><td>{(r.get("imported_at") or "")[:16]}</td></tr>'
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{APP_NAME} Report</title>
<style>body{{margin:0;padding:24px;background:#0d1117;color:#c9d1d9;font-family:'Segoe UI',Arial,sans-serif;font-size:13px}}
h1{{color:#1f6feb;border-bottom:2px solid #21262d;padding-bottom:8px}}
h2{{color:#8b949e;font-size:11px;letter-spacing:2px;text-transform:uppercase;margin-top:24px}}
.cards{{display:flex;gap:16px;flex-wrap:wrap;margin:16px 0}}
.card{{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:16px 24px;border-top:3px solid}}
.card .val{{font-size:28px;font-weight:bold}}.card .lbl{{font-size:11px;color:#8b949e;letter-spacing:1px}}
table{{width:100%;border-collapse:collapse;margin-top:8px}}
th{{background:#161b22;color:#8b949e;padding:8px 12px;text-align:left;font-size:11px;letter-spacing:1px;border-bottom:2px solid #21262d}}
td{{padding:7px 12px;border-bottom:1px solid #21262d;font-size:12px}}tr:hover td{{background:#161b22}}
</style></head><body>
<h1>🔍 {APP_NAME} — Evidence Report</h1>
<p style="color:#8b949e">Case: <b>{case.get('name','')}</b> | Investigator: {case.get('investigator','—')} | Case No: {case.get('case_number','—')} | Generated: {now}</p>
<h2>Summary</h2><div class="cards">
<div class="card" style="border-top-color:#1f6feb"><div class="val" style="color:#1f6feb">{stats['total']}</div><div class="lbl">TOTAL</div></div>
<div class="card" style="border-top-color:#f85149"><div class="val" style="color:#f85149">{stats['flagged']}</div><div class="lbl">FLAGGED</div></div>
<div class="card" style="border-top-color:#3fb950"><div class="val" style="color:#3fb950">{stats['with_faces']}</div><div class="lbl">FACES</div></div>
</div>
<h2>Media ({len(rows)} records{', first 500 shown' if len(rows)>500 else ''})</h2>
<table><tr><th>Filename</th><th>Category</th><th>Faces</th><th>Object Tags</th><th>Custom Tags</th><th>Hash Match</th><th>CSAM</th><th>Imported</th></tr>
{trs}</table></body></html>"""
        with open(filepath,'w',encoding='utf-8') as f: f.write(html)
        return len(rows)


# ─── Analysis Engine ─────────────────────────────────────────────────────────
class AnalysisEngine:
    FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    @staticmethod
    def hashes(fp):
        r = dict(md5=None,sha256=None,phash=None,dhash=None,whash=None)
        try:
            data = open(fp,'rb').read()
            r['md5']    = hashlib.md5(data).hexdigest()
            r['sha256'] = hashlib.sha256(data).hexdigest()
        except: pass
        try:
            img = PILImage.open(fp).convert('RGB')
            r['phash'] = str(imagehash.phash(img))
            r['dhash'] = str(imagehash.dhash(img))
            r['whash'] = str(imagehash.whash(img))
        except: pass
        return r

    @staticmethod
    def detect_faces(fp):
        try:
            img = cv2.imread(fp)
            if img is None: return 0
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            return len(AnalysisEngine.FACE_CASCADE.detectMultiScale(gray,1.1,5,minSize=(30,30)))
        except: return 0

    @staticmethod
    def detect_faces_annotated(fp):
        try:
            img = cv2.imread(fp)
            if img is None: return None
            gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = AnalysisEngine.FACE_CASCADE.detectMultiScale(gray,1.1,5,minSize=(30,30))
            for i,(x,y,w,h) in enumerate(faces):
                cv2.rectangle(img,(x,y),(x+w,y+h),(31,111,235),2)
                cv2.putText(img,f"FACE {i+1}",(x,y-8),cv2.FONT_HERSHEY_SIMPLEX,0.45,(31,111,235),1)
            rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB); h2,w2,ch=rgb.shape
            return QPixmap.fromImage(QImage(rgb.data,w2,h2,ch*w2,QImage.Format_RGB888))
        except: return None

    # ── Additional cascades ──────────────────────────────────────────────────
    BODY_CASCADE   = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
    UPPER_CASCADE  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_upperbody.xml')
    LOWER_CASCADE  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_lowerbody.xml')
    PROFILE_CASCADE= cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
    CAT_CASCADE    = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalcatface_extended.xml')
    EYE_CASCADE    = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    SMILE_CASCADE  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')
    PLATE_CASCADE  = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_license_plate_rus_16stages.xml')

    @staticmethod
    def _detect(cascade, gray, scale=1.1, neighbors=4, min_sz=(30,30)):
        try:
            r = cascade.detectMultiScale(gray, scale, neighbors, minSize=min_sz)
            return r if len(r) > 0 else []
        except: return []

    @staticmethod
    def classify(fp):
        """
        Enhanced object/scene/content classification returning structured tags.
        Categories: composition, lighting, faces/people, gender hints, nudity signals,
        animals, vehicles, weapons, environment, content warnings.
        """
        tags = []
        try:
            img = cv2.imread(fp)
            if img is None: return tags
            h, w = img.shape[:2]
            if h == 0 or w == 0: return tags

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            asp  = w / h

            # ── Composition ────────────────────────────────────────────────
            if asp > 1.6:   tags.append("landscape")
            elif asp < 0.65: tags.append("portrait orientation")
            else:            tags.append("square")

            mpx = (w * h) / 1_000_000
            if mpx < 0.1:  tags.append("low resolution")
            elif mpx > 8:  tags.append("high resolution")

            # ── Lighting / quality ─────────────────────────────────────────
            br  = gray.mean()
            std = gray.std()
            blr = cv2.Laplacian(gray, cv2.CV_64F).var()
            if br < 45:   tags.append("very dark")
            elif br < 80: tags.append("dark")
            elif br > 210: tags.append("overexposed")
            elif br > 170: tags.append("bright")
            if std < 20:  tags.append("low contrast")
            if blr < 25:  tags.append("blurry")
            elif blr > 2000: tags.append("sharp")

            # ── Face & person detection ────────────────────────────────────
            faces    = AnalysisEngine._detect(AnalysisEngine.FACE_CASCADE,  gray, 1.1, 5, (30,30))
            profiles = AnalysisEngine._detect(AnalysisEngine.PROFILE_CASCADE,gray, 1.1, 4, (30,30))
            bodies   = AnalysisEngine._detect(AnalysisEngine.BODY_CASCADE,  gray, 1.1, 3, (60,60))
            upper    = AnalysisEngine._detect(AnalysisEngine.UPPER_CASCADE, gray, 1.1, 3, (50,50))
            lower    = AnalysisEngine._detect(AnalysisEngine.LOWER_CASCADE, gray, 1.1, 3, (30,30))
            eyes     = AnalysisEngine._detect(AnalysisEngine.EYE_CASCADE,   gray, 1.1, 5, (15,15))

            n_faces = len(faces)
            n_prof  = len(profiles)
            n_body  = len(bodies)
            n_upper = len(upper)

            if n_faces == 1:      tags.append("1 face")
            elif n_faces == 2:    tags.append("2 faces")
            elif 3 <= n_faces <= 5: tags.append(f"{n_faces} faces")
            elif n_faces > 5:     tags.append("crowd/group")

            if n_prof > 0 and n_faces == 0: tags.append("profile face")
            if n_body > 0: tags.append("full body visible")
            if n_upper > 0 and n_body == 0: tags.append("upper body")
            if len(lower) > 0 and n_body == 0: tags.append("lower body")

            # Smile / expression
            if n_faces > 0:
                smiles = AnalysisEngine._detect(AnalysisEngine.SMILE_CASCADE, gray, 1.7, 22, (25,25))
                if len(smiles) > 0: tags.append("smiling")

            # ── Skin tone & nudity signals ─────────────────────────────────
            # Skin in YCrCb — more robust than HSV alone
            ycrcb     = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
            skin_mask = cv2.inRange(ycrcb, (0,133,77), (255,173,127))
            # Combine with HSV skin
            hsv_skin  = cv2.inRange(hsv, (0,20,50), (25,255,255))
            skin_combined = cv2.bitwise_or(skin_mask, hsv_skin)
            total_px  = h * w
            skin_ratio = cv2.countNonZero(skin_combined) / total_px

            if skin_ratio > 0.55:
                tags.append("⚠ high skin exposure")
                tags.append("nudity signal")
            elif skin_ratio > 0.30:
                tags.append("significant skin visible")
            elif skin_ratio > 0.12:
                tags.append("skin tones")

            # ── Gender estimation (heuristic — hair + face region analysis) ─
            if n_faces > 0:
                gender_hints = []
                for (fx, fy, fw, fh) in (faces if len(faces) <= 4 else faces[:4]):
                    # Hair region above face
                    hair_y1 = max(0, fy - int(fh * 0.8))
                    hair_y2 = fy
                    hair_x1 = max(0, fx - int(fw * 0.3))
                    hair_x2 = min(w, fx + fw + int(fw * 0.3))
                    if hair_y2 > hair_y1 and hair_x2 > hair_x1:
                        hair_roi = gray[hair_y1:hair_y2, hair_x1:hair_x2]
                        hair_std  = hair_roi.std() if hair_roi.size > 0 else 0
                        hair_mean = hair_roi.mean() if hair_roi.size > 0 else 0
                        # Longer hair → more edge complexity above head
                        hair_edges = cv2.Canny(hair_roi, 30, 100) if hair_roi.size > 0 else None
                        hair_edge_density = hair_edges.mean() if hair_edges is not None else 0

                    # Face aspect: female faces tend to be slightly rounder
                    face_crop = gray[fy:fy+fh, fx:fx+fw]
                    face_skin = cv2.countNonZero(skin_combined[fy:fy+fh, fx:fx+fw])
                    face_skin_ratio = face_skin / (fw * fh) if fw*fh > 0 else 0

                    # Very rough heuristic — flag as uncertain
                    if hair_edge_density > 8 or (hair_std > 35 and hair_mean < 120):
                        gender_hints.append("female")
                    else:
                        gender_hints.append("male")

                if gender_hints:
                    female_ct = gender_hints.count("female")
                    male_ct   = gender_hints.count("male")
                    if female_ct > male_ct:
                        tags.append("female subject(s)")
                    elif male_ct > female_ct:
                        tags.append("male subject(s)")
                    else:
                        tags.append("mixed gender")

            # ── Animal detection ───────────────────────────────────────────
            # Cat detection via cascade
            cats = AnalysisEngine._detect(AnalysisEngine.CAT_CASCADE, gray, 1.1, 4, (40,40))
            if len(cats) > 0:
                tags.append(f"cat ({len(cats)})" if len(cats) > 1 else "cat")

            # Animal heuristics — fur texture + natural colour patterns
            # Check for brown/tan tones (dogs, horses, deer)
            brown_mask = cv2.inRange(hsv, (5,40,40), (30,255,200))
            brown_ratio = cv2.countNonZero(brown_mask) / total_px
            # Check for black/white animal patterns (zebra, cow, dog)
            bw_mask = cv2.inRange(gray, 200, 255)
            dark_mask= cv2.inRange(gray, 0, 60)

            # Texture roughness (fur/feathers have high Laplacian variance in patches)
            lap_map  = cv2.Laplacian(gray, cv2.CV_64F)
            lap_abs  = cv2.convertScaleAbs(lap_map)
            _, tex   = cv2.threshold(lap_abs, 40, 255, cv2.THRESH_BINARY)
            tex_ratio = cv2.countNonZero(tex) / total_px

            if brown_ratio > 0.20 and n_faces == 0 and tex_ratio > 0.15:
                tags.append("animal (possible dog/horse/deer)")
            elif brown_ratio > 0.30 and n_faces == 0:
                tags.append("animal (brown)")

            # Bird / feather detection: blue-sky + small moving object
            green_mask = cv2.inRange(hsv, (36,40,40), (85,255,255))
            green_ratio = cv2.countNonZero(green_mask) / total_px
            if green_ratio > 0.35 and n_faces == 0 and tex_ratio > 0.10:
                tags.append("outdoor animal habitat")

            # ── Vehicle detection ──────────────────────────────────────────
            # License plate cascade
            plates = AnalysisEngine._detect(AnalysisEngine.PLATE_CASCADE, gray, 1.1, 3, (60,20))
            if len(plates) > 0:
                tags.append(f"license plate ({len(plates)})")
                tags.append("vehicle")

            # Colour region heuristics: large uniform metallic/dark rectangles
            edges_img = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges_img, 1, 3.14/180, threshold=80, minLineLength=w//4, maxLineGap=20)
            h_lines = 0; v_lines = 0
            if lines is not None:
                for l in lines:
                    x1,y1,x2,y2 = l[0]
                    angle = abs(float(y2-y1)/(x2-x1+1e-6))
                    if angle < 0.15: h_lines += 1
                    elif angle > 4:  v_lines += 1

            # Strong horizontal structure + metallic colours → vehicle likely
            metallic = cv2.inRange(hsv, (0,0,120), (180,30,255))
            metal_ratio = cv2.countNonZero(metallic) / total_px
            if h_lines > 6 and metal_ratio > 0.25 and n_faces == 0:
                tags.append("vehicle (possible)")

            # Road / tarmac: grey-dominant, horizontal-heavy lower half
            lower_half = gray[h//2:, :]
            grey_mask  = cv2.inRange(
                cv2.cvtColor(img[h//2:,:], cv2.COLOR_BGR2HSV), (0,0,60),(180,40,200)
            )
            grey_ratio = cv2.countNonZero(grey_mask) / (lower_half.size + 1)
            if grey_ratio > 0.45 and h_lines > 4:
                tags.append("road/street")

            # ── Weapon heuristics ──────────────────────────────────────────
            # Long thin dark objects with high edge density → possible firearm / blade
            # Detect elongated dark shapes
            dark_img = cv2.inRange(gray, 0, 80)
            contours, _ = cv2.findContours(dark_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            weapon_cands = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < 400: continue
                rect = cv2.minAreaRect(cnt)
                rw, rh = rect[1]
                if rw == 0 or rh == 0: continue
                ratio = max(rw, rh) / (min(rw, rh) + 1e-6)
                # Very elongated (barrel/blade ratio typically > 6)
                if ratio > 6 and min(rw,rh) < w * 0.08 and area > 500:
                    weapon_cands += 1

            if weapon_cands >= 2:
                tags.append("⚠ possible weapon/firearm")
            elif weapon_cands == 1 and n_faces > 0:
                tags.append("possible weapon")

            # Knife/blade: bright silver elongated object
            bright_elongated = cv2.inRange(gray, 180, 255)
            cnt2, _ = cv2.findContours(bright_elongated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            blade_cands = 0
            for cnt in cnt2:
                area = cv2.contourArea(cnt)
                if area < 300: continue
                rect = cv2.minAreaRect(cnt)
                rw, rh = rect[1]
                if min(rw,rh) == 0: continue
                ratio = max(rw,rh)/(min(rw,rh)+1e-6)
                if ratio > 5 and min(rw,rh) < w*0.06:
                    blade_cands += 1
            if blade_cands >= 2:
                tags.append("possible blade/knife")

            # ── Environment / scene ────────────────────────────────────────
            sky_region = img[:int(h*0.28), :]
            sky_hsv    = cv2.cvtColor(sky_region, cv2.COLOR_BGR2HSV) if sky_region.size > 0 else None
            if sky_hsv is not None:
                blue_sky  = cv2.inRange(sky_hsv, (95,50,80),(130,255,255))
                cloud_sky = cv2.inRange(sky_hsv, (0,0,200),(180,30,255))
                sky_px    = sky_region.shape[0] * sky_region.shape[1]
                if cv2.countNonZero(blue_sky)/sky_px > 0.25:  tags.append("clear sky")
                elif cv2.countNonZero(cloud_sky)/sky_px > 0.3: tags.append("overcast sky")

            if green_ratio > 0.30: tags.append("vegetation/outdoor")
            elif green_ratio > 0.15: tags.append("some vegetation")

            # Water (blue-green low saturation areas in lower image)
            water_mask = cv2.inRange(
                cv2.cvtColor(img[h//2:,:], cv2.COLOR_BGR2HSV),(85,20,30),(140,180,200)
            )
            if cv2.countNonZero(water_mask)/(total_px//2+1) > 0.25:
                tags.append("water/ocean")

            # Night / artificial light
            if br < 55 and std > 30:
                bright_spots = cv2.inRange(gray, 220, 255)
                if cv2.countNonZero(bright_spots)/total_px > 0.02:
                    tags.append("night/artificial light")

            # Indoor vs outdoor
            if green_ratio < 0.05 and grey_ratio > 0.30 and n_faces > 0:
                tags.append("indoor")

            # Text/document detection (high edge density, uniform background)
            edge_density = edges_img.mean()
            if edge_density > 25 and br > 160 and std < 70:
                tags.append("document/text")
            elif edge_density > 18:
                tags.append("high detail")
            elif edge_density < 4:
                tags.append("minimal detail")

            # ── Sexual content signals ─────────────────────────────────────
            # Heuristic: high skin + face + lower body exposure + close crop
            if skin_ratio > 0.45 and n_faces > 0 and len(lower) > 0:
                tags.append("⚠ sexual content signal")
            elif skin_ratio > 0.50 and n_body > 0:
                tags.append("⚠ sexual content signal")

        except Exception:
            pass
        return tags

    @staticmethod
    def exif(fp):
        """
        Enhanced EXIF extraction: captures all key fields, decodes GPS to decimal,
        computes derived values, and extracts Pillow metadata for non-EXIF formats.
        """
        d = {}
        try:
            with open(fp, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='UNDEF', details=True)

            # ── Comprehensive field map ──────────────────────────────────
            field_map = {
                # Datetime
                'EXIF DateTimeOriginal':    'Date/Time (Original)',
                'EXIF DateTimeDigitized':   'Date/Time (Digitized)',
                'Image DateTime':           'Date/Time (Modified)',
                # Camera
                'Image Make':               'Camera Make',
                'Image Model':              'Camera Model',
                'EXIF LensModel':           'Lens Model',
                'EXIF LensMake':            'Lens Make',
                'EXIF LensSpecification':   'Lens Specification',
                # Exposure
                'EXIF ExposureTime':        'Exposure Time',
                'EXIF FNumber':             'F-Number (Aperture)',
                'EXIF ApertureValue':       'Aperture Value',
                'EXIF ISOSpeedRatings':     'ISO Speed',
                'EXIF ExposureBiasValue':   'Exposure Bias',
                'EXIF ExposureMode':        'Exposure Mode',
                'EXIF ExposureProgram':     'Exposure Program',
                'EXIF ShutterSpeedValue':   'Shutter Speed (APEX)',
                'EXIF MaxApertureValue':    'Max Aperture',
                'EXIF MeteringMode':        'Metering Mode',
                'EXIF SensingMethod':       'Sensing Method',
                # Focus
                'EXIF FocalLength':         'Focal Length',
                'EXIF FocalLengthIn35mmFilm':'Focal Length (35mm equiv.)',
                'EXIF SubjectDistance':     'Subject Distance',
                'EXIF SubjectDistanceRange':'Subject Distance Range',
                # Flash
                'EXIF Flash':               'Flash',
                'EXIF FlashEnergy':         'Flash Energy',
                # White Balance & Colour
                'EXIF WhiteBalance':        'White Balance',
                'EXIF ColorSpace':          'Colour Space',
                'EXIF Saturation':          'Saturation',
                'EXIF Sharpness':           'Sharpness',
                'EXIF Contrast':            'Contrast',
                'EXIF BrightnessValue':     'Brightness Value',
                'EXIF LightSource':         'Light Source',
                # Image dimensions
                'EXIF ExifImageWidth':      'EXIF Width (px)',
                'EXIF ExifImageLength':     'EXIF Height (px)',
                'Image XResolution':        'X Resolution',
                'Image YResolution':        'Y Resolution',
                'Image ResolutionUnit':     'Resolution Unit',
                # Orientation
                'Image Orientation':        'Orientation',
                # Software / authorship
                'Image Software':           'Software',
                'Image Artist':             'Artist/Author',
                'Image Copyright':          'Copyright',
                'EXIF UserComment':         'User Comment',
                'Image ImageDescription':   'Image Description',
                # File source
                'EXIF FileSource':          'File Source',
                'EXIF SceneType':           'Scene Type',
                'EXIF SceneCaptureType':    'Scene Capture Type',
                'EXIF DigitalZoomRatio':    'Digital Zoom Ratio',
                'EXIF GainControl':         'Gain Control',
                # Thumbnail
                'Thumbnail Compression':    'Thumbnail Type',
                # Device
                'MakerNote Tag 0x0001':     'MakerNote (0x0001)',
            }

            for raw_key, friendly in field_map.items():
                if raw_key in tags:
                    val = str(tags[raw_key])
                    # Clean up exifread's fraction strings for human readability
                    if raw_key == 'EXIF ExposureTime':
                        try:
                            n, dn = val.split('/')
                            val = f"1/{int(int(dn)/int(n))}s" if int(n)==1 else f"{eval(val):.5f}s"
                        except: pass
                    elif raw_key in ('EXIF FNumber','EXIF ApertureValue'):
                        try:
                            import fractions
                            fv = float(fractions.Fraction(val))
                            val = f"f/{fv:.1f}"
                        except: pass
                    elif raw_key == 'EXIF FocalLength':
                        try:
                            import fractions
                            fv = float(fractions.Fraction(val))
                            val = f"{fv:.0f}mm"
                        except: pass
                    d[friendly] = val

            # ── GPS: decode to decimal degrees ──────────────────────────
            def _rat_to_float(val_str):
                """Convert exifread ratio string like '[40, 26, 0]' to float."""
                try:
                    import fractions
                    parts = str(val_str).strip('[]').split(',')
                    deg   = float(fractions.Fraction(parts[0].strip()))
                    mn    = float(fractions.Fraction(parts[1].strip())) if len(parts)>1 else 0
                    sec   = float(fractions.Fraction(parts[2].strip())) if len(parts)>2 else 0
                    return deg + mn/60 + sec/3600
                except: return None

            lat = _rat_to_float(tags.get('GPS GPSLatitude'))
            lon = _rat_to_float(tags.get('GPS GPSLongitude'))
            lat_ref = str(tags.get('GPS GPSLatitudeRef','N'))
            lon_ref = str(tags.get('GPS GPSLongitudeRef','E'))

            if lat is not None:
                if 'S' in lat_ref.upper(): lat = -lat
                d['GPS Latitude']  = f"{lat:.6f}°"
            if lon is not None:
                if 'W' in lon_ref.upper(): lon = -lon
                d['GPS Longitude'] = f"{lon:.6f}°"
            if lat is not None and lon is not None:
                d['GPS Decimal']   = f"{lat:.6f}, {lon:.6f}"
                d['GPS Maps Link'] = f"https://maps.google.com/?q={lat:.6f},{lon:.6f}"

            if 'GPS GPSAltitude' in tags:
                try:
                    import fractions
                    alt = float(fractions.Fraction(str(tags['GPS GPSAltitude'])))
                    ref = str(tags.get('GPS GPSAltitudeRef','0'))
                    sign = -1 if ref.strip() in ('1','Below Sea Level') else 1
                    d['GPS Altitude'] = f"{sign*alt:.1f}m"
                except: d['GPS Altitude'] = str(tags['GPS GPSAltitude'])

            if 'GPS GPSDateStamp' in tags:
                d['GPS Date'] = str(tags['GPS GPSDateStamp'])
            if 'GPS GPSImgDirection' in tags:
                try:
                    import fractions
                    direction = float(fractions.Fraction(str(tags['GPS GPSImgDirection'])))
                    d['GPS Direction'] = f"{direction:.1f}°"
                except: pass

            # ── Derived / computed fields ────────────────────────────────
            try:
                import fractions
                if 'EXIF ISOSpeedRatings' in tags and 'EXIF ExposureTime' in tags and 'EXIF FNumber' in tags:
                    iso = int(str(tags['EXIF ISOSpeedRatings']))
                    et2 = float(fractions.Fraction(str(tags['EXIF ExposureTime'])))
                    fn  = float(fractions.Fraction(str(tags['EXIF FNumber'])))
                    ev  = (fn**2) / (et2 * iso / 100) if et2 > 0 else 0
                    d['Exposure Value (EV)'] = f"{ev:.1f}"
            except: pass

            # Estimate approximate distance from subject distance
            if 'EXIF SubjectDistance' in tags:
                try:
                    import fractions
                    dist = float(fractions.Fraction(str(tags['EXIF SubjectDistance'])))
                    d['Subject Distance'] = f"{dist:.2f}m"
                except: pass

        except Exception:
            pass

        # ── PIL / file-level metadata (works for PNG, WEBP, GIF, BMP) ──
        try:
            img_pil = PILImage.open(fp)
            d['Format']         = img_pil.format or 'unknown'
            d['Colour Mode']    = img_pil.mode
            d['Pixel Size']     = f"{img_pil.width} × {img_pil.height} px"
            d['Megapixels']     = f"{img_pil.width*img_pil.height/1_000_000:.2f} MP"

            # DPI
            dpi = img_pil.info.get('dpi')
            if dpi: d['DPI'] = f"{dpi[0]:.0f} × {dpi[1]:.0f}"

            # PNG / GIF metadata chunks
            for key in ('comment','description','author','title','software','creation_time','source'):
                val = img_pil.info.get(key)
                if val: d[f'PNG/GIF {key.title()}'] = str(val)

            # ICC profile
            if 'icc_profile' in img_pil.info:
                d['ICC Profile'] = 'Present'

            # Animation
            if hasattr(img_pil, 'n_frames') and img_pil.n_frames > 1:
                d['Animation Frames'] = str(img_pil.n_frames)

        except Exception:
            pass

        # ── OS-level file metadata ───────────────────────────────────────
        try:
            st = os.stat(fp)
            d['File Size']      = f"{st.st_size:,} bytes ({st.st_size/1024:.1f} KB)"
            d['File Modified']  = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            d['File Created']   = datetime.datetime.fromtimestamp(st.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
            d['File Extension'] = os.path.splitext(fp)[1].lower()
        except Exception:
            pass

        return d

    @staticmethod
    def analyze(fp, db, case_id=1):
        stat = os.stat(fp); h = AnalysisEngine.hashes(fp)
        faces = AnalysisEngine.detect_faces(fp); tags = AnalysisEngine.classify(fp); ex = AnalysisEngine.exif(fp)
        try:
            img = PILImage.open(fp); W,H = img.size; mime=f"image/{img.format.lower()}" if img.format else "image/unknown"
        except: W=H=0; mime="unknown"
        match = None
        for ht,hv in [('md5',h['md5']),('sha256',h['sha256']),('phash',h['phash'])]:
            if hv:
                m = db.check_ref(hv,ht)
                if m: match=f"{m['db_name']}:{m['label']}:{m['severity']}"; break
        csam = 1 if (match and 'CSAM' in match.upper()) else 0
        return {'case_id':case_id,'filepath':fp,'filename':os.path.basename(fp),'size':stat.st_size,
                'width':W,'height':H,'md5':h['md5'],'sha256':h['sha256'],'phash':h['phash'],'dhash':h['dhash'],'whash':h['whash'],
                'mime_type':mime,'face_count':faces,'object_tags':json.dumps(tags),'custom_tags':'[]',
                'csam_flag':csam,'hash_match':match,'imported_at':datetime.datetime.now().isoformat(),
                'exif_data':json.dumps(ex),'category':'Flagged' if match else 'Uncategorized'}

    @staticmethod
    def face_search(query_fp, candidates, threshold=10):
        results = []
        try:
            qimg  = cv2.imread(query_fp)
            if qimg is None: return []
            qgray = cv2.cvtColor(qimg,cv2.COLOR_BGR2GRAY)
            qf    = AnalysisEngine.FACE_CASCADE.detectMultiScale(qgray,1.1,5,minSize=(30,30))
            if len(qf)==0:
                qi = PILImage.open(query_fp).convert('RGB').resize((64,64))
            else:
                x,y,w,h = qf[0]
                qi = PILImage.fromarray(cv2.cvtColor(qimg[y:y+h,x:x+w],cv2.COLOR_BGR2RGB)).resize((64,64))
            qhash = imagehash.phash(qi)
            for fp in candidates:
                try:
                    ci = cv2.imread(fp)
                    if ci is None: continue
                    cf = AnalysisEngine.FACE_CASCADE.detectMultiScale(cv2.cvtColor(ci,cv2.COLOR_BGR2GRAY),1.1,5,minSize=(30,30))
                    if len(cf)==0: continue
                    x,y,w,h = cf[0]
                    crop = PILImage.fromarray(cv2.cvtColor(ci[y:y+h,x:x+w],cv2.COLOR_BGR2RGB)).resize((64,64))
                    d = qhash - imagehash.phash(crop)
                    if d<=threshold: results.append((fp,d))
                except: pass
        except: pass
        results.sort(key=lambda x:x[1]); return [fp for fp,_ in results]

    @staticmethod
    def image_search(query_fp, candidates, threshold=15):
        results = []
        try:
            qh = imagehash.phash(PILImage.open(query_fp).convert('RGB'))
            for fp in candidates:
                try:
                    d = qh - imagehash.phash(PILImage.open(fp).convert('RGB'))
                    if d<=threshold: results.append((fp,d))
                except: pass
        except: pass
        results.sort(key=lambda x:x[1]); return [fp for fp,_ in results]


# ─── Workers ─────────────────────────────────────────────────────────────────
class ImportWorker(QThread):
    progress = pyqtSignal(int,int,str)
    finished = pyqtSignal(int,int)
    error    = pyqtSignal(str)
    def __init__(self, fps, db, case_id=1):
        super().__init__(); self.fps=fps; self.db=db; self.case_id=case_id; self._stop=False
    def run(self):
        ok=0
        for i,fp in enumerate(self.fps):
            if self._stop: break
            try:
                self.progress.emit(i+1,len(self.fps),os.path.basename(fp))
                self.db.insert_media(AnalysisEngine.analyze(fp,self.db,self.case_id)); ok+=1
            except Exception as e: self.error.emit(str(e))
        self.finished.emit(ok,len(self.fps))
    def stop(self): self._stop=True

class VisualSearchWorker(QThread):
    finished = pyqtSignal(list)
    def __init__(self, qfp, candidates, threshold, mode):
        super().__init__(); self.qfp=qfp; self.candidates=candidates; self.threshold=threshold; self.mode=mode
    def run(self):
        if self.mode=='face': r=AnalysisEngine.face_search(self.qfp,self.candidates,self.threshold)
        else: r=AnalysisEngine.image_search(self.qfp,self.candidates,self.threshold)
        self.finished.emit(r)


# ─── Search Panel (separate widget, 100px, distinct background) ──────────────
class SearchPanel(QWidget):
    search_changed        = pyqtSignal(dict)
    visual_search_req     = pyqtSignal(str,int,str)

    def __init__(self):
        super().__init__()
        self.setObjectName("searchPanel")
        self.setFixedHeight(100)
        self._build()

    def _build(self):
        vb = QVBoxLayout(self); vb.setContentsMargins(14,8,14,8); vb.setSpacing(6)

        # Row 1 – text search
        r1 = QHBoxLayout(); r1.setSpacing(10)
        lbl = QLabel("🔍"); lbl.setStyleSheet(f"font-size:16px;color:{ACC};background:transparent;")
        r1.addWidget(lbl)
        self.q = QLineEdit(); self.q.setPlaceholderText("Search filename, tags, notes, hashes…")
        self.q.textChanged.connect(self._emit); r1.addWidget(self.q,3)
        r1.addWidget(self._lbl("CATEGORY"))
        self.cat = QComboBox(); self.cat.addItem("All")
        for c in CATEGORY_COLORS: self.cat.addItem(c)
        self.cat.currentTextChanged.connect(self._emit); r1.addWidget(self.cat,1)
        self.cb_face = QCheckBox("Has Faces"); self.cb_face.stateChanged.connect(self._emit); r1.addWidget(self.cb_face)
        self.cb_flag = QCheckBox("Flagged Only"); self.cb_flag.stateChanged.connect(self._emit); r1.addWidget(self.cb_flag)
        btn_clr = QPushButton("Clear"); btn_clr.setFixedWidth(64); btn_clr.clicked.connect(self._clear); r1.addWidget(btn_clr)
        vb.addLayout(r1)

        # Row 2 – visual/face search
        r2 = QHBoxLayout(); r2.setSpacing(10)
        r2.addWidget(self._lbl("VISUAL SEARCH"))
        self.vq = QLineEdit(); self.vq.setPlaceholderText("Browse an image or face to find similar…"); self.vq.setReadOnly(True)
        r2.addWidget(self.vq,3)
        btn_br = QPushButton("Browse…"); btn_br.setFixedWidth(80); btn_br.clicked.connect(self._browse); r2.addWidget(btn_br)
        r2.addWidget(self._lbl("THRESHOLD"))
        self.thr = QSpinBox(); self.thr.setRange(1,50); self.thr.setValue(12); self.thr.setFixedWidth(56); r2.addWidget(self.thr)
        self.mode = QComboBox(); self.mode.addItems(["Face Match","Image Match"]); self.mode.setFixedWidth(110); r2.addWidget(self.mode)
        self.btn_vs = QPushButton("🧬  Search"); self.btn_vs.setObjectName("btnSearchFace")
        self.btn_vs.setFixedWidth(100); self.btn_vs.clicked.connect(self._vs); r2.addWidget(self.btn_vs)
        vb.addLayout(r2)

    def _lbl(self,t):
        l=QLabel(t); l.setStyleSheet(f"color:{FG1};font-size:13px;font-weight:bold;letter-spacing:1px;background:transparent;"); return l

    def _emit(self):
        self.search_changed.emit({'search':self.q.text(),'category':self.cat.currentText(),
                                  'face_only':self.cb_face.isChecked(),'flagged_only':self.cb_flag.isChecked()})
    def _clear(self):
        self.q.clear(); self.cat.setCurrentIndex(0); self.cb_face.setChecked(False)
        self.cb_flag.setChecked(False); self.vq.clear()

    def _browse(self):
        fp,_=QFileDialog.getOpenFileName(self,"Select Query Image","","Images (*.jpg *.jpeg *.png *.bmp *.webp);;All (*)")
        if fp: self.vq.setText(fp)

    def _vs(self):
        fp=self.vq.text().strip()
        if not fp: QMessageBox.information(self,"No Image","Please browse an image first."); return
        mode="face" if self.mode.currentIndex()==0 else "image"
        self.visual_search_req.emit(fp,self.thr.value(),mode)


# ─── Thumbnail Grid ───────────────────────────────────────────────────────────
class ThumbnailWidget(QListWidget):
    item_selected   = pyqtSignal(int)
    tags_updated    = pyqtSignal()          # emitted whenever custom tags change

    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(120,120)); self.setSpacing(8)
        self.setResizeMode(QListWidget.Adjust); self.setMovement(QListWidget.Static)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemClicked.connect(lambda it: self.item_selected.emit(it.data(Qt.UserRole)) if it.data(Qt.UserRole) else None)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)
        self._cat_cb  = None   # (mid, cat) -> None
        self._del_cb  = None   # (mid,) -> None
        self._db      = None   # set by MainWindow after construction
        self._all_tags = []    # cache of current tags for "remove tag" submenu

    def load_media(self, ml):
        self.clear()
        for m in ml:
            it = QListWidgetItem()
            it.setData(Qt.UserRole, m['id'])
            # store full custom_tags on item for fast ctx menu use
            it.setData(Qt.UserRole + 1, json.loads(m.get('custom_tags') or '[]'))
            atags = ', '.join(json.loads(m.get('object_tags') or '[]'))[:40]
            ctags = ', '.join(json.loads(m.get('custom_tags') or '[]'))
            it.setToolTip(
                f"{m['filename']}\n{self._sz(m['size'])} | {m['width']}×{m['height']}\n"
                f"Category: {m['category']} | Faces: {m['face_count']}\n"
                f"Tags: {atags}" + (f"\nCustom: {ctags}" if ctags else "")
            )
            it.setIcon(QIcon(self._thumb(m['filepath'])))
            it.setText((m['filename'][:15]+"…" if len(m['filename'])>15 else m['filename']))
            it.setForeground(QColor(CATEGORY_COLORS.get(m['category'],'#607D8B')))
            if m.get('csam_flag') or m.get('hash_match'): it.setBackground(QColor('#1a0000'))
            self.addItem(it)

    def get_ids(self):
        return [it.data(Qt.UserRole) for it in self.selectedItems() if it.data(Qt.UserRole)]

    def _thumb(self,fp,sz=120):
        try:
            p=QPixmap(fp)
            if p.isNull(): return self._placeholder(sz)
            return p.scaled(sz,sz,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        except: return self._placeholder(sz)

    def _placeholder(self,sz=120):
        p=QPixmap(sz,sz); p.fill(QColor(BG3))
        pr=QPainter(p); pr.setPen(QPen(QColor(FG1))); pr.setFont(QFont("Arial",9))
        pr.drawText(p.rect(),Qt.AlignCenter,"NO\nPREVIEW"); pr.end(); return p

    def _sz(self,s):
        if s>1e6: return f"{s/1e6:.1f}MB"
        if s>1e3: return f"{s/1e3:.0f}KB"
        return f"{s}B"

    def _ctx(self, pos):
        it = self.itemAt(pos)
        if not it: return
        mid  = it.data(Qt.UserRole)
        ctags = it.data(Qt.UserRole + 1) or []
        menu = QMenu(self); menu.setStyleSheet(DARK_STYLE)

        # ── Category submenu ──
        cm = menu.addMenu("⚑  Set Category")
        for cat in CATEGORY_COLORS:
            a = cm.addAction(cat); a.setData(('cat', mid, cat))

        menu.addSeparator()

        # ── Custom Tag submenu ──
        tag_menu = menu.addMenu("🏷  Custom Tags")

        # Add new tag
        add_act = tag_menu.addAction("➕  Add Tag…")
        add_act.setData(('tag_add', mid))

        # Add from existing tags (quick-apply)
        if self._all_tags:
            quick_menu = tag_menu.addMenu("⚡  Quick-Apply")
            for tag, count in self._all_tags[:20]:   # top 20 most-used
                if tag not in ctags:
                    qa = quick_menu.addAction(f"{tag}  ({count})")
                    qa.setData(('tag_apply', mid, tag))

        # Remove existing tags on this item
        if ctags:
            tag_menu.addSeparator()
            rm_menu = tag_menu.addMenu("✖  Remove Tag")
            for tag in ctags:
                ra = rm_menu.addAction(tag)
                ra.setData(('tag_rm', mid, tag))

        # Bulk-apply to all selected
        sel_ids = self.get_ids()
        if len(sel_ids) > 1:
            tag_menu.addSeparator()
            bulk_act = tag_menu.addAction(f"📋  Apply Tag to {len(sel_ids)} Selected…")
            bulk_act.setData(('tag_bulk', sel_ids))

        menu.addSeparator()
        a_v = menu.addAction("👁  View Details"); a_v.setData(('view', mid))
        a_d = menu.addAction("✖  Remove from Case"); a_d.setData(('del', mid))

        act = menu.exec_(self.mapToGlobal(pos))
        if not act: return
        d = act.data()
        if not d: return

        if d[0] == 'cat' and self._cat_cb:
            self._cat_cb(d[1], d[2])
        elif d[0] == 'view':
            self.item_selected.emit(d[1])
        elif d[0] == 'del' and self._del_cb:
            self._del_cb(d[1])
        elif d[0] == 'tag_add':
            self._prompt_add_tag(d[1])
        elif d[0] == 'tag_apply':
            self._apply_tag(d[1], d[2])
        elif d[0] == 'tag_rm':
            self._remove_tag(d[1], d[2])
        elif d[0] == 'tag_bulk':
            self._prompt_bulk_tag(d[1])

    def _prompt_add_tag(self, mid):
        dlg = QDialog(self); dlg.setWindowTitle("Add Custom Tag"); dlg.setStyleSheet(DARK_STYLE)
        dlg.setFixedWidth(340)
        vb = QVBoxLayout(dlg); vb.setSpacing(10)
        lbl = QLabel("Enter tag name:"); lbl.setStyleSheet(f"color:{FG0};font-size:12px;"); vb.addWidget(lbl)
        ed = QLineEdit(); ed.setPlaceholderText("e.g. vehicle, weapon, suspect…"); vb.addWidget(ed)
        # Suggest existing tags
        if self._all_tags:
            suggest_lbl = QLabel("Or click an existing tag:"); suggest_lbl.setStyleSheet(f"color:{FG1};font-size:11px;"); vb.addWidget(suggest_lbl)
            flow = QWidget(); fl = QHBoxLayout(flow); fl.setContentsMargins(0,0,0,0); fl.setSpacing(4); fl.setAlignment(Qt.AlignLeft)
            for tag, _ in self._all_tags[:12]:
                tb = QPushButton(tag)
                tb.setStyleSheet(f"background:#1a2a3a;border:1px solid {ACC};border-radius:10px;padding:2px 10px;font-size:11px;color:{ACC};")
                tb.clicked.connect(lambda checked, t=tag: ed.setText(t))
                fl.addWidget(tb)
            vb.addWidget(flow)
        br = QHBoxLayout()
        bc = QPushButton("Cancel"); bc.clicked.connect(dlg.reject)
        bk = QPushButton("Add Tag"); bk.setObjectName("btnPrimary"); bk.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(bc); br.addWidget(bk); vb.addLayout(br)
        if dlg.exec_() == QDialog.Accepted and ed.text().strip():
            self._apply_tag(mid, ed.text().strip())

    def _apply_tag(self, mid, tag):
        if not self._db: return
        m = self._db.get_media_by_id(mid)
        if not m: return
        tags = json.loads(m.get('custom_tags') or '[]')
        if tag not in tags:
            tags.append(tag)
            self._db.update_media(mid, {'custom_tags': json.dumps(tags)})
            self.tags_updated.emit()

    def _remove_tag(self, mid, tag):
        if not self._db: return
        m = self._db.get_media_by_id(mid)
        if not m: return
        tags = [t for t in json.loads(m.get('custom_tags') or '[]') if t != tag]
        self._db.update_media(mid, {'custom_tags': json.dumps(tags)})
        self.tags_updated.emit()

    def _prompt_bulk_tag(self, ids):
        dlg = QDialog(self); dlg.setWindowTitle("Bulk Apply Tag"); dlg.setStyleSheet(DARK_STYLE)
        dlg.setFixedWidth(340)
        vb = QVBoxLayout(dlg); vb.setSpacing(10)
        vb.addWidget(QLabel(f"Apply tag to {len(ids)} selected items:"))
        ed = QLineEdit(); ed.setPlaceholderText("Tag name…"); vb.addWidget(ed)
        br = QHBoxLayout(); bc=QPushButton("Cancel"); bc.clicked.connect(dlg.reject)
        bk=QPushButton("Apply"); bk.setObjectName("btnPrimary"); bk.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(bc); br.addWidget(bk); vb.addLayout(br)
        if dlg.exec_() == QDialog.Accepted and ed.text().strip():
            tag = ed.text().strip()
            for mid in ids: self._apply_tag(mid, tag)


# ─── Detail Panel ─────────────────────────────────────────────────────────────
class DetailPanel(QWidget):
    category_changed = pyqtSignal(int,str)
    notes_changed    = pyqtSignal(int,str)

    def __init__(self,db):
        super().__init__(); self.db=db; self.cur=None; self._build()

    def _build(self):
        vb=QVBoxLayout(self); vb.setContentsMargins(0,0,0,0); vb.setSpacing(0)
        self.preview=QLabel(); self.preview.setAlignment(Qt.AlignCenter); self.preview.setMinimumHeight(200)
        self.preview.setStyleSheet(f"background:{BG0};border-bottom:1px solid {BRD};"); self.preview.setText("Select an image")
        vb.addWidget(self.preview)
        tabs=QTabWidget(); tabs.setTabPosition(QTabWidget.South); vb.addWidget(tabs)

        # INFO
        iw=QWidget(); iv=QVBoxLayout(iw); iv.setContentsMargins(6,6,6,6); iv.setSpacing(6)
        self.info_t=QTableWidget(0,2); self.info_t.setHorizontalHeaderLabels(["Field","Value"])
        self.info_t.horizontalHeader().setStretchLastSection(True); self.info_t.verticalHeader().setVisible(False)
        self.info_t.setEditTriggers(QAbstractItemView.NoEditTriggers); self.info_t.setAlternatingRowColors(True)
        self.info_t.verticalHeader().setDefaultSectionSize(26); iv.addWidget(self.info_t)
        cr=QHBoxLayout(); cr.addWidget(QLabel("Category:"))
        self.cat_cb=QComboBox()
        for c in CATEGORY_COLORS: self.cat_cb.addItem(c)
        self.cat_cb.currentTextChanged.connect(lambda v: self.category_changed.emit(self.cur,v) if self.cur else None)
        cr.addWidget(self.cat_cb); iv.addLayout(cr)
        tabs.addTab(iw,"INFO")

        # TAGS
        tw=QWidget(); tv=QVBoxLayout(tw); tv.setContentsMargins(6,6,6,6); tv.setSpacing(6)
        tv.addWidget(QLabel("Auto-detected Object Tags:"))
        self.auto_tags=QLabel(); self.auto_tags.setWordWrap(True); self.auto_tags.setStyleSheet(f"color:{FG1};font-size:12px;padding:4px;")
        tv.addWidget(self.auto_tags)
        tv.addWidget(QFrame(frameShape=QFrame.HLine))
        tv.addWidget(QLabel("Custom Tags:"))
        self.ctag_list=QListWidget(); self.ctag_list.setMaximumHeight(90); tv.addWidget(self.ctag_list)
        ar=QHBoxLayout(); self.tag_ed=QLineEdit(); self.tag_ed.setPlaceholderText("Add tag…")
        btn_at=QPushButton("Add"); btn_at.setObjectName("btnPrimary"); btn_at.setFixedWidth(60); btn_at.clicked.connect(self._add_tag)
        ar.addWidget(self.tag_ed); ar.addWidget(btn_at); tv.addLayout(ar); tv.addStretch()
        tabs.addTab(tw,"TAGS")

        # EXIF
        ew=QWidget(); ev=QVBoxLayout(ew); ev.setContentsMargins(6,6,6,6)
        self.exif_t=QTableWidget(0,2); self.exif_t.setHorizontalHeaderLabels(["Tag","Value"])
        self.exif_t.horizontalHeader().setStretchLastSection(True); self.exif_t.verticalHeader().setVisible(False)
        self.exif_t.setAlternatingRowColors(True); self.exif_t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.exif_t.verticalHeader().setDefaultSectionSize(24); ev.addWidget(self.exif_t)
        tabs.addTab(ew,"EXIF")

        # HASHES
        hw=QWidget(); hv=QVBoxLayout(hw); hv.setContentsMargins(6,6,6,6)
        self.hash_te=QTextEdit(); self.hash_te.setReadOnly(True); self.hash_te.setFont(QFont("Courier New",10))
        hv.addWidget(self.hash_te); tabs.addTab(hw,"HASHES")

        # NOTES
        nw=QWidget(); nv=QVBoxLayout(nw); nv.setContentsMargins(6,6,6,6)
        self.notes_te=QTextEdit(); self.notes_te.setPlaceholderText("Investigator notes…"); self.notes_te.setFont(QFont("Segoe UI",12))
        self.notes_te.textChanged.connect(lambda: self.notes_changed.emit(self.cur,self.notes_te.toPlainText()) if self.cur else None)
        nv.addWidget(self.notes_te); tabs.addTab(nw,"NOTES")

    def load(self,mid):
        self.cur=mid; m=self.db.get_media_by_id(mid)
        if not m: return
        pix=AnalysisEngine.detect_faces_annotated(m['filepath'])
        if not pix: pix=QPixmap(m['filepath'])
        self.preview.setPixmap(pix.scaled(290,220,Qt.KeepAspectRatio,Qt.SmoothTransformation)) if pix and not pix.isNull() else self.preview.setText("Preview unavailable")
        # info
        self.info_t.setRowCount(0)
        for k,v in [("Filename",m['filename']),("File Size",self._sz(m['size'])),("Dimensions",f"{m['width']}×{m['height']}"),
                    ("MIME",m['mime_type'] or "—"),("Faces",str(m['face_count'])),("Imported",(m['imported_at'] or '')[:19]),
                    ("CSAM","⚠ YES" if m['csam_flag'] else "No"),("Hash Match",m['hash_match'] or "None"),("Path",m['filepath'])]:
            r=self.info_t.rowCount(); self.info_t.insertRow(r)
            ki=QTableWidgetItem(k); ki.setForeground(QColor(FG1))
            vi=QTableWidgetItem(str(v))
            if k=="CSAM" and m['csam_flag']: vi.setForeground(QColor(ERR)); vi.setFont(QFont("Segoe UI",12,QFont.Bold))
            elif k=="Hash Match" and m['hash_match']: vi.setForeground(QColor(WARN))
            self.info_t.setItem(r,0,ki); self.info_t.setItem(r,1,vi)
        # tags
        self.auto_tags.setText(", ".join(json.loads(m.get('object_tags') or '[]')) or "—")
        self.ctag_list.clear()
        for t in json.loads(m.get('custom_tags') or '[]'): self.ctag_list.addItem(t)
        # exif
        self.exif_t.setRowCount(0)
        for k,v in (json.loads(m.get('exif_data') or '{}')).items():
            r=self.exif_t.rowCount(); self.exif_t.insertRow(r)
            ki=QTableWidgetItem(k); ki.setForeground(QColor(FG1))
            self.exif_t.setItem(r,0,ki); self.exif_t.setItem(r,1,QTableWidgetItem(str(v)))
        # hashes
        self.hash_te.setPlainText(f"MD5    : {m.get('md5') or 'N/A'}\nSHA256 : {m.get('sha256') or 'N/A'}\n\npHash  : {m.get('phash') or 'N/A'}\ndHash  : {m.get('dhash') or 'N/A'}\nwHash  : {m.get('whash') or 'N/A'}")
        idx=self.cat_cb.findText(m['category'])
        if idx>=0: self.cat_cb.blockSignals(True); self.cat_cb.setCurrentIndex(idx); self.cat_cb.blockSignals(False)
        self.notes_te.blockSignals(True); self.notes_te.setPlainText(m.get('notes') or ''); self.notes_te.blockSignals(False)

    def _add_tag(self):
        tag=self.tag_ed.text().strip()
        if not tag or not self.cur: return
        m=self.db.get_media_by_id(self.cur)
        if not m: return
        tags=json.loads(m.get('custom_tags') or '[]')
        if tag not in tags:
            tags.append(tag); self.db.update_media(self.cur,{'custom_tags':json.dumps(tags)}); self.ctag_list.addItem(tag)
        self.tag_ed.clear()

    def _sz(self,s):
        if s>1e6: return f"{s/1e6:.2f} MB"
        if s>1e3: return f"{s/1e3:.1f} KB"
        return f"{s} B"


# ─── Case Manager Dialog ──────────────────────────────────────────────────────
class CaseManagerDialog(QDialog):
    case_changed = pyqtSignal(int)   # emits new active case_id

    def __init__(self,db,cur_case,parent=None):
        super().__init__(parent); self.db=db; self.cur=cur_case
        self.setWindowTitle("Case Management"); self.setMinimumSize(780,560); self.setStyleSheet(DARK_STYLE); self._build(); self._refresh()

    def _build(self):
        vb=QVBoxLayout(self); vb.setSpacing(12)
        hdr=QLabel("CASE MANAGEMENT"); hdr.setStyleSheet(f"font-size:15px;font-weight:bold;color:{ACC};letter-spacing:2px;"); vb.addWidget(hdr)
        self.tbl=QTableWidget(0,6); self.tbl.setHorizontalHeaderLabels(["ID","Case Name","Case #","Investigator","Status","Created"])
        self.tbl.horizontalHeader().setStretchLastSection(True); self.tbl.setAlternatingRowColors(True)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows); self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tbl.verticalHeader().setDefaultSectionSize(18); self.tbl.verticalHeader().setVisible(False); vb.addWidget(self.tbl)
        grp=QGroupBox("CREATE NEW CASE"); fg=QFormLayout(grp); fg.setSpacing(10); fg.setContentsMargins(12,16,12,12)
        self.nc_name=QLineEdit(); self.nc_name.setPlaceholderText("Case name (required)")
        self.nc_num=QLineEdit(); self.nc_num.setPlaceholderText("e.g. 2024-001")
        self.nc_inv=QLineEdit(); self.nc_inv.setPlaceholderText("Investigator name")
        self.nc_desc=QTextEdit(); self.nc_desc.setPlaceholderText("Case description…"); self.nc_desc.setMaximumHeight(60)
        fg.addRow("Name *:",self.nc_name); fg.addRow("Case Number:",self.nc_num); fg.addRow("Investigator:",self.nc_inv); fg.addRow("Description:",self.nc_desc)
        br2=QHBoxLayout(); bc=QPushButton("Create Case"); bc.setObjectName("btnPrimary"); bc.clicked.connect(self._create); br2.addStretch(); br2.addWidget(bc); fg.addRow("",br2)
        vb.addWidget(grp)
        br=QHBoxLayout(); br.setSpacing(8)
        bd=QPushButton("Delete Case"); bd.setObjectName("btnDanger"); bd.clicked.connect(self._delete); br.addWidget(bd); br.addStretch()
        bcl=QPushButton("Close"); bcl.clicked.connect(self.accept)
        bsw=QPushButton("Switch to Selected"); bsw.setObjectName("btnPrimary"); bsw.clicked.connect(self._switch)
        br.addWidget(bcl); br.addWidget(bsw); vb.addLayout(br)

    def _refresh(self):
        self.tbl.setRowCount(0)
        for c in self.db.get_cases():
            r=self.tbl.rowCount(); self.tbl.insertRow(r)
            self.tbl.setItem(r,0,QTableWidgetItem(str(c['id'])))
            ni=QTableWidgetItem(c['name']+(  "  ✓" if c['id']==self.cur else ""))
            if c['id']==self.cur: ni.setForeground(QColor(ACC)); ni.setFont(QFont("Segoe UI",12,QFont.Bold))
            self.tbl.setItem(r,1,ni); self.tbl.setItem(r,2,QTableWidgetItem(c.get('case_number') or ''))
            self.tbl.setItem(r,3,QTableWidgetItem(c.get('investigator') or ''))
            si=QTableWidgetItem(c.get('status','active'))
            si.setForeground(QColor(OK if c.get('status')=='active' else FG1)); self.tbl.setItem(r,4,si)
            self.tbl.setItem(r,5,QTableWidgetItem((c.get('created_at') or '')[:10]))

    def _sel_id(self):
        row=self.tbl.currentRow()
        if row<0: return None
        try: return int(self.tbl.item(row,0).text())
        except: return None

    def _create(self):
        name=self.nc_name.text().strip()
        if not name: QMessageBox.warning(self,"Error","Case name required."); return
        self.db.create_case(name,self.nc_desc.toPlainText().strip(),self.nc_inv.text().strip(),self.nc_num.text().strip())
        self.nc_name.clear(); self.nc_num.clear(); self.nc_inv.clear(); self.nc_desc.clear()
        self._refresh()

    def _switch(self):
        cid=self._sel_id()
        if cid: self.cur=cid; self.case_changed.emit(cid); self._refresh(); self.accept()

    def _delete(self):
        cid=self._sel_id()
        if not cid: return
        if cid==1: QMessageBox.warning(self,"Error","Cannot delete the default case."); return
        if QMessageBox.question(self,"Confirm","Delete case and ALL its media?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.db.delete_case(cid); self._refresh()


# ─── Reference DB Dialog ──────────────────────────────────────────────────────
class RefDBDialog(QDialog):
    def __init__(self,db,parent=None):
        super().__init__(parent); self.db=db
        self.setWindowTitle("Reference Database Manager"); self.setMinimumSize(720,520); self.setStyleSheet(DARK_STYLE); self._build(); self._refresh()

    def _build(self):
        vb=QVBoxLayout(self); vb.setSpacing(10)
        hdr=QLabel("REFERENCE HASH DATABASES"); hdr.setStyleSheet(f"font-size:14px;font-weight:bold;color:{ACC};"); vb.addWidget(hdr)
        info=QLabel("Manage hash databases for matching. Supports MD5, SHA256, pHash (PhotoDNA-style)."); info.setStyleSheet(f"color:{FG1};"); info.setWordWrap(True); vb.addWidget(info)
        self.tbl=QTableWidget(0,4); self.tbl.setHorizontalHeaderLabels(["Database Name","Entries","Type","Added"])
        self.tbl.horizontalHeader().setStretchLastSection(True); self.tbl.setAlternatingRowColors(True)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tbl.verticalHeader().setVisible(False)
        self.tbl.verticalHeader().setDefaultSectionSize(26); vb.addWidget(self.tbl)
        grp=QGroupBox("ADD HASH ENTRY"); ag=QGridLayout(grp); ag.setSpacing(8)
        ag.addWidget(QLabel("DB Name:"),0,0); self.dbn=QComboBox(); self.dbn.setEditable(True)
        self.dbn.addItems(["NCMEC/CSAM","PhotoDNA","MD5-NSRL","Custom-HashSet","KFF-Ignore"]); ag.addWidget(self.dbn,0,1)
        ag.addWidget(QLabel("Hash Type:"),0,2); self.ht=QComboBox(); self.ht.addItems(["md5","sha256","phash"]); ag.addWidget(self.ht,0,3)
        ag.addWidget(QLabel("Severity:"),0,4); self.sv=QComboBox(); self.sv.addItems(["low","medium","high","critical"]); self.sv.setCurrentText("high"); ag.addWidget(self.sv,0,5)
        ag.addWidget(QLabel("Hash Value:"),1,0); self.hv=QLineEdit(); self.hv.setPlaceholderText("Hash value…"); ag.addWidget(self.hv,1,1,1,3)
        ag.addWidget(QLabel("Label:"),1,4); self.lbl_ed=QLineEdit(); ag.addWidget(self.lbl_ed,1,5)
        btn_add=QPushButton("Add Hash"); btn_add.setObjectName("btnPrimary"); btn_add.clicked.connect(self._add); ag.addWidget(btn_add,2,5); vb.addWidget(grp)
        ig=QGroupBox("IMPORT FROM FILE"); il=QHBoxLayout(ig); il.addWidget(QLabel("CSV/TXT (one hash per line):"))
        btn_i=QPushButton("Import File"); btn_i.clicked.connect(self._import); il.addWidget(btn_i)
        btn_d=QPushButton("Load Demo DB"); btn_d.clicked.connect(self._demo); il.addWidget(btn_d); vb.addWidget(ig)
        bc=QPushButton("Close"); bc.clicked.connect(self.accept); vb.addWidget(bc,alignment=Qt.AlignRight)

    def _refresh(self):
        self.tbl.setRowCount(0)
        for r in self.db.get_ref_dbs():
            i=self.tbl.rowCount(); self.tbl.insertRow(i)
            self.tbl.setItem(i,0,QTableWidgetItem(r['db_name'])); self.tbl.setItem(i,1,QTableWidgetItem(str(r['count'])))
            self.tbl.setItem(i,2,QTableWidgetItem("Hash-based")); self.tbl.setItem(i,3,QTableWidgetItem((r['added'] or '')[:10]))

    def _add(self):
        name=self.dbn.currentText().strip(); val=self.hv.text().strip()
        if not name or not val: QMessageBox.warning(self,"Error","DB Name and Hash Value required."); return
        self.db.add_ref_hash(name,val,self.ht.currentText(),self.lbl_ed.text().strip(),self.sv.currentText())
        self.hv.clear(); self.lbl_ed.clear(); self._refresh()

    def _import(self):
        fp,_=QFileDialog.getOpenFileName(self,"Import Hash File","","Text/CSV (*.txt *.csv);;All (*)")
        if not fp: return
        name=self.dbn.currentText().strip() or "Imported"; count=0
        with open(fp,'r') as f:
            for line in f:
                v=line.strip().split(',')[0].strip()
                if v and len(v) in (16,32,64): self.db.add_ref_hash(name,v,self.ht.currentText(),"","medium"); count+=1
        QMessageBox.information(self,"Done",f"Imported {count} hashes."); self._refresh()

    def _demo(self):
        for d in [("NCMEC/CSAM","a3f1234567890abcdef1234567890abc","md5","Demo-CSAM-1","critical"),
                  ("NCMEC/CSAM","deadbeef1234567890abcdef12345678","md5","Demo-CSAM-2","critical"),
                  ("PhotoDNA","0000ffff0000ffff","phash","PhotoDNA-Ref-1","high"),
                  ("PhotoDNA","aaaa5555aaaa5555","phash","PhotoDNA-Ref-2","high"),
                  ("MD5-NSRL","9e107d9d372bb6826bd81d3542a419d6","md5","NSRL-Known-1","low"),
                  ("KFF-Ignore","d41d8cd98f00b204e9800998ecf8427e","md5","Empty-File","low")]:
            self.db.add_ref_hash(*d)
        QMessageBox.information(self,"Done","Loaded 6 demo reference hashes."); self._refresh()


# ─── Create Hash DB Dialog ────────────────────────────────────────────────────
class CreateHashDBDialog(QDialog):
    def __init__(self,db,ids,parent=None):
        super().__init__(parent); self.db=db; self.ids=ids
        self.setWindowTitle("Create Custom Hash Database"); self.setMinimumWidth(480); self.setStyleSheet(DARK_STYLE); self._build()

    def _build(self):
        vb=QVBoxLayout(self); vb.setSpacing(12)
        hdr=QLabel("CREATE CUSTOM HASH DATABASE"); hdr.setStyleSheet(f"font-size:14px;font-weight:bold;color:{ACC};"); vb.addWidget(hdr)
        info=QLabel(f"Build a reference DB from {len(self.ids)} selected media item(s).\nUse this DB to flag matching images in future imports.")
        info.setWordWrap(True); info.setStyleSheet(f"color:{FG1};"); vb.addWidget(info)
        fg=QFormLayout(); fg.setSpacing(10)
        self.name_ed=QLineEdit(); self.name_ed.setPlaceholderText("e.g. Case-2024-Evidence")
        self.ht=QComboBox(); self.ht.addItems(["md5","sha256","phash","dhash"])
        fg.addRow("Database Name *:",self.name_ed); fg.addRow("Hash Type:",self.ht); vb.addLayout(fg)
        br=QHBoxLayout(); bc=QPushButton("Cancel"); bc.clicked.connect(self.reject)
        bk=QPushButton("Create Database"); bk.setObjectName("btnPrimary"); bk.clicked.connect(self._create)
        br.addStretch(); br.addWidget(bc); br.addWidget(bk); vb.addLayout(br)

    def _create(self):
        name=self.name_ed.text().strip()
        if not name: QMessageBox.warning(self,"Error","Name required."); return
        n=self.db.create_hash_db_from_ids(self.ids,name,self.ht.currentText())
        QMessageBox.information(self,"Done",f"Created '{name}' with {n} hash entries."); self.accept()


# ─── Report Dialog ────────────────────────────────────────────────────────────
class ReportDialog(QDialog):
    """Full-featured report builder with live preview, tag stats, and export options."""

    def __init__(self, db, case_id, filters, parent=None):
        super().__init__(parent)
        self.db      = db
        self.cid     = case_id
        self.filters = filters
        self.setWindowTitle("Report Builder")
        self.setMinimumSize(1080, 760)
        self.setStyleSheet(DARK_STYLE)
        self._media  = []
        self._stats  = {}
        self._case   = {}
        self._build()
        self._load_data()
        self._render_preview()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        root = QHBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # ── Left: controls panel ──
        ctrl = QWidget(); ctrl.setFixedWidth(300)
        ctrl.setStyleSheet(f"background:{BG2}; border-right:1px solid {BRD};")
        cvb = QVBoxLayout(ctrl); cvb.setContentsMargins(14,14,14,14); cvb.setSpacing(10)

        hdr = QLabel("REPORT BUILDER")
        hdr.setStyleSheet(f"font-size:14px;font-weight:bold;color:{ACC};letter-spacing:2px;")
        cvb.addWidget(hdr)

        # Scope
        scope_grp = QGroupBox("REPORT SCOPE")
        sg = QVBoxLayout(scope_grp); sg.setSpacing(6)
        self.rb_all  = QCheckBox("All media in case");  self.rb_all.setChecked(True)
        self.rb_filt = QCheckBox("Current filtered view only")
        self.rb_flag = QCheckBox("Flagged / Hash Matches only")
        self.rb_face = QCheckBox("Images with faces only")
        for cb in [self.rb_all, self.rb_filt, self.rb_flag, self.rb_face]:
            cb.stateChanged.connect(self._on_scope_change); sg.addWidget(cb)
        cvb.addWidget(scope_grp)

        # Sections
        sec_grp = QGroupBox("INCLUDE SECTIONS")
        sl = QVBoxLayout(sec_grp); sl.setSpacing(5)
        self.chk_summary   = QCheckBox("Executive Summary");      self.chk_summary.setChecked(True)
        self.chk_stats     = QCheckBox("Case Statistics");         self.chk_stats.setChecked(True)
        self.chk_tag_stats = QCheckBox("Tag Analysis");            self.chk_tag_stats.setChecked(True)
        self.chk_table     = QCheckBox("Evidence Table");          self.chk_table.setChecked(True)
        self.chk_flagged   = QCheckBox("Flagged Items Section");   self.chk_flagged.setChecked(True)
        self.chk_thumbs    = QCheckBox("Thumbnail Sheet");         self.chk_thumbs.setChecked(False)
        self.chk_exif      = QCheckBox("EXIF Metadata Detail");    self.chk_exif.setChecked(False)
        for cb in [self.chk_summary, self.chk_stats, self.chk_tag_stats, self.chk_table,
                   self.chk_flagged, self.chk_thumbs, self.chk_exif]:
            cb.stateChanged.connect(self._render_preview); sl.addWidget(cb)
        cvb.addWidget(sec_grp)

        # Report metadata
        meta_grp = QGroupBox("REPORT METADATA")
        ml2 = QFormLayout(meta_grp); ml2.setSpacing(8)
        self.title_ed    = QLineEdit("Digital Evidence Report"); ml2.addRow("Title:", self.title_ed)
        self.analyst_ed  = QLineEdit(); ml2.addRow("Analyst:", self.analyst_ed)
        self.agency_ed   = QLineEdit(); ml2.addRow("Agency:", self.agency_ed)
        self.ref_ed      = QLineEdit(); ml2.addRow("Reference:", self.ref_ed)
        self.classify_cb = QComboBox()
        self.classify_cb.addItems(["UNCLASSIFIED","CONFIDENTIAL","RESTRICTED","OFFICIAL USE ONLY"])
        ml2.addRow("Classification:", self.classify_cb)
        cvb.addWidget(meta_grp)

        cvb.addStretch()

        # Buttons
        btn_prev  = QPushButton("🔄  Refresh Preview"); btn_prev.clicked.connect(self._render_preview)
        btn_html  = QPushButton("💾  Save HTML Report"); btn_html.setObjectName("btnPrimary"); btn_html.clicked.connect(self._save_html)
        btn_csv   = QPushButton("📋  Export CSV");       btn_csv.clicked.connect(self._save_csv)
        btn_hash  = QPushButton("🔑  Export Hash List"); btn_hash.clicked.connect(self._save_hashes)
        btn_close = QPushButton("Close");                btn_close.clicked.connect(self.accept)
        for b in [btn_prev, btn_html, btn_csv, btn_hash, btn_close]:
            cvb.addWidget(b)

        root.addWidget(ctrl)

        # ── Right: preview ──
        right = QWidget(); rvb = QVBoxLayout(right); rvb.setContentsMargins(0,0,0,0); rvb.setSpacing(0)
        prev_hdr = QLabel("  LIVE PREVIEW")
        prev_hdr.setStyleSheet(f"background:{BG2};color:{FG1};font-size:11px;letter-spacing:2px;padding:8px 12px;border-bottom:1px solid {BRD};font-weight:bold;")
        rvb.addWidget(prev_hdr)
        self.preview = QTextEdit(); self.preview.setReadOnly(True)
        self.preview.setStyleSheet(f"background:#ffffff; color:#111; font-family:Arial,sans-serif; font-size:12px; border:none;")
        rvb.addWidget(self.preview)
        root.addWidget(right)

    # ── Data loading ──────────────────────────────────────────────────────────
    def _get_filters(self):
        f = dict(self.filters); f['case_id'] = self.cid
        if self.rb_all.isChecked():
            f.pop('search', None); f.pop('category', None); f.pop('face_only', None); f.pop('flagged_only', None)
        elif self.rb_flag.isChecked():
            f['flagged_only'] = True
        elif self.rb_face.isChecked():
            f['face_only'] = True
        return f

    def _load_data(self):
        self._media  = self.db.get_all_media(self._get_filters())
        self._stats  = self.db.get_stats(self.cid)
        cases        = self.db.get_cases()
        self._case   = next((c for c in cases if c['id']==self.cid),
                            {'name':'Default','investigator':'','case_number':'','status':'active','description':''})
        self._tags   = self.db.get_all_custom_tags(self.cid)
        self._ref_dbs = self.db.get_ref_dbs()

    def _on_scope_change(self):
        # mutual exclusion for scope checkboxes
        sender = self.sender()
        if sender.isChecked():
            for cb in [self.rb_all, self.rb_filt, self.rb_flag, self.rb_face]:
                if cb is not sender: cb.setChecked(False)
        self._load_data(); self._render_preview()

    # ── Preview renderer ──────────────────────────────────────────────────────
    def _render_preview(self):
        self._load_data()
        html = self._build_html(preview=True)
        self.preview.setHtml(html)

    def _build_html(self, preview=False):
        now   = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        case  = self._case
        stats = self._stats
        media = self._media
        tags  = self._tags
        clf   = self.classify_cb.currentText()
        clf_color = {"UNCLASSIFIED":"#388e3c","CONFIDENTIAL":"#f57c00",
                     "RESTRICTED":"#d32f2f","OFFICIAL USE ONLY":"#1565c0"}.get(clf,"#388e3c")

        flagged = [m for m in media if m.get('csam_flag') or m.get('hash_match')]
        faces   = [m for m in media if m.get('face_count',0) > 0]

        # ── cat breakdown ──
        cat_rows_html = ""
        total = max(stats.get('total',1),1)
        for cat, cnt in sorted((stats.get('by_category') or {}).items(), key=lambda x:-x[1]):
            col = CATEGORY_COLORS.get(cat,'#607D8B')
            pct = int(cnt/total*100)
            cat_rows_html += f"""<tr>
  <td><span style="color:{col};font-weight:bold">■</span> {cat}</td>
  <td style="text-align:right;font-weight:bold">{cnt}</td>
  <td style="text-align:right;color:#888">{pct}%</td>
  <td style="padding-left:8px"><div style="background:#e0e0e0;border-radius:3px;height:8px;width:120px">
    <div style="background:{col};width:{pct}%;height:8px;border-radius:3px"></div></div></td>
</tr>"""

        # ── tag stats ──
        tag_html = ""
        if self.chk_tag_stats.isChecked() and tags:
            tag_html = '<h2 style="color:#1f6feb;border-bottom:2px solid #1f6feb;padding-bottom:4px">Tag Analysis</h2>'
            tag_html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0">'
            for tag, count in tags[:40]:
                tag_html += f'<span style="background:#e3f2fd;border:1px solid #90caf9;border-radius:12px;padding:3px 12px;font-size:12px;color:#1565c0"><b>{tag}</b> <span style="color:#888;font-size:11px">×{count}</span></span>'
            tag_html += '</div>'
            if len(tags) > 40:
                tag_html += f'<p style="color:#888;font-size:11px">… and {len(tags)-40} more tags</p>'

        # ── flagged section ──
        flagged_html = ""
        if self.chk_flagged.isChecked() and flagged:
            flagged_html = f'<h2 style="color:#d32f2f;border-bottom:2px solid #d32f2f;padding-bottom:4px">⚠ Flagged Items ({len(flagged)})</h2>'
            flagged_html += '<table style="width:100%;border-collapse:collapse;margin-top:8px">'
            flagged_html += '<tr style="background:#fce4e4"><th>Filename</th><th>Category</th><th>Hash Match</th><th>CSAM</th><th>Faces</th><th>Imported</th></tr>'
            for m in flagged[:100]:
                cat_col = CATEGORY_COLORS.get(m.get('category',''),'#607D8B')
                flagged_html += f'''<tr style="border-bottom:1px solid #f5c6c6">
  <td style="font-family:monospace;font-size:11px">{m["filename"]}</td>
  <td style="color:{cat_col};font-weight:bold">{m.get("category","")}</td>
  <td style="font-family:monospace;font-size:10px;color:#d32f2f">{(m.get("hash_match") or "")[:50]}</td>
  <td style="color:#d32f2f;font-weight:bold;text-align:center">{"YES" if m.get("csam_flag") else "—"}</td>
  <td style="text-align:center">{m.get("face_count",0)}</td>
  <td style="color:#888;font-size:11px">{(m.get("imported_at") or "")[:16]}</td>
</tr>'''
            flagged_html += '</table>'

        # ── evidence table ──
        table_html = ""
        if self.chk_table.isChecked():
            limit = 200
            table_html = f'<h2 style="color:#1f6feb;border-bottom:2px solid #1f6feb;padding-bottom:4px">Evidence Table ({len(media)} records{", first "+str(limit)+" shown" if len(media)>limit else ""})</h2>'
            table_html += '<table style="width:100%;border-collapse:collapse;font-size:11px">'
            table_html += '<tr style="background:#e8eaf6"><th>Filename</th><th>Category</th><th>Faces</th><th>Object Tags</th><th>Custom Tags</th><th>Hash Match</th><th>Imported</th></tr>'
            for i, m in enumerate(media[:limit]):
                bg   = "#fce4e4" if (m.get('csam_flag') or m.get('hash_match')) else ("#f3e5f5" if m.get('face_count',0)>0 else ("" if i%2==0 else "#f5f5f5"))
                col  = CATEGORY_COLORS.get(m.get('category',''),'#607D8B')
                atags = ', '.join(json.loads(m.get('object_tags') or '[]'))[:50]
                ctags = ', '.join(json.loads(m.get('custom_tags') or '[]'))[:40]
                table_html += f'''<tr style="background:{bg};border-bottom:1px solid #e0e0e0">
  <td style="font-family:monospace;font-size:10px;max-width:180px;overflow:hidden">{m["filename"]}</td>
  <td style="color:{col};font-weight:bold;white-space:nowrap">{m.get("category","")}</td>
  <td style="text-align:center">{m.get("face_count",0)}</td>
  <td style="color:#555;font-size:10px">{atags}</td>
  <td style="color:#1565c0;font-size:10px">{ctags}</td>
  <td style="font-family:monospace;font-size:9px;color:#d32f2f">{(m.get("hash_match") or "")[:30]}</td>
  <td style="color:#888;font-size:10px;white-space:nowrap">{(m.get("imported_at") or "")[:16]}</td>
</tr>'''
            table_html += '</table>'

        # ── thumbnail sheet ──
        thumb_html = ""
        if self.chk_thumbs.isChecked() and not preview:
            import base64
            thumb_html = '<h2 style="color:#1f6feb;border-bottom:2px solid #1f6feb;padding-bottom:4px">Thumbnail Sheet</h2>'
            thumb_html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin:12px 0">'
            for m in media[:60]:
                try:
                    pil = PILImage.open(m['filepath']).convert('RGB')
                    pil.thumbnail((100,100))
                    import io
                    buf = io.BytesIO(); pil.save(buf,'JPEG',quality=60)
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    col = CATEGORY_COLORS.get(m.get('category',''),'#607D8B')
                    thumb_html += f'<div style="border:2px solid {col};border-radius:4px;padding:2px;text-align:center;width:104px">'
                    thumb_html += f'<img src="data:image/jpeg;base64,{b64}" style="width:100px;height:100px;object-fit:cover">'
                    thumb_html += f'<div style="font-size:9px;color:#555;overflow:hidden;white-space:nowrap">{m["filename"][:16]}</div></div>'
                except: pass
            thumb_html += '</div>'

        # ── EXIF section ──
        exif_html = ""
        if self.chk_exif.isChecked():
            exif_html = '<h2 style="color:#1f6feb;border-bottom:2px solid #1f6feb;padding-bottom:4px">EXIF Metadata</h2>'
            exif_html += '<table style="width:100%;border-collapse:collapse;font-size:11px">'
            exif_html += '<tr style="background:#e8eaf6"><th>Filename</th><th>Date/Time</th><th>Camera</th><th>GPS</th><th>Software</th></tr>'
            for m in media[:100]:
                ex = json.loads(m.get('exif_data') or '{}')
                exif_html += f'''<tr style="border-bottom:1px solid #e0e0e0">
  <td style="font-family:monospace;font-size:10px">{m["filename"]}</td>
  <td style="font-size:10px">{ex.get("DateTimeOriginal","—")}</td>
  <td style="font-size:10px">{ex.get("Make","")+" "+ex.get("Model","") or "—"}</td>
  <td style="font-size:10px">{ex.get("GPSLatitude","—")}</td>
  <td style="font-size:10px">{ex.get("Software","—")}</td>
</tr>'''
            exif_html += '</table>'

        # ── Ref DB summary ──
        ref_html = ""
        for r in self._ref_dbs:
            ref_html += f'<tr><td>{r["db_name"]}</td><td style="text-align:right">{r["count"]}</td><td style="color:#888">{(r["added"] or "")[:10]}</td></tr>'

        # ── Assemble ──
        clf_badge = f'<div style="background:{clf_color};color:white;padding:4px 16px;border-radius:4px;font-weight:bold;font-size:11px;letter-spacing:1px;display:inline-block;margin-bottom:12px">{clf}</div>'

        summary_html = ""
        if self.chk_summary.isChecked():
            summary_html = f"""
<div style="background:#e8f5e9;border-left:4px solid #4caf50;padding:12px 16px;border-radius:4px;margin:12px 0">
<b>EXECUTIVE SUMMARY</b><br><br>
This report documents digital media evidence for <b>{case.get('name','')}</b>
(Case No. {case.get('case_number','—')}).
A total of <b>{stats.get('total',0)} media files</b> were examined,
of which <b>{stats.get('flagged',0)} were flagged</b> through hash matching or CSAM detection.
<b>{stats.get('with_faces',0)} images</b> contained identifiable faces.
The case contains <b>{len(tags)} custom tag type(s)</b> across all evidence.
</div>"""

        stats_html = ""
        if self.chk_stats.isChecked():
            stats_html = f"""
<h2 style="color:#1f6feb;border-bottom:2px solid #1f6feb;padding-bottom:4px">Case Statistics</h2>
<div style="display:flex;gap:12px;flex-wrap:wrap;margin:12px 0">
  {"".join(f'<div style="border:1px solid #e0e0e0;border-top:3px solid {col};border-radius:6px;padding:10px 18px;min-width:110px;text-align:center"><div style="font-size:24px;font-weight:bold;color:{col}">{val}</div><div style="font-size:10px;color:#888;letter-spacing:1px">{lbl}</div></div>'
    for lbl,val,col in [("TOTAL",str(stats.get('total',0)),"#1f6feb"),("FLAGGED",str(stats.get('flagged',0)),"#d32f2f"),
                         ("WITH FACES",str(stats.get('with_faces',0)),"#388e3c"),("REF HASHES",str(stats.get('ref_hashes',0)),"#7b1fa2")])}
</div>
<table style="width:50%;border-collapse:collapse;font-size:12px;margin-top:8px">
  <tr style="background:#e8eaf6"><th style="text-align:left;padding:6px">Category</th><th>Count</th><th>%</th><th>Bar</th></tr>
  {cat_rows_html}
</table>
<br>
<table style="width:50%;border-collapse:collapse;font-size:12px">
  <tr style="background:#e8eaf6"><th style="text-align:left;padding:6px">Reference DB</th><th>Entries</th><th>Since</th></tr>
  {ref_html}
</table>"""

        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<title>{self.title_ed.text()}</title>
<style>
  body {{margin:0;padding:20px 28px;background:#fff;color:#111;font-family:Arial,'Segoe UI',sans-serif;font-size:13px;line-height:1.5}}
  h1 {{color:#0d1117;margin-bottom:4px}}
  h2 {{margin-top:24px;margin-bottom:8px;font-size:14px}}
  table th {{padding:6px 10px;text-align:left;font-size:11px;letter-spacing:0.5px}}
  table td {{padding:5px 10px}}
  .meta {{color:#555;font-size:12px;margin:2px 0}}
  @media print {{ .no-print {{display:none}} }}
</style></head><body>
{clf_badge}
<h1>{self.title_ed.text()}</h1>
<p class="meta"><b>Case:</b> {case.get('name','')} &nbsp;|&nbsp; <b>Case No:</b> {case.get('case_number','—')} &nbsp;|&nbsp; <b>Status:</b> {case.get('status','')}</p>
<p class="meta"><b>Investigator:</b> {case.get('investigator','—')} &nbsp;|&nbsp; <b>Analyst:</b> {self.analyst_ed.text() or '—'} &nbsp;|&nbsp; <b>Agency:</b> {self.agency_ed.text() or '—'}</p>
<p class="meta"><b>Reference No:</b> {self.ref_ed.text() or '—'} &nbsp;|&nbsp; <b>Generated:</b> {now} &nbsp;|&nbsp; <b>Records:</b> {len(media)}</p>
<hr style="border:none;border-top:2px solid #1f6feb;margin:14px 0">
{summary_html}
{stats_html}
{tag_html}
{flagged_html}
{table_html}
{thumb_html}
{exif_html}
<hr style="border:none;border-top:1px solid #ccc;margin-top:28px">
<p style="font-size:10px;color:#aaa;text-align:center">{APP_NAME} v{APP_VERSION} — {clf} — Generated {now}</p>
</body></html>"""
        return html

    # ── Save actions ──────────────────────────────────────────────────────────
    def _save_html(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Save HTML Report", "evidence_report.html", "HTML (*.html)")
        if not fp: return
        html = self._build_html(preview=False)
        with open(fp, 'w', encoding='utf-8') as f: f.write(html)
        QMessageBox.information(self, "Saved", f"Report saved to:\n{fp}\n\n{len(self._media)} records included.")

    def _save_csv(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Save CSV", "evidence.csv", "CSV (*.csv)")
        if not fp: return
        n = self.db.export_csv(fp, self._get_filters())
        QMessageBox.information(self, "Saved", f"Exported {n} records to:\n{fp}")

    def _save_hashes(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Save Hash List", "hashes.txt", "Text (*.txt)")
        if not fp: return
        count = 0
        with open(fp, 'w') as f:
            for m in self._media:
                h = m.get('md5')
                if h: f.write(h + '\n'); count += 1
        QMessageBox.information(self, "Saved", f"Exported {count} MD5 hashes to:\n{fp}")


# ─── Statistics Dashboard ─────────────────────────────────────────────────────
class Dashboard(QWidget):
    def __init__(self,db):
        super().__init__(); self.db=db; self._cid=None; self._build()

    def set_case(self,cid): self._cid=cid

    def _build(self):
        vb=QVBoxLayout(self); vb.setContentsMargins(16,36,26,26); vb.setSpacing(14)
        t=QLabel("CASE STATISTICS"); t.setStyleSheet(f"font-size:15px;font-weight:bold;color:{ACC};letter-spacing:2px;"); vb.addWidget(t)
        self.cards=QGridLayout(); self.cards.setSpacing(15); vb.addLayout(self.cards)
        cg=QGroupBox("CATEGORY BREAKDOWN"); self.cat_vb=QVBoxLayout(cg); self.cat_vb.setSpacing(25); vb.addWidget(cg)
        lg=QGroupBox("ACTIVITY LOG"); ll=QVBoxLayout(lg)
        self.log=QTextEdit(); self.log.setReadOnly(True); self.log.setMaximumHeight(130); self.log.setFont(QFont("Courier New",10)); ll.addWidget(self.log)
        vb.addWidget(lg); vb.addStretch(); self.refresh()

    def refresh(self):
        s=self.db.get_stats(self._cid)
        for i in reversed(range(self.cards.count())):
            w=self.cards.itemAt(i).widget()
            if w: w.deleteLater()
        for i,(lbl,val,col) in enumerate([("TOTAL MEDIA",str(s.get('total',0)),ACC),("FLAGGED",str(s.get('flagged',0)),ERR),
                                          ("WITH FACES",str(s.get('with_faces',0)),OK),("REF HASHES",str(s.get('ref_hashes',0)),"#d2a8ff"),("CASES",str(s.get('cases',0)),WARN)]):
            self.cards.addWidget(self._card(lbl,val,col),0,i)
        for i in reversed(range(self.cat_vb.count())):
            w=self.cat_vb.itemAt(i).widget()
            if w: w.deleteLater()
        total=max(s.get('total',1),1)
        for cat,cnt in (s.get('by_category') or {}).items():
            col=CATEGORY_COLORS.get(cat,'#607D8B'); row=QWidget(); rl=QHBoxLayout(row); rl.setContentsMargins(0,1,0,1)
            lbl=QLabel(cat); lbl.setFixedWidth(172); lbl.setStyleSheet(f"color:{col};font-size:12px;")
            bar=QProgressBar(); bar.setValue(int(cnt/total*100)); bar.setTextVisible(False)
            bar.setStyleSheet(f"QProgressBar{{background:{BG3};border:none;border-radius:3px;height:6px;}}QProgressBar::chunk{{background:{col};border-radius:3px;}}")
            num=QLabel(str(cnt)); num.setFixedWidth(36); num.setStyleSheet(f"color:{FG1};font-size:12px;")
            rl.addWidget(lbl); rl.addWidget(bar); rl.addWidget(num); self.cat_vb.addWidget(row)

    def _card(self,label,value,color):
        f=QFrame(); f.setStyleSheet(f"QFrame{{background:{BG2};border:1px solid {BRD};border-top:3px solid {color};border-radius:8px;}}")
        vb=QVBoxLayout(f); vb.setContentsMargins(10,10,10,10)
        v=QLabel(value); v.setStyleSheet(f"font-size:26px;font-weight:bold;color:{color};"); v.setAlignment(Qt.AlignCenter); vb.addWidget(v)
        l=QLabel(label); l.setStyleSheet(f"font-size:12px;color:{FG1};letter-spacing:1px;"); l.setAlignment(Qt.AlignCenter); vb.addWidget(l)
        return f

    def add_log(self,msg):
        ts=datetime.datetime.now().strftime("%H:%M:%S")
        self.log.append(f"[{ts}]  {msg}")


# ─── Main Window ─────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db=Database(DB_PATH); self.imp_worker=None; self.vs_worker=None
        self.cur_case=1; self.filters={}
        self._build(); self._connect(); self._refresh(); self._stats(); self._case_lbl()
        self.statusBar().showMessage(f"  {APP_NAME} v{APP_VERSION}  |  DB: {DB_PATH}")

    def _build(self):
        self.setWindowTitle(f"{APP_NAME} — Digital Media Analysis Platform")
        self.setMinimumSize(1600,900); self.setStyleSheet(DARK_STYLE)
        self._menu(); self._toolbar()
        cw=QWidget(); self.setCentralWidget(cw)
        mvb=QVBoxLayout(cw); mvb.setContentsMargins(0,0,0,0); mvb.setSpacing(0)

        # Search Panel
        self.sp=SearchPanel(); mvb.addWidget(self.sp)

        # Main Splitter
        self.spl=QSplitter(Qt.Horizontal); mvb.addWidget(self.spl)

        # ── Left: Navigation ──
        nav_w=QWidget(); nav_w.setMaximumWidth(232); nav_w.setMinimumWidth(170); nav_w.setStyleSheet(f"background:{BG2};")
        nvb=QVBoxLayout(nav_w); nvb.setContentsMargins(0,0,0,0); nvb.setSpacing(0)
        hdr=QLabel("  NAVIGATION"); hdr.setStyleSheet(f"background:{BG2};color:{FG1};font-size:11px;letter-spacing:2px;padding:10px 8px 8px;border-bottom:1px solid {BRD};font-weight:bold;")
        nvb.addWidget(hdr)
        self.nav=QTreeWidget(); self.nav.setHeaderHidden(True)
        self.nav.setStyleSheet(f"QTreeWidget{{background:{BG2};border:none;font-size:14px;outline:none;}}QTreeWidget::item{{padding:6px 6px;margin:0px 2px;border-radius:3px;font-size:14px;}}QTreeWidget::item:selected{{background:{ACC};color:white;}}QTreeWidget::item:hover:!selected{{background:{BG3};}}QTreeWidget::branch{{background:{BG2};}}")
        self.nav.setUniformRowHeights(True)
        self.nav.setIndentation(14)
        self._build_nav(); nvb.addWidget(self.nav); self.spl.addWidget(nav_w)

        # ── Center ──
        ctr=QWidget(); cvb=QVBoxLayout(ctr); cvb.setContentsMargins(0,0,0,0); cvb.setSpacing(0)
        self.vtabs=QTabWidget()
        self.grid=ThumbnailWidget(); self.vtabs.addTab(self.grid,"  GRID VIEW  ")
        self.ltbl=QTableWidget(0,9)
        self.ltbl.setHorizontalHeaderLabels(["Filename","Size","Dimensions","Category","Faces","Object Tags","Custom Tags","Hash Match","Imported"])
        self.ltbl.horizontalHeader().setStretchLastSection(True)
        self.ltbl.setSelectionBehavior(QAbstractItemView.SelectRows); self.ltbl.setAlternatingRowColors(True)
        self.ltbl.setEditTriggers(QAbstractItemView.NoEditTriggers); self.ltbl.verticalHeader().setVisible(False)
        self.ltbl.verticalHeader().setDefaultSectionSize(28); self.ltbl.itemSelectionChanged.connect(self._list_sel)
        self.vtabs.addTab(self.ltbl,"  LIST VIEW  ")
        self.dash=Dashboard(self.db); self.vtabs.addTab(self.dash,"  DASHBOARD  ")
        cvb.addWidget(self.vtabs)
        # Progress strip
        ps=QWidget(); ps.setStyleSheet(f"background:{BG2};border-top:1px solid {BRD};")
        pl=QHBoxLayout(ps); pl.setContentsMargins(10,4,10,4); pl.setSpacing(8)
        self.prog_lbl=QLabel("Ready"); self.prog_lbl.setStyleSheet(f"color:{FG1};font-size:12px;"); pl.addWidget(self.prog_lbl)
        self.prog_bar=QProgressBar(); self.prog_bar.setTextVisible(False); self.prog_bar.setFixedHeight(6); pl.addWidget(self.prog_bar)
        self.btn_cancel=QPushButton("Cancel"); self.btn_cancel.setObjectName("btnDanger"); self.btn_cancel.setFixedWidth(72)
        self.btn_cancel.clicked.connect(self._cancel); self.btn_cancel.hide(); pl.addWidget(self.btn_cancel)
        cvb.addWidget(ps); self.spl.addWidget(ctr)

        # ── Right: Detail ──
        self.detail=DetailPanel(self.db); self.detail.setMinimumWidth(290); self.detail.setMaximumWidth(370)
        self.spl.addWidget(self.detail); self.spl.setSizes([200,790,330])

        # Status bar
        self.setStatusBar(QStatusBar())
        self.case_lbl_w=QLabel(); self.case_lbl_w.setStyleSheet(f"color:{ACC};font-size:12px;padding:0 12px;")
        self.cnt_lbl=QLabel(); self.cnt_lbl.setStyleSheet(f"color:{FG1};font-size:12px;padding:0 12px;")
        self.statusBar().addPermanentWidget(self.case_lbl_w); self.statusBar().addPermanentWidget(self.cnt_lbl)

    def _build_nav(self):
        self.nav.clear()
        def sec(label):
            it=QTreeWidgetItem([f"  {label}"]); it.setForeground(0,QColor(FG1))
            it.setFont(0,QFont("Segoe UI",10,QFont.Bold)); it.setFlags(it.flags() & ~Qt.ItemIsSelectable); return it

        cs=sec("CASES")
        for c in self.db.get_cases():
            ci=QTreeWidgetItem(cs,[f"  📁  {c['name']}"]);
            ci.setData(0,Qt.UserRole,('case',c['id'])); ci.setForeground(0,QColor(ACC if c['id']==self.cur_case else FG0))
            ci.setToolTip(0,f"{c['name']}\nInvestigator: {c.get('investigator','')}")
        self.nav.addTopLevelItem(cs); cs.setExpanded(True)

        cats=sec("CATEGORIES")
        ai=QTreeWidgetItem(cats,["  ◈  All Media"]); ai.setForeground(0,QColor(FG0)); ai.setData(0,Qt.UserRole,('filter',{}))
        for cat,col in CATEGORY_COLORS.items():
            ci=QTreeWidgetItem(cats,[f"  ●  {cat}"]); ci.setForeground(0,QColor(col)); ci.setData(0,Qt.UserRole,('filter',{'category':cat}))
        self.nav.addTopLevelItem(cats); cats.setExpanded(True)

        flts=sec("QUICK FILTERS")
        for label,data,col in [("  👤  Images with Faces",{'face_only':True},FG0),
                                ("  ⚠   Hash Matches",{'flagged_only':True},ERR),
                                ("  ✔  Reviewed",{'category':'Reviewed'},OK),
                                ("  🔴  CSAM Hits",{'category':'CSAM Hit'},"#B71C1C"),
                                ("  🕵  Person of Interest",{'category':'Person of Interest'},"#4fc3f7")]:
            fi=QTreeWidgetItem(flts,[label]); fi.setForeground(0,QColor(col)); fi.setData(0,Qt.UserRole,('filter',data))
        self.nav.addTopLevelItem(flts); flts.setExpanded(True)

        # ── Custom Tags (collapsible, dynamic) ──
        tag_pairs = self.db.get_all_custom_tags(self.cur_case)
        ctags_sec = sec("CUSTOM TAGS")
        ctags_sec.setToolTip(0, "Filter by custom tag applied to images")
        if tag_pairs:
            all_ti = QTreeWidgetItem(ctags_sec, ["  🏷  All Tagged"])
            all_ti.setForeground(0, QColor("#d2a8ff"))
            all_ti.setData(0, Qt.UserRole, ('tag_filter', None))
            for tag, count in tag_pairs:
                short = tag[:22] + ("…" if len(tag) > 22 else "")
                ti = QTreeWidgetItem(ctags_sec, [f"  #  {short}  ({count})"])
                ti.setForeground(0, QColor("#a5d6ff"))
                ti.setData(0, Qt.UserRole, ('tag_filter', tag))
                ti.setToolTip(0, f"Filter: custom tag = '{tag}' ({count} image{'s' if count!=1 else ''})")
        else:
            empty = QTreeWidgetItem(ctags_sec, ["  (no tags yet)"])
            empty.setForeground(0, QColor(FG1))
            empty.setFlags(empty.flags() & ~Qt.ItemIsSelectable)
        self.nav.addTopLevelItem(ctags_sec)
        ctags_sec.setExpanded(True)

    def _menu(self):
        mb=self.menuBar()
        fm=mb.addMenu("File")
        fm.addAction("Import Images…",self._imp_files,"Ctrl+O")
        fm.addAction("Import Folder…",self._imp_folder,"Ctrl+Shift+O")
        fm.addSeparator()
        fm.addAction("Export / Report…",self._export,"Ctrl+E")
        fm.addSeparator()
        fm.addAction("Exit",self.close,"Ctrl+Q")
        cm=mb.addMenu("Case")
        cm.addAction("Case Manager…",self._case_mgr,"Ctrl+M")
        cm.addAction("New Case…",self._new_case_quick)
        cm.addSeparator()
        cm.addAction("Refresh",self._rebuild_nav_refresh)
        am=mb.addMenu("Analysis")
        am.addAction("Re-analyze Selected",self._reanalyze)
        am.addAction("Hash Check All vs. Ref DB",self._hash_check)
        am.addAction("Re-tag Objects (Selected/All)",self._retag)
        am.addSeparator()
        am.addAction("Create Hash DB from Selection…",self._create_hashdb)
        am.addAction("Reference Database Manager…",self._refdb)
        vm=mb.addMenu("View")
        vm.addAction("Refresh", self._refresh, "F5")
        vm.addAction("Dashboard",lambda:self.vtabs.setCurrentIndex(2))
        vm.addSeparator()
        vm.addAction("Clear All in Case",self._clear_all)
        mb.addMenu("Help").addAction("About",self._about)

    def _toolbar(self):
        tb=QToolBar(); tb.setMovable(False); self.addToolBar(tb)
        def btn(l,s,t=""): b=QPushButton(l); b.setToolTip(t); b.clicked.connect(s); tb.addWidget(b)
        btn("⊕  Import Images",self._imp_files); btn("⊕  Import Folder",self._imp_folder); tb.addSeparator()
        btn("📁  Case Manager",self._case_mgr); tb.addSeparator()
        btn("⚡  Hash Check All",self._hash_check,"Check all vs reference DBs")
        btn("🏷  Tag Objects",self._retag,"Run object classification on selected/all")
        btn("🗄  Ref DB",self._refdb,"Reference hash databases")
        btn("🔐  Create Hash DB",self._create_hashdb,"Create reference DB from selection"); tb.addSeparator()
        btn("📊  Dashboard",lambda:self.vtabs.setCurrentIndex(2))
        btn("📤  Export / Report",self._export); tb.addSeparator()
        btn("🔄  Refresh",self._refresh)

    def _connect(self):
        self.grid.item_selected.connect(self.detail.load)
        self.grid._cat_cb  = self._cat_change
        self.grid._del_cb  = lambda mid: (self.db.delete_media(mid), self._refresh(), self._stats())
        self.grid._db      = self.db
        self.grid.tags_updated.connect(self._on_tags_updated)
        self.detail.category_changed.connect(self._cat_change)
        self.detail.notes_changed.connect(lambda mid,n: self.db.update_media(mid,{'notes':n}))
        self.nav.itemClicked.connect(self._nav_click)
        self.sp.search_changed.connect(lambda f: self._set_filters(f))
        self.sp.visual_search_req.connect(self._visual_search)

    # ── Helpers ──
    def _on_tags_updated(self):
        """Called when custom tags change on any item — rebuild nav tags section and refresh grid."""
        self._build_nav()
        self._refresh()

    def _filt(self): f=dict(self.filters); f['case_id']=self.cur_case; return f
    def _sz(self,s):
        if s>1e6: return f"{s/1e6:.1f}MB"
        if s>1e3: return f"{s/1e3:.0f}KB"
        return f"{s}B"

    def _refresh(self):
        ml=self.db.get_all_media(self._filt())
        # Update grid's tag cache so context menu shows current tags
        self.grid._all_tags = self.db.get_all_custom_tags(self.cur_case)
        self.grid.load_media(ml); self._list_load(ml); self.cnt_lbl.setText(f"{len(ml)} items")

    def _list_load(self,ml):
        self.ltbl.setRowCount(0)
        for m in ml:
            r=self.ltbl.rowCount(); self.ltbl.insertRow(r)
            at=', '.join(json.loads(m.get('object_tags') or '[]'))[:40]
            ct=', '.join(json.loads(m.get('custom_tags') or '[]'))[:30]
            for col,val in enumerate([m['filename'],self._sz(m['size']),f"{m['width']}×{m['height']}",
                                       m['category'],str(m['face_count']),at,ct,m.get('hash_match') or '',(m.get('imported_at') or '')[:16]]):
                it=QTableWidgetItem(val); it.setData(Qt.UserRole,m['id'])
                if col==3: it.setForeground(QColor(CATEGORY_COLORS.get(val,'#607D8B')))
                if m.get('csam_flag') or m.get('hash_match'): it.setBackground(QColor('#1a0000'))
                self.ltbl.setItem(r,col,it)

    def _stats(self): self.dash.set_case(self.cur_case); self.dash.refresh()
    def _case_lbl(self):
        cases=self.db.get_cases(); c=next((x for x in cases if x['id']==self.cur_case),None)
        self.case_lbl_w.setText(f"  Case: {c['name'] if c else 'Default'}  ")

    def _set_filters(self,f): self.filters=f; self._refresh()

    def _list_sel(self):
        sel=self.ltbl.selectedItems()
        if sel:
            mid=sel[0].data(Qt.UserRole)
            if mid: self.detail.load(mid)

    def _nav_click(self,item,col):
        d=item.data(0,Qt.UserRole)
        if not d: return
        if d[0]=='filter':
            self.filters=d[1]; self._refresh()
        elif d[0]=='tag_filter':
            tag=d[1]
            self.filters = {'tagged_any': True} if tag is None else {'custom_tag': tag}
            self._refresh()
        elif d[0]=='case':
            self.cur_case=d[1]; self.filters={}
            self._case_lbl(); self._refresh(); self._stats(); self._build_nav()

    def _cat_change(self,mid,cat): self.db.update_media(mid,{'category':cat}); self._refresh(); self._stats()

    # ── Import ──
    def _imp_files(self):
        fps,_=QFileDialog.getOpenFileNames(self,"Import Images","","Images (*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp);;All (*)")
        if fps: self._start_import(fps)

    def _imp_folder(self):
        d=QFileDialog.getExistingDirectory(self,"Select Folder")
        if not d: return
        fps=[os.path.join(r,f) for r,ds,fs in os.walk(d) for f in fs if os.path.splitext(f)[1].lower() in SUPPORTED_EXT]
        if not fps: QMessageBox.information(self,"","No supported images found."); return
        self._start_import(fps)

    def _start_import(self,fps):
        if self.imp_worker and self.imp_worker.isRunning(): QMessageBox.warning(self,"Busy","Import in progress."); return
        self.prog_bar.setMaximum(len(fps)); self.prog_bar.setValue(0); self.btn_cancel.show()
        self.dash.add_log(f"Importing {len(fps)} files into case #{self.cur_case}…")
        self.imp_worker=ImportWorker(fps,self.db,self.cur_case)
        self.imp_worker.progress.connect(lambda c,t,n: (self.prog_bar.setValue(c), self.prog_lbl.setText(f"Importing ({c}/{t}): {n}")))
        self.imp_worker.finished.connect(self._imp_done)
        self.imp_worker.error.connect(lambda e: self.dash.add_log(f"⚠ {e}"))
        self.imp_worker.start()

    def _cancel(self):
        if self.imp_worker: self.imp_worker.stop()

    def _imp_done(self,ok,tot):
        self.prog_lbl.setText(f"Import complete: {ok}/{tot}"); self.btn_cancel.hide()
        self.dash.add_log(f"✓ Import done: {ok}/{tot}"); self._refresh(); self._stats()

    # ── Visual Search ──
    def _visual_search(self,qfp,thr,mode):
        ml=self.db.get_all_media(self._filt()); candidates=[m['filepath'] for m in ml if os.path.exists(m['filepath'])]
        if not candidates: QMessageBox.information(self,"","No media to search."); return
        self.prog_bar.setMaximum(0); self.prog_lbl.setText(f"Searching {len(candidates)} images…")
        self.dash.add_log(f"Visual search ({mode}) threshold={thr}…")
        self.vs_worker=VisualSearchWorker(qfp,candidates,thr,mode)
        self.vs_worker.finished.connect(lambda r: self._vs_done(r,ml))
        self.vs_worker.start()

    def _vs_done(self,fps,ml):
        self.prog_bar.setMaximum(100); self.prog_bar.setValue(0); self.prog_lbl.setText("Ready")
        fp_set=set(fps); matches=[m for m in ml if m['filepath'] in fp_set]
        self.grid.load_media(matches); self._list_load(matches); self.cnt_lbl.setText(f"{len(matches)} matches")
        self.dash.add_log(f"✓ Visual search: {len(matches)} match(es)")
        QMessageBox.information(self,"Search Complete",f"Found {len(matches)} similar image(s).\nClick Refresh to restore full view.")

    # ── Case actions ──
    def _case_mgr(self):
        dlg=CaseManagerDialog(self.db,self.cur_case,self)
        dlg.case_changed.connect(lambda cid: self._switch_case(cid)); dlg.exec_()

    def _switch_case(self,cid):
        self.cur_case=cid; self.filters={}; self._case_lbl(); self._rebuild_nav_refresh()

    def _new_case_quick(self):
        dlg=QDialog(self); dlg.setWindowTitle("New Case"); dlg.setStyleSheet(DARK_STYLE)
        vb=QVBoxLayout(dlg); vb.addWidget(QLabel("Case name:"))
        ed=QLineEdit(); vb.addWidget(ed)
        br=QHBoxLayout(); bc=QPushButton("Cancel"); bc.clicked.connect(dlg.reject)
        bk=QPushButton("Create"); bk.setObjectName("btnPrimary"); bk.clicked.connect(dlg.accept)
        br.addStretch(); br.addWidget(bc); br.addWidget(bk); vb.addLayout(br)
        if dlg.exec_()==QDialog.Accepted and ed.text().strip():
            cid=self.db.create_case(ed.text().strip()); self._switch_case(cid)

    def _rebuild_nav_refresh(self):
        self._build_nav(); self._case_lbl(); self._refresh(); self._stats()

    # ── Analysis ──
    def _reanalyze(self):
        ids=self.grid.get_ids()
        if not ids: QMessageBox.information(self,"","Select items first."); return
        ok=0
        for mid in ids:
            m=self.db.get_media_by_id(mid)
            if m:
                try:
                    d=AnalysisEngine.analyze(m['filepath'],self.db,m.get('case_id',1)); d.pop('filepath',None)
                    self.db.update_media(mid,d); ok+=1
                except Exception as e: self.dash.add_log(f"⚠ {e}")
        QMessageBox.information(self,"Done",f"Re-analyzed {ok} files."); self._refresh()

    def _retag(self):
        ids=self.grid.get_ids()
        if not ids: ids=[m['id'] for m in self.db.get_all_media(self._filt())]
        if not ids: return
        ok=0
        for mid in ids:
            m=self.db.get_media_by_id(mid)
            if m and os.path.exists(m['filepath']):
                try: self.db.update_media(mid,{'object_tags':json.dumps(AnalysisEngine.classify(m['filepath']))}); ok+=1
                except: pass
        QMessageBox.information(self,"Done",f"Re-tagged {ok} images."); self._refresh()

    def _hash_check(self):
        ml=self.db.get_all_media({'case_id':self.cur_case})
        if not ml: QMessageBox.information(self,"","No media in current case."); return
        matches=0
        for m in ml:
            match=None
            for ht,hv in [('md5',m.get('md5')),('sha256',m.get('sha256')),('phash',m.get('phash'))]:
                if hv:
                    mx=self.db.check_ref(hv,ht)
                    if mx: match=f"{mx['db_name']}:{mx['label']}:{mx['severity']}"; break
            csam=1 if (match and 'CSAM' in match.upper()) else 0
            cat=m['category']
            if match and cat=='Uncategorized': cat='CSAM Hit' if csam else 'Hash Match'
            self.db.update_media(m['id'],{'hash_match':match,'csam_flag':csam,'category':cat})
            if match: matches+=1
        self._refresh(); self._stats()
        msg=f"Hash check done.\n{matches} match(es) across {len(ml)} files."
        self.dash.add_log(f"✓ {msg}"); QMessageBox.information(self,"Done",msg)

    def _create_hashdb(self):
        ids=self.grid.get_ids()
        if not ids: QMessageBox.information(self,"","Select images in the grid first."); return
        CreateHashDBDialog(self.db,ids,self).exec_(); self._stats()

    def _refdb(self):
        RefDBDialog(self.db,self).exec_(); self._stats()

    def _export(self):
        ReportDialog(self.db, self.cur_case, self._filt(), self).exec_()

    def _clear_all(self):
        if QMessageBox.question(self,"Confirm","Remove ALL media from current case?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            with self.db.lock:
                self.db.conn.execute("DELETE FROM media WHERE case_id=?",(self.cur_case,)); self.db.conn.commit()
            self._refresh(); self._stats()

    def _about(self):
        QMessageBox.about(self,f"About {APP_NAME}",
            f"<b>{APP_NAME}</b> v{APP_VERSION}<br><br>Griffeye-inspired Digital Media Analysis Platform<br><br>"
            "<b>Features:</b><br>• Multi-case management<br>• Bulk import with MD5/SHA256/pHash hashing<br>"
            "• Face detection &amp; visual face/image search<br>• Extended object/scene classification<br>"
            "• Custom tag system per image<br>• Reference DBs: NCMEC/CSAM, PhotoDNA, NSRL, Custom<br>"
            "• Create custom hash DB from selection<br>• HTML case report &amp; CSV/hash list export<br>• EXIF metadata<br>")

    def closeEvent(self,ev):
        if self.imp_worker and self.imp_worker.isRunning(): self.imp_worker.stop(); self.imp_worker.wait(3000)
        ev.accept()


# ─── Entry Point ─────────────────────────────────────────────────────────────
def main():
    app=QApplication(sys.argv)
    app.setApplicationName(APP_NAME); app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion"); app.setFont(QFont("Segoe UI",12))
    w=MainWindow(); w.show(); sys.exit(app.exec_())

if __name__=="__main__":
    main()
