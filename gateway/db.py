import os, sqlite3, threading, json, time
from contextlib import contextmanager

DB_PATH = os.getenv("AGENTFLOW_DB", "agentflow.db")
_lock = threading.RLock()
_conn = None
_depth = 0

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents(id TEXT PRIMARY KEY, name TEXT, role TEXT, pubkey TEXT, endpoint TEXT, manifest TEXT, status TEXT DEFAULT 'active', healthy INTEGER DEFAULT 1, created_at REAL);
CREATE TABLE IF NOT EXISTS reputation(agent_id TEXT, capability TEXT, succ REAL DEFAULT 0, fail REAL DEFAULT 0, PRIMARY KEY(agent_id, capability));
CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, idem_key TEXT UNIQUE, user_id TEXT, goal TEXT, budget INTEGER, priority TEXT, mode TEXT, status TEXT, result TEXT, spent INTEGER DEFAULT 0, wasted INTEGER DEFAULT 0, created_at REAL, finished_at REAL);
CREATE TABLE IF NOT EXISTS contracts(id TEXT PRIMARY KEY, task_id TEXT, capability TEXT, provider_id TEXT, price INTEGER, fee INTEGER, state TEXT, terms TEXT, buyer_sig TEXT, provider_sig TEXT, created_at REAL);
CREATE TABLE IF NOT EXISTS txns(txn_id TEXT PRIMARY KEY, idem_key TEXT UNIQUE, kind TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY AUTOINCREMENT, txn_id TEXT, account TEXT, debit INTEGER DEFAULT 0, credit INTEGER DEFAULT 0, memo TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, task_id TEXT, type TEXT, payload TEXT, prev_hash TEXT, hash TEXT);
"""

def conn():
    global _conn
    with _lock:
        if _conn is None:
            _conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            _conn.executescript(SCHEMA)
        return _conn

def reset(delete_file=True):
    global _conn
    with _lock:
        if _conn: _conn.close(); _conn = None
        if delete_file:
            for s in ("", "-wal", "-shm"):
                try: os.remove(DB_PATH + s)
                except FileNotFoundError: pass
        conn()

@contextmanager
def tx():
    """Atomic block; nested calls join the outer transaction. All money + state + audit changes happen inside one."""
    global _depth
    with _lock:
        c = conn()
        if _depth == 0: c.execute("BEGIN IMMEDIATE")
        _depth += 1
        try:
            yield c
        except BaseException:
            _depth -= 1
            if _depth == 0: c.execute("ROLLBACK")
            raise
        else:
            _depth -= 1
            if _depth == 0: c.execute("COMMIT")

def q(sql, args=()):
    with _lock: return [dict(r) for r in conn().execute(sql, args).fetchall()]

def q1(sql, args=()):
    r = q(sql, args); return r[0] if r else None

def x(sql, args=()):
    with _lock: return conn().execute(sql, args)
