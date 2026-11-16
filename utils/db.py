import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER,
        user_id INTEGER,
        moderator_id INTEGER,
        reason TEXT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS guild_config (
        guild_id INTEGER PRIMARY KEY,
        mod_log_channel INTEGER,
        mute_role INTEGER,
        automod_enabled INTEGER DEFAULT 1
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS reaction_roles (
        message_id INTEGER,
        emoji TEXT,
        role_id INTEGER,
        guild_id INTEGER,
        PRIMARY KEY (message_id, emoji)
    )""")

    conn.commit()
    conn.close()


def get_guild_config(guild_id: int):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    conn.close()
    return row


def set_guild_config(guild_id: int, **kwargs):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO guild_config (guild_id) VALUES (?)", (guild_id,))
    for key, value in kwargs.items():
        c.execute(
            f"UPDATE guild_config SET {key} = ? WHERE guild_id = ?", (value, guild_id)
        )
    conn.commit()
    conn.close()


def add_warn(guild_id: int, user_id: int, moderator_id: int, reason: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO warns (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
        (guild_id, user_id, moderator_id, reason),
    )
    conn.commit()
    conn.close()


def get_warns(guild_id: int, user_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM warns WHERE guild_id = ? AND user_id = ? ORDER BY timestamp DESC",
        (guild_id, user_id),
    ).fetchall()
    conn.close()
    return rows


def clear_warns(guild_id: int, user_id: int):
    conn = get_conn()
    conn.execute(
        "DELETE FROM warns WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
    )
    conn.commit()
    conn.close()


def add_reaction_role(message_id: int, emoji: str, role_id: int, guild_id: int):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO reaction_roles (message_id, emoji, role_id, guild_id) VALUES (?, ?, ?, ?)",
        (message_id, emoji, role_id, guild_id),
    )
    conn.commit()
    conn.close()


def get_reaction_role(message_id: int, emoji: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM reaction_roles WHERE message_id = ? AND emoji = ?",
        (message_id, emoji),
    ).fetchone()
    conn.close()
    return row
