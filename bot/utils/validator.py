#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session 验证工具
"""
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.account import GetPasswordRequest
from bot.config import Config
from bot.utils.country import parse_phone_country_code


async def validate_session(session_file: str):
    """
    验证 Session 文件
    返回: (is_valid, phone, country_code, error_msg)
    """
    try:
        # 创建客户端
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        
        await client.connect()
        
        # 检查是否已登录
        if not await client.is_user_authorized():
            await client.disconnect()
            return False, None, None, "Session 无效：未授权"
        
        # 获取用户信息
        me = await client.get_me()
        phone = me.phone
        
        if not phone:
            await client.disconnect()
            return False, None, None, "无法获取手机号"
        
        # 解析国家区号
        country_code = parse_phone_country_code(phone)
        if not country_code:
            await client.disconnect()
            return False, phone, None, "无法识别国家区号"
        
        # 检查账号是否设置了密码（2FA）
        try:
            password_info = await client(GetPasswordRequest())
            has_2fa = password_info.has_password
        except Exception as e:
            # 如果无法检查，假设没有 2FA
            await client.disconnect()
            return False, phone, country_code, "未开启 2FA"
        
        await client.disconnect()
        
        if not has_2fa:
            return False, phone, country_code, "未开启 2FA"
        
        return True, phone, country_code, None
        
    except Exception as e:
        return False, None, None, f"验证失败: {str(e)}"


async def send_code_request(phone: str, session_file: str):
    """
    发送验证码请求
    返回: (success, phone_code_hash, error_msg)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"正在发送验证码到: {phone}")
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        # 发送验证码
        sent_code = await client.send_code_request(phone)
        phone_code_hash = sent_code.phone_code_hash
        
        logger.info(f"验证码发送成功: {phone}, hash: {phone_code_hash[:10]}...")
        
        await client.disconnect()
        return True, phone_code_hash, None
        
    except Exception as e:
        logger.error(f"发送验证码失败: {phone}, 错误: {str(e)}")
        return False, None, f"发送验证码失败: {str(e)}"


async def sign_in_with_code(phone: str, code: str, phone_code_hash: str, session_file: str):
    """
    使用验证码登录（第一步）
    返回: (success, needs_password, error_msg)
    """
    try:
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            # 登录成功，不需要密码
            await client.disconnect()
            return True, False, None
        except SessionPasswordNeededError:
            # 需要 2FA 密码
            await client.disconnect()
            return False, True, None
        except Exception as e:
            await client.disconnect()
            return False, False, f"验证码错误: {str(e)}"
        
    except Exception as e:
        return False, False, f"登录失败: {str(e)}"


async def sign_in_with_password(password: str, session_file: str):
    """
    使用 2FA 密码登录（第二步）
    返回: (success, phone, country_code, error_msg)
    """
    try:
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        try:
            await client.sign_in(password=password)
        except Exception as e:
            await client.disconnect()
            return False, None, None, f"2FA 密码错误: {str(e)}"
        
        # 检查是否成功
        if not await client.is_user_authorized():
            await client.disconnect()
            return False, None, None, "登录失败"
        
        # 获取用户信息
        me = await client.get_me()
        phone = me.phone
        country_code = parse_phone_country_code(phone)
        
        await client.disconnect()
        return True, phone, country_code, None
        
    except Exception as e:
        return False, None, None, f"登录失败: {str(e)}"


def generate_session_filename(phone: str):
    """
    生成 Session 文件名
    格式: sessions/+86xxxxxxxxxx.session
    """
    # 移除所有非数字字符，保留 +
    clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not clean_phone.startswith('+'):
        clean_phone = '+' + clean_phone
    
    filename = f"{clean_phone}.session"
    return os.path.join(Config.SESSION_DIR, filename)

