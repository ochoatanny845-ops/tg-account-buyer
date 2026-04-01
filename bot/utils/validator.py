#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session 验证工具
"""
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
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
        
        # 检查 2FA
        try:
            # 尝试获取完整的用户信息（需要密码才能访问某些信息）
            full = await client(GetFullUserRequest('me'))
        except SessionPasswordNeededError:
            # 需要密码，说明开启了 2FA
            await client.disconnect()
            return True, phone, country_code, None
        except Exception:
            pass
        
        # 检查账号是否设置了密码（2FA）
        # 通过检查 account.getPassword 来验证
        try:
            from telethon.tl.functions.account import GetPasswordRequest
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


async def login_with_code(phone: str, code: str, session_file: str):
    """
    使用验证码登录
    返回: (success, error_msg)
    """
    try:
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        # 如果已经登录，返回成功
        if await client.is_user_authorized():
            await client.disconnect()
            return True, None
        
        # 发送验证码
        await client.send_code_request(phone)
        
        # 使用验证码登录
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            # 需要 2FA 密码
            await client.disconnect()
            return False, "需要 2FA 密码，请使用已登录的 Session 文件上传"
        
        # 检查是否成功
        if await client.is_user_authorized():
            await client.disconnect()
            return True, None
        else:
            await client.disconnect()
            return False, "登录失败"
        
    except Exception as e:
        return False, f"登录失败: {str(e)}"


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
