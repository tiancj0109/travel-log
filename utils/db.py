import pymysql
from contextlib import contextmanager
import config

def get_db_connection():
    """创建数据库连接"""
    return pymysql.connect(**config.DB_CONFIG)

@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def execute_query(query, params=None, fetch=False, fetchone=False, commit=True):
    """
    执行SQL查询
    
    Args:
        query: SQL查询语句
        params: 查询参数
        fetch: 是否返回所有结果
        fetchone: 是否只返回一条结果
        commit: 是否提交事务
    
    Returns:
        根据参数返回不同结果
    """
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            
            if fetchone:
                result = cursor.fetchone()
            elif fetch:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid if commit else None
            
            if commit:
                conn.commit()
            
            return result

def fetch_one(query, params=None):
    """获取单条记录"""
    return execute_query(query, params, fetchone=True, commit=False)

def fetch_all(query, params=None):
    """获取所有记录"""
    return execute_query(query, params, fetch=True, commit=False)

def insert(query, params=None):
    """插入数据并返回ID"""
    return execute_query(query, params, commit=True)

def update(query, params=None):
    """更新数据"""
    execute_query(query, params, commit=True)
    return True

def delete(query, params=None):
    """删除数据"""
    execute_query(query, params, commit=True)
    return True
