#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国A股市场 - baostock数据源
{"market":"a", "count":5686,"stocks":[{"code":"000001","name":"1","market":"a","full_code":"000001.SH","industry":"","list_date":""}]}
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta
import os


def get_a_stocks_by_baostock() -> Optional[Dict[str, Any]]:
    """
    使用baostock获取中国A股市场所有股票列表

    Returns:
        包含A股股票列表的字典
    """
    try:
        import baostock as bs

        # 登录Baostock
        lg = bs.login()
        if lg.error_code != '0':
            print(f"[baostock] 登录失败: {lg.error_msg}")
            return None
        # 获取所有股票列表
        # query_all_stock()返回指定日期的所有股票列表
        # 使用当前日期作为查询日期，如果当前日期没有数据，尝试前一个交易日
        # 先尝试不指定日期（或者使用最新可用日期）
        print("[baostock] 尝试不指定日期查询...")
        rs = bs.query_all_stock()
        if rs.error_code == '0':
            data_list = []
            while (rs.error_code == '0') and rs.next():
                data_list.append(rs.get_row_data())
            if len(data_list) > 0:
                print(f"[baostock] 不指定日期查询成功，获取到 {len(data_list)} 条数据")
            else:
                print("[baostock] 不指定日期查询为空，尝试指定日期")
        else:
            data_list = []

        if not data_list:
            # 如果不指定日期没获取到，再尝试日期策略
            print("[baostock] 尝试按日期查询...")
            # 先尝试最近几个月
            test_dates = [
                datetime.now().strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                '2024-12-31',
                '2023-12-31'
            ]
            
            for test_date in test_dates:
                try:
                    print(f"[baostock] 尝试日期: {test_date}")
                    rs = bs.query_all_stock(test_date)
                    if rs.error_code == '0':
                        data_list = []
                        while (rs.error_code == '0') and rs.next():
                            data_list.append(rs.get_row_data())
                        if data_list:
                            print(f"[baostock] 成功使用 {test_date} 获取到 {len(data_list)} 条数据")
                            break
                except Exception as e:
                    print(f"[baostock] 日期 {test_date} 查询异常: {e}")
                    continue

        if not data_list:
            print("[baostock] 所有日期均无数据")
            bs.logout()
            return None

        # 登出
        bs.logout()

        # 转换为DataFrame
        # baostock返回列顺序是 [code, tradeStatus, code_name]
        df = pd.DataFrame(data_list, columns=['code', 'tradeStatus', 'code_name'])

        # 过滤出A股股票（代码以sh.或sz.开头）
        a_shares_df = df[df['code'].str.startswith(('sh.', 'sz.'))]

        if a_shares_df.empty:
            print("[baostock] 未找到A股股票")
            return None

        # 转换为列表格式
        stocks = []
        for _, row in a_shares_df.iterrows():
            # 解析股票代码
            bs_code = row['code']  # 格式如: sh.600000
            code_name = row['code_name']

            # 提取纯数字代码
            if bs_code.startswith('sh.'):
                code = bs_code[3:]  # 600000
                market = 'sh'
                full_code = f"{code}.SH"
            elif bs_code.startswith('sz.'):
                code = bs_code[3:]  # 000001
                market = 'sz'
                full_code = f"{code}.SZ"
            else:
                continue

            stock = {
                'code': code,
                'name': code_name,
                'market': 'a',
                'full_code': full_code,
                'industry': '',  # baostock需要额外查询获取行业信息
                'list_date': ''  # baostock需要额外查询获取上市日期
            }
            stocks.append(stock)

        result = {
            'market': 'a',
            'count': len(stocks),
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'baostock'
        }

        print(f"[baostock] 成功获取 {len(stocks)} 只A股股票")
        return result

    except ImportError:
        print("[baostock] baostock库未安装，请运行: pip install baostock")
        return None
    except Exception as e:
        print(f"[baostock] 获取A股股票列表时发生错误: {e}")
        # 确保登出
        try:
            import baostock as bs
            bs.logout()
        except:
            pass
        return None


def is_baostock_available() -> bool:
    """检查baostock是否可用"""
    try:
        import baostock as bs
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    # 测试代码
    print(f"baostock可用: {is_baostock_available()}")

    if is_baostock_available():
        result = get_a_stocks_by_baostock()
        if result:
            print(f"测试成功: 获取到 {result['count']} 只A股股票")
            print(f"数据源: {result['source']}")
            print(f"第一只股票: {result['stocks'][0]}")
        else:
            print("测试失败: 获取A股股票列表失败")
    else:
        print("请安装baostock库: pip install baostock")
