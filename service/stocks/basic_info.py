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
        secid = f"{market}.{code}"
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f162,f167,f168,f169,f170",
            "fltt": "2",
            "invt": "2",
            "ut": "b2884a393a59ad64002292a3e90d46a5",
            "cb": f"jQuery112406132355515699313_{int(time.time()*1000)}",
            "_": int(time.time()*1000)
        }
        
        headers = {
            'Referer': 'https://quote.eastmoney.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        text = response.text
        
        import re
        import json
        match = re.search(r'jQuery\d+_\d+\((.*)\)', text)
        if not match:
            return None
            
        data = json.loads(match.group(1))
        
        if data.get('rc') != 0 or not data.get('data'):
            return None
            
        stock_info = data['data']
        
        return {
            "code": code,
            "name": stock_info.get('f58') or f"股票{code}",
            "currentPrice": stock_info.get('f43') or 0,
            "change": stock_info.get('f169') or 0,
            "changePercent": stock_info.get('f170') or 0,
            "volume": stock_info.get('f47') or 0,
            "amount": stock_info.get('f48') or 0,
            "marketCap": stock_info.get('f51') or 0,
            "peRatio": stock_info.get('f162') or 0,
            "pbRatio": stock_info.get('f167') or 0,
            "turnoverRate": stock_info.get('f168') or 0,
            "high": stock_info.get('f44') or 0,
            "low": stock_info.get('f45') or 0,
            "open": stock_info.get('f46') or 0,
            "prevClose": stock_info.get('f60') or 0,
            "timestamp": int(time.time()*1000)
        }
    except Exception as e:
        print(f"fetch_stock_basic_data_from_eastmoney error: {e}")
        return None

def fetch_us_stock_basic_data(code: str) -> Optional[Dict[str, Any]]:
    """
    专门为美股获取基本信息
    """
    try:
        markets_to_try = ['105', '106', '107']
        
        for market in markets_to_try:
            secid = f"{market}.{code}"
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": secid,
                "fields": "f8,f9,f20,f23,f43,f44,f45,f46,f47,f48,f57,f58,f60,f107,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f8,f9,f20,f23"
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'http://quote.eastmoney.com/'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if data and data.get('rc') == 0 and data.get('data'):
                stock_data = data['data']
                current_price = stock_data.get('f43') or 0
                previous_close = stock_data.get('f60') or 0
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close else 0
                
                volume_str = stock_data.get('f47')
                volume = int(volume_str) if volume_str and str(volume_str).isdigit() else 0
                
                amount_str = stock_data.get('f48')
                try:
                    amount = float(amount_str) if amount_str else 0
                except ValueError:
                    amount = 0
                    
                return {
                    "code": code,
                    "name": stock_data.get('f58') or f"股票{code}",
                    "currentPrice": current_price or 0,
                    "change": change or 0,
                    "changePercent": change_percent or 0,
                    "volume": volume,
                    "amount": amount,
                    "marketCap": 0,
                    "peRatio": 0,
                    "pbRatio": 0,
                    "turnoverRate": 0,
                    "high": stock_data.get('f44') or 0,
                    "low": stock_data.get('f45') or 0,
                    "open": stock_data.get('f46') or 0,
                    "prevClose": previous_close or 0,
                    "timestamp": int(time.time()*1000)
                }
                
        return None
    except Exception as e:
        print(f"fetch_us_stock_basic_data error: {e}")
        return None

def get_stock_basic_info(code: str) -> Optional[Dict[str, Any]]:
    market_info = get_market_info(code)
    market_type = market_info['type']
    
    if market_type in ['a', 'hk']:
        return fetch_stock_basic_data_from_eastmoney(market_info['market'], code)
    elif market_type == 'us':
        return fetch_us_stock_basic_data(code)
        
    return None
