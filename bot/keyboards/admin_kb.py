#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员键盘布局 - 使用普通 Unicode Emoji
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def session_review_keyboard(session_id: int, price: float):
    """Session 审核键盘"""
    keyboard = [
        [
            InlineKeyboardButton(f"✅ 通过 +{price} USDT", callback_data=f"approve_session:{session_id}"),
            InlineKeyboardButton("❌ 拒绝：2FA错误", callback_data=f"reject_session:{session_id}:no_2fa"),
        ],
        [
            InlineKeyboardButton("❌ 拒绝：其他原因", callback_data=f"reject_session:{session_id}:other"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def withdrawal_review_keyboard(withdrawal_id: int):
    """提现审核键盘"""
    keyboard = [
        [
            InlineKeyboardButton("✅ 已付款", callback_data=f"approve_withdrawal:{withdrawal_id}"),
            InlineKeyboardButton("❌ 拒绝", callback_data=f"reject_withdrawal:{withdrawal_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
