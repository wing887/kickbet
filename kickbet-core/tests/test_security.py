"""
KickBet安全模块测试

测试覆盖:
1. JWT认证流程
2. 密码哈希验证
3. Rate Limit
4. 输入验证
5. 权限控制
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.auth import (
    hash_password, verify_password,
    generate_token, verify_token,
    create_user, authenticate_user,
    User, VALIDATION_RULES, validate_field,
    init_default_users, _users_db
)


class TestPasswordHashing:
    """密码哈希测试"""
    
    def test_hash_password_returns_string(self):
        """哈希返回字符串"""
        password = "test123"
        hashed = hash_password(password)
        assert isinstance(hashed, str)
        assert len(hashed) > 20  # bcrypt哈希长度
    
    def test_hash_password_different_each_time(self):
        """每次哈希结果不同(不同salt)"""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """正确密码验证"""
        password = "test123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) == True
    
    def test_verify_password_wrong(self):
        """错误密码验证"""
        password = "test123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) == False
    
    def test_verify_password_empty(self):
        """空密码验证"""
        hashed = hash_password("test123")
        assert verify_password("", hashed) == False
    
    def test_verify_password_invalid_hash(self):
        """无效哈希验证"""
        assert verify_password("test123", "invalid_hash") == False


class TestJWTToken:
    """JWT Token测试"""
    
    @pytest.fixture
    def test_user(self):
        """测试用户"""
        return User(
            user_id='test_user_001',
            username='testuser',
            email='test@example.com',
            password_hash=hash_password('password123'),
            role='user',
            created_at='2026-05-11T00:00:00',
            is_active=True
        )
    
    def test_generate_token_returns_string(self, test_user):
        """生成Token返回字符串"""
        token = generate_token(test_user)
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_valid(self, test_user):
        """验证有效Token"""
        token = generate_token(test_user)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload['user_id'] == test_user.user_id
        assert payload['username'] == test_user.username
        assert payload['role'] == test_user.role
    
    def test_verify_token_invalid(self):
        """验证无效Token"""
        payload = verify_token('invalid_token_string')
        assert payload is None
    
    def test_verify_token_empty(self):
        """验证空Token"""
        payload = verify_token('')
        assert payload is None
    
    def test_token_contains_expiration(self, test_user):
        """Token包含过期时间"""
        token = generate_token(test_user)
        payload = verify_token(token)
        
        assert 'exp' in payload
        assert 'iat' in payload


class TestUserManagement:
    """用户管理测试"""
    
    def test_create_user_success(self):
        """创建用户成功"""
        # 清空测试数据
        _users_db.clear()
        
        user, error = create_user('newuser', 'new@example.com', 'password123')
        
        assert user is not None
        assert error is None
        assert user.username == 'newuser'
        assert user.email == 'new@example.com'
        assert user.role == 'user'
    
    def test_create_user_duplicate_username(self):
        """重复用户名"""
        _users_db.clear()
        create_user('duplicate', 'dup1@example.com', 'password123')
        
        user, error = create_user('duplicate', 'dup2@example.com', 'password123')
        
        assert user is None
        assert error == '用户名已存在'
    
    def test_create_user_duplicate_email(self):
        """重复邮箱"""
        _users_db.clear()
        create_user('user1', 'duplicate@example.com', 'password123')
        
        user, error = create_user('user2', 'duplicate@example.com', 'password123')
        
        assert user is None
        assert error == '邮箱已注册'
    
    def test_authenticate_user_success(self):
        """认证成功"""
        _users_db.clear()
        create_user('authuser', 'auth@example.com', 'password123')
        
        user, error = authenticate_user('authuser', 'password123')
        
        assert user is not None
        assert error is None
        assert user.username == 'authuser'
    
    def test_authenticate_user_by_email(self):
        """用邮箱认证"""
        _users_db.clear()
        create_user('emailuser', 'email@example.com', 'password123')
        
        user, error = authenticate_user('email@example.com', 'password123')
        
        assert user is not None
        assert error is None
    
    def test_authenticate_user_wrong_password(self):
        """密码错误"""
        _users_db.clear()
        create_user('wrongpass', 'wrong@example.com', 'password123')
        
        user, error = authenticate_user('wrongpass', 'wrongpassword')
        
        assert user is None
        assert error == '密码错误'
    
    def test_authenticate_user_not_found(self):
        """用户不存在"""
        _users_db.clear()
        
        user, error = authenticate_user('nonexistent', 'password123')
        
        assert user is None
        assert error == '用户不存在'
    
    def test_init_default_users(self):
        """初始化默认用户"""
        # 清理数据库
        from database.models import db, init_database
        init_database()
        
        init_default_users()
        
        # 检查数据库中用户存在
        admin = db.get_user_by_username('admin')
        test = db.get_user_by_username('test')
        
        assert admin is not None or test is not None


class TestInputValidation:
    """输入验证测试"""
    
    def test_validate_lambda_home_valid(self):
        """验证lambda_home"""
        is_valid, error = validate_field('lambda_home', 2.5, VALIDATION_RULES['lambda_home'])
        assert is_valid == True
        assert error is None
    
    def test_validate_lambda_home_negative(self):
        """负lambda值"""
        is_valid, error = validate_field('lambda_home', -1.0, VALIDATION_RULES['lambda_home'])
        assert is_valid == False
        assert '最小值' in error
    
    def test_validate_lambda_home_too_large(self):
        """过大lambda值"""
        is_valid, error = validate_field('lambda_home', 15.0, VALIDATION_RULES['lambda_home'])
        assert is_valid == False
        assert '最大值' in error
    
    def test_validate_line_valid(self):
        """验证盘口线"""
        is_valid, error = validate_field('line', 2.5, VALIDATION_RULES['line'])
        assert is_valid == True
    
    def test_validate_handicap_valid(self):
        """验证让球盘"""
        is_valid, error = validate_field('handicap', -1.5, VALIDATION_RULES['handicap'])
        assert is_valid == True
    
    def test_validate_handicap_out_of_range(self):
        """让球盘超出范围"""
        is_valid, error = validate_field('handicap', -10.0, VALIDATION_RULES['handicap'])
        assert is_valid == False
    
    def test_validate_email_valid(self):
        """验证邮箱"""
        is_valid, error = validate_field('email', 'test@example.com', VALIDATION_RULES['email'])
        assert is_valid == True
    
    def test_validate_email_invalid(self):
        """无效邮箱"""
        is_valid, error = validate_field('email', 'invalid_email', VALIDATION_RULES['email'])
        assert is_valid == False
        assert '格式' in error
    
    def test_validate_password_min_length(self):
        """密码最短"""
        is_valid, error = validate_field('password', 'abc', VALIDATION_RULES['password'])
        assert is_valid == False
        assert '最短' in error
    
    def test_validate_match_id_valid(self):
        """验证match_id"""
        is_valid, error = validate_field('match_id', 'match-123-abc', VALIDATION_RULES['match_id'])
        assert is_valid == True
    
    def test_validate_match_id_invalid_chars(self):
        """无效match_id字符"""
        is_valid, error = validate_field('match_id', 'match@123', VALIDATION_RULES['match_id'])
        assert is_valid == False


class TestSecurityIntegration:
    """安全集成测试"""
    
    def test_full_auth_flow(self):
        """完整认证流程"""
        _users_db.clear()
        
        # 1. 创建用户
        user, _ = create_user('flowuser', 'flow@example.com', 'password123')
        
        # 2. 生成Token
        token = generate_token(user)
        
        # 3. 验证Token
        payload = verify_token(token)
        
        assert payload['user_id'] == user.user_id
        
        # 4. 用Token认证用户
        auth_user, _ = authenticate_user('flowuser', 'password123')
        
        assert auth_user.user_id == user.user_id
    
    def test_admin_role_flow(self):
        """管理员角色流程"""
        _users_db.clear()
        
        admin, _ = create_user('adminuser', 'admin@example.com', 'adminpass', 'admin')
        
        token = generate_token(admin)
        payload = verify_token(token)
        
        assert payload['role'] == 'admin'


class TestRateLimits:
    """Rate Limit配置测试"""
    
    def test_rate_limits_defined(self):
        """Rate Limit配置存在"""
        from security.auth import RATE_LIMITS
        
        assert 'default' in RATE_LIMITS
        assert 'auth' in RATE_LIMITS
        assert 'calculate' in RATE_LIMITS
        assert 'analysis' in RATE_LIMITS
    
    def test_auth_rate_limit_stricter(self):
        """认证Rate Limit更严格"""
        from security.auth import RATE_LIMITS
        
        # 认证端点应比默认更严格
        auth_limit = RATE_LIMITS['auth']
        default_limit = RATE_LIMITS['default']
        
        # 认证: 5/min, 默认: 60/min
        assert '5 per' in auth_limit