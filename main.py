from dotenv import load_dotenv
import logging
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 抑制 pymongo 的噪音日志
logging.getLogger('pymongo').setLevel(logging.WARNING)
logging.getLogger('pymongo.server').setLevel(logging.WARNING)
logging.getLogger('pymongo.topology').setLevel(logging.WARNING)
logging.getLogger('pymongo.pool').setLevel(logging.WARNING)

app = FastAPI()

# 添加 CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源跨域访问，生产环境可以将其限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)


@app.get("/api/health")
async def health_check():
    """
    健康检查接口 - 必须快速响应（<100ms）

    注意：此接口不导入任何重型模块，确保冷启动时也能快速响应
    """
    start_time = time.time()
    result = {
        "status": "healthy",
        "message": "it works",
        "response_time_ms": round((time.time() - start_time) * 1000, 2)
    }
    return JSONResponse(content=result)


@app.get("/api/health/detailed")
async def detailed_health_check():
    """
    详细健康检查 - 包含服务状态信息

    此接口会检查各服务的初始化状态，可能较慢
    仅用于运维监控，不建议频繁调用
    """
    from service.utils.lazy_loader import get_all_service_stats

    start_time = time.time()

    # 获取服务状态
    service_stats = get_all_service_stats()

    result = {
        "status": "healthy",
        "message": "detailed health check",
        "response_time_ms": round((time.time() - start_time) * 1000, 2),
        "services": service_stats,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }
    return JSONResponse(content=result)


@app.delete("/api/cache/clear")
async def clear_all_cache():
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()
    cache.clear_all()
    return JSONResponse(content={"message": "所有K线缓存已清除"})


def normalize_date(date_str: str) -> str:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


@app.get("/api/kline")
async def get_kline(code: str, start_date: str = None, end_date: str = None, start: str = None, end: str = None, name: str = None):
    """
    获取股票K线数据

    注意：此接口会触发kline模块的延迟加载（首次调用较慢）
    :param code: 股票代码
    :param start_date: 开始日期（格式：YYYY-MM-DD）
    :param end_date: 结束日期（格式：YYYY-MM-DD）
    :param start: 开始日期（兼容参数，支持 YYYY-MM-DD 或 YYYYMMDD 格式）
    :param end: 结束日期（兼容参数，支持 YYYY-MM-DD 或 YYYYMMDD 格式）
    :param name: 股票名称（可选）
    :return: K线数据
    """
    # 延迟导入 - 仅在首次调用时加载重型模块
    from service.kline.kline import get_kline_data

    final_start_date = normalize_date(start_date) or normalize_date(start)
    final_end_date = normalize_date(end_date) or normalize_date(end)
    print(f'获取股票K线数据，股票代码：{code}，开始日期：{final_start_date}，结束日期：{final_end_date}，股票名称：{name}')

    try:
        result = get_kline_data(code, final_start_date, final_end_date)

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



@app.get("/api/stock/main-force")
async def api_get_main_force(code: str):
    """
    获取指定股票的主力动向分析数据
    :param code: 股票代码
    :return: 主力动向分析结果
    """
    # 延迟导入
    from service.main_force.main_force import get_main_force_analysis

    print(f'获取股票主力动向分析，股票代码：{code}')

    try:
        result = get_main_force_analysis(code)

        if result is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的主力动向信息")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f'获取股票主力动向分析出错：{e}')
        raise HTTPException(status_code=500, detail=f"获取股票主力动向分析失败：{str(e)}")


@app.get("/api/stock/baseinfo")
async def api_get_stock_baseinfo(code: str):
    """
    获取股票基本信息 (包含静态档案与实时行情)
    :param code: 股票代码
    :return: 股票档案数据
    """
    # 延迟导入
    from service.baseinfo.baseinfo import get_stock_baseinfo

    print(f'获取股票基本信息，股票代码：{code}')

    try:
        result = get_stock_baseinfo(code)

        if result is None or not result.get("full_name"):
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的档案信息")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f'获取股票基本信息出错：{e}')
        raise HTTPException(status_code=500, detail=f"获取股票基本信息失败：{str(e)}")


@app.get("/api/stock/market")
async def get_stock_market(marketCode: str):
    """
    获取指定市场的所有股票列表
    :param marketCode: 市场代码 (a, hk, us)
    :return: 股票列表数据
    """
    # 延迟导入
    from service.stocks.stocks import get_stock_by_market

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

@app.get("/api/stock-basic-info")
async def api_get_stock_basic_info(code: str):
    """
    获取股票基本信息
    :param code: 股票代码
    :return: 股票基本信息
    """
    # 延迟导入
    from service.stocks.basic_info import get_stock_basic_info

    print(f'获取股票基本信息，股票代码：{code}')

    try:
        result = get_stock_basic_info(code)

        if result is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的基本信息")

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f'获取股票基本信息出错：{e}')
        raise HTTPException(status_code=500, detail=f"获取股票基本信息失败：{str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
