#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baostock数据源模块
用于获取A股K线数据
{
  "code": "600519",
  "name": "茅台",
  "market": "A",
  "data_source": "baostock",
  "data": [
    {
      "date": "2025-11-21",
      "open": 1470.5,
      "high": 1480,
      "low": 1456,
      "close": 1466.6,
      "volume": 4260720
    }
  ]
}
"""

import os
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

from ..utils import process_kline_data


def get_kline_data_from_baostock(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict[str, Any]]:
    """
    从Baostock获取K线数据
    
    Args:
        code: 股票代码（如：000001）
        formatted_code: 格式化后的股票代码（如：000001.SZ）
        market_type: 市场类型（A股为'A'）
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        
    Returns:
        包含K线数据的字典，格式为：
        {
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "baostock",
            "data": processed_data
        }
        如果失败则返回None
    """
    try:
        # 使用绝对导入避免本地文件冲突
        import sys
        import os
        
        # 确保从系统包导入baostock，而不是本地文件
        # 临时从sys.path中移除可能包含本地baostock文件的目录
        original_path = sys.path.copy()
        
        # 移除可能包含本地baostock文件的目录
        paths_to_remove = []
        for path in sys.path:
            if os.path.exists(path) and os.path.isdir(path):
                # 检查是否包含本地baostock.py文件
                local_baostock_path = os.path.join(path, 'baostock.py')
                if os.path.exists(local_baostock_path):
                    paths_to_remove.append(path)
                # 检查是否包含bs_stocks.py文件（可能被误导入）
                local_bs_stocks_path = os.path.join(path, 'bs_stocks.py')
                if os.path.exists(local_bs_stocks_path):
                    paths_to_remove.append(path)
        
        for path in paths_to_remove:
            if path in sys.path:
                sys.path.remove(path)
        
        try:
            import baostock as bs
        finally:
            # 恢复原始sys.path
            sys.path = original_path
        
        # 检查baostock是否可用
        if not is_baostock_available():
            print("baostock 库不可用")
            return None
        
        # 登录Baostock
        print(f'11 - bs模块属性: {dir(bs)}')
        print(f'11 - bs模块是否有login属性: {"login" in dir(bs)}')
        print(f'11 - bs模块位置: {bs.__file__}')
        
        # 检查login属性是否存在
        if not hasattr(bs, 'login'):
            print('错误: bs模块没有login属性')
            print(f'bs模块的所有属性: {dir(bs)}')
            return None
            
        lg = bs.login()
        print('22 - login成功')
        if lg.error_code != '0':
            print(f"baostock 登录失败: {lg.error_msg}")
            return None
        
        # 根据市场类型确定股票代码
        if market_type == 'A':
            # Baostock使用格式：sz.000001 或 sh.600000
            # 使用原始code判断，因为formatted_code移除了后缀
            if code.endswith('.SH') or code.endswith('.sh'):
                bs_code = f"sh.{code.split('.')[0]}"
            elif code.endswith('.SZ') or code.endswith('.sz'):
                bs_code = f"sz.{code.split('.')[0]}"
            else:
                # 如果没有后缀，尝试根据代码前缀判断
                if code.startswith('6'):
                    bs_code = f"sh.{code}"
                elif code.startswith('0') or code.startswith('3'):
                    bs_code = f"sz.{code}"
                else:
                    print(f"baostock 无法确定市场: {code}")
                    bs.logout()
                    return None
        else:
            print(f"baostock 不支持的市场类型: {market_type}")
            bs.logout()
            return None
        
        # 获取日线数据
        fields = "date,open,high,low,close,volume"
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="3"  # 复权类型：3=不复权
        )
        
        if rs.error_code != '0':
            print(f"baostock 查询失败: {rs.error_msg}")
            bs.logout()
            return None
        
        # 转换为DataFrame
        data_list = []
        while (rs.error_code == '0') and rs.next():
            data_list.append(rs.get_row_data())
        
        if not data_list:
            print(f"baostock 未找到数据: {bs_code}")
            bs.logout()
            return None
        
        print(f"baostock 获取到 {len(data_list)} 条数据")
        print(f"数据字段: {fields}")
        print(f"第一条数据: {data_list[0] if data_list else '空'}")
        
        df = pd.DataFrame(data_list, columns=fields.split(','))
        
        # 登出
        bs.logout()
        
        # 转换数据类型
        df['open'] = pd.to_numeric(df['open'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        
        # 转换日期格式
        df['date'] = pd.to_datetime(df['date'])
        
        # 按日期排序
        df = df.sort_values('date')
        
        # 处理数据
        processed_data = process_kline_data(df, 'baostock')
        
        if not processed_data:
            print("baostock 数据处理失败")
            return None
        
        return {
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "baostock",
            "data": processed_data
        }
        
    except Exception as e:
        import traceback
        print(f"baostock 数据源失败: {type(e).__name__}: {e}")
        print("完整错误信息:")
        traceback.print_exc()
        # 确保登出
        try:
            import baostock as bs
            bs.logout()
        except:
            pass
        return None


def is_baostock_available() -> bool:
    """检查baostock是否可用"""
    try:
        # 使用与主函数相同的导入逻辑避免本地文件冲突
        import sys
        import os
        
        # 确保从系统包导入baostock，而不是本地文件
        # 临时从sys.path中移除可能包含本地baostock文件的目录
        original_path = sys.path.copy()
        
        # 移除可能包含本地baostock文件的目录
        paths_to_remove = []
        for path in sys.path:
            if os.path.exists(path) and os.path.isdir(path):
                # 检查是否包含本地baostock.py文件
                local_baostock_path = os.path.join(path, 'baostock.py')
                if os.path.exists(local_baostock_path):
                    paths_to_remove.append(path)
                # 检查是否包含bs_stocks.py文件（可能被误导入）
                local_bs_stocks_path = os.path.join(path, 'bs_stocks.py')
                if os.path.exists(local_bs_stocks_path):
                    paths_to_remove.append(path)
        
        for path in paths_to_remove:
            if path in sys.path:
                sys.path.remove(path)
        
        try:
            import baostock as bs
            return True
        finally:
            # 恢复原始sys.path
            sys.path = original_path
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"baostock可用: {is_baostock_available()}")
    
    if is_baostock_available():
        # 测试获取A股数据
        result = get_kline_data_from_baostock(
            code="000001",
            formatted_code="000001.SZ",
            market_type="A",
            start_date="2024-01-01",
            end_date="2024-01-10"
        )
        
        if result:
            print(f"成功获取A股数据: {result['data_source']}, 数据条数: {len(result['data'])}")
        else:
            print("获取A股数据失败")
    else:
        print("请安装baostock库: pip install baostock")