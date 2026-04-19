#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试几个 akshare 的港股函数
"""

import akshare as ak
import time

print("=" * 70)
print("测试 akshare 的港股函数")
print("=" * 70)

functions_to_test = [
    ("stock_hk_main_board_spot_em", "港股主板实时行情"),
    ("stock_hk_ggt_components_em", "港股通成分股"),
    ("stock_hk_ggt_ss_em", "港股通标的"),
    ("stock_hk_index_spot_em", "港股指数"),
    ("stock_hk_famous_spot_em", "港股热门股"),
]

all_hk_stocks = {}

for func_name, desc in functions_to_test:
    try:
        if not hasattr(ak, func_name):
            print(f"❌ {func_name} 不存在，跳过")
            continue
        
        print(f"\n{'='*70}")
        print(f"测试 {desc} ({func_name})")
        print(f"{'='*70}")
        
        func = getattr(ak, func_name)
        start_time = time.time()
        
        try:
            result = func()
            elapsed = time.time() - start_time
            
            if hasattr(result, 'empty') and not result.empty:
                print(f"✅ 成功，共 {len(result)} 行，耗时 {elapsed:.2f}s")
                print("列名:", result.columns.tolist())
                print("\n前 5 行:")
                print(result.head())
                
                # 尝试提取股票代码和名称
                for col1, col2 in [
                    ('symbol', 'name'), ('代码', '名称'), ('code', 'name'),
                    ('stock_code', 'stock_name'), ('stock', 'name'),
                ]:
                    if col1 in result.columns and col2 in result.columns:
                        print(f"\n✅ 找到列 {col1} 和 {col2}")
                        valid = result[
                            result[col1].notna() & 
                            result[col2].notna()
                        ]
                        print(f"有效数据共 {len(valid)} 行")
                        
                        # 添加到总列表
                        for idx, row in valid.iterrows():
                            code = str(row[col1]).strip()
                            name = str(row[col2]).strip()
                            # 港股代码标准化
                            if code and code.isdigit():
                                code = code.zfill(5)
                                if code not in all_hk_stocks:
                                    all_hk_stocks[code] = name
                        break
                        
        except Exception as e:
            print(f"❌ 执行失败: {e}")
            
    except Exception as e:
        print(f"❌ 加载失败: {e}")

print(f"\n{'='*70}")
print(f"汇总：总共收集到 {len(all_hk_stocks)} 只港股")
print(f"{'='*70}")
if len(all_hk_stocks) > 0:
    print("\n前 20 只港股:")
    for idx, (code, name) in enumerate(list(all_hk_stocks.items())[:20]):
        print(f"{idx+1}. {code}: {name}")
