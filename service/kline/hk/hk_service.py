#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股数据服务模块
提供港股K线数据、盘口数据、资金流向、市场情绪等数据获取服务
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

# 导入港股数据源模块
from .akshare_hk import (
    get_kline_data_from_akshare_hk,
    get_hk_realtime_data,
    get_hk_market_sentiment,
    get_hk_sector_performance,
    get_hk_fund_flow,
    get_hk_order_book,
    is_akshare_hk_available
)

# 导入工具函数
from ..utils import process_kline_data
from utils.stock import get_market_type, format_stock_code


def get_hk_kline_data(
    code: str,
    start_date: str = None,
    end_date: str = None
) -> Optional[Dict]:
    """
    获取港股K线数据
    
    Args:
        code: 股票代码（如'00700'或'0700.HK'）
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        包含K线数据的字典
    """
    # 获取市场类型和格式化代码
    market_type = get_market_type(code)
    formatted_code = format_stock_code(code)
    
    if market_type != 'HK':
        print(f"港股服务仅支持港股市场，不支持{market_type}市场")
        return None
    
    # 设置默认日期范围
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 尝试使用akshare_hk数据源
    if is_akshare_hk_available():
        result = get_kline_data_from_akshare_hk(
            code=code.replace('.HK', ''),
            formatted_code=formatted_code,
            market_type=market_type,
            start_date=start_date,
            end_date=end_date
        )
        if result:
            return result
    
    print(f"所有港股数据源均失败")
    return None


def get_hk_order_book_data(code: str) -> Optional[Dict]:
    """
    获取港股盘口数据（买卖五档）
    
    Args:
        code: 港股代码（如'00700'或'0700.HK'）
        
    Returns:
        包含盘口数据的字典
    """
    # 获取市场类型
    market_type = get_market_type(code)
    
    if market_type != 'HK':
        print(f"港股服务仅支持港股市场，不支持{market_type}市场")
        return None
    
    # 清理代码格式
    clean_code = code.replace('.HK', '')
    
    # 尝试使用akshare_hk获取盘口数据
    if is_akshare_hk_available():
        order_book = get_hk_order_book(clean_code)
        if order_book:
            return order_book
    
    print(f"获取港股盘口数据失败")
    return None


def get_hk_fund_flow_data() -> Optional[Dict]:
    """
    获取港股资金流向数据
    
    Returns:
        包含资金流向数据的字典
    """
    if is_akshare_hk_available():
        fund_flow = get_hk_fund_flow()
        if fund_flow:
            return fund_flow
    
    print(f"获取港股资金流向数据失败")
    return None


def get_hk_market_sentiment_data() -> Optional[Dict]:
    """
    获取港股市场情绪数据
    
    Returns:
        包含市场情绪数据的字典
    """
    if is_akshare_hk_available():
        sentiment = get_hk_market_sentiment()
        if sentiment:
            return sentiment
    
    print(f"获取港股市场情绪数据失败")
    return None


def get_hk_sector_performance_data() -> Optional[Dict]:
    """
    获取港股板块表现数据
    
    Returns:
        包含板块表现数据的字典
    """
    if is_akshare_hk_available():
        sector = get_hk_sector_performance()
        if sector:
            return sector
    
    print(f"获取港股板块表现数据失败")
    return None


def get_hk_realtime_quote(code: str) -> Optional[Dict]:
    """
    获取港股实时行情数据
    
    Args:
        code: 港股代码（如'00700'或'0700.HK'）
        
    Returns:
        包含实时行情数据的字典
    """
    # 获取市场类型
    market_type = get_market_type(code)
    
    if market_type != 'HK':
        print(f"港股服务仅支持港股市场，不支持{market_type}市场")
        return None
    
    # 清理代码格式
    clean_code = code.replace('.HK', '')
    
    # 尝试使用akshare_hk获取实时数据
    if is_akshare_hk_available():
        realtime_data = get_hk_realtime_data(clean_code)
        if realtime_data:
            return realtime_data
    
    print(f"获取港股实时行情数据失败")
    return None


if __name__ == "__main__":
    # 测试代码
    print(f"akshare_hk可用: {is_akshare_hk_available()}")
    
    # 测试K线数据
    kline_result = get_hk_kline_data("00700", "2024-01-01", "2024-01-10")
    if kline_result:
        print(f"成功获取港股K线数据: {kline_result['data_source']}, 数据条数: {len(kline_result['data'])}")
    
    # 测试盘口数据
    order_book_result = get_hk_order_book_data("00700")
    if order_book_result:
        print(f"成功获取港股盘口数据: {order_book_result['data_source']}")
        print(f"最新价: {order_book_result['last_price']}")
    
    # 测试资金流向数据
    fund_flow_result = get_hk_fund_flow_data()
    if fund_flow_result:
        print(f"成功获取港股资金流向数据，数据条数: {len(fund_flow_result['data'])}")
    
    # 测试市场情绪数据
    sentiment_result = get_hk_market_sentiment_data()
    if sentiment_result:
        print(f"成功获取港股市场情绪数据，数据条数: {len(sentiment_result['data'])}")
    
    # 测试板块表现数据
    sector_result = get_hk_sector_performance_data()
    if sector_result:
        print(f"成功获取港股板块表现数据，数据条数: {len(sector_result['data'])}")
    
    # 测试实时行情数据
    realtime_result = get_hk_realtime_quote("00700")
    if realtime_result:
        print(f"成功获取港股实时行情数据: {realtime_result['data_source']}, 数据条数: {len(realtime_result['data'])}")