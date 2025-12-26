#!/usr/bin/env python3
"""检查 intrinio 提供者支持的功能"""

from openbb import obb
import inspect

print("检查 intrinio 提供者支持的功能...")

# 检查 equity 模块
print("\n检查 equity 模块:")
equity_methods = [attr for attr in dir(obb.equity) if not attr.startswith('_')]
for method in equity_methods:
    try:
        func = getattr(obb.equity, method)
        if hasattr(func, '__doc__') and func.__doc__:
            if 'intrinio' in func.__doc__.lower():
                print(f"  {method}: 支持 intrinio")
    except:
        pass

# 检查其他可能包含股票列表的模块
print("\n检查其他模块:")
modules_to_check = ['stocks', 'reference', 'screener']
for module_name in modules_to_check:
    if hasattr(obb, module_name):
        module = getattr(obb, module_name)
        methods = [attr for attr in dir(module) if not attr.startswith('_')]
        for method in methods:
            try:
                func = getattr(module, method)
                if hasattr(func, '__doc__') and func.__doc__:
                    if 'intrinio' in func.__doc__.lower():
                        print(f"  {module_name}.{method}: 支持 intrinio")
            except:
                pass