#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试MongoDB缓存功能
"""

import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志，显示详细日志信息
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 设置pymongo的日志级别为WARNING，避免过多的内部调试信息
logging.getLogger('pymongo').setLevel(logging.WARNING)

from service.cache.mongodb_cache import get_cache, MongoDBCache
from service.stocks.stocks import get_stock_by_market
import time


def test_cache_connection():
    """测试MongoDB连接"""
    print("=== 测试MongoDB缓存连接 ===")
    
    cache = get_cache()
    
    if cache.is_connected():
        print("✓ MongoDB连接成功")
        
        # 获取统计信息
        stats = cache.get_stats()
        print(f"缓存统计: {stats}")
        
        return True
    else:
        print("✗ MongoDB连接失败")
        return False


def test_market_cache():
    """测试市场股票列表缓存"""
    print("\n=== 测试市场股票列表缓存 ===")
    
    # 测试CN市场
    print("1. 第一次获取CN市场数据（应该从数据源获取）...")
    start_time = time.time()
    cn_data = get_stock_by_market("cn")
    elapsed = time.time() - start_time
    
    if cn_data:
        print(f"   ✓ 获取成功，耗时: {elapsed:.2f}秒")
        print(f"     股票数量: {cn_data.get('count', 0)}")
        print(f"     是否缓存: {cn_data.get('_cached', False)}")
    else:
        print("   ✗ 获取失败")
        return False
    
    # 等待1秒
    time.sleep(1)
    
    # 第二次获取（应该从缓存获取）
    print("2. 第二次获取CN市场数据（应该从缓存获取）...")
    start_time = time.time()
    cn_data_cached = get_stock_by_market("cn")
    elapsed = time.time() - start_time
    
    if cn_data_cached:
        print(f"   ✓ 获取成功，耗时: {elapsed:.2f}秒")
        print(f"     股票数量: {cn_data_cached.get('count', 0)}")
        print(f"     是否缓存: {cn_data_cached.get('_cached', True)}")
        
        # 验证数据一致性
        if cn_data.get('count') == cn_data_cached.get('count'):
            print("   ✓ 缓存数据与原始数据一致")
        else:
            print("   ✗ 缓存数据与原始数据不一致")
            return False
    else:
        print("   ✗ 获取失败")
        return False
    
    # 测试HK市场
    print("\n3. 测试HK市场数据...")
    hk_data = get_stock_by_market("hk")
    
    if hk_data:
        print(f"   ✓ 获取成功，股票数量: {hk_data.get('count', 0)}")
        print(f"     是否缓存: {hk_data.get('_cached', False)}")
    else:
        print("   ✗ 获取失败")
        
    # 测试US市场
    print("\n4. 测试US市场数据...")
    us_data = get_stock_by_market("us")
    
    if us_data:
        print(f"   ✓ 获取成功，股票数量: {us_data.get('count', 0)}")
        print(f"     是否缓存: {us_data.get('_cached', False)}")
    else:
        print("   ✗ 获取失败")
    
    return True


def test_cache_management():
    """测试缓存管理功能"""
    print("\n=== 测试缓存管理功能 ===")
    
    cache = get_cache()
    
    # 获取缓存统计
    stats = cache.get_stats()
    print(f"当前缓存统计: {stats}")
    
    # 测试删除缓存
    print("1. 删除CN市场缓存...")
    if cache.delete("cn"):
        print("   ✓ 删除成功")
    else:
        print("   ✗ 删除失败")
    
    # 再次获取统计
    stats = cache.get_stats()
    print(f"删除后缓存统计: {stats}")
    
    # 测试清除所有缓存
    print("\n2. 清除所有缓存...")
    if cache.clear_all():
        print("   ✓ 清除成功")
    else:
        print("   ✗ 清除失败")
    
    # 最终统计
    stats = cache.get_stats()
    print(f"最终缓存统计: {stats}")
    
    return True


def test_direct_cache_api():
    """测试直接缓存API"""
    print("\n=== 测试直接缓存API ===")
    
    cache = get_cache()
    
    # 测试数据
    test_data = {
        "test_key": "test_value",
        "count": 100,
        "timestamp": "2024-01-01T00:00:00"
    }
    
    # 设置缓存
    print("1. 设置测试缓存...")
    if cache.set("test", "2024-01-01", "2024-12-31", test_data, ttl_days=1):
        print("   ✓ 设置成功")
    else:
        print("   ✗ 设置失败")
        return False
    
    # 获取缓存
    print("2. 获取测试缓存...")
    cached_data = cache.get("test", "2024-01-01", "2024-12-31")
    
    if cached_data:
        print(f"   ✓ 获取成功: {cached_data}")
        
        # 验证数据
        if cached_data.get("test_key") == "test_value":
            print("   ✓ 缓存数据验证成功")
        else:
            print("   ✗ 缓存数据验证失败")
            return False
    else:
        print("   ✗ 获取失败")
        return False
    
    # 删除测试缓存
    cache.delete("test", "2024-01-01", "2024-12-31")
    
    return True


def main():
    """主测试函数"""
    print("开始测试MongoDB缓存功能\n")
    
    all_passed = True
    
    # 测试连接
    if not test_cache_connection():
        print("\n⚠️  警告: MongoDB连接失败，缓存功能可能无法正常工作")
        print("   请检查MongoDB连接字符串和网络连接")
        print("   连接字符串: mongodb+srv://qubaoming:cVO8ANavyXm4ls3U@cluster0.hnnjj.mongodb.net/stock?retryWrites=true&w=majority&ssl=true")
        all_passed = False
    
    # 测试市场缓存
    if not test_market_cache():
        print("\n✗ 市场缓存测试失败")
        all_passed = False
    else:
        print("\n✓ 市场缓存测试通过")
    
    # 测试缓存管理
    if not test_cache_management():
        print("\n✗ 缓存管理测试失败")
        all_passed = False
    else:
        print("\n✓ 缓存管理测试通过")
    
    # 测试直接缓存API
    if not test_direct_cache_api():
        print("\n✗ 直接缓存API测试失败")
        all_passed = False
    else:
        print("\n✓ 直接缓存API测试通过")
    
    # 关闭缓存连接
    cache = get_cache()
    cache.close()
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ 所有测试通过！缓存功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查上述错误信息。")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)