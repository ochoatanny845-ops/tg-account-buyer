#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置类"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Telegram API
    API_ID = int(os.getenv('API_ID', 0))
    API_HASH = os.getenv('API_HASH')
    
    # 管理员
    ADMIN_GROUP_ID = int(os.getenv('ADMIN_GROUP_ID', 0))
    ADMIN_USER_IDS = [int(x.strip()) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x.strip()]
    
    # 数据库
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///buyer_bot.db')
    
    # 提现配置
    MIN_WITHDRAWAL = float(os.getenv('MIN_WITHDRAWAL', 10))
    WITHDRAWAL_FEE = float(os.getenv('WITHDRAWAL_FEE', 1))
    
    # 默认价格
    DEFAULT_PRICE = float(os.getenv('DEFAULT_PRICE', 0.2))
    
    # 日志
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Session 存储目录
    SESSION_DIR = 'sessions'
    
    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN 未配置")
        
        if not cls.API_ID or not cls.API_HASH:
            errors.append("API_ID 或 API_HASH 未配置")
        
        if not cls.ADMIN_GROUP_ID:
            errors.append("ADMIN_GROUP_ID 未配置")
        
        if not cls.ADMIN_USER_IDS:
            errors.append("ADMIN_USER_IDS 未配置")
        
        if errors:
            return False, "\n".join(errors)
        
        return True, "配置验证通过"
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """检查是否为管理员"""
        return user_id in cls.ADMIN_USER_IDS
