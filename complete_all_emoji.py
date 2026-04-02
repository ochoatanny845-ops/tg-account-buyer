#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整替换所有普通 Emoji 为动态版本"""

import re
from bot.utils.emoji import EMOJI_IDS

files = ['bot/handlers/user.py', 'bot/handlers/admin.py']

for filepath in files:
    print(f"\nProcessing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 对每个 Emoji，替换所有不在 tg-emoji 标签内的实例
    for emoji_char, emoji_id in EMOJI_IDS.items():
        # 跳过已经在 tg-emoji 标签内的
        # 查找所有独立的 emoji（不在标签内）
        
        # 策略：先找到所有 <tg-emoji...>emoji</tg-emoji> 的位置，标记为"保护区"
        # 然后只替换保护区外的 emoji
        
        # 简单方法：直接替换所有不在 > 和 < 之间的 emoji
        # 使用负向前瞻和后瞻
        
        # 更简单的方法：替换所有，但跳过已经是 <tg-emoji emoji-id="ID">EMOJI</tg-emoji> 格式的
        existing_tag = f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
        
        if emoji_char in content and existing_tag not in content:
            # 这个 emoji 还没被替换
            new_tag = f'<tg-emoji emoji-id="{emoji_id}">{emoji_char}</tg-emoji>'
            content = content.replace(emoji_char, new_tag)
            print(f"  Replaced emoji ID: {emoji_id}")
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"OK Updated!")
    else:
        print(f"  No changes needed")

print("\nDone!")
