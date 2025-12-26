from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException

from service.kline.kline import get_kline_data

# 加载环境变量
load_dotenv()

app = FastAPI()



@app.get("/api/kline")
async def get_kline(code: str, start_date: str = None, end_date: str = None, name: str = None):
    """
    获取股票K线数据
    :param code: 股票代码
    :param start_date: 开始日期（格式：YYYY-MM-DD）
    :param end_date: 结束日期（格式：YYYY-MM-DD）
    :param name: 股票名称（可选）
    :return: K线数据
    """
    print(f'获取股票K线数据，股票代码：{code}，开始日期：{start_date}，结束日期：{end_date}，股票名称：{name}')

    try:
        # 调用新的kline服务获取数据
        result = get_kline_data(code, start_date, end_date)
        
        # 转换结果为API响应格式
        return {
            "code": code,
            "name": name or code,
            "market": result["market"],
            "data_source": result["data_source"],
            "data": result["data"]
        }
        
    except ImportError:
        raise HTTPException(status_code=500, detail="OpenBB未安装，请先安装openbb")
    except Exception as e:
        print(f'获取股票数据出错：{e}')
        raise HTTPException(status_code=500, detail=f"获取股票数据失败：{str(e)}")


from service.stocks.stocks import get_stock_by_market


@app.get("/api/stock/market")
async def get_stock_market(marketCode: str):
    """
    获取指定市场的所有股票列表
    :param marketCode: 市场代码 (cn, hk, us)
    :return: 股票列表数据
    """
    print(f'获取市场股票列表，市场代码：{marketCode}')

    try:
        # 调用股票市场服务获取数据
        result = get_stock_by_market(marketCode)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"未找到市场代码为 {marketCode} 的股票列表")
        
        # 转换结果为API响应格式
        return {
            "market": marketCode,
            "count": result["count"],
            "stocks": result["stocks"],
            "timestamp": result["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f'获取市场股票列表出错：{e}')
        raise HTTPException(status_code=500, detail=f"获取市场股票列表失败：{str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    