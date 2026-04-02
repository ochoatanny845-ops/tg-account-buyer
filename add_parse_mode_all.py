#!/usr/bin/env python3
import re

files = ['bot/handlers/user.py', 'bot/handlers/admin.py']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找到所有 reply_text 和 send_message 调用
    matches = list(re.finditer(r'(await .*?\.(reply_text|send_message)\([^)]+\))', content, re.DOTALL))

    print(f"\n{filepath}:")
    print(f"  Total calls: {len(matches)}")

    # 找到包含 <emoji 但没有 parse_mode 的
    need_fix = []
    for match in matches:
        text = match.group(0)
        if '<emoji' in text and 'parse_mode' not in text:
            need_fix.append((match.start(), match.end(), text))

    print(f"  Need to add parse_mode: {len(need_fix)}")

    if need_fix:
        # 从后往前替换
        for start, end, original in reversed(need_fix):
            fixed = original.rstrip(')')
            
            if ',' in fixed:
                fixed += ", parse_mode='HTML')"
            else:
                fixed += ", parse_mode='HTML')"
            
            content = content[:start] + fixed + content[end:]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Fixed!")
    else:
        print(f"  OK")

print("\nDone!")
