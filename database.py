import sqlite3
import hashlib
from datetime import datetime, timedelta

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    
    # 创建用户表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建日程任务表
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            task_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建甘特图任务表
    c.execute('''
        CREATE TABLE IF NOT EXISTS gantt_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            color TEXT,
            progress INTEGER DEFAULT 0,
            is_completed BOOLEAN DEFAULT FALSE,
            completed_at TIMESTAMP,
            score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # 创建点赞
    c.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 初始化点赞数为0
    c.execute('SELECT COUNT(*) FROM likes')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO likes (count) VALUES (0)')
    
    conn.commit()
    conn.close()

def get_likes_count():
    """获取点赞总数"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('SELECT count FROM likes ORDER BY id DESC LIMIT 1')
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

def increment_likes():
    """增加点赞数"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('UPDATE likes SET count = count + 1, updated_at = CURRENT_TIMESTAMP')
    conn.commit()
    conn.close()
    return get_likes_count()

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """创建新用户"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    try:
        password_hash = hash_password(password)
        c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                 (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """验证用户"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[1] == hash_password(password):
        return result[0]
    return None

# 日程任务相关函数
def get_user_tasks(user_id):
    """获取用户的所有日程任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, description, task_date, start_time, end_time 
        FROM tasks WHERE user_id = ? ORDER BY task_date, start_time
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def add_task(user_id, title, description, task_date, start_time, end_time):
    """添加日程任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO tasks (user_id, title, description, task_date, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, task_date, start_time, end_time))
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id

def update_task(task_id, title, description, task_date, start_time, end_time):
    """更新日程任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        UPDATE tasks 
        SET title=?, description=?, task_date=?, start_time=?, end_time=?
        WHERE id=?
    ''', (title, description, task_date, start_time, end_time, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    """删除日程任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def get_user_tasks_by_date_range(user_id, start_date, end_date):
    """获取用户在指定日期范围内的日程任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, description, task_date, start_time, end_time 
        FROM tasks 
        WHERE user_id = ? AND task_date BETWEEN ? AND ?
        ORDER BY task_date, start_time
    ''', (user_id, start_date, end_date))
    tasks = c.fetchall()
    conn.close()
    return tasks

# 甘特图任务相关函数
def get_user_gantt_tasks(user_id):
    """获取用户的甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, description, start_date, end_date, color, progress, score
        FROM gantt_tasks WHERE user_id = ? ORDER BY start_date
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def add_gantt_task(user_id, title, description, start_date, end_date, color=None, progress=0):
    """添加甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO gantt_tasks (user_id, title, description, start_date, end_date, color, progress)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, title, description, start_date, end_date, color, progress))
    conn.commit()
    task_id = c.lastrowid
    conn.close()
    return task_id

def update_gantt_task(task_id, title, description, start_date, end_date, color=None, progress=0):
    """更新甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        UPDATE gantt_tasks 
        SET title=?, description=?, start_date=?, end_date=?, color=?, progress=?
        WHERE id=?
    ''', (title, description, start_date, end_date, color, progress, task_id))
    conn.commit()
    conn.close()

def delete_gantt_task(task_id):
    """删除甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('DELETE FROM gantt_tasks WHERE id=?', (task_id,))
    conn.commit()
    conn.close()

def mark_task_completed(task_id, score=None):
    """标记任务为已完成"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        UPDATE gantt_tasks 
        SET is_completed=1, completed_at=?, progress=100, score=?
        WHERE id=?
    ''', (completed_time, score, task_id))
    conn.commit()
    conn.close()

def get_completed_tasks(user_id):
    """获取用户已完成的甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, start_date, end_date, score, completed_at
        FROM gantt_tasks 
        WHERE user_id = ? AND is_completed = 1
        ORDER BY completed_at DESC
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def get_incomplete_tasks(user_id):
    """获取用户未完成的甘特图任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, description, start_date, end_date, color, progress, score
        FROM gantt_tasks 
        WHERE user_id = ? AND is_completed = 0
        ORDER BY start_date
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def update_task_score(task_id, score):
    """更新任务评分"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        UPDATE gantt_tasks 
        SET score=?
        WHERE id=?
    ''', (score, task_id))
    conn.commit()
    conn.close()

def get_unscored_completed_tasks(user_id):
    """获取已完成但未评分的任务"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, title, start_date, end_date
        FROM gantt_tasks 
        WHERE user_id = ? AND is_completed = 1 AND score IS NULL
        ORDER BY completed_at DESC
    ''', (user_id,))
    tasks = c.fetchall()
    conn.close()
    return tasks

def check_and_mark_expired_tasks(user_id):
    """检查并自动标记过期任务为完成（但不评分）"""
    conn = sqlite3.connect('user_tasks.db')
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 查找过期且未完成的任务
    c.execute('''
        SELECT id FROM gantt_tasks 
        WHERE user_id = ? AND is_completed = 0 AND end_date < ?
    ''', (user_id, today))
    expired_tasks = c.fetchall()
    
    # 标记这些任务为完成
    for task in expired_tasks:
        task_id = task[0]
        completed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('''
            UPDATE gantt_tasks 
            SET is_completed=1, completed_at=?, progress=100
            WHERE id=?
        ''', (completed_time, task_id))
    
    conn.commit()
    conn.close()
    
    return [task[0] for task in expired_tasks]

# 初始化数据库
init_db()