"""
股票市场代码判断工具
"""

def get_market_type(code: str) -> str:
    """
    根据股票代码判断市场类型
    
    规则:
    - 6位纯数字: A股
    - 5位纯数字: 港股
    - 其他: 美股
    
    Args:
        code: 股票代码
        
    Returns:
        str: 市场类型 ('A', 'HK', 'US')
    """
    if not code:
        return 'US'
    
    # 移除可能的交易所后缀
    clean_code = code
    if '.' in code:
        clean_code = code.split('.')[0]
    
    # 判断市场类型
    if clean_code.isdigit():
        if len(clean_code) == 6:
            return 'A'
        elif len(clean_code) == 5:
            return 'HK'
    
    return 'US'


def format_stock_code(code: str) -> str:
    """
    根据市场类型格式化股票代码
    
    Args:
        code: 原始股票代码
        
    Returns:
        str: 格式化后的股票代码
    """
    market_type = get_market_type(code)
    
    if market_type == 'HK':
        # 港股添加.HK后缀
        clean_code = code.split('.')[0] if '.' in code else code
        return f"{clean_code}.HK"
    elif market_type == 'A':
        # A股代码保持不变
        clean_code = code.split('.')[0] if '.' in code else code
        return clean_code
    else:
        # 美股代码保持不变
        return code
