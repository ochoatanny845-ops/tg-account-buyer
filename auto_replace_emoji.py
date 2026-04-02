#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能替换所有 Emoji 为动态版本 - 正确处理 Python 语法"""

import re
from bot.utils.emoji import EMOJI_IDS

def smart_replace_emoji(content):
    """智能替换 Emoji，确保 parse_mode='HTML' 存在"""
    
    # 第一步：确保所有 reply_text 都有 parse_mode='HTML'
    # 匹配所有 await xxx.reply_text(...) 调用
    def add_parse_mode(match):
        func_call = match.group(0)
        # 如果已经有 parse_mode，跳过
        if 'parse_mode' in func_call:
            return func_call
        
        # 在最后的 ) 前添加 parse_mode='HTML'
        # 找到最后一个 )
        last_paren = func_call.rfind(')')
        if last_paren > 0:
            # 检查倒数第二个字符是否是逗号
            before_paren = func_call[:last_paren].rstrip()
            if before_paren.endswith(','):
                # 已经有逗号，直接添加
                return func_call[:last_paren] + ", parse_mode='HTML'" + func_call[last_paren:]
            else:
                # 添加逗号和参数
                return func_call[:last_paren] + ", parse_mode='HTML'" + func_call[last_paren:]
        return func_call
    
    # 匹配 reply_text 调用（多行）
    content = re.sub(
        r'(await\s+\w+\.(?:reply_text|send_message)\s*\([^)]+(?:\([^)]*\)[^)]*)*\))',
        add_parse_mode,
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # 第二步：替换字符串中的 Emoji
    # 只替换在字符串内的 Emoji（用 f"..." 或 """...""" 包裹的）
    for emoji_char, emoji_id in EMOJI_IDS.items():
        # 生成动态 Emoji 的 HTML 标签
        replacement = f'<emoji id="{emoji_id}">{emoji_char}</emoji>'
        
        # 替换所有出现的 Emoji
        content = content.replace(emoji_char, replacement)
    
    return content

# 需要处理的文件
files = [
    'bot/handlers/user.py',
    'bot/handlers/admin.py',
    'bot/keyboards/user_kb.py',
    'bot/keyboards/admin_kb.py',
]

for filepath in files:
    try:
        print(f"Processing {filepath}...")
        
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        
        # 统计 Emoji 数量
        emoji_count = sum(content.count(e) for e in EMOJI_IDS.keys())
        
        if emoji_count == 0:
            print(f"  No emojis found in {filepath}")
            continue
        
        print(f"  Found {emoji_count} emojis")
        
        # 应用替换
        new_content = smart_replace_emoji(content)
        
        # 写回文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  OK: Replaced {emoji_count} emojis and added parse_mode")
        
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nAll done! Now checking syntax...")
