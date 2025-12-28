#!/usr/bin/env python3
from openbb import obb

print('Testing eastmoney provider...')
try:
    result = obb.equity.screener(country='hk', provider='eastmoney')
    print('Success:', result is not None)
except Exception as e:
    print('Error:', e)

print('\nTesting fmp provider...')
try:
    result = obb.equity.screener(country='hk', provider='fmp')
    print('Success:', result is not None)
except Exception as e:
    print('Error:', e)

print('\nTesting yfinance provider...')
try:
    result = obb.equity.screener(country='hk', provider='yfinance')
    print('Success:', result is not None)
except Exception as e:
    print('Error:', e)