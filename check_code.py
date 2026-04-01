#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量检查脚本
运行此脚本确保代码没有常见错误
"""
import os
import sys
import ast
from pathlib import Path


def check_duplicate_functions():
    """检查是否有重复定义的函数（同一作用域内）"""
    errors = []
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8-sig') as f:  # 处理 BOM
                tree = ast.parse(f.read())
            
            # 只检查模块级别的函数
            function_names = {}
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    if node.name in function_names:
                        errors.append(
                            f"❌ {py_file}: 重复定义函数 '{node.name}' "
                            f"(第{function_names[node.name]}行 和 第{node.lineno}行)"
                        )
                    else:
                        function_names[node.name] = node.lineno
        except Exception as e:
            pass  # 跳过无法解析的文件
    
    return errors


def check_undefined_imports():
    """检查导入的函数是否存在"""
    errors = []
    
    # 检查 validator.py 中定义的函数（只检查模块级别）
    validator_functions = set()
    try:
        with open('bot/utils/validator.py', 'r', encoding='utf-8-sig') as f:
            tree = ast.parse(f.read())
            for node in tree.body:  # 只检查顶层
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    validator_functions.add(node.name)
    except Exception as e:
        return errors  # 跳过
    
    # 检查 user.py 是否导入了不存在的函数
    try:
        with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
            content = f.read()
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == 'bot.utils.validator':
                        for alias in node.names:
                            if alias.name not in validator_functions:
                                errors.append(
                                    f"❌ user.py 导入了不存在的函数: {alias.name}"
                                )
    except Exception as e:
        pass  # 跳过
    
    return errors


def check_syntax():
    """检查所有 Python 文件的语法"""
    errors = []
    
    for py_file in Path('.').rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8-sig') as f:  # 处理 BOM
                ast.parse(f.read())
        except SyntaxError as e:
            errors.append(f"❌ {py_file}: 语法错误 (第{e.lineno}行: {e.msg})")
    
    return errors


def main():
    import sys
    # 修复 Windows 编码问题
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("=" * 60)
    print("🔍 代码质量检查")
    print("=" * 60)
    print()
    
    all_errors = []
    
    # 1. 检查语法
    print("[1/3] 检查语法错误...")
    syntax_errors = check_syntax()
    if syntax_errors:
        all_errors.extend(syntax_errors)
        print(f"  ⚠️  发现 {len(syntax_errors)} 个语法错误")
    else:
        print("  ✅ 语法检查通过")
    print()
    
    # 2. 检查重复函数
    print("[2/3] 检查重复定义...")
    duplicate_errors = check_duplicate_functions()
    if duplicate_errors:
        all_errors.extend(duplicate_errors)
        print(f"  ⚠️  发现 {len(duplicate_errors)} 个重复定义")
    else:
        print("  ✅ 无重复定义")
    print()
    
    # 3. 检查导入
    print("[3/3] 检查导入错误...")
    import_errors = check_undefined_imports()
    if import_errors:
        all_errors.extend(import_errors)
        print(f"  ⚠️  发现 {len(import_errors)} 个导入错误")
    else:
        print("  ✅ 导入检查通过")
    print()
    
    # 输出结果
    print("=" * 60)
    if all_errors:
        print("❌ 检查失败！发现以下问题：")
        print()
        for error in all_errors:
            print(error)
        print()
        print("=" * 60)
        sys.exit(1)
    else:
        print("✅ 所有检查通过！代码质量良好。")
        print("=" * 60)
        sys.exit(0)


if __name__ == '__main__':
    main()
