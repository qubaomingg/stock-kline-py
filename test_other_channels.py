import sys
import os

sys.path.insert(0, os.path.abspath('.'))

def test_bs():
    try:
        from service.stocks.a.bs_stocks import get_a_stocks_by_baostock
        print("=== 测试 baostock ===")
        res = get_a_stocks_by_baostock()
        if res:
            print(f"✅ Baostock 成功获取 {res.get('count')} 只股票。前3只: {[s['code'] for s in res.get('stocks', [])[:3]]}")
        else:
            print("❌ Baostock 返回为空")
    except Exception as e:
        print(f"❌ Baostock 测试失败: {e}")

if __name__ == '__main__':
    test_bs()
