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

## 📚 API文档展示

FastAPI自动生成交互式API文档，启动服务后可以通过以下地址访问：

### Swagger UI
- **地址**: `http://localhost:8000/docs`
- **特点**: 交互式API文档，支持在线测试API接口
- **功能**:
  - 查看所有API端点
  - 查看请求/响应模型
  - 在线发送测试请求
  - 查看请求示例

### ReDoc
- **地址**: `http://localhost:8000/redoc`
- **特点**: 更美观的API文档展示
- **功能**:
  - 更清晰的API文档布局
  - 更好的可读性
  - 支持Markdown格式的描述

### OpenAPI JSON
- **地址**: `http://localhost:8000/openapi.json`
- **特点**: 原始的OpenAPI规范JSON文件
- **用途**:
  - 用于API客户端生成
  - 导入到其他API工具
  - 自动化API测试

### 如何访问API文档

1. 启动FastAPI服务：
   ```bash
   python3 -m hypercorn main:app --reload --bind 0.0.0.0:8000
   ```

2. 打开浏览器访问：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. 在Swagger UI中，您可以：
   - 点击"Try it out"按钮测试API
   - 查看请求参数和响应格式
   - 查看API的详细描述

### 自定义API文档

当前项目使用FastAPI的默认配置，您可以在`main.py`中自定义API文档的标题和描述以提供更好的文档体验：

```python
app = FastAPI(
    title="股票K线数据API",
    description="提供股票K线数据查询服务的API接口",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI地址（默认）
    redoc_url="/redoc",  # ReDoc地址（默认）
    openapi_url="/openapi.json"  # OpenAPI JSON地址（默认）
)
```

**当前配置说明**：
- 项目使用`app = FastAPI()`默认初始化
- Swagger UI地址：`http://localhost:8000/docs`
- ReDoc地址：`http://localhost:8000/redoc`
- OpenAPI JSON地址：`http://localhost:8000/openapi.json`

**自定义选项**：
- 可以修改`docs_url`或`redoc_url`来改变文档地址
- 设置`docs_url=None`或`redoc_url=None`可以禁用对应的文档界面
- 可以通过`openapi_tags`参数对API进行分组和分类

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
