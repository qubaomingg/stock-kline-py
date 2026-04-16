import logging
import os
import requests

logger = logging.getLogger(__name__)

def _get_from_finnhub(code: str) -> dict:
    finnhub_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_key:
        url = f"https://finnhub.io/api/v1/stock/profile2?symbol={code}&token={finnhub_key}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and data.get("name"):
                return {
                    "full_name": data.get("name", ""),
                    "industry": data.get("finnhubIndustry", ""),
                    "listing_date": data.get("ipo", "")
                }
    return {}

def _get_from_yfinance(code: str) -> dict:
    import yfinance as yf
    t = yf.Ticker(code)
    info = t.info
    if info and "longName" in info:
        return {
            "full_name": info.get("longName", ""),
            "industry": info.get("industry", ""),
            "main_business": info.get("longBusinessSummary", "")
        }
    return {}

def get_us_baseinfo(code: str) -> dict:
    """获取 美股 基本信息，支持多渠道 fallback 和补充合并"""
    data = {}
    
    channels = [
        _get_from_finnhub,
        _get_from_yfinance,
    ]
    
    for channel in channels:
        try:
            res = channel(code)
            if res:
                # 合并数据
                for k, v in res.items():
                    if v and not data.get(k):
                        data[k] = v
                
                # 如果已经同时拿到了名字和主营业务，就不再请求其他渠道了
                if data.get("full_name") and data.get("main_business"):
                    break
        except Exception as e:
            logger.warning(f"美股档案获取失败({channel.__name__}): {e}")
            continue
            
    return data
