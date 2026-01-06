#!/usr/bin/env python3
"""
测试缓存调试脚本
"""

from service.cache.mongodb_cache import get_cache
from pymongo import MongoClient
import json
import time

def test_cache_set_and_get():
    """测试缓存设置和获取"""
    cache = get_cache()
    print('MongoDB连接状态:', cache.is_connected())
    
    # 测试数据
    test_data = {'test': 'data', 'market': 'test_market'}
    
    # 设置缓存
    result = cache.set('test_market', test_data, ttl_days=1)
    print('缓存设置结果:', result)
    
    # 等待一下
    time.sleep(1)
    
    # 直接从MongoDB检查
    client = MongoClient('mongodb://localhost:27017/')
    db = client['stock']
    collection = db['MarketStockCache']
    
    item = collection.find_one({'cache_key': 'test_market'})
    print('MongoDB中查找结果:', item is not None)
    
    if item:
        print('缓存键:', item.get('cache_key'))
        print('code:', item.get('code'))
        print('数据:', item.get('data'))
        print('过期时间:', item.get('expires_at'))
        
        # 检查数据是否可序列化
        try:
            data = item.get('data')
            if data:
                json_str = json.dumps(data)
                print('数据可序列化，长度:', len(json_str))
            else:
                print('数据为空')
        except Exception as e:
            print('数据序列化错误:', e)
    
    # 通过缓存API获取
    cached = cache.get('test_market')
    print('通过缓存API获取结果:', cached is not None)
    if cached:
        print('获取到的数据:', cached)
    
    client.close()

if __name__ == '__main__':
    test_cache_set_and_get()