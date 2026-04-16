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
        str: 市场类型 ('a', 'hk', 'us')
    """
    if not code:
        return 'us'

    # A股市场判断 (6位数字)
    if len(code) == 6 and code.isdigit():
        return 'a'

    # 港股市场判断 (5位数字)
    if len(code) == 5 and code.isdigit():
        return 'hk'

    # 默认美股
    return 'us'


def format_stock_code(code: str) -> str:
    """
    根据市场类型格式化股票代码

    Args:
        code: 原始股票代码

    Returns:
        str: 格式化后的股票代码
    """
    # 提取无后缀代码进行判断，以便兼容带后缀的输入
    clean_code_for_check = code.split('.')[0] if '.' in code else code
    market_type = get_market_type(clean_code_for_check)

    if market_type == 'hk':
        # 港股添加.HK后缀
        clean_code = code.split('.')[0] if '.' in code else code
        return f"{clean_code}.HK"
    elif market_type == 'a':
        # A股代码保持不变
        clean_code = code.split('.')[0] if '.' in code else code
        return clean_code
    else:
        # 美股代码保持不变
        return code
