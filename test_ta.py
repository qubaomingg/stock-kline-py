import pandas as pd
from service.kline.kline import get_kline_data
from datetime import datetime, timedelta

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=200)).strftime('%Y-%m-%d')

res = get_kline_data('000001', start_date=start_date, end_date=end_date)
df = pd.DataFrame(res['data'])

delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
rs = gain / loss
df['rsi'] = 100 - (100 / (1 + rs))

print(df[['date', 'close', 'rsi']].tail())
