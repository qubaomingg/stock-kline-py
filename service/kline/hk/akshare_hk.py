#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
akshare港股数据源模块
用于从akshare获取港股K线数据，支持以下数据源：
1. Sina Finance：实时行情快照、盘口数据、资金流向基础数据
2. Tencent Finance：分时行情、板块涨跌幅排行、市场情绪统计
3. 东方财富网：行业板块数据、概念题材排行、资金净流入基础数据
4. 雪球：个股讨论热度、市场情绪数据，辅助舆情分析
{
  "code": "01024",
  "name": "快手",
  "market": "HK",
  "data_source": "akshare_hk",
  "data": [
    {
      "date": "2025-11-24",
      "open": 65,
      "high": 68.9,
      "low": 65,
      "close": 68.55,
      "volume": 67219569
    }
    ]
}
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import time
from datetime import datetime

# 导入数据处理函数
from ..utils import process_kline_data


def get_kline_data_from_akshare_hk(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str
) -> Optional[Dict]:
    """
    从akshare获取港股K线数据
    
    Args:
        code: 原始股票代码（如'00700'）
        formatted_code: 格式化后的股票代码（如'0700.HK'）
        market_type: 市场类型（应为'HK'）
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        
    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "akshare_hk",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    
    if market_type != 'HK':
        print(f"akshare_hk模块仅支持港股市场，不支持{market_type}市场")
        return None
    
    try:
        import akshare as ak
    except ImportError:
        print("akshare未安装，无法使用akshare_hk数据源")
        return None
    
    # 尝试不同的akshare函数获取港股数据
    data_sources = [
        {"name": "stock_hk_hist", "func": ak.stock_hk_hist},
        {"name": "stock_hk_daily", "func": ak.stock_hk_daily},
    ]
    
    for source in data_sources:
        try:
            print(f"尝试使用 {source['name']} 获取港股数据...")
            
            if source['name'] == "stock_hk_hist":
                # stock_hk_hist函数
                data = source['func'](
                    symbol=code,  # 使用原始代码，如'00700'
                    period='daily',
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust='qfq'  # 前复权
                )
            elif source['name'] == "stock_hk_daily":
                # stock_hk_daily函数（可能需要不同的参数格式）
                # 先尝试获取所有数据，然后过滤日期范围
                try:
                    data = source['func'](
                        symbol=code,
                        adjust='qfq'
                    )
                    # 过滤日期范围
                    if data is not None and not data.empty:
                        data = data[(data.index >= start_date) & (data.index <= end_date)]
                except Exception as e:
                    print(f"stock_hk_daily调用失败: {e}")
                    data = None
            else:
                continue
                
            if data is not None and not data.empty:
                print(f"{source['name']} 成功获取港股数据，数据形状: {data.shape}")
                
                # 处理数据
                processed_data = process_kline_data(data, 'akshare_hk')
                
                return {
                    "code": code,
                    "formatted_code": formatted_code,
                    "market": market_type,
                    "data_source": "akshare_hk",
                    "data": processed_data
                }
                
        except Exception as e:
            print(f"{source['name']} 获取港股数据失败: {e}")
            continue
    
    # 如果所有数据源都失败，尝试获取实时数据
    print("所有历史数据源失败，尝试获取实时数据...")
    try:
        # 获取实时行情数据
        realtime_data = get_hk_realtime_data(code)
        if realtime_data:
            print(f"成功获取港股实时数据")
            return realtime_data
    except Exception as e:
        print(f"获取实时数据失败: {e}")
    
    print(f"所有akshare港股数据源均失败")
    return None


def get_hk_realtime_data(code: str) -> Optional[Dict]:
    """
    获取港股实时行情数据
    
    Args:
        code: 港股代码（如'00700'）
        
    Returns:
        包含实时数据的字典
    """
    try:
        import akshare as ak
        
        # 尝试获取实时行情
        realtime = ak.stock_hk_spot_em()
        if realtime is not None and not realtime.empty:
            # 查找指定代码的数据
            stock_data = realtime[realtime['代码'] == code]
            if not stock_data.empty:
                # 转换为K线数据格式
                today = datetime.now().strftime('%Y-%m-%d')
                kline_data = [{
                    "date": today,
                    "open": float(stock_data.iloc[0]['今开']),
                    "high": float(stock_data.iloc[0]['最高']),
                    "low": float(stock_data.iloc[0]['最低']),
                    "close": float(stock_data.iloc[0]['最新价']),
                    "volume": float(stock_data.iloc[0]['成交量'])
                }]
                
                return {
                    "code": code,
                    "formatted_code": f"{code}.HK",
                    "market": "HK",
                    "data_source": "akshare_hk_realtime",
                    "data": kline_data
                }
    except Exception as e:
        print(f"获取实时数据失败: {e}")
    
    return None


def get_hk_market_sentiment() -> Optional[Dict]:
    """
    获取港股市场情绪数据
    
    Returns:
        包含市场情绪数据的字典
    """
    try:
        import akshare as ak
        
        # 获取港股指数数据
        hk_index_data = ak.stock_hk_index_spot_sina()
        
        if hk_index_data is not None and not hk_index_data.empty:
            # 格式化数据
            formatted_data = []
            for _, row in hk_index_data.iterrows():
                formatted_data.append({
                    "index_code": row['代码'],
                    "index_name": row['名称'],
                    "latest_price": float(row['最新价']),
                    "change_amount": float(row['涨跌额']),
                    "change_percent": float(row['涨跌幅'].rstrip('%')) if isinstance(row['涨跌幅'], str) else float(row['涨跌幅']),
                    "open_price": float(row['今开']),
                    "high_price": float(row['最高']),
                    "low_price": float(row['最低']),
                    "prev_close": float(row['昨收'])
                })
            
            return {
                "data_source": "akshare_hk",
                "type": "market_sentiment",
                "data": formatted_data
            }
    except Exception as e:
        print(f"获取市场情绪数据失败: {e}")
    
    return None


def get_hk_sector_performance() -> Optional[Dict]:
    """
    获取港股板块表现数据
    
    Returns:
        包含板块表现数据的字典
    """
    try:
        import akshare as ak
        
        # 获取行业板块数据
        industry_data = ak.stock_board_industry_name_em()
        
        if industry_data is not None and not industry_data.empty:
            # 格式化数据
            formatted_data = []
            for _, row in industry_data.iterrows():
                formatted_data.append({
                    "rank": row.get("排名"),
                    "sector_name": row.get("板块名称"),
                    "sector_code": row.get("板块代码"),
                    "latest_price": row.get("最新价"),
                    "change_amount": row.get("涨跌额"),
                    "change_percent": row.get("涨跌幅"),
                    "total_market_cap": row.get("总市值"),
                    "turnover_rate": row.get("换手率"),
                    "rising_count": row.get("上涨家数"),
                    "falling_count": row.get("下跌家数"),
                    "leading_stock": row.get("领涨股票"),
                    "leading_stock_change": row.get("领涨股票-涨跌幅")
                })
            
            return {
                "data_source": "akshare_hk",
                "type": "sector_performance",
                "data": formatted_data
            }
    except Exception as e:
        print(f"获取板块表现数据失败: {e}")
    
    return None


def get_hk_fund_flow() -> Optional[Dict]:
    """
    获取港股资金流向数据（沪深港通资金流向）
    
    Returns:
        包含资金流向数据的字典
    """
    try:
        import akshare as ak
        
        # 获取沪深港通资金流向数据
        fund_flow = ak.stock_hsgt_fund_flow_summary_em()
        
        if fund_flow is not None and not fund_flow.empty:
            # 筛选港股通数据
            hk_fund_flow = fund_flow[fund_flow['板块'].str.contains('港股通')]
            
            if not hk_fund_flow.empty:
                return {
                    "data_source": "akshare_hk",
                    "type": "fund_flow",
                    "data": hk_fund_flow.to_dict('records')
                }
    except Exception as e:
        print(f"获取资金流向数据失败: {e}")
    
    return None


def get_hk_order_book(code: str) -> Optional[Dict]:
    """
    获取港股盘口数据（买卖五档）
    
    Args:
        code: 港股代码（如'00700'）
        
    Returns:
        包含盘口数据的字典
    """
    try:
        import akshare as ak
        
        # 获取实时行情数据，其中包含盘口信息
        realtime = ak.stock_hk_spot_em()
        if realtime is not None and not realtime.empty:
            # 查找指定代码的数据
            stock_data = realtime[realtime['代码'] == code]
            if not stock_data.empty:
                # 提取盘口数据
                order_book = {
                    "code": code,
                    "formatted_code": f"{code}.HK",
                    "market": "HK",
                    "data_source": "akshare_hk",
                    "type": "order_book",
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "bid_prices": [],
                    "bid_volumes": [],
                    "ask_prices": [],
                    "ask_volumes": [],
                    "last_price": float(stock_data.iloc[0]['最新价']),
                    "volume": float(stock_data.iloc[0]['成交量']),
                    "turnover": float(stock_data.iloc[0]['成交额']),
                    "high": float(stock_data.iloc[0]['最高']),
                    "low": float(stock_data.iloc[0]['最低']),
                    "open": float(stock_data.iloc[0]['今开']),
                    "prev_close": float(stock_data.iloc[0]['昨收']),
                    "change": float(stock_data.iloc[0]['涨跌额']),
                    "change_percent": float(stock_data.iloc[0]['涨跌幅'])
                }
                
                # 注意：akshare的实时数据可能不包含完整的买卖五档数据
                # 这里我们使用实时行情中的相关字段
                # 如果需要完整的买卖五档，可能需要使用其他API
                
                return order_book
    except Exception as e:
        print(f"获取盘口数据失败: {e}")
    
    return None


def is_akshare_hk_available() -> bool:
    """检查akshare_hk是否可用"""
    try:
        import akshare
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"akshare_hk可用: {is_akshare_hk_available()}")
    
    # 测试获取港股数据
    result = get_kline_data_from_akshare_hk(
        code="00700",
        formatted_code="0700.HK",
        market_type="HK",
        start_date="2024-01-01",
        end_date="2024-01-10"
    )
    
    if result:
        print(f"成功获取港股数据: {result['data_source']}, 数据条数: {len(result['data'])}")
        print(f"第一条数据: {result['data'][0] if result['data'] else '空'}")
    else:
        print("获取港股数据失败")
    
    # 测试市场情绪数据
    sentiment = get_hk_market_sentiment()
    if sentiment:
        print(f"成功获取市场情绪数据，数据条数: {len(sentiment['data'])}")
    
    # 测试板块表现数据
    sector = get_hk_sector_performance()
    if sector:
        print(f"成功获取板块表现数据，数据条数: {len(sector['data'])}")
    
    # 测试资金流向数据
    fund_flow = get_hk_fund_flow()
    if fund_flow:
        print(f"成功获取资金流向数据，数据条数: {len(fund_flow['data'])}")