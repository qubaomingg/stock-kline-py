import akshare as ak
import inspect

# 获取akshare所有成员
members = inspect.getmembers(ak)

# 筛选行业/板块相关函数
sector_funcs = []
for name, obj in members:
    if callable(obj):
        name_lower = name.lower()
        if ('industry' in name_lower or 
            'sector' in name_lower or 
            'board' in name_lower or
            '板块' in name_lower or
            '行业' in name_lower):
            sector_funcs.append(name)

print(f'行业/板块相关函数数量: {len(sector_funcs)}')
print('所有相关函数:')
for func in sector_funcs:
    print(f'  {func}')

# 测试几个可能相关的函数
print('\n测试可能相关的函数:')
test_funcs = ['stock_board_industry_name_em', 'stock_board_industry_hist_em', 'stock_board_concept_name_em', 'stock_board_concept_hist_em']

for func_name in test_funcs:
    if hasattr(ak, func_name):
        try:
            print(f'\n测试 {func_name}:')
            data = getattr(ak, func_name)()
            if hasattr(data, 'shape'):
                print(f'  数据形状: {data.shape}')
                print(f'  列名: {list(data.columns)}')
                if not data.empty:
                    print(f'  前几行数据:')
                    print(data.head(2))
            else:
                print(f'  返回类型: {type(data)}')
                print(f'  数据: {data}')
        except Exception as e:
            print(f'  错误: {e}')
    else:
        print(f'\n{func_name} 不存在')