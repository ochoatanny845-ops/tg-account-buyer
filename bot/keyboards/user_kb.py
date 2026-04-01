#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户键盘布局
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    """主菜单键盘"""
    keyboard = [
        ["💰 查看价格", "💵 我的余额"],
        ["📱 接码登录", "📤 上传 Session"],
        ["💸 申请提现", "📊 我的记录"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard():
    """取消操作键盘"""
    keyboard = [["❌ 取消"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def withdrawal_confirm_keyboard(amount: float, fee: float):
    """提现确认键盘"""
    total = amount + fee
    keyboard = [
        [
            InlineKeyboardButton(f"✅ 确认提现 ({total} USDT)", callback_data=f"withdraw_confirm:{amount}"),
            InlineKeyboardButton("❌ 取消", callback_data="withdraw_cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
