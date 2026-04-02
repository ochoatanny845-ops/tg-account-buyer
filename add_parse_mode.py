#!/usr/bin/env python3
import re

with open('bot/handlers/user.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到所有 reply_text 调用
matches = list(re.finditer(r'(await .*?\.reply_text\([^)]+\))', content, re.DOTALL))

print(f"Total reply_text calls: {len(matches)}")

# 找到包含 <emoji 但没有 parse_mode 的
need_fix = []
for match in matches:
    text = match.group(0)
    if '<emoji' in text and 'parse_mode' not in text:
        need_fix.append((match.start(), match.end(), text))

print(f"Need to add parse_mode: {len(need_fix)}")

if need_fix:
    # 从后往前替换（避免位置偏移）
    for start, end, original in reversed(need_fix):
        # 在最后一个 ) 前添加 parse_mode='HTML'
        fixed = original.rstrip(')')
        
        # 检查是否已经有其他参数
        if ',' in fixed:
            fixed += ", parse_mode='HTML')"
        else:
            # 只有一个参数（消息文本）
            fixed += ", parse_mode='HTML')"
        
        content = content[:start] + fixed + content[end:]
        print(f"Fixed at position {start}")
    
    with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("All fixed!")
else:
    print("No fixes needed")
