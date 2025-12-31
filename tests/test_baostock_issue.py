#!/usr/bin/env python3
"""测试baostock模块是否存在'login'属性问题"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 测试直接导入baostock库
    import baostock
    print(f"baostock版本: {baostock.__version__ if hasattr(baostock, '__version__') else '未知'}")
    print(f"baostock有login属性: {hasattr(baostock, 'login')}")
    print(f"baostock有logout属性: {hasattr(baostock, 'logout')}")
    print(f"baostock有query_history_k_data_plus属性: {hasattr(baostock, 'query_history_k_data_plus')}")
    
    # 测试从项目导入
    from service.kline.cn.baostock import is_baostock_available, get_kline_data_from_baostock
    print(f"\n从项目导入成功")
    print(f"is_baostock_available: {is_baostock_available()}")
    
    if is_baostock_available():
        print("\n测试获取数据...")
        result = get_kline_data_from_baostock(
            code="000001",
            formatted_code="000001.SZ",
            market_type="A",
            start_date="2024-01-01",
            end_date="2024-01-10"
        )
        if result:
            print(f"成功获取数据，数据源: {result['data_source']}, 数据条数: {len(result['data'])}")
        else:
            print("获取数据失败")
    else:
        print("baostock不可用")
        
except AttributeError as e:
    print(f"属性错误: {e}")
    import traceback
    traceback.print_exc()
except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()