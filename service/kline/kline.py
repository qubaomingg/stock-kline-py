"""
股票K线数据获取服务
根据openBB.md中的免费数据源信息，按市场类型选择数据源
重构版本：使用独立的数据源模块
"""
import os
import sys
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import time

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入数据源模块
from service.kline.us.yfinance import get_kline_data_from_yfinance, is_yfinance_available
from service.kline.cn.akshare import get_kline_data_from_akshare, is_akshare_available
from service.kline.hk.akshare_hk import get_kline_data_from_akshare_hk, is_akshare_hk_available
from service.kline.us.alpha_vantage import get_kline_data_from_alpha_vantage, is_alpha_vantage_available
from service.kline.us.tiingo import get_kline_data_from_tiingo, is_tiingo_available
from service.kline.cn.baostock import get_kline_data_from_baostock, is_baostock_available
from service.kline.hk.eastmoney_hk import get_kline_data_from_eastmoney_hk, is_eastmoney_hk_available
from service.kline.cn.eastmoney_cn import get_kline_data_from_eastmoney_cn, is_eastmoney_cn_available


# 导入工具函数
# 使用绝对导入避免与本地utils.py冲突
try:
    from utils.stock import get_market_type, format_stock_code
except ImportError:
    # 如果无法导入，尝试从项目根目录直接导入
    import importlib.util
    spec = importlib.util.spec_from_file_location("stock", os.path.join(project_root, "utils", "stock.py"))
    stock_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stock_module)
    get_market_type = stock_module.get_market_type
    format_stock_code = stock_module.format_stock_code

# 数据源配置
DATA_SOURCES_CONFIG = {
    'A': ['eastmoney_cn', 'akshare', 'baostock'],
    'HK': ['eastmoney_hk', 'akshare_hk'],
    'US': ['yfinance', 'alpha_vantage', 'tiingo']
}

# API密钥配置
API_KEYS = {
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
    'tiingo': os.getenv('TIINGO_API_KEY', ''),
}


def process_kline_data(data: pd.DataFrame, source: str) -> List[Dict]:
    """
    处理K线数据，统一格式
    
    Args:
        data: 原始数据DataFrame
        source: 数据源名称
        
    Returns:
        处理后的数据列表
    """
    if data.empty:
        return []
    
    # 确保有日期列
    if 'date' not in data.columns and data.index.name == 'date':
        data = data.reset_index()
    
    # 统一列名映射
    column_mapping = {
        'open': ['open', 'Open', 'OPEN'],
        'high': ['high', 'High', 'HIGH'],
        'low': ['low', 'Low', 'LOW'],
        'close': ['close', 'Close', 'CLOSE', 'last'],
        'volume': ['volume', 'Volume', 'VOLUME', 'vol'],
        'date': ['date', 'Date', 'DATE', 'datetime', 'time']
    }
    
    # 重命名列
    for target_col, possible_cols in column_mapping.items():
        for col in possible_cols:
            if col in data.columns:
                if col != target_col:
                    data = data.rename(columns={col: target_col})
                break
    
    # 确保必要的列存在
    required_cols = ['date', 'open', 'high', 'low', 'close']
    for col in required_cols:
        if col not in data.columns:
            print(f"警告: {source} 数据源缺少 {col} 列")
            return []
    
    # 转换日期格式
    data['date'] = pd.to_datetime(data['date'])
    
    # 转换为字典列表
    result = []
    for _, row in data.iterrows():
        item = {
            'date': row['date'].strftime('%Y-%m-%d'),
            'open': float(row['open']),
            'high': float(row['high']),
            'low': float(row['low']),
            'close': float(row['close']),
        }
        
        # 添加成交量（如果有）
        if 'volume' in data.columns:
            item['volume'] = int(row['volume']) if pd.notna(row['volume']) else 0
        
        result.append(item)
    
    return result


def get_kline_data(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_sources: Optional[List[str]] = None
) -> Dict:
    """
    获取股票K线数据
    
    Args:
        code: 股票代码
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        data_sources: 指定数据源列表，如果为None则使用默认配置
        
    Returns:
        包含K线数据的字典
    """
    # 判断市场类型
    market_type = get_market_type(code)
    
    # 格式化股票代码
    formatted_code = format_stock_code(code)
    
    # 设置默认日期范围
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # 确定使用的数据源
    if data_sources is None:
        data_sources = DATA_SOURCES_CONFIG.get(market_type, [])
    
    last_error = None
    
    # 按优先级尝试各个数据源
    for source in data_sources:
        try:
            result = None
            
            if source == 'yfinance':
                if not is_yfinance_available():
                    print("yfinance不可用，跳过")
                    continue
                
                result = get_kline_data_from_yfinance(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
            elif source == 'akshare_hk':
                if not is_akshare_hk_available():
                    print("akshare_hk不可用，跳过")
                    continue
                
                result = get_kline_data_from_akshare_hk(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
            elif source == 'akshare':
                if not is_akshare_available():
                    print("akshare不可用，跳过")
                    continue
                
                result = get_kline_data_from_akshare(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
            
            elif source == 'eastmoney_hk':
                if not is_eastmoney_hk_available():
                    print("eastmoney_hk不可用，跳过")
                    continue
                
                result = get_kline_data_from_eastmoney_hk(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
            
            elif source == 'eastmoney_cn':
                if not is_eastmoney_cn_available():
                    print("eastmoney_cn不可用，跳过")
                    continue
                
                result = get_kline_data_from_eastmoney_cn(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
            elif source == 'alpha_vantage':
                if not is_alpha_vantage_available():
                    print("alpha_vantage不可用，跳过")
                    continue
                
                api_key = API_KEYS.get('alpha_vantage', '')
                if not api_key:
                    print("alpha_vantage需要API密钥，跳过")
                    continue
                
                result = get_kline_data_from_alpha_vantage(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date,
                    api_key=api_key
                )
                
            elif source == 'tiingo':
                if not is_tiingo_available():
                    print("tiingo不可用，跳过")
                    continue
                
                api_key = API_KEYS.get('tiingo', '')
                print(f"tiingo API密钥: {api_key}")
                if not api_key:
                    print("tiingo需要API密钥，跳过")
                    continue
                
                result = get_kline_data_from_tiingo(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date,
                    api_key=api_key
                )
                
            elif source == 'baostock':
                if not is_baostock_available():
                    print("baostock不可用，跳过")
                    continue
                
                result = get_kline_data_from_baostock(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
            elif source == 'google_finance':
                if not is_google_finance_available():
                    print("google_finance不可用，跳过")
                    continue
                
                result = get_kline_data_from_google_finance(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
            
            # 如果成功获取数据，返回结果
            if result and result.get('data'):
                print(f"{source} 数据源成功获取数据，数据条数: {len(result['data'])}")
                # 确保返回的字典包含source字段
                if 'data_source' in result and 'source' not in result:
                    result['source'] = result['data_source']
                return result
                
        except Exception as e:
            print(f"{source} 数据源失败: {e}")
            last_error = e
            continue
    
    # 如果所有数据源都失败，返回错误信息
    error_msg = f"所有数据源都失败，最后错误: {last_error}" if last_error else "所有数据源都失败"
    print(error_msg)
    
    return {
        "code": code,
        "formatted_code": formatted_code,
        "market": market_type,
        "data_source": "none",
        "data": [],
        "error": error_msg
    }


def set_api_credentials(source: str, api_key: str):
    """
    设置数据源的API密钥
    
    Args:
        source: 数据源名称
        api_key: API密钥
    """
    API_KEYS[source] = api_key
    print(f"已设置 {source} 的API密钥")


def test_kline_service():
    """测试K线数据服务"""
    test_cases = [
        ('TSLA', 'US'),
        ('03690', 'HK'),
        ('600036', 'A'),
    ]
    
    for code, expected_market in test_cases:
        try:
            print(f"\n测试股票代码: {code}")
            result = get_kline_data(code)
            print(f"成功获取数据，市场: {result['market']}, 数据源: {result['data_source']}, 数据条数: {len(result['data'])}")
        except Exception as e:
            print(f"获取失败: {e}")


if __name__ == "__main__":
    test_kline_service()