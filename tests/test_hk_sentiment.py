import akshare as ak
import re

# 搜索所有包含hk的函数
functions = [f for f in dir(ak) if 'hk' in f.lower()]
print('HK functions:')
for f in functions:
    print(f'  {f}')

# 搜索可能包含市场情绪的函数
sentiment_keywords = ['sentiment', 'indicator', 'overview', 'market', 'index', 'vix', 'fear', 'greed']
print('\nPossible sentiment functions:')
for f in functions:
    for keyword in sentiment_keywords:
        if keyword in f.lower():
            print(f'  {f}')
            break

# 测试一些可能的函数
print('\nTesting some functions:')
try:
    # 尝试获取港股指数数据
    hk_index = ak.stock_hk_spot_em()
    print('stock_hk_spot_em shape:', hk_index.shape if hk_index is not None else 'None')
    print('Columns:', list(hk_index.columns) if hk_index is not None else 'None')
except Exception as e:
    print(f'stock_hk_spot_em error: {e}')

try:
    # 尝试获取港股历史数据
    hk_hist = ak.stock_hk_hist(symbol='00700', period='daily', start_date='20240101', end_date='20241231', adjust='')
    print('stock_hk_hist shape:', hk_hist.shape if hk_hist is not None else 'None')
except Exception as e:
    print(f'stock_hk_hist error: {e}')

try:
    # 尝试获取港股指数
    hk_index_data = ak.stock_hk_index_spot_sina()
    print('stock_hk_index_spot_sina shape:', hk_index_data.shape if hk_index_data is not None else 'None')
except Exception as e:
    print(f'stock_hk_index_spot_sina error: {e}')