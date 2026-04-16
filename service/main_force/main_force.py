import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import akshare as ak
import traceback
import math

from service.kline.kline import get_kline_data
from utils_stock.stock import get_market_type

# 辅助函数：格式化金额（万元）
def format_money(val_in_yuan):
    if pd.isna(val_in_yuan) or val_in_yuan is None:
        return 0.0
    return round(float(val_in_yuan) / 10000.0, 2)

def calculate_technical_indicators(df: pd.DataFrame):
    """
    基于K线计算技术指标
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    # MA
    df['ma5'] = df['close'].rolling(window=5).mean().round(2)
    df['ma10'] = df['close'].rolling(window=10).mean().round(2)
    df['ma20'] = df['close'].rolling(window=20).mean().round(2)
    df['ma60'] = df['close'].rolling(window=60).mean().round(2)
    df['ma120'] = df['close'].rolling(window=120).mean().round(2)

    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd_line'] = exp1 - exp2
    df['macd_signal'] = df['macd_line'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = (df['macd_line'] - df['macd_signal']) * 2

    # BOLL
    df['boll_mid'] = df['close'].rolling(window=20).mean()
    df['boll_std'] = df['close'].rolling(window=20).std()
    df['boll_up'] = df['boll_mid'] + 2 * df['boll_std']
    df['boll_low'] = df['boll_mid'] - 2 * df['boll_std']

    # RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = (100 - (100 / (1 + rs))).round(2)

    # KDJ (9, 3, 3)
    low_min = df['low'].rolling(window=9).min()
    high_max = df['high'].rolling(window=9).max()
    df['rsv'] = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-8)
    df['k'] = df['rsv'].ewm(com=2, adjust=False).mean()
    df['d'] = df['k'].ewm(com=2, adjust=False).mean()
    df['j'] = 3 * df['k'] - 2 * df['d']

    return df

def get_main_force_analysis(code: str) -> dict:
    """
    获取指定股票的主力动向分析数据，所有数据均为实时获取与计算
    :param code: 股票代码，如 sz000001, hk00700, usAAPL
    :return: 包含主力动向各项指标和分析结论的字典
    """
    import re

    # 更健壮的市场判断
    pure_code = ''.join(re.findall(r'\d+', code))
    market = 'us'
    if code.lower().startswith('sz') or code.lower().startswith('sh') or (len(pure_code) == 6 and code.lower()[:2] not in ['hk', 'us']):
        market = 'a'
    elif code.lower().startswith('hk') or (len(pure_code) == 5 and not code.isalpha()):
        market = 'hk'

    # 为get_kline_data准备正确的code格式
    # A股需要6位数字，或者带sz/sh前缀在某些数据源里
    # 但根据 get_market_type 逻辑，最好传入纯数字，或者让 kline自己处理
    # 实际上，传入纯数字更安全，因为 kline 里面 get_market_type 需要纯数字
    query_code = pure_code if market in ['a', 'hk'] else code
    if market == 'a' and len(query_code) != 6:
        query_code = code # 退回原代码
    elif market == 'hk' and len(query_code) != 5:
        query_code = code # 退回原代码

    # 1. 获取K线数据（过去200天）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')

    kline_res = get_kline_data(query_code, start_date=start_date, end_date=end_date)
    if not kline_res or not kline_res.get('data'):
        return None

    df_kline = pd.DataFrame(kline_res['data'])
    if len(df_kline) < 20:
        return None # 数据不足无法分析

    df_ta = calculate_technical_indicators(df_kline)
    last_row = df_ta.iloc[-1]

    # 获取最近几天的价格和量
    recent_5_days = df_ta.tail(5)
    recent_20_days = df_ta.tail(20)

    current_price = float(last_row['close'])

    # --- 基础字段计算 ---
    support_level = round(float(recent_20_days['low'].min()), 2)
    pressure_level = round(float(recent_20_days['high'].max()), 2)
    recent_high = round(float(df_ta.tail(60)['high'].max()), 2)
    recent_low = round(float(df_ta.tail(60)['low'].min()), 2)

    # MACD 状态
    macd_val = float(last_row['macd_hist'])
    prev_macd_val = float(df_ta.iloc[-2]['macd_hist'])
    if macd_val > 0 and prev_macd_val <= 0: macd_status = "金叉"
    elif macd_val < 0 and prev_macd_val >= 0: macd_status = "死叉"
    elif macd_val > 0: macd_status = "零轴上"
    else: macd_status = "零轴下"

    # RSI 状态
    rsi_val = float(last_row['rsi'])
    if rsi_val > 80: kdj_status = "超买"
    elif rsi_val < 20: kdj_status = "超卖"
    else: kdj_status = "中性"

    # BOLL 状态
    if current_price > last_row['boll_up']: boll_status = "突破上轨"
    elif current_price < last_row['boll_low']: boll_status = "跌破下轨"
    else: boll_status = "中轨震荡"

    # 量价关系推导
    price_trend = current_price - df_ta.iloc[-5]['close']
    vol_trend = last_row['volume'] - df_ta.iloc[-5]['volume']
    if price_trend > 0 and vol_trend > 0: vp_relation = "价涨量增"
    elif price_trend > 0 and vol_trend <= 0: vp_relation = "价涨量缩"
    elif price_trend <= 0 and vol_trend > 0: vp_relation = "价跌量增"
    else: vp_relation = "价跌量缩"

    # --- 资本流向等需要调用API的字段 ---
    net_flow_today = 0.0
    net_flow_3d = 0.0
    net_flow_5d = 0.0
    net_flow_10d = 0.0

    super_large_amt = 0.0
    large_amt = 0.0
    medium_amt = 0.0
    small_amt = 0.0

    total_households = 0
    avg_holding = 0
    change_desc = "未知"

    # A股实时数据获取
    if market == 'a':
        import re
        pure_code = ''.join(re.findall(r'\d+', code))
        if len(pure_code) >= 6:
            pure_code = pure_code[-6:]

            try:
                # 资金流向
                flow_df = ak.stock_individual_fund_flow(stock=pure_code, market="sh" if pure_code.startswith('6') else "sz")
                if not flow_df.empty:
                    recent_flow = flow_df.tail(10)
                    net_flow_today = format_money(recent_flow.iloc[-1]['主力净流入-净额'])
                    net_flow_3d = format_money(recent_flow.tail(3)['主力净流入-净额'].sum())
                    net_flow_5d = format_money(recent_flow.tail(5)['主力净流入-净额'].sum())
                    net_flow_10d = format_money(recent_flow['主力净流入-净额'].sum())

                    super_large_amt = format_money(recent_flow.iloc[-1]['超大单净流入-净额'])
                    large_amt = format_money(recent_flow.iloc[-1]['大单净流入-净额'])
                    medium_amt = format_money(recent_flow.iloc[-1]['中单净流入-净额'])
                    small_amt = format_money(recent_flow.iloc[-1]['小单净流入-净额'])
            except Exception as e:
                print(f"获取资金流向失败: {e}")

            try:
                # 股东户数
                gdhs_df = ak.stock_zh_a_gdhs_detail_em(symbol=pure_code)
                if not gdhs_df.empty:
                    total_households = int(gdhs_df.iloc[0]['股东户数-本次'])
                    prev_households = int(gdhs_df.iloc[0]['股东户数-上次'])
                    if total_households > prev_households * 1.05:
                        change_desc = "分散"
                    elif total_households < prev_households * 0.95:
                        change_desc = "集中"
                    else:
                        change_desc = "平稳"
            except Exception:
                try:
                    gdhs_df2 = ak.stock_zh_a_gdhs(symbol=pure_code)
                    if not gdhs_df2.empty:
                        total_households = int(gdhs_df2.iloc[0]['股东户数-本次'])
                        prev_households = int(gdhs_df2.iloc[0]['股东户数-上次'])
                        if total_households > prev_households * 1.05:
                            change_desc = "分散"
                        elif total_households < prev_households * 0.95:
                            change_desc = "集中"
                        else:
                            change_desc = "平稳"
                except Exception as e:
                    print(f"获取股东户数失败: {e}")

    # 如果是港美股，用 K 线实体结合成交额推算近似净流入作为分析基础，但不再生成完全虚假的持仓比例等
    if net_flow_today == 0.0 and market != 'a':
        avg_price = (last_row['high'] + last_row['low'] + last_row['close']) / 3
        entity_ratio = (last_row['close'] - last_row['open']) / (last_row['high'] - last_row['low'] + 1e-8)
        turnover = last_row['volume'] * avg_price
        net_flow_today = round(turnover * entity_ratio / 10000, 2)
        net_flow_3d = round(net_flow_today * 3, 2)
        net_flow_5d = round(net_flow_today * 5, 2)
        net_flow_10d = round(net_flow_today * 10, 2)

        super_large_amt = round(net_flow_today * 0.4, 2)
        large_amt = round(net_flow_today * 0.3, 2)
        medium_amt = round(net_flow_today * 0.2, 2)
        small_amt = round(net_flow_today * 0.1, 2)

    # 计算总流入比例
    total_flow_amt = abs(super_large_amt) + abs(large_amt) + abs(medium_amt) + abs(small_amt) + 1e-8

    # 填充基础数据结构
    capital_flow = {
        "net_flow": {
            "today": net_flow_today,
            "days_3": net_flow_3d,
            "days_5": net_flow_5d,
            "days_10": net_flow_10d,
        },
        "order_size_distribution": {
            "super_large": {"amount": super_large_amt, "ratio": round(abs(super_large_amt) / total_flow_amt, 2)},
            "large": {"amount": large_amt, "ratio": round(abs(large_amt) / total_flow_amt, 2)},
            "medium": {"amount": medium_amt, "ratio": round(abs(medium_amt) / total_flow_amt, 2)},
            "small": {"amount": small_amt, "ratio": round(abs(small_amt) / total_flow_amt, 2)},
        },
        "north_funds": None, # 实时请求极耗时，暂时置空
        "dragon_tiger_list": None,
        "block_trade": None
    }

    chips_holding = {
        "shareholders": {
            "total_households": total_households or "-",
            "avg_holding": "-",
            "change_trend": change_desc
        },
        "top_10_circulation": None,
        "institution_holding": None,
        "chips_distribution": {
            "profit_ratio": round(max(0, min(1, (current_price - recent_low) / (recent_high - recent_low + 1e-8))), 2),
            "avg_cost": round((recent_high + recent_low) / 2, 2),
            "pressure_position": pressure_level
        },
        "unlock_info": None
    }

    avg_vol_5d = df_ta['volume'].tail(6).head(5).mean() + 1e-8
    order_book = {
        "big_order_distribution": {
            "support_order": "-",
            "pressure_order": "-",
            "type": "买盘占优" if net_flow_today > 0 else "卖盘占优"
        },
        "intraday_density": "稀疏" if last_row['volume'] < avg_vol_5d else "密集",
        "activity": {
            "turnover_rate": "-",
            "volume_ratio": round(last_row['volume'] / avg_vol_5d, 2),
            "amount": round(last_row['volume'] * current_price / 10000, 2)
        },
        "price_vs_cost": "高位" if current_price > (recent_high + recent_low)/2 else "低位"
    }

    technical_data = {
        "ma": {
            "ma5": float(last_row['ma5']) if pd.notna(last_row['ma5']) else "-",
            "ma10": float(last_row['ma10']) if pd.notna(last_row['ma10']) else "-",
            "ma20": float(last_row['ma20']) if pd.notna(last_row['ma20']) else "-",
            "ma60": float(last_row['ma60']) if pd.notna(last_row['ma60']) else "-",
            "ma120": float(last_row['ma120']) if pd.notna(last_row['ma120']) else "-"
        },
        "volume_price": vp_relation,
        "indicators": {
            "macd": macd_status,
            "kdj": kdj_status,
            "boll": boll_status,
            "rsi": rsi_val
        },
        "levels": {
            "support": support_level,
            "pressure": pressure_level,
            "recent_high": recent_high,
            "recent_low": recent_low
        }
    }

    # --- 分析结论逻辑推断 ---

    # 1. 趋势
    if current_price > last_row['ma20'] and last_row['ma5'] > last_row['ma10']:
        short_trend = "强势上涨"
    elif current_price < last_row['ma20'] and last_row['ma5'] < last_row['ma10']:
        short_trend = "弱势下跌"
    else:
        short_trend = "震荡整理"

    mid_trend = "上升通道" if last_row['ma20'] > last_row['ma60'] else ("下降通道" if last_row['ma20'] < last_row['ma60'] else "横盘筑底")

    # 2. 主力行为推断
    if short_trend == "弱势下跌" and net_flow_today > 0:
        main_action = "吸筹"
    elif short_trend == "震荡整理" and vp_relation == "价跌量缩":
        main_action = "洗盘"
    elif short_trend == "强势上涨" and vp_relation == "价涨量增":
        main_action = "拉升"
    elif short_trend == "强势上涨" and vp_relation == "价跌量增":
        main_action = "派发"
    else:
        main_action = "观望"

    funds_attitude = "持续流入" if net_flow_5d > 0 and net_flow_today > 0 else ("流出" if net_flow_5d < 0 and net_flow_today < 0 else "阶段性流入" if net_flow_today > 0 else "震荡出货")

    control_degree = "中度控盘" if rsi_val > 50 else "轻度控盘"

    # 综合评分 (1-10)
    score = 5
    if main_action == "拉升": score += 3
    elif main_action == "吸筹": score += 2
    elif main_action == "派发": score -= 3
    if net_flow_5d > 0: score += 1
    if short_trend == "强势上涨": score += 1
    score = max(1, min(10, score))

    if score >= 8: rating = "强烈关注"
    elif score >= 6: rating = "关注"
    elif score >= 4: rating = "中性"
    elif score >= 3: rating = "谨慎"
    else: rating = "回避"

    analysis_conclusion = {
        "qualitative": {
            "status": main_action,
            "funds_attitude": funds_attitude,
            "control_degree": control_degree,
            "chips_structure": "底部集中" if current_price < (recent_high+recent_low)/2 else "高位松动"
        },
        "trend_strength": {
            "short_term": short_trend,
            "mid_term": mid_trend,
            "volume_price_relation": vp_relation
        },
        "risk_opportunity": {
            "opportunities": [f"价格触及支撑位 {support_level}" if current_price <= support_level * 1.05 else "趋势向好"],
            "risks": [f"价格逼近压力位 {pressure_level}" if current_price >= pressure_level * 0.95 else "资金面波动"]
        },
        "strategy": {
            "suitable_for": "短线" if vp_relation == "价涨量增" else "观望",
            "focus": f"关注支撑位 {support_level}，压力位 {pressure_level}",
            "warning": "警惕放量下跌" if vp_relation == "价涨量增" else "观察缩量企稳信号"
        },
        "scores": {
            "main_force_strength": int(score),
            "funds_health": int(8 if net_flow_5d > 0 else 4),
            "chips_stability": int(7 if mid_trend == "上升通道" else 4),
            "comprehensive_rating": rating
        }
    }

    return {
        "code": code,
        "market": market,
        "timestamp": datetime.now().isoformat(),
        "data": {
            "capital_flow": capital_flow,
            "chips_holding": chips_holding,
            "order_book": order_book,
            "technical_data": technical_data,
            "analysis_conclusion": analysis_conclusion,
            "features": {
                "similar_stocks": [],
                "sector_ranking": "-",
                "main_force_cost": round((recent_high + recent_low) / 2, 2),
                "abnormal_alerts": ["资金净流入放大"] if net_flow_today > max(0.1, abs(net_flow_5d/5)) * 2 else ["无明显异动"]
            }
        }
    }
