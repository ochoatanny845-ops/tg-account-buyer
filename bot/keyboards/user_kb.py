#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户键盘布局 - 动态 Emoji 版本
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.emoji import emoji as e


def main_menu_keyboard():
    """主菜单键盘"""
    keyboard = [
        [f"{e('💰')} 查看价格", f"{e('💵')} 我的余额"],
        [f"{e('📱')} 接码登录", f"{e('📤')} 上传 Session"],
        [f"{e('💸')} 申请提现", f"{e('⚙️')} 设置地址"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def cancel_keyboard():
    """取消操作键盘"""
    keyboard = [[f"{e('❌')} 取消"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def withdrawal_confirm_keyboard(amount):
    """提现确认键盘"""
    keyboard = [
        [
            InlineKeyboardButton(f"{e('✅')} 确认提现 {amount} USDT", callback_data=f"withdraw_confirm_{amount}"),
        ],
        [
            InlineKeyboardButton(f"{e('❌')} 取消", callback_data="withdraw_cancel"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)
