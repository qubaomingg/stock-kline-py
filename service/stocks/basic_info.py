import requests
import time
from typing import Dict, Optional, Any

def get_market_info(code: str) -> Dict[str, str]:
    """
    根据股票代码获取市场信息
    返回格式: {'market': '市场代码', 'type': 'a/hk/us'}
    """
    clean_code = code.split('.')[0] if '.' in code else code
    
    # A股判断
    if len(clean_code) == 6 and clean_code.isdigit():
        if clean_code.startswith(('60', '68', '688', '900')):
            return {'market': '1', 'type': 'a'}
        if clean_code.startswith(('00', '30', '300', '301', '200')):
            return {'market': '0', 'type': 'a'}
        if clean_code.startswith('8'):
            return {'market': '0', 'type': 'a'}
        return {'market': '1', 'type': 'a'}
        
    # 港股判断
    if len(clean_code) == 5 and clean_code.isdigit():
        return {'market': '116', 'type': 'hk'}
        
    # 默认为美股
    return {'market': '105', 'type': 'us'}

def get_us_market(code: str) -> str:
    # 简单实现，由于没有 njMarkets 和 mjMarkets 列表，我们先默认尝试 105，如果失败再试 106, 107
    return '105'

def fetch_stock_basic_data_from_eastmoney(market: str, code: str) -> Optional[Dict[str, Any]]:
    """
    从东方财富API获取A股/港股基本信息
    """
    try:
        markets_to_try = ['116', '128', '131'] if market == '116' else ['1', '0'] # 兼容 A股/港股
        try:
            import akshare as ak
            if market == 'a':
                a_spot = ak.stock_zh_a_spot_em()
                target = a_spot[a_spot['代码'] == code]
                if not target.empty:
                    record = target.iloc[0]
                    current_price = float(record.get('最新价', 0) or 0)
                    change = float(record.get('涨跌额', 0) or 0)
                    prev_close = current_price - change
                    return {
                        "code": code,
                        "name": str(record.get('名称', '')),
                        "currentPrice": current_price,
                        "change": change,
                        "changePercent": float(record.get('涨跌幅', 0) or 0),
                        "volume": int(record.get('成交量', 0) or 0),
                        "amount": float(record.get('成交额', 0) or 0),
                        "marketCap": float(record.get('总市值', 0) or 0),
                        "peRatio": float(record.get('市盈率-动态', 0) or 0),
                        "pbRatio": float(record.get('市净率', 0) or 0),
                        "turnoverRate": float(record.get('换手率', 0) or 0),
                        "high": float(record.get('最高', 0) or 0),
                        "low": float(record.get('最低', 0) or 0),
                        "open": float(record.get('今开', 0) or 0),
                        "prevClose": float(record.get('昨收', 0) or prev_close),
                        "timestamp": int(time.time()*1000)
                    }
            elif market == 'hk':
                hk_spot = ak.stock_hk_spot_em()
                target = hk_spot[hk_spot['代码'] == code]
                if not target.empty:
                    record = target.iloc[0]
                    current_price = float(record.get('最新价', 0) or 0)
                    change = float(record.get('涨跌额', 0) or 0)
                    prev_close = current_price - change
                    return {
                        "code": code,
                        "name": str(record.get('名称', '')),
                        "currentPrice": current_price,
                        "change": change,
                        "changePercent": float(record.get('涨跌幅', 0) or 0),
                        "volume": int(record.get('成交量', 0) or 0),
                        "amount": float(record.get('成交额', 0) or 0),
                        "marketCap": 0,
                        "peRatio": 0,
                        "pbRatio": 0,
                        "turnoverRate": 0,
                        "high": float(record.get('最高价', 0) or 0),
                        "low": float(record.get('最低价', 0) or 0),
                        "open": float(record.get('开盘价', 0) or 0),
                        "prevClose": prev_close,
                        "timestamp": int(time.time()*1000)
                    }
        except Exception as e:
            print(f"akshare fetch_stock_basic_data error: {e}")
            
        nodes = ["82.152.17.133", "push2", "72.push2", "84.push2", "18.push2"]
        
        for node in nodes:
            for m in markets_to_try:
                try:
                    secid = f"{m}.{code}"
                    url = f"http://{node}.eastmoney.com/api/qt/stock/get"
                    if node.replace('.','').isdigit():
                        url = f"http://{node}/api/qt/stock/get"
                    params = {
                        "secid": secid,
                        "fields": "f8,f9,f20,f23,f43,f44,f45,f46,f47,f48,f57,f58,f59,f60,f107,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f8,f9,f20,f23"
                    }
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'http://quote.eastmoney.com/'
                    }
                    if node.replace('.','').isdigit():
                        headers['Host'] = "push2.eastmoney.com"
                        
                    response = requests.get(url, params=params, headers=headers, timeout=5)
                    data = response.json()
                    
                    if data and data.get('rc') == 0 and data.get('data'):
                        stock_data = data['data']
                        
                        current_price = stock_data.get('f43') or 0
                        previous_close = stock_data.get('f60') or 0
                        
                        if current_price == "-":
                            current_price = 0
                        if previous_close == "-":
                            previous_close = 0
                            
                        change = stock_data.get('f169') or (current_price - previous_close if isinstance(current_price, (int, float)) and isinstance(previous_close, (int, float)) else 0)
                        change_percent = stock_data.get('f170') or ((change / previous_close * 100) if previous_close and isinstance(previous_close, (int, float)) else 0)
                        
                        volume_str = stock_data.get('f47')
                        volume = int(volume_str) if volume_str and str(volume_str).isdigit() else 0
                        
                        amount_str = stock_data.get('f48')
                        try:
                            amount = float(amount_str) if amount_str else 0
                        except ValueError:
                            amount = 0
                            
                        # 判断如果获取到了真实价格数据，就直接返回
                        if current_price and current_price != "-":
                            
                            # 东财接口经常对不同市场的数据做扩大处理 (比如把 12.34 扩大为 1234 或者 12340)
                            # 根据 f59 (价格小数点位数) 来进行转换
                            decimal_places = stock_data.get('f59', 0)
                            if decimal_places > 0:
                                divisor = 10 ** decimal_places
                                current_price = current_price / divisor
                                previous_close = previous_close / divisor
                                change = change / divisor
                                
                            return {
                                "code": code,
                                "name": stock_data.get('f58') or f"股票{code}",
                                "currentPrice": current_price,
                                "change": change,
                                "changePercent": change_percent,
                                "volume": volume,
                                "amount": amount,
                                "marketCap": stock_data.get('f116') or stock_data.get('f51') or 0,
                                "peRatio": stock_data.get('f162') or 0,
                                "pbRatio": stock_data.get('f167') or 0,
                                "turnoverRate": stock_data.get('f168') or 0,
                                "high": (stock_data.get('f44') or 0) / (10 ** decimal_places) if decimal_places > 0 and stock_data.get('f44') else (stock_data.get('f44') or 0),
                                "low": (stock_data.get('f45') or 0) / (10 ** decimal_places) if decimal_places > 0 and stock_data.get('f45') else (stock_data.get('f45') or 0),
                                "open": (stock_data.get('f46') or 0) / (10 ** decimal_places) if decimal_places > 0 and stock_data.get('f46') else (stock_data.get('f46') or 0),
                                "prevClose": previous_close or 0,
                                "timestamp": int(time.time()*1000)
                            }
                except Exception as e:
                    print(f"eastmoney fetch_stock_basic_data error: {e}")
                    continue
                
        return None
    except Exception as e:
        print(f"fetch_stock_basic_data_from_eastmoney error: {e}")
        return None

def fetch_us_stock_basic_data(code: str) -> Optional[Dict[str, Any]]:
    """
    获取美股基础信息
    :param code: 股票代码
    :return: 股票基础信息
    """
    try:
        markets_to_try = ['105', '106', '107']
        
        # 对于美股，优先使用 akshare 作为兜底行情数据源
        import akshare as ak
        try:
            us_spot = ak.stock_us_spot_em()
            # 从 us_spot 中过滤
            target = us_spot[us_spot['代码'] == str(code)]
            if not target.empty:
                record = target.iloc[0]
                current_price = float(record.get('最新价', 0) or 0)
                change = float(record.get('涨跌额', 0) or 0)
                prev_close = current_price - change
                return {
                    "code": code,
                    "name": str(record.get('名称', '')),
                    "currentPrice": current_price,
                    "change": change,
                    "changePercent": float(record.get('涨跌幅', 0) or 0),
                    "volume": int(record.get('成交量', 0) or 0),
                    "amount": float(record.get('成交额', 0) or 0),
                    "marketCap": float(record.get('总市值', 0) or 0),
                    "peRatio": float(record.get('市盈率', 0) or 0),
                    "pbRatio": 0,
                    "turnoverRate": 0,
                    "high": float(record.get('最高价', 0) or 0),
                    "low": float(record.get('最低价', 0) or 0),
                    "open": float(record.get('开盘价', 0) or 0),
                    "prevClose": prev_close,
                    "timestamp": int(time.time()*1000)
                }
        except Exception as e:
            print(f"akshare fetch_us_stock_basic_data error: {e}")
            
        nodes = ["82.152.17.133", "push2", "72.push2", "84.push2", "18.push2"]
        
        for node in nodes:
            for m in markets_to_try:
                try:
                    secid = f"{m}.{code}"
                    url = f"http://{node}.eastmoney.com/api/qt/stock/get"
                    if node.replace('.','').isdigit():
                        url = f"http://{node}/api/qt/stock/get"
                    params = {
                        "secid": secid,
                        "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116,f162,f167,f168,f169,f170",
                        "fltt": "2",
                        "invt": "2",
                        "ut": "b2884a393a59ad64002292a3e90d46a5",
                        "cb": f"jQuery112406132355515699313_{int(time.time()*1000)}",
                        "_": int(time.time()*1000)
                    }
                    headers = {
                        'Referer': 'http://quote.eastmoney.com/',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    if node.replace('.','').isdigit():
                        headers['Host'] = "push2.eastmoney.com"
                        
                    response = requests.get(url, params=params, headers=headers, timeout=5)
                    text = response.text
                    
                    import re
                    import json
                    match = re.search(r'jQuery\d+_\d+\((.*)\)', text)
                    if not match:
                        continue
                        
                    data = json.loads(match.group(1))
                    
                    if data.get('rc') != 0 or not data.get('data'):
                        continue
                        
                    stock_data = data['data']
                    
                    current_price = stock_data.get('f43') or 0
                    previous_close = stock_data.get('f60') or 0
                    
                    if current_price == "-":
                        current_price = 0
                    if previous_close == "-":
                        previous_close = 0
                        
                    change = stock_data.get('f169') or (current_price - previous_close if isinstance(current_price, (int, float)) and isinstance(previous_close, (int, float)) else 0)
                    change_percent = stock_data.get('f170') or ((change / previous_close * 100) if previous_close and isinstance(previous_close, (int, float)) else 0)
                    
                    volume_str = stock_data.get('f47')
                    volume = int(volume_str) if volume_str and str(volume_str).isdigit() else 0
                    
                    amount_str = stock_data.get('f48')
                    try:
                        amount = float(amount_str) if amount_str else 0
                    except ValueError:
                        amount = 0
                        
                    # 判断如果获取到了真实价格数据，就直接返回
                    if current_price and current_price != "-":
                        return {
                            "code": code,
                            "name": stock_data.get('f58') or f"股票{code}",
                            "currentPrice": current_price,
                            "change": change,
                            "changePercent": change_percent,
                            "volume": volume,
                            "amount": amount,
                            "marketCap": stock_data.get('f116') or stock_data.get('f51') or 0,
                            "peRatio": stock_data.get('f162') or 0,
                            "pbRatio": stock_data.get('f167') or 0,
                            "turnoverRate": stock_data.get('f168') or 0,
                            "high": stock_data.get('f44') or 0,
                            "low": stock_data.get('f45') or 0,
                            "open": stock_data.get('f46') or 0,
                            "prevClose": previous_close or 0,
                            "timestamp": int(time.time()*1000)
                        }
                except Exception as e:
                    print(f"eastmoney fetch_us_stock_basic_data error: {e}")
                    continue
                
        return None
    except Exception as e:
        print(f"fetch_us_stock_basic_data error: {e}")
        return None

def get_stock_basic_info(code: str) -> Optional[Dict[str, Any]]:
    market_info = get_market_info(code)
    market_type = market_info['type']
    
    basic_info = None
    if market_type in ['a', 'hk']:
        basic_info = fetch_stock_basic_data_from_eastmoney(market_info['market'], code)
    elif market_type == 'us':
        basic_info = fetch_us_stock_basic_data(code)
        
    # 如果 basic_info 获取失败，尝试构建一个默认结构，以免 profile_data 合并时出错
    if not basic_info:
        basic_info = {
            "code": code,
            "name": "",
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
        
    return basic_info
