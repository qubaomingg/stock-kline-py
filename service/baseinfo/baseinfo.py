import logging
from typing import Dict, Any, Optional

from utils_stock.stock import get_market_type
from service.stocks.basic_info import get_stock_basic_info

from service.baseinfo.a.a_baseinfo import get_a_baseinfo
from service.baseinfo.hk.hk_baseinfo import get_hk_baseinfo
from service.baseinfo.us.us_baseinfo import get_us_baseinfo

logger = logging.getLogger(__name__)

def get_stock_baseinfo(code: str) -> Optional[Dict[str, Any]]:
    """
    获取股票基本信息(包含静态档案与实时行情)，支持 A股、港股、美股。
    包含: 公司全称、行业、上市时间、主营业务、当前价格、涨跌幅、市值等。
    """
    # 提取无后缀代码进行判断，以便兼容带后缀的输入
    clean_code = code.split('.')[0] if '.' in code else code
    market_type = get_market_type(clean_code)  # 'a', 'hk', 'us'

    profile_data = {
        "code": code,
        "market": market_type.lower(),
        "name": "",
        "full_name": "",
        "industry": "",
        "listing_date": "",
        "main_business": "",
        "currency": "CNY" if market_type == 'a' else ("HKD" if market_type == 'hk' else "USD"),
        "currentPrice": 0,
        "change": 0,
        "changePercent": 0,
        "volume": 0,
        "amount": 0,
        "marketCap": 0,
        "peRatio": 0,
        "pbRatio": 0,
        "turnoverRate": 0,
        "high": 0,
        "low": 0,
        "open": 0,
        "prevClose": 0
    }

    # 先获取行情基本信息，作为合并的基础
    basic_info = get_stock_basic_info(code)
    if basic_info:
        for key, value in basic_info.items():
            # 避免覆盖 code 和 market
            if key not in ["code", "market"]:
                profile_data[key] = value

    # 根据市场类型分发到不同渠道
    static_data = {}
    if market_type == 'a':
        static_data = get_a_baseinfo(clean_code)
    elif market_type == 'hk':
        static_data = get_hk_baseinfo(clean_code)
    else:
        static_data = get_us_baseinfo(clean_code)
        
    # 合并静态档案数据
    if static_data:
        for k, v in static_data.items():
            if v:  # 只有有效值才覆盖
                profile_data[k] = v

    # 如果核心数据获取失败，确保 full_name 有一个默认值 (basic_info 中的 name)
    if not profile_data["full_name"]:
        if basic_info and "name" in basic_info:
            profile_data["full_name"] = basic_info.get("name", "")

    # 确保 name 字段有值
    if not profile_data["name"]:
        profile_data["name"] = profile_data["full_name"]

    return profile_data
