import logging

logger = logging.getLogger(__name__)

def _get_from_akshare(code: str) -> dict:
    import akshare as ak
    hk_code = code.zfill(5)
    df = ak.stock_hk_company_profile_em(symbol=hk_code)
    if not df.empty:
        record = df.iloc[0].to_dict()
        return {
            "full_name": str(record.get("公司名称", "")),
            "industry": str(record.get("所属行业", "")),
            "main_business": str(record.get("公司介绍", ""))
        }
    return {}

def _get_from_futu(code: str) -> dict:
    # futu/富途 API 需要安装 futu-api 并本地启动 FutuOpenD
    # 由于环境未准备，暂时使用 yfinance 兜底获取港股数据 (需要 .HK 后缀)
    import yfinance as yf
    try:
        # 港股在 yfinance 里的后缀通常是 4位数字.HK
        clean_code = code.zfill(4)[-4:] if code.isdigit() else code
        t = yf.Ticker(f"{clean_code}.HK")
        info = t.info
        
        # yfinance 对于港股的返回字段可能只有 shortName 
        name = info.get("longName") or info.get("shortName") or ""
        if name:
            return {
                "full_name": name,
                "industry": info.get("industry", ""),
                "main_business": info.get("longBusinessSummary", "")
            }
    except Exception as e:
        logger.debug(f"Futu fallback (yfinance) fetch error: {e}")
    return {}

def get_hk_baseinfo(code: str) -> dict:
    """获取 港股 基本信息，支持多渠道 fallback"""
    data = {}
    
    channels = [
        _get_from_akshare,
        _get_from_futu,
    ]
    
    for channel in channels:
        try:
            res = channel(code)
            if res and res.get("full_name"):
                return res
        except Exception as e:
            logger.warning(f"港股档案获取失败({channel.__name__}): {e}")
            continue
            
    return data
