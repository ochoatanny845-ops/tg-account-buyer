#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全局替换 Emoji 为动态版本 - 正确处理引号"""

import re
from emoji_map import EMOJI_MAP

def safe_emoji_replace(content):
    """安全地替换 Emoji，处理引号冲突"""
    for emoji_char, emoji_id in EMOJI_MAP.items():
        # 生成替换模式：emoji("X") 或 e("X")
        # 使用 f-string 表达式
        replacement = f'{{e("{emoji_char}")}}'
        # 直接替换原始 Emoji（只在字符串内）
        content = content.replace(emoji_char, replacement)
    
    return content

# 处理文件
files = [
    'bot/handlers/user.py',
]

for filepath in files:
    print(f"Processing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # 统计
    count = sum(content.count(e) for e in EMOJI_MAP.keys())
    print(f"  Found {count} emojis")
    
    if count > 0:
        new_content = safe_emoji_replace(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"  Replaced {count} emojis")

print("Done!")
