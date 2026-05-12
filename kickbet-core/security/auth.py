"""
KickBet 安全认证模块

功能:
- JWT认证 (生成/验证token)
- 用户密码哈希 (bcrypt)
- Rate Limit配置
- 输入验证装饰器

使用方式:
    from security.auth import token_required, validate_input, limiter
    
    @app.route('/api/protected')
    @token_required
    @limiter.limit("10 per minute")
    def protected_endpoint():
        ...
"""

import jwt
import bcrypt
import re
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, Optional, Tuple, List, Callable
from dataclasses import dataclass
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# ==================== 配置 ====================

# JWT配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'kickbet-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Rate Limit配置
RATE_LIMITS = {
    'default': '60 per minute',       # 默认限制
    'auth': '5 per minute',           # 认证端点
    'calculate': '30 per minute',     # 计算端点
    'analysis': '10 per minute',      # 分析端点
    'matches': '20 per minute',       # 比赛列表
}

# 输入验证规则
VALIDATION_RULES = {
    'lambda_home': {'min': 0.0, 'max': 10.0, 'type': float},
    'lambda_away': {'min': 0.0, 'max': 10.0, 'type': float},
    'line': {'min': 0.0, 'max': 10.0, 'type': float},
    'handicap': {'min': -5.0, 'max': 5.0, 'type': float},
    'match_id': {'pattern': r'^[\w-]+$', 'max_length': 50, 'type': str},
    'days': {'min': 1, 'max': 30, 'type': int},
    'email': {'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$', 'max_length': 100, 'type': str},
    'password': {'min_length': 6, 'max_length': 100, 'type': str},
    'username': {'pattern': r'^[\w]{3,30}$', 'type': str},
}


# ==================== Rate Limiter ====================

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMITS['default']],
    storage_uri="memory://",  # 使用内存存储，生产环境建议Redis
)


# ==================== 用户模型 ====================

@dataclass
class User:
    """用户数据模型"""
    user_id: str
    username: str
    email: str
    password_hash: str
    role: str  # 'admin', 'user', 'guest'
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True


# 内存用户存储 (生产环境应使用数据库)
_users_db: Dict[str, User] = {}


# ==================== 密码处理 ====================

def hash_password(password: str) -> str:
    """
    哈希密码
    
    Args:
        password: 明文密码
        
    Returns:
        bcrypt哈希后的密码字符串
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    验证密码
    
    Args:
        password: 明文密码
        password_hash: 存储的哈希密码
        
    Returns:
        密码是否匹配
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


# ==================== JWT处理 ====================

def generate_token(user: User) -> str:
    """
    生成JWT token
    
    Args:
        user: 用户对象
        
    Returns:
        JWT token字符串
    """
    payload = {
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow(),
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> Optional[Dict]:
    """
    验证JWT token
    
    Args:
        token: JWT token字符串
        
    Returns:
        解码后的payload，验证失败返回None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token过期
    except jwt.InvalidTokenError:
        return None  # Token无效


def decode_token_from_request() -> Optional[Dict]:
    """
    从请求中提取并验证token
    
    支持两种方式:
    1. Authorization header: Bearer <token>
    2. Query parameter: ?token=<token>
    
    Returns:
        解码后的payload，失败返回None
    """
    # 从header获取
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        return verify_token(token)
    
    # 从query参数获取
    token = request.args.get('token')
    if token:
        return verify_token(token)
    
    return None


# ==================== 认证装饰器 ====================

def token_required(f: Callable) -> Callable:
    """
    JWT认证装饰器
    
    使用方式:
        @app.route('/api/protected')
        @token_required
        def protected():
            user_id = g.current_user['user_id']
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        payload = decode_token_from_request()
        
        if payload is None:
            return jsonify({
                'error': '认证失败',
                'message': '需要有效的JWT token',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        # 存储用户信息到g对象
        g.current_user = payload
        g.user_id = payload.get('user_id')
        g.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f: Callable) -> Callable:
    """
    管理员权限装饰器
    
    使用方式:
        @app.route('/api/admin/...')
        @token_required
        @admin_required
        def admin_only():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user_role != 'admin':
            return jsonify({
                'error': '权限不足',
                'message': '需要管理员权限',
                'code': 'ADMIN_REQUIRED'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated


# ==================== 输入验证 ====================

def validate_field(name: str, value: any, rules: Dict) -> Tuple[bool, Optional[str]]:
    """
    验证单个字段
    
    Args:
        name: 字段名
        value: 字段值
        rules: 验证规则
        
    Returns:
        (是否有效, 错误消息)
    """
    # 类型检查
    expected_type = rules.get('type')
    if expected_type and not isinstance(value, expected_type):
        try:
            # 尝试类型转换
            value = expected_type(value)
        except (ValueError, TypeError):
            return False, f'{name} 类型错误，期望 {expected_type.__name__}'
    
    # 数值范围检查
    if 'min' in rules and value < rules['min']:
        return False, f'{name} 最小值为 {rules["min"]}'
    if 'max' in rules and value > rules['max']:
        return False, f'{name} 最大值为 {rules["max"]}'
    
    # 字符串长度检查
    if 'min_length' in rules and len(str(value)) < rules['min_length']:
        return False, f'{name} 最短 {rules["min_length"]} 字符'
    if 'max_length' in rules and len(str(value)) > rules['max_length']:
        return False, f'{name} 最长 {rules["max_length"]} 字符'
    
    # 正则模式检查
    if 'pattern' in rules:
        if not re.match(rules['pattern'], str(value)):
            return False, f'{name} 格式不正确'
    
    return True, None


def validate_input(*field_names: str) -> Callable:
    """
    输入验证装饰器
    
    Args:
        field_names: 需要验证的字段名
        
    使用方式:
        @app.route('/api/calculate')
        @validate_input('lambda_home', 'lambda_away', 'line')
        def calculate():
            ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json() or {}
            errors = []
            
            for field in field_names:
                if field not in data:
                    errors.append(f'{field} 缺失')
                    continue
                
                rules = VALIDATION_RULES.get(field)
                if rules:
                    is_valid, error_msg = validate_field(field, data[field], rules)
                    if not is_valid:
                        errors.append(error_msg)
            
            if errors:
                return jsonify({
                    'error': '输入验证失败',
                    'details': errors,
                    'code': 'VALIDATION_ERROR'
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def sanitize_string(value: str, max_length: int = 100) -> str:
    """
    清理字符串输入
    
    Args:
        value: 输入字符串
        max_length: 最大长度
        
    Returns:
        清理后的字符串
    """
    if not isinstance(value, str):
        return ''
    
    # 移除危险字符
    value = re.sub(r'[<>"\'\&]', '', value)
    
    # 限制长度
    if len(value) > max_length:
        value = value[:max_length]
    
    return value.strip()


# ==================== 用户管理 ====================

def create_user(username: str, email: str, password: str, role: str = 'user') -> Tuple[Optional[User], Optional[str]]:
    """
    创建新用户
    
    Args:
        username: 用户名
        email: 邮箱
        password: 密码
        role: 角色
        
    Returns:
        (用户对象, 错误消息)
    """
    # 导入数据库模块
    try:
        from database.models import db, UserModel
    except ImportError:
        # 数据库模块未初始化，使用内存存储
        return _create_user_memory(username, email, password, role)
    
    # 检查用户名是否已存在
    if db.get_user_by_username(username):
        return None, '用户名已存在'
    if db.get_user_by_email(email):
        return None, '邮箱已注册'
    
    # 创建用户
    user_id = f'user_{int(time.time() * 1000)}'
    password_hash = hash_password(password)
    
    user_model = db.create_user(user_id, username, email, password_hash, role)
    
    if user_model:
        return User(
            user_id=user_model.user_id,
            username=user_model.username,
            email=user_model.email,
            password_hash=user_model.password_hash,
            role=user_model.role,
            created_at=user_model.created_at,
            last_login=user_model.last_login,
            is_active=user_model.is_active
        ), None
    
    return None, '创建用户失败'


def _create_user_memory(username: str, email: str, password: str, role: str = 'user') -> Tuple[Optional[User], Optional[str]]:
    """内存存储的用户创建 (备用)"""
    # 检查用户名是否已存在
    for user in _users_db.values():
        if user.username == username:
            return None, '用户名已存在'
        if user.email == email:
            return None, '邮箱已注册'
    
    # 创建用户
    user_id = f'user_{int(time.time() * 1000)}'
    password_hash = hash_password(password)
    
    user = User(
        user_id=user_id,
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    _users_db[user_id] = user
    
    return user, None


def authenticate_user(username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """
    认证用户
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        (用户对象, 错误消息)
    """
    try:
        from database.models import db
    except ImportError:
        return _authenticate_user_memory(username, password)
    
    # 查找用户
    user_model = db.get_user_by_username(username)
    if not user_model:
        user_model = db.get_user_by_email(username)
    
    if user_model is None:
        return None, '用户不存在'
    
    if not user_model.is_active:
        return None, '用户已被禁用'
    
    if not verify_password(password, user_model.password_hash):
        return None, '密码错误'
    
    # 更新最后登录时间
    db.update_user_login(user_model.user_id)
    
    return User(
        user_id=user_model.user_id,
        username=user_model.username,
        email=user_model.email,
        password_hash=user_model.password_hash,
        role=user_model.role,
        created_at=user_model.created_at,
        last_login=user_model.last_login,
        is_active=user_model.is_active
    ), None


def _authenticate_user_memory(username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
    """内存存储的用户认证 (备用)"""
    # 查找用户
    user = None
    for u in _users_db.values():
        if u.username == username or u.email == username:
            user = u
            break
    
    if user is None:
        return None, '用户不存在'
    
    if not user.is_active:
        return None, '用户已被禁用'
    
    if not verify_password(password, user.password_hash):
        return None, '密码错误'
    
    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    
    return user, None


def get_user_by_id(user_id: str) -> Optional[User]:
    """
    通过ID获取用户
    """
    try:
        from database.models import db
        user_model = db.get_user_by_id(user_id)
        if user_model:
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                email=user_model.email,
                password_hash=user_model.password_hash,
                role=user_model.role,
                created_at=user_model.created_at,
                last_login=user_model.last_login,
                is_active=user_model.is_active
            )
        return None
    except ImportError:
        return _users_db.get(user_id)


def init_default_users():
    """
    初始化默认用户 (仅用于测试)
    """
    # 创建管理员账户
    admin_exists = get_user_by_username('admin') or get_user_by_email('admin@kickbet.local')
    if not admin_exists:
        create_user('admin', 'admin@kickbet.local', 'admin123', 'admin')
    
    # 创建测试用户
    test_exists = get_user_by_username('test') or get_user_by_email('test@kickbet.local')
    if not test_exists:
        create_user('test', 'test@kickbet.local', 'test123', 'user')


def get_user_by_username(username: str) -> Optional[User]:
    """通过用户名获取用户"""
    try:
        from database.models import db
        user_model = db.get_user_by_username(username)
        if user_model:
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                email=user_model.email,
                password_hash=user_model.password_hash,
                role=user_model.role,
                created_at=user_model.created_at,
                last_login=user_model.last_login,
                is_active=user_model.is_active
            )
        return None
    except ImportError:
        for u in _users_db.values():
            if u.username == username:
                return u
        return None


def get_user_by_email(email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    try:
        from database.models import db
        user_model = db.get_user_by_email(email)
        if user_model:
            return User(
                user_id=user_model.user_id,
                username=user_model.username,
                email=user_model.email,
                password_hash=user_model.password_hash,
                role=user_model.role,
                created_at=user_model.created_at,
                last_login=user_model.last_login,
                is_active=user_model.is_active
            )
        return None
    except ImportError:
        for u in _users_db.values():
            if u.email == email:
                return u
        return None


# ==================== 安全审计 ====================

def log_auth_event(event_type: str, user_id: Optional[str], details: str):
    """
    记录认证事件 (生产环境应写入数据库)
    
    Args:
        event_type: 事件类型 (login, logout, token_expired, auth_failed)
        user_id: 用户ID
        details: 详细信息
    """
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': get_remote_address(),
        'details': details
    }
    # TODO: 写入数据库或日志系统
    print(f"[AUTH] {log_entry}")


# ==================== 导出 ====================

__all__ = [
    'limiter',
    'token_required',
    'admin_required',
    'validate_input',
    'sanitize_string',
    'generate_token',
    'verify_token',
    'create_user',
    'authenticate_user',
    'get_user_by_id',
    'init_default_users',
    'User',
    'RATE_LIMITS',
    'JWT_SECRET_KEY',
    'JWT_EXPIRATION_HOURS',
]