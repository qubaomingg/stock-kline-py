"""
股票K线数据获取服务
根据openBB.md中的免费数据源信息，按市场类型选择数据源
重构版本：使用独立的数据源模块
"""
import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime, timedelta
import time

# 设置日志
logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 导入数据源模块
from service.kline.us.yfinance import get_kline_data_from_yfinance, is_yfinance_available
from service.kline.a.akshare import get_kline_data_from_akshare, is_akshare_available
from service.kline.hk.akshare_hk import get_kline_data_from_akshare_hk, is_akshare_hk_available
from service.kline.us.alpha_vantage import get_kline_data_from_alpha_vantage, is_alpha_vantage_available
from service.kline.us.tiingo import get_kline_data_from_tiingo, is_tiingo_available
from service.kline.us.finnhub import get_kline_data_from_finnhub, is_finnhub_available
from service.kline.a.baostock import get_kline_data_from_baostock, is_baostock_available
from service.kline.hk.eastmoney_hk import get_kline_data_from_eastmoney_hk, is_eastmoney_hk_available
from service.kline.a.eastmoney_a import get_kline_data_from_eastmoney_a, is_eastmoney_a_available
from service.kline.a.sina_a import get_kline_data_from_sina, is_sina_available

# 导入缓存装饰器
from service.cache.decorators import cache_kline_data

# 导入工具函数
# 使用绝对导入避免与本地utils.py冲突
try:
    from utils_stock.stock import get_market_type, format_stock_code
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
    'a': ['sina', 'eastmoney_a', 'akshare', 'baostock'],
    'hk': ['eastmoney_hk', 'akshare_hk'],
    'us': ['yfinance', 'alpha_vantage', 'tiingo', 'finnhub']
}

# API密钥配置
API_KEYS = {
    'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
    'tiingo': os.getenv('TIINGO_API_KEY', ''),
    'finnhub': os.getenv('FINNHUB_API_KEY', ''),
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
            logger.debug(f"数据源 {source} 缺少 {col} 列")
            return []

    # 转换日期格式
    data['date'] = pd.to_datetime(data['date'])

    # 按日期升序排序
    data = data.sort_values('date', ascending=True)

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


@cache_kline_data()
def get_kline_data(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_sources: Optional[List[str]] = None,
    force: bool = False
) -> Dict:
    """
    获取股票K线数据

    Args:
        code: 股票代码
        start_date: 开始日期，格式：YYYY-MM-DD
        end_date: 结束日期，格式：YYYY-MM-DD
        data_sources: 指定数据源优先级（None 表示使用默认配置）
        force: 强制跳过缓存，直接从数据源获取（True=强制刷新）

    Returns:
        包含K线数据的字典
    """
    # 为了兼容带后缀的代码，在判断市场类型前先提取无后缀代码
    clean_code = code.split('.')[0] if '.' in code else code
    market_type = get_market_type(clean_code)

    logger.info(f"[{code.upper()}] 市场类型: {market_type.upper()}, 请求日期范围: {start_date or 'auto'} ~ {end_date or 'auto'}")

    # 格式化股票代码
    formatted_code = format_stock_code(code)

    # 设置默认日期范围
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

    # 确定使用的数据源
    if data_sources is None:
        data_sources = DATA_SOURCES_CONFIG.get(market_type, [])

    last_error = None
    log_prefix = f"[{code.upper()}] [market={market_type}]"
    consecutive_network_errors = 0  # 连续网络错误计数
    total_start_time = time.time()
    MAX_TOTAL_TIME = 30  # 单只股票最大总耗时（秒），超过则停止尝试

    # 按优先级尝试各个数据源
    for idx, source in enumerate(data_sources, 1):
        # 检查是否超过总时间限制
        elapsed_total = time.time() - total_start_time
        if elapsed_total > MAX_TOTAL_TIME:
            logger.warning(
                f"{log_prefix} ⏱️ 已耗时 {elapsed_total:.1f}s，超过 {MAX_TOTAL_TIME}s 限制，停止尝试剩余数据源"
            )
            break

        # 检查连续网络错误短路
        if consecutive_network_errors >= 2:
            logger.warning(
                f"{log_prefix} 🔌 连续 {consecutive_network_errors} 次网络错误，推断当前网络无法访问该市场API，跳过剩余 {len(data_sources) - idx + 1} 个数据源"
            )
            break

        try:
            result = None
            elapsed = 0.0
            loop_t0 = time.time()
            logger.info(f"{log_prefix} 🔄 开始尝试数据源 {source} ({idx}/{len(data_sources)})...")

            if source == 'yfinance':
                if not is_yfinance_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_yfinance(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'akshare_hk':
                if not is_akshare_hk_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_akshare_hk(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'akshare':
                if not is_akshare_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_akshare(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'eastmoney_hk':
                if not is_eastmoney_hk_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_eastmoney_hk(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'sina':
                if not is_sina_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 网络不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_sina(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'eastmoney_a':
                if not is_eastmoney_a_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_eastmoney_a(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'alpha_vantage':
                if not is_alpha_vantage_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                api_key = API_KEYS.get('alpha_vantage', '')
                if not api_key:
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 需要API密钥，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_alpha_vantage(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date,
                    api_key=api_key
                )
                elapsed = time.time() - t0

            elif source == 'tiingo':
                if not is_tiingo_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                api_key = API_KEYS.get('tiingo', '')
                if not api_key:
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 需要API密钥，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_tiingo(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date,
                    api_key=api_key
                )
                elapsed = time.time() - t0

            elif source == 'finnhub':
                if not is_finnhub_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                api_key = API_KEYS.get('finnhub', '')
                if not api_key:
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 需要API密钥，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_finnhub(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date,
                    api_key=api_key
                )
                elapsed = time.time() - t0

            elif source == 'baostock':
                if not is_baostock_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_baostock(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            elif source == 'google_finance':
                if not is_google_finance_available():
                    logger.info(f"{log_prefix} ⏭️ 数据源 {source} ({idx}/{len(data_sources)}) 不可用，跳过")
                    continue

                t0 = time.time()
                result = get_kline_data_from_google_finance(
                    code=code,
                    market_type=market_type,
                    formatted_code=formatted_code,
                    start_date=start_date,
                    end_date=end_date
                )
                elapsed = time.time() - t0

            else:
                logger.warning(f"{log_prefix} 未知数据源: {source} ({idx}/{len(data_sources)}), 跳过")
                continue

            # 如果成功获取数据，返回结果
            if result and result.get('data'):
                data_count = len(result['data'])
                logger.info(f"{log_prefix} ✅ 数据源 {source} ({idx}/{len(data_sources)}) 获取成功: {data_count} 条数据, 耗时 {elapsed:.1f}s")
                # 确保返回的字典包含source字段
                if 'data_source' in result and 'source' not in result:
                    result['source'] = result['data_source']

                # 按照日期从远到近排序
                result['data'].sort(key=lambda x: x['date'])

                return result
            elif result is None:
                # 数据源函数返回None（网络错误、API不可用等）
                # 将其视为网络错误，用于短路判断
                consecutive_network_errors += 1
                logger.warning(
                    f"{log_prefix} ❌ 数据源 {source} ({idx}/{len(data_sources)}) 失败（返回None，已在上方记录详细错误）, "
                    f"耗时 {elapsed:.1f}s（连续网络错误 {consecutive_network_errors}/2）"
                )
            else:
                # 返回了字典但没有数据（可能是数据处理失败）
                logger.warning(f"{log_prefix} ⚠️ 数据源 {source} ({idx}/{len(data_sources)}) 返回空数据, 耗时 {elapsed:.1f}s")

        except Exception as e:
            elapsed = time.time() - loop_t0
            error_str = str(e).lower()
            # 检测是否为网络相关错误（ConnectionError, timeout, RemoteDisconnected 等）
            is_network_error = any(
                keyword in error_str or keyword in type(e).__name__.lower()
                for keyword in ['connection', 'timeout', 'network', 'remote', 'socket', 'timed out', 'disconnect', 'pipe', 'dns', 'resolve', 'refused', 'unreachable']
            )

            if is_network_error:
                consecutive_network_errors += 1
                logger.warning(
                    f"{log_prefix} ❌ 数据源 {source} ({idx}/{len(data_sources)}) 网络失败 ({elapsed:.1f}s): "
                    f"{type(e).__name__}（连续网络错误 {consecutive_network_errors}/2）"
                )
            else:
                # 非网络错误（数据格式问题等），不影响短路
                logger.warning(
                    f"{log_prefix} ❌ 数据源 {source} ({idx}/{len(data_sources)}) 异常 ({elapsed:.1f}s): {type(e).__name__}: {e}"
                )
            last_error = e
            continue

    # 如果所有数据源都失败，返回错误信息
    error_msg = f"所有数据源都失败，最后错误: {last_error}" if last_error else "所有数据源都失败"
    logger.error(f"{log_prefix} ❌ {error_msg}. 已尝试的数据源: {data_sources}")

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
    logger.info(f"已设置 {source} 的API密钥")


def test_kline_service():
    """测试K线数据服务"""
    # 测试用例
    test_cases = [
        ('00700', 'hk'),  # 腾讯控股 (不带后缀)
        ('00700.HK', 'hk'),  # 腾讯控股 (带后缀)
        ('600036', 'a'),  # 招商银行 (不带后缀)
        ('600036.SH', 'a'),  # 招商银行 (带后缀)
        ('AAPL', 'us'),   # 苹果公司
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
