#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股市场 - openbb-china eastmoney数据源
"""

from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt


def get_hk_stocks_by_eastmoney() -> Optional[Dict[str, Any]]:
    """
    直接调用东方财富API获取港股市场所有股票列表
    
    Returns:
        包含港股股票列表的字典
    """
    try:
        print("[eastmoney] 正在获取港股全列表...")
        
        # 直接调用东方财富API获取港股列表
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        
        # 先获取第一页数据，了解总数
        params = {
            "pn": 1, "pz": 100,  # 每页100条（API限制）
            "po": 1, "np": 1, "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": 2, "invt": 2, "fid": "f3", "fs": "m:128+t:3,m:128+t:4",  # 港股主板+创业板
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152",
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        total = data.get("data", {}).get("total", 0)
        print(f"[eastmoney] 港股总数: {total}只")
        
        if total == 0:
            print("[eastmoney] 获取港股股票列表失败: 数据为空")
            return None
        
        # 收集所有数据
        all_diffs = []
        all_diffs.extend(data["data"]["diff"])
        
        # 计算需要多少页（每页100条）
        pages_needed = (total + 99) // 100  # 向上取整
        
        if pages_needed > 1:
            print(f"[eastmoney] 需要分页获取，共{pages_needed}页")
            
            for page in range(2, pages_needed + 1):
                params["pn"] = page
                print(f"[eastmoney] 正在获取第{page}/{pages_needed}页...")
                
                response = requests.get(url, params=params)
                page_data = response.json()
                
                if page_data.get("data", {}).get("diff"):
                    all_diffs.extend(page_data["data"]["diff"])
                
                # 避免请求过快
                time.sleep(0.1)
        
        # 解析所有数据
        df = pd.DataFrame(all_diffs)
        
        if df.empty:
            print("[eastmoney] 获取港股股票列表失败: 数据为空")
            return None
        
        # 字段映射（标准化）
        df.rename(columns={
            "f12": "symbol",  # 股票代码
            "f14": "name",    # 股票名称
            "f2": "price",    # 当前价格
            "f3": "price_change_pct",  # 涨跌幅
            "f18": "market_cap"  # 市值
        }, inplace=True)
        
        # 核心清洗步骤
        df_clean = (
            df.drop_duplicates(subset=["symbol"])  # 按股票代码去重
            .dropna(subset=["symbol", "name", "price"])  # 删除关键字段为空的行
            .reset_index(drop=True)  # 重置索引
        )
        
        # 标准化字段（统一单位/格式）
        df_clean["price"] = pd.to_numeric(df_clean["price"], errors="coerce")  # 价格转数值
        df_clean["market_cap"] = pd.to_numeric(df_clean["market_cap"], errors="coerce")  # 市值转数值
        df_clean["symbol"] = df_clean["symbol"].str.strip()  # 去除代码前后空格
        
        # 转换为列表格式
        stocks = []
        for _, row in df_clean.iterrows():
            stock = {
                'code': str(row['symbol']),
                'name': str(row['name']),
                'market': 'hk',
                'full_code': f"{row['symbol']}.HK",
                'industry': '',  # 东方财富API不提供行业信息
                'list_date': ''  # 需要额外获取上市日期
            }
            stocks.append(stock)
        
        result = {
            'market': 'hk',
            'count': len(stocks),
            'stocks': stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'source': 'eastmoney'
        }
        
        print(f"[eastmoney] 港股全列表清洗完成，共{len(stocks)}只标的")
        return result
        
    except Exception as e:
        print(f"[eastmoney] 获取港股股票列表时发生错误: {e}")
        return None


def filter_hk_stocks(df_clean: pd.DataFrame) -> pd.DataFrame:
    """
    多条件筛选港股（示例：金融行业、市值>1000亿、股价>10港元）
    
    Args:
        df_clean: 清洗后的港股DataFrame
        
    Returns:
        筛选后的DataFrame
    """
    print("\n正在筛选符合条件的港股...")
    
    # 条件筛选
    filter_condition = (
        (df_clean["sector"].str.contains("金融", na=False)) &  # 金融行业
        (df_clean["market_cap"] >= 1000 * 10**8) &  # 市值≥1000亿港元
        (df_clean["price"] >= 10)  # 股价≥10港元
    )
    df_filtered = df_clean[filter_condition].copy()
    
    # 按市值降序排序
    df_filtered = df_filtered.sort_values("market_cap", ascending=False).reset_index(drop=True)
    
    print(f"筛选完成，共{len(df_filtered)}只符合条件的港股：")
    
    # 展示核心字段
    display_cols = ["symbol", "name", "price", "market_cap", "price_change_pct", "sector"]
    display_cols = [col for col in display_cols if col in df_filtered.columns]
    if display_cols:
        print(df_filtered[display_cols].head(10))
    
    return df_filtered


def get_hk_stock_history(symbol: str = "00700.HK", 
                         start_date: str = "2025-10-01", 
                         end_date: str = "2025-12-28") -> Optional[pd.DataFrame]:
    """
    获取单只港股的历史行情（日线）
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        历史行情DataFrame
    """
    print(f"\n正在获取{symbol}的历史行情...")
    
    # 避免高频请求被限制，加1秒间隔
    time.sleep(1)
    
    try:
        # 调用东方财富数据源获取历史行情
        history_data = obb.equity.price.historical(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval="1d",  # 日线数据
            provider="eastmoney"
        )
        
        df_history = history_data.to_df()
        
        if df_history.empty:
            print(f"[eastmoney] 获取{symbol}历史行情失败: 数据为空")
            return None
        
        # 清洗行情数据
        df_history["date"] = pd.to_datetime(df_history["date"])  # 日期标准化
        df_history = df_history.sort_values("date").reset_index(drop=True)
        
        print(f"{symbol}近{len(df_history)}日行情获取完成")
        return df_history
        
    except Exception as e:
        print(f"[eastmoney] 获取{symbol}历史行情时发生错误: {e}")
        return None


def plot_hk_stock_price(df_history: pd.DataFrame, symbol: str = "00700.HK") -> None:
    """
    可视化港股收盘价走势
    
    Args:
        df_history: 历史行情DataFrame
        symbol: 股票代码
    """
    print(f"\n正在绘制{symbol}收盘价走势...")
    
    # 设置中文字体（解决matplotlib中文乱码）
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei"]
    plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
    
    plt.figure(figsize=(12, 6))
    plt.plot(df_history["date"], df_history["close"], color="#1f77b4", linewidth=1.5, label="收盘价")
    plt.title(f"{symbol} 收盘价走势（2025.10-2025.12）", fontsize=14)
    plt.xlabel("日期", fontsize=12)
    plt.ylabel("价格（港元）", fontsize=12)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # 保存图片
    output_file = f"{symbol}_price_trend.png"
    plt.savefig(output_file, dpi=300)
    print(f"图表已保存为: {output_file}")
    plt.show()


def export_hk_data(df_clean: pd.DataFrame, 
                   df_filtered: pd.DataFrame, 
                   df_history: pd.DataFrame) -> None:
    """
    导出数据到本地CSV文件
    
    Args:
        df_clean: 清洗后的港股全列表
        df_filtered: 筛选后的港股列表
        df_history: 单只股票历史行情
    """
    print("\n正在导出数据到本地...")
    
    # 导出全列表
    df_clean.to_csv("港股全列表_清洗后.csv", index=False, encoding="utf-8-sig")
    
    # 导出筛选结果
    df_filtered.to_csv("港股金融股_筛选结果.csv", index=False, encoding="utf-8-sig")
    
    # 导出单只股票行情
    df_history.to_csv("腾讯控股_00700.HK_历史行情.csv", index=False, encoding="utf-8-sig")
    
    print("数据导出完成，文件保存在当前目录下")
    print("  - 港股全列表_清洗后.csv")
    print("  - 港股金融股_筛选结果.csv")
    print("  - 腾讯控股_00700.HK_历史行情.csv")


def get_hk_stocks_by_eastmoney_with_env() -> Optional[Dict[str, Any]]:
    """
    使用环境变量配置的eastmoney数据源获取港股股票列表
    
    Returns:
        包含港股股票列表的字典
    """
    # eastmoney不需要API密钥，直接调用
    return get_hk_stocks_by_eastmoney()


def main():
    """主函数（执行全流程）"""
    print("=== openbb-china 港股数据处理全流程 ===\n")
    
    # 1. 获取并清洗港股全列表
    result = get_hk_stocks_by_eastmoney()
    if not result:
        print("获取港股全列表失败，流程终止")
        return
    
    # 将结果转换为DataFrame用于后续处理
    stocks_list = result['stocks']
    df_clean = pd.DataFrame(stocks_list)
    
    # 2. 条件筛选港股
    df_filtered = filter_hk_stocks(df_clean)
    
    # 3. 获取腾讯控股（00700.HK）历史行情
    tencent_history = get_hk_stock_history(symbol="00700.HK")
    
    if tencent_history is not None:
        # 4. 可视化腾讯股价走势
        plot_hk_stock_price(tencent_history, symbol="00700.HK")
        
        # 5. 导出所有数据到CSV
        export_hk_data(df_clean, df_filtered, tencent_history)
    
    print("\n全流程执行完成！")


if __name__ == "__main__":
    # 测试单个功能
    # result = get_hk_stocks_by_eastmoney()
    # if result:
    #     print(f"测试成功: 获取到 {result['count']} 只港股")
    #     print(f"数据源: {result['source']}")
    #     print(f"第一只股票: {result['stocks'][0]}")
    # else:
    #     print("测试失败: 获取港股股票列表失败")
    
    # 执行全流程
    main()