#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员键盘布局 - 动态 Emoji 版本
"""
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils.emoji import emoji as e


def session_review_keyboard(session_id: int, price: float):
    """Session 审核键盘"""
    keyboard = [
        [
            InlineKeyboardButton(f"{e('✅')} 通过 +{price} USDT", callback_data=f"approve_session:{session_id}"),
            InlineKeyboardButton(f"{e('❌')} 拒绝：2FA错误", callback_data=f"reject_session:{session_id}:no_2fa"),
        ],
        [
            InlineKeyboardButton(f"{e('❌')} 拒绝：其他原因", callback_data=f"reject_session:{session_id}:other"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def withdrawal_review_keyboard(withdrawal_id: int):
    """提现审核键盘"""
    keyboard = [
        [
            InlineKeyboardButton(f"{e('✅')} 已付款", callback_data=f"approve_withdrawal:{withdrawal_id}"),
            InlineKeyboardButton(f"{e('❌')} 拒绝", callback_data=f"reject_withdrawal:{withdrawal_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
