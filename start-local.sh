#!/bin/bash

# 启动股票K线数据服务
PYTHONPATH=. python3 -m hypercorn main:app --reload --bind 0.0.0.0:8000
