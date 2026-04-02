#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整的 Emoji 替换 - 扫描所有文件"""

import re
from bot.utils.emoji import EMOJI_IDS

def has_emoji(text):
    """检查文本是否包含 Emoji"""
    return any(emoji in text for emoji in EMOJI_IDS.keys())

def replace_all_emojis(text):
    """替换所有 Emoji 为动态版本"""
    for emoji_char, emoji_id in EMOJI_IDS.items():
        if emoji_char in text:
            # 如果已经是 tg-emoji 标签包裹的，跳过
            pattern = f'<tg-emoji emoji-id="[^"]+?">{re.escape(emoji_char)}</tg-emoji>'
            if not re.search(pattern, text):
                # 替换为动态版本
                replacement = f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
                text = text.replace(emoji_char, replacement)
    return text

files = [
    'bot/handlers/user.py',
    'bot/handlers/admin.py',
]

for filepath in files:
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    replaced_count = 0
    
    for line in lines:
        if has_emoji(line) and '<tg-emoji' not in line:
            new_line = replace_all_emojis(line)
            if new_line != line:
                replaced_count += 1
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    
    if replaced_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  Replaced emojis in {replaced_count} lines")
    else:
        print(f"  No changes needed")

print("\nDone!")
