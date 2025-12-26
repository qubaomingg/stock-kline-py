import sys
sys.path.append('.')

from service.stock.hk.akshare_hk import get_hk_sector_performance

result = get_hk_sector_performance()
print('Result type:', type(result))
if result:
    print('Data length:', len(result.get('data', [])))
    if result.get('data'):
        print('First item:', result.get('data')[0])
    else:
        print('No data in result')
else:
    print('Result is None')