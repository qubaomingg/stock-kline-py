"""
tiingo数据源模块
用于从Tiingo获取美股K线数据
{
  "code": "TSLA",
  "name": "特斯拉",
  "market": "US",
  "data_source": "tiingo",
  "data": [
    {
      "date": "2025-11-17",
      "open": 398.74,
      "high": 423.96,
      "low": 398.74,
      "close": 408.92,
      "volume": 102214259
    }
 ]
}
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

def get_kline_data_from_tiingo(
    code: str,
    formatted_code: str,
    market_type: str,
    start_date: str,
    end_date: str,
    api_key: str
) -> Optional[Dict]:
    """
    从Tiingo获取K线数据
    
    Args:
        code: 原始股票代码
        formatted_code: 格式化后的股票代码
        market_type: 市场类型 (A, HK, US)
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        api_key: Tiingo API密钥
        
    Returns:
        包含K线数据的字典，格式为:
        {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "tiingo",
            "data": processed_data
        }
        如果获取失败则返回None
    """
    
    try:
        from tiingo import TiingoClient
    except ImportError:
        print("tiingo未安装，无法使用tiingo数据源")
        return None
    
    if not api_key:
        print("tiingo需要API密钥，跳过")
        return None
    
    try:
        config = {
            'api_key': api_key,
            'session': True
        }
        client = TiingoClient(config)
        
        # 获取日线数据
        # start_date和end_date已经是字符串格式，直接使用
        data = client.get_ticker_price(formatted_code, 
                                      fmt='json', 
                                      startDate=start_date,
                                      endDate=end_date,
                                      frequency='daily')
        
        # tiingo返回的数据格式需要特殊处理
        if isinstance(data, list) and len(data) > 0:
            # 确保每个字典都有正确的键
            for item in data:
                if 'date' not in item:
                    item['date'] = item.get('date', item.get('timestamp', ''))
                # 重命名列
                item['open'] = item.get('open', item.get('adjOpen', 0))
                item['high'] = item.get('high', item.get('adjHigh', 0))
                item['low'] = item.get('low', item.get('adjLow', 0))
                item['close'] = item.get('close', item.get('adjClose', 0))
                item['volume'] = item.get('volume', item.get('adjVolume', 0))
        
        if not data:
            print(f"tiingo 数据源返回空数据")
            return None
        
        # 转换为DataFrame
        data = pd.DataFrame(data)
        data['date'] = pd.to_datetime(data['date'])
        data.set_index('date', inplace=True)
        
        print(f"tiingo 数据源成功获取数据，数据形状: {data.shape}")
        
        # 处理数据 - 注意：process_kline_data函数需要从主模块导入
        from ..kline import process_kline_data
        processed_data = process_kline_data(data, 'tiingo')
        
        return {
            "code": code,
            "formatted_code": formatted_code,
            "market": market_type,
            "data_source": "tiingo",
            "data": processed_data
        }
        
    except Exception as e:
        print(f"tiingo 数据源失败: {e}")
        return None


def is_tiingo_available() -> bool:
    """检查tiingo是否可用"""
    try:
        from tiingo import TiingoClient
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"tiingo可用: {is_tiingo_available()}")
    
    # 需要API密钥才能实际测试
    import os
    api_key = os.environ.get('TIINGO_API_KEY', '')
    
    if api_key:
        # 测试获取美股数据
        result = get_kline_data_from_tiingo(
            code="AAPL",
            formatted_code="AAPL",
            market_type="US",
            start_date="2024-01-01",
            end_date="2024-01-10",
            api_key=api_key
        )
        
        if result:
            print(f"成功获取美股数据: {result['data_source']}, 数据条数: {len(result['data'])}")
        else:
            print("获取美股数据失败")
    else:
        print("未设置TIINGO_API_KEY环境变量，跳过实际测试")