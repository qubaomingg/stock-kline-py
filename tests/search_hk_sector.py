import akshare as ak
import inspect

# 获取akshare所有成员
members = inspect.getmembers(ak)

# 筛选包含'hk'的函数
hk_funcs = []
for name, obj in members:
    if callable(obj) and 'hk' in name.lower():
        hk_funcs.append(name)

print(f'akshare港股相关函数数量: {len(hk_funcs)}')
print('前20个函数:')
for func in hk_funcs[:20]:
    print(f'  {func}')

# 筛选可能包含板块或行业数据的函数
sector_keywords = ['sector', 'industry', 'board', '板块', '行业']
sector_funcs = []
for name in hk_funcs:
    name_lower = name.lower()
    for keyword in sector_keywords:
        if keyword in name_lower:
            sector_funcs.append(name)
            break

print(f'\n可能包含板块数据的函数数量: {len(sector_funcs)}')
for func in sector_funcs:
    print(f'  {func}')