#!/usr/bin/env python3
"""测试时间参数的使用"""

from service.kline.kline import get_kline_data

# 测试1：验证时间参数是否被使用
print("测试1：验证时间参数是否被使用")
print("请求时间范围：2025-10-01 到 2025-10-15")
result = get_kline_data('000001', '2025-10-01', '2025-10-15', ['eastmoney_cn'])
print(f"数据条数: {len(result['data'])}")
print("所有数据日期:")
for item in result['data']:
    print(f"  {item['date']}")

# 测试2：验证完整的时间范围
print("\n测试2：验证完整的时间范围")
print("请求时间范围：2025-10-01 到 2025-12-20")
result = get_kline_data('000001', '2025-10-01', '2025-12-20', ['eastmoney_cn'])
print(f"数据条数: {len(result['data'])}")
print(f"第一条数据日期: {result['data'][0]['date']}")
print(f"最后一条数据日期: {result['data'][-1]['date']}")

# 测试3：验证没有交易数据的日期
print("\n测试3：验证周末和节假日")
print("2025-10-01是国庆节，2025-10-04-05是周末")
print("所以实际交易数据从2025-10-09开始是正常的")