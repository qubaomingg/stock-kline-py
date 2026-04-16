import logging

logger = logging.getLogger(__name__)

def _get_from_akshare(code: str) -> dict:
    import akshare as ak
    df = ak.stock_profile_cninfo(symbol=code)
    if not df.empty:
        record = df.iloc[0].to_dict()
        return {
            "full_name": str(record.get("公司名称", "")),
            "industry": str(record.get("所属行业", "")),
            "listing_date": str(record.get("上市日期", "")),
            "main_business": str(record.get("主营业务", ""))
        }
    return {}

def _get_from_eastmoney(code: str) -> dict:
    # 从东方财富获取 A 股基本面数据
    # 东财的F10接口能获取到公司资料
    import requests
    try:
        # A股：上交所SH开头，深交所SZ开头
        prefix = "SH" if code.startswith(('60', '68')) else "SZ"
        url = f"https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/CompanySurveyAjax?code={prefix}{code}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Referer': f'https://emweb.securities.eastmoney.com/PC_HSF10/CompanySurvey/Index?type=web&code={prefix}{code}'
        }
        
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data and data.get("jbzl"):
                jbzl = data["jbzl"]
                # 接口返回的结构其实是一个对象，直接取字段
                return {
                    "full_name": str(jbzl.get("gsmc", "")),
                    "industry": str(jbzl.get("sszjhhy", "")),
                    "listing_date": str(jbzl.get("agssrq", "")[:10]) if jbzl.get("agssrq") else "",
                    "main_business": str(jbzl.get("zyyw", ""))
                }
    except Exception as e:
        logger.debug(f"Eastmoney profile fetch error: {e}")
        
    return {}

def _get_from_baostock(code: str) -> dict:
    import baostock as bs
    # baostock 的代码格式需要加前缀：sh.600519 或 sz.000001
    prefix = "sh." if code.startswith(('60', '68')) else "sz."
    full_code = f"{prefix}{code}"
    
    bs.login()
    try:
        rs = bs.query_stock_basic(code=full_code)
        df = rs.get_data()
        if not df.empty:
            record = df.iloc[0]
            return {
                "full_name": str(record.get("code_name", "")),
                "listing_date": str(record.get("ipoDate", ""))
                # baostock 不提供 industry 和 main_business，能取到什么算什么
            }
    finally:
        bs.logout()
        
    return {}

def get_a_baseinfo(code: str) -> dict:
    """获取 A股 基本信息，支持多渠道 fallback"""
    data = {}
    
    channels = [
        _get_from_akshare,
        _get_from_eastmoney,
        _get_from_baostock,
    ]
    
    for channel in channels:
        try:
            res = channel(code)
            if res and res.get("full_name"):
                return res
        except Exception as e:
            logger.warning(f"A股档案获取失败({channel.__name__}): {e}")
            continue
            
    return data
