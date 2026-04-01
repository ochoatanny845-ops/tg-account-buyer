#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session 验证工具
"""
import os
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
from bot.config import Config
from bot.utils.country import parse_phone_country_code

logger = logging.getLogger(__name__)


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


async def send_verification_code(phone: str, session_file: str):
    """
    发送验证码（仅发送，不登录）
    返回: (success, error_msg)
    """
    try:
        logger.info(f"发送验证码到: {phone}")
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        # 发送验证码
        await client.send_code_request(phone)
        
        await client.disconnect()
        logger.info(f"验证码已发送: {phone}")
        return True, None
        
    except Exception as e:
        logger.error(f"发送验证码失败: {phone}, 错误: {str(e)}")
        return False, f"发送验证码失败: {str(e)}"


async def login_with_code(phone: str, code: str, session_file: str):
    """
    使用验证码登录
    返回: (success, needs_password, error_msg)
    """
    try:
        logger.info(f"尝试使用验证码登录: {phone}")
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        # 使用验证码登录
        try:
            await client.sign_in(phone, code)
            
            # 检查是否成功
            if await client.is_user_authorized():
                logger.info(f"登录成功（无 2FA）: {phone}")
                await client.disconnect()
                return True, False, None
            else:
                logger.error(f"登录失败: {phone}")
                await client.disconnect()
                return False, False, "登录失败"
                
        except SessionPasswordNeededError:
            # 需要 2FA 密码
            logger.info(f"需要 2FA 密码: {phone}")
            # 保持连接，等待输入密码
            await client.disconnect()
            return False, True, None
            
        except PhoneCodeInvalidError:
            logger.error(f"验证码错误: {phone}")
            await client.disconnect()
            return False, False, "验证码错误"
            
    except Exception as e:
        logger.error(f"登录异常: {phone}, 错误: {str(e)}")
        return False, False, f"登录失败: {str(e)}"


async def login_with_password(phone: str, password: str, session_file: str):
    """
    使用 2FA 密码登录
    返回: (success, error_msg)
    """
    try:
        logger.info(f"使用 2FA 密码登录: {phone}")
        client = TelegramClient(session_file, Config.API_ID, Config.API_HASH)
        await client.connect()
        
        # 检查是否需要密码
        if await client.is_user_authorized():
            logger.info(f"已授权，无需密码: {phone}")
            await client.disconnect()
            return True, None
        
        # 使用密码登录
        try:
            await client.sign_in(password=password)
            
            # 检查是否成功
            if await client.is_user_authorized():
                logger.info(f"2FA 登录成功: {phone}")
                await client.disconnect()
                return True, None
            else:
                logger.error(f"2FA 登录失败: {phone}")
                await client.disconnect()
                return False, "登录失败"
                
        except Exception as e:
            logger.error(f"2FA 密码错误: {phone}, {str(e)}")
            await client.disconnect()
            return False, f"密码错误: {str(e)}"
            
    except Exception as e:
        logger.error(f"2FA 登录异常: {phone}, 错误: {str(e)}")
        return False, f"登录失败: {str(e)}"


def generate_session_filename(phone: str):
    """生成 Session 文件名"""
    # 清理手机号，只保留数字
    clean_phone = ''.join(filter(str.isdigit, phone))
    return os.path.join(Config.SESSION_DIR, f"{clean_phone}.session")
