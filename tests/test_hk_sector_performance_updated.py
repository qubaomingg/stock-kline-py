import sys
sys.path.append('.')

from service.stock.hk.akshare_hk import get_hk_sector_performance

result = get_hk_sector_performance()
print('Result type:', type(result))

if result:
    print('Data source:', result.get('data_source'))
    print('Type:', result.get('type'))
    
    data = result.get('data')
    if data:
        print('Data length:', len(data))
        print('\nFirst item:')
        import json
        print(json.dumps(data[0], ensure_ascii=False, indent=2))
        
        # 显示前5个板块
        print('\nTop 5 sectors:')
        for i, sector in enumerate(data[:5]):
            print(f"{i+1}. {sector['sector_name']}: {sector['change_percent']}%")
    else:
        print('No data')
else:
    print('Result is None')