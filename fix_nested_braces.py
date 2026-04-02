#!/usr/bin/env python3
with open('bot/handlers/user.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 {'{e('X')}'} -> {e('X')}
content = content.replace("{'{e(", "{e(")
content = content.replace(")'}", ")}")

with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed")
