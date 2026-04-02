#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查所有 tg-emoji 标签是否有 parse_mode='HTML'"""

import re

filepath = 'bot/handlers/user.py'

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找所有包含 tg-emoji 的消息块
issues = []
current_block = []
block_start = 0

for i, line in enumerate(lines, 1):
    current_block.append(line)
    
    # 检测消息发送
    if 'reply_text' in line or 'send_message' in line:
        # 检查前20行是否有 tg-emoji
        block_text = ''.join(current_block[-20:])
        
        if 'tg-emoji' in block_text and 'parse_mode' not in block_text:
            issues.append({
                'line': i,
                'snippet': line.strip()[:80]
            })
        
        current_block = []

print(f"Total lines with tg-emoji: {sum(1 for l in lines if 'tg-emoji' in l)}")
print(f"Issues found: {len(issues)}")

if issues:
    print("\nMissing parse_mode='HTML':")
    for issue in issues[:10]:
        print(f"  Line {issue['line']}: {issue['snippet']}")
else:
    print("\n✓ All tg-emoji usages have parse_mode='HTML'!")
