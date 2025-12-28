#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
openbb-china 示例代码 - 港股数据处理全流程

# 安装核心依赖
pip install openbb openbb-china pandas matplotlib
"""

# 导入核心库
from openbb import obb
import pandas as pd
import matplotlib.pyplot as plt
import time

# ===================== 1. 全局配置（可选） =====================
# 设置中文字体（解决matplotlib中文乱码）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# ===================== 2. 获取港股全列表并清洗 =====================
def get_clean_hk_stocks():
    """获取清洗后的港股全列表（去重、去空、格式标准化）"""
    print("正在获取港股全列表...")
    
    try:
        # 调用东方财富数据源获取港股列表
        hk_stocks = obb.equity.screener(
            country="hk",          # 指定香港市场
            provider="eastmoney"   # 东方财富数据源
        )
        
        # 转换为DataFrame并清洗
        df = hk_stocks.to_df()
        
        if df.empty:
            print("获取港股列表失败: 数据为空")
            return None
        
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
        
        print(f"港股全列表清洗完成，共{len(df_clean)}只标的")
        return df_clean
        
    except Exception as e:
        print(f"获取港股全列表时发生错误: {e}")
        return None

# ===================== 3. 条件筛选港股（多维度） =====================
def filter_hk_stocks(df_clean):
    """多条件筛选港股（示例：金融行业、市值>1000亿、股价>10港元）"""
    print("\n正在筛选符合条件的港股...")
    
    # 检查必要的列是否存在
    required_cols = ["sector", "market_cap", "price"]
    missing_cols = [col for col in required_cols if col not in df_clean.columns]
    if missing_cols:
        print(f"警告: 缺少必要的列 {missing_cols}")
        print(f"可用列: {list(df_clean.columns)}")
        return pd.DataFrame()
    
    # 条件筛选
    filter_condition = (
        (df_clean["sector"].str.contains("金融", na=False)) &  # 金融行业
        (df_clean["market_cap"] >= 1000 * 10**8) &  # 市值≥1000亿港元（需确认字段单位，东方财富默认单位为港元）
        (df_clean["price"] >= 10)  # 股价≥10港元
    )
    df_filtered = df_clean[filter_condition].copy()
    
    # 按市值降序排序
    df_filtered = df_filtered.sort_values("market_cap", ascending=False).reset_index(drop=True)
    
    print(f"筛选完成，共{len(df_filtered)}只符合条件的港股：")
    
    # 展示核心字段
    display_cols = ["symbol", "name", "price", "market_cap", "price_change_pct", "sector"]
    display_cols = [col for col in display_cols if col in df_filtered.columns]
    
    if len(df_filtered) > 0 and display_cols:
        print(df_filtered[display_cols].head(10))
    elif len(df_filtered) == 0:
        print("没有找到符合条件的港股")
    
    return df_filtered

# ===================== 4. 获取单只港股历史行情 =====================
def get_hk_stock_history(symbol="00700.HK", start_date="2025-10-01", end_date="2025-12-28"):
    """获取单只港股的历史行情（日线）"""
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
            print(f"获取{symbol}历史行情失败: 数据为空")
            return None
        
        # 清洗行情数据
        df_history["date"] = pd.to_datetime(df_history["date"])  # 日期标准化
        df_history = df_history.sort_values("date").reset_index(drop=True)
        
        print(f"{symbol}近{len(df_history)}日行情获取完成")
        return df_history
        
    except Exception as e:
        print(f"获取{symbol}历史行情时发生错误: {e}")
        return None

# ===================== 5. 可视化港股行情 =====================
def plot_hk_stock_price(df_history, symbol="00700.HK"):
    """可视化港股收盘价走势"""
    print(f"\n正在绘制{symbol}收盘价走势...")
    
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

# ===================== 6. 导出数据到CSV =====================
def export_hk_data(df_clean, df_filtered, df_history):
    """导出数据到本地CSV文件"""
    print("\n正在导出数据到本地...")
    
    # 导出全列表
    df_clean.to_csv("港股全列表_清洗后.csv", index=False, encoding="utf-8-sig")
    
    # 导出筛选结果
    if not df_filtered.empty:
        df_filtered.to_csv("港股金融股_筛选结果.csv", index=False, encoding="utf-8-sig")
    
    # 导出单只股票行情
    if df_history is not None:
        df_history.to_csv("腾讯控股_00700.HK_历史行情.csv", index=False, encoding="utf-8-sig")
    
    print("数据导出完成，文件保存在当前目录下")
    print("  - 港股全列表_清洗后.csv")
    if not df_filtered.empty:
        print("  - 港股金融股_筛选结果.csv")
    if df_history is not None:
        print("  - 腾讯控股_00700.HK_历史行情.csv")

# ===================== 主函数（执行全流程） =====================
def main():
    """主函数（执行全流程）"""
    print("=== openbb-china 港股数据处理全流程 ===\n")
    
    # 1. 获取并清洗港股全列表
    hk_stocks_clean = get_clean_hk_stocks()
    
    if hk_stocks_clean is None:
        print("获取港股全列表失败，流程终止")
        return
    
    # 2. 条件筛选港股
    hk_filtered = filter_hk_stocks(hk_stocks_clean)
    
    # 3. 获取腾讯控股（00700.HK）历史行情
    tencent_history = get_hk_stock_history(symbol="00700.HK")
    
    if tencent_history is not None:
        # 4. 可视化腾讯股价走势
        plot_hk_stock_price(tencent_history, symbol="00700.HK")
        
        # 5. 导出所有数据到CSV
        export_hk_data(hk_stocks_clean, hk_filtered, tencent_history)
    
    print("\n全流程执行完成！")

if __name__ == "__main__":
    main()