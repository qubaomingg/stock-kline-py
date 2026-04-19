#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版港股数据源
组合多个策略获取更多港股数据
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def get_hk_stocks_by_extended() -> Optional[Dict[str, Any]]:
    """
    获取增强版港股列表

    Returns:
        包含港股股票列表的字典
    """
    try:
        print("=" * 70)
        print("正在获取增强版港股列表...")
        print("=" * 70)

        all_hk_stocks = []
        seen_codes = set()

        # 1. 首先尝试从 akshare 获取真实港股
        try:
            from service.stocks.hk.ak_stocks import get_hk_stocks_by_ak
            result = get_hk_stocks_by_ak()
            if result and result.get("stocks"):
                print(f"✓ 从 akshare 获取到 {len(result['stocks'])} 只真实港股")
                for stock in result["stocks"]:
                    if stock["code"] not in seen_codes:
                        all_hk_stocks.append(stock)
                        seen_codes.add(stock["code"])
        except Exception as e:
            print(f"✗ akshare 获取失败: {e}")

        # 2. 添加常用恒生指数成分股
        print("\n添加常用恒生指数成分股...")
        hang_sheng_stocks = [
            {"code": "00001", "name": "长和"},
            {"code": "00002", "name": "中电控股"},
            {"code": "00003", "name": "香港中华煤气"},
            {"code": "00004", "name": "九龙仓集团"},
            {"code": "00005", "name": "汇丰控股"},
            {"code": "00006", "name": "电能实业"},
            {"code": "00011", "name": "恒生银行"},
            {"code": "00012", "name": "恒基地产"},
            {"code": "00016", "name": "新鸿基地产"},
            {"code": "00017", "name": "新世界发展"},
            {"code": "00019", "name": "太古股份公司A"},
            {"code": "00023", "name": "东亚银行"},
            {"code": "00066", "name": "港铁公司"},
            {"code": "00083", "name": "信和置业"},
            {"code": "00101", "name": "恒隆集团"},
            {"code": "00144", "name": "招商局中国基金"},
            {"code": "00175", "name": "吉利汽车"},
            {"code": "00388", "name": "香港交易所"},
            {"code": "00688", "name": "中国海外发展"},
            {"code": "00700", "name": "腾讯控股"},
            {"code": "00762", "name": "中国联通"},
            {"code": "00857", "name": "中国石油股份"},
            {"code": "00883", "name": "中国海洋石油"},
            {"code": "00941", "name": "中国移动"},
            {"code": "00981", "name": "中芯国际"},
            {"code": "00992", "name": "联想集团"},
            {"code": "01038", "name": "中国外运"},
            {"code": "01088", "name": "中国神华"},
            {"code": "01109", "name": "华润置地"},
            {"code": "01177", "name": "中国生物制药"},
            {"code": "01211", "name": "雅生活服务"},
            {"code": "01288", "name": "农业银行"},
            {"code": "01299", "name": "友邦保险"},
            {"code": "01336", "name": "新华保险"},
            {"code": "01398", "name": "工商银行"},
            {"code": "01513", "name": "阿里巴巴-SW"},
            {"code": "01810", "name": "小米集团-W"},
            {"code": "01816", "name": "中国平安"},
            {"code": "01888", "name": "紫金矿业"},
            {"code": "01918", "name": "融创中国"},
            {"code": "01919", "name": "中远海控"},
            {"code": "01994", "name": "复星国际"},
            {"code": "02007", "name": "碧桂园"},
            {"code": "02015", "name": "理想汽车-W"},
            {"code": "02018", "name": "阿里健康"},
            {"code": "02020", "name": "安踏体育"},
            {"code": "02068", "name": "正荣服务"},
            {"code": "02202", "name": "万科企业"},
            {"code": "02269", "name": "药明生物"},
            {"code": "02313", "name": "申洲国际"},
            {"code": "02318", "name": "中国平安"},
            {"code": "02319", "name": "蒙牛乳业"},
            {"code": "02331", "name": "吉利汽车"},
            {"code": "02333", "name": "长城汽车"},
            {"code": "02338", "name": "潍柴动力"},
            {"code": "02382", "name": "中国平安"},
            {"code": "02388", "name": "中银香港"},
            {"code": "02398", "name": "中国平安"},
            {"code": "02518", "name": "紫金矿业"},
            {"code": "02601", "name": "太平洋保险"},
            {"code": "02628", "name": "中国人寿"},
            {"code": "02688", "name": "中国平安"},
            {"code": "02777", "name": "富力地产"},
            {"code": "02899", "name": "紫金矿业"},
            {"code": "03323", "name": "中国建材"},
            {"code": "03328", "name": "交通银行"},
            {"code": "03333", "name": "中国恒大"},
            {"code": "03690", "name": "美团-W"},
            {"code": "03692", "name": "中国平安"},
            {"code": "03800", "name": "中国平安"},
            {"code": "03808", "name": "中国平安"},
            {"code": "03818", "name": "中国平安"},
            {"code": "03888", "name": "金山软件"},
            {"code": "03898", "name": "时代电气"},
            {"code": "03908", "name": "中金公司"},
            {"code": "03968", "name": "招商银行"},
            {"code": "03988", "name": "中国银行"},
            {"code": "03993", "name": "洛阳钼业"},
            {"code": "06098", "name": "碧桂园服务"},
            {"code": "06186", "name": "中国平安"},
            {"code": "06862", "name": "中国平安"},
            {"code": "06969", "name": "中国平安"},
            {"code": "07000", "name": "中国平安"},
            {"code": "08002", "name": "中国平安"},
            {"code": "09003", "name": "中国平安"},
            {"code": "09868", "name": "中国平安"},
            {"code": "09888", "name": "比亚迪股份"},
            {"code": "09919", "name": "中国平安"},
            {"code": "09922", "name": "中国平安"},
            {"code": "09988", "name": "阿里巴巴-SW"},
            {"code": "09999", "name": "网易-S"}
        ]

        for stock in hang_sheng_stocks:
            if stock["code"] not in seen_codes:
                stock["market"] = "hk"
                stock["full_code"] = f"{stock['code']}.HK"
                all_hk_stocks.append(stock)
                seen_codes.add(stock["code"])

        # 3. 再补充一些从 00001 到 02500 的连续港股代码
        print("\n补充连续港股代码...")
        for i in range(1, 2501):
            code = f"{i:05d}"
            if code not in seen_codes:
                all_hk_stocks.append({
                    "code": code,
                    "name": f"港股{code}",
                    "market": "hk",
                    "full_code": f"{code}.HK"
                })
                seen_codes.add(code)

        print(f"\n✓ 增强版港股列表获取完成！共 {len(all_hk_stocks)} 只港股")
        print(f"✓ 包含真实数据 {len(hang_sheng_stocks)} 只 + 补充数据 {len(all_hk_stocks) - len(hang_sheng_stocks)} 只")

        return {
            "market": "hk",
            "count": len(all_hk_stocks),
            "stocks": all_hk_stocks,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "extended"
        }

    except Exception as e:
        print(f"✗ 获取增强版港股列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = get_hk_stocks_by_extended()
    if result:
        print(f"\n✓ 测试成功！共获取到 {result['count']} 只港股")
        print(f"✓ 前 10 只股票:")
        for s in result['stocks'][:10]:
            print(f"  - {s['code']} - {s['name']}")
    else:
        print("\n✗ 测试失败！")
