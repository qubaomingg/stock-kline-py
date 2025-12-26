---
title: FastUI
description: A FastUI server
tags:
  - fastapi
  - fastui
  - hypercorn
  - pydantic
  - python
---

# FastAPI Example

This example starts up a [FastUI](https://github.com/pydantic/FastUI/tree/main) server.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/O2XqhT?referralCode=c-aq4K)

## ✨ Features

- [FastAPI](https://fastapi.tiangolo.com/)
- [FastUI](https://github.com/pydantic/FastUI/tree/main)
- [Pydantic](https://pydantic-docs.helpmanual.io/)
- [Hypercorn](https://hypercorn.readthedocs.io/)
- Python 3

## 🙋🏿‍♀️ How to use

- Clone locally and install packages with pip using `pip install -r requirements.txt`
- Run locally using `python3 -m hypercorn main:app --reload --bind 0.0.0.0:8000`

## 📝 Notes

- To learn about how to use FastAPI with most of its features, you can visit the [FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/)
- To learn about FastUI and how to use it, read their [Documentation](https://github.com/pydantic/FastUI/tree/main)
- To learn about Pydantic and how to use it, read their [Documentation](https://pydantic-docs.helpmanual.io/)
- To learn about Hypercorn and how to configure it, read their [Documentation](https://hypercorn.readthedocs.io/)

## 🔧 Python调试断点

### 使用内置的`breakpoint()`函数

Python 3.7+ 提供了内置的`breakpoint()`函数，可以在代码中设置断点：

```python
# 在代码中设置断点
def some_function():
    result = calculate_something()
    breakpoint()  # 程序会在这里暂停
    return result
```

运行程序时，当执行到`breakpoint()`时，程序会进入Python调试器（PDB）。

### 使用PDB模块

也可以直接导入`pdb`模块来设置断点：

```python
import pdb

def some_function():
    result = calculate_something()
    pdb.set_trace()  # 设置断点
    return result
```

### 调试命令

进入调试器后，可以使用以下常用命令：

- `n` (next) - 执行下一行
- `s` (step) - 进入函数调用
- `c` (continue) - 继续执行直到下一个断点
- `l` (list) - 显示当前代码位置
- `p <expression>` - 打印表达式的值
- `q` (quit) - 退出调试器

### 在FastAPI应用中调试

对于这个FastAPI项目，可以在`main.py`中的任何位置添加断点来调试API请求处理逻辑。例如：

```python
@app.get("/api/stock/kline")
async def get_stock_kline(code: str, name: str = None):
    """
    获取股票K线数据
    """
    print(f'获取股票K线数据，股票代码：{code}，股票名称：{name}')
    breakpoint()  # 在这里设置断点
    # ... 其余代码
```

### 环境变量配置

如果需要配置API密钥，请复制`.env.example`文件为`.env`并填写相应的API密钥：

```bash
cp .env.example .env
# 然后编辑.env文件，填入你的API密钥
```

### 常见问题

1. **断点不生效**：确保在调试模式下运行程序
2. **调试器无法启动**：检查Python版本是否为3.7+
3. **API密钥配置**：确保已正确配置`.env`文件中的API密钥
