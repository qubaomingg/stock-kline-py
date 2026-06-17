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


@app.get("/api/cache/status")
async def cache_status():
    """
    诊断接口：查看当前缓存连接状态
    用于排查 "MongoDB未连接" 这类问题
    """
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()

    # 打印到终端日志
    info = cache.get_connection_info()
    print(f"[Cache Status] {info}")

    # 统计一下库里有多少数据
    stats = {"mongodb_records": None}
    try:
        if cache.is_connected():
            stats["mongodb_records"] = cache.collection.count_documents({})
    except Exception as e:
        stats["count_error"] = str(e)

    return {
        "status": "ok",
        "connection": info,
        "stats": stats,
    }


@app.get("/api/cache/reconnect")
async def cache_reconnect():
    """
    强制重连 MongoDB（之前连接失败了可以通过这个接口重试）
    """
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()
    result = cache.reconnect()
    print(f"[Cache Reconnect] {result}")
    return result


@app.get("/api/cache/clear")
async def clear_all_cache_get():
    """
    浏览器友好版本：清空所有缓存（GET 请求直接访问即可）
    """
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()
    print("[Cache Clear] 清空所有缓存...")
    cache.clear_all()
    print("[Cache Clear] ✅ 所有缓存已清空")
    return {"success": True, "message": "✅ 所有缓存已清空，下次请求将从数据源重新获取"}


@app.get("/api/cache/clear/kline")
async def clear_kline_cache(code: str = None):
    """
    清空 K线 缓存（浏览器友好）
    - 不传 code = 清空**所有** K线 缓存
    - 传 code = 清空该股票的 K线 缓存

    用法: /api/cache/clear/kline                 → 清空所有 K线
    用法: /api/cache/clear/kline?code=LITE       → 只清空 LITE
    用法: /api/cache/clear/kline?code=00700      → 只清空 00700
    """
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()

    if not code:
        # 不传 code → 清空所有 K线
        print("[Cache Clear] 清空所有 K线 缓存...")
        result = cache.delete_all_kline()
        print(f"[Cache Clear] → 结果: {result}")
        return {
            "success": result["success"],
            "scope": "all_kline",
            "deleted": result.get("deleted", 0),
            "message": result.get("message", "")
        }

    # 传 code → 清空该股票的缓存
    print(f"[Cache Clear] 清空股票 {code} 的缓存...")
    result = cache.delete_by_code(code)
    print(f"[Cache Clear] → 结果: {result}")
    return {
        "success": result["success"],
        "scope": "single_stock",
        "code": code,
        "deleted_kline": result.get("deleted_kline", 0),
        "deleted_market": result.get("deleted_market", 0),
        "message": result.get("message", "")
    }


@app.get("/api/cache/clear/market")
async def clear_market_cache(marketCode: str = None):
    """
    清空指定市场的列表缓存（浏览器友好）

    用法: /api/cache/clear/market?marketCode=us
    用法: /api/cache/clear/market?marketCode=hk
    用法: /api/cache/clear/market?marketCode=a
    """
    from service.cache.mongodb_cache import get_cache
    cache = get_cache()

    if not marketCode:
        return {"success": False, "message": "❌ 请提供 marketCode 参数: /api/cache/clear/market?marketCode=us"}

    print(f"[Cache Clear] 清空 market:{marketCode} 缓存...")
    result = cache.delete_by_market(marketCode)
    print(f"[Cache Clear] → 结果: {result}")
    return {
        "success": result["success"],
        "market_code": marketCode,
        "deleted": result.get("deleted", 0),
        "message": result.get("message", "")
    }


def normalize_date(date_str: str) -> str:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    if len(date_str) == 8 and date_str.isdigit():
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str


@app.get("/api/kline")
async def get_kline(code: str, start_date: str = None, end_date: str = None, start: str = None, end: str = None, name: str = None, force: bool = False):
    """
    获取股票K线数据

    注意：此接口会触发kline模块的延迟加载（首次调用较慢）
    :param code: 股票代码
    :param start_date: 开始日期（格式：YYYY-MM-DD）
    :param end_date: 结束日期（格式：YYYY-MM-DD）
    :param start: 开始日期（兼容参数，支持 YYYY-MM-DD 或 YYYYMMDD 格式）
    :param end: 结束日期（兼容参数，支持 YYYY-MM-DD 或 YYYYMMDD 格式）
    :param name: 股票名称（可选）
    :param force: 强制跳过缓存，直接从数据源获取（True=强制刷新，默认False）
    :return: K线数据
    """
    # 延迟导入 - 仅在首次调用时加载重型模块
    from service.kline.kline import get_kline_data

    final_start_date = normalize_date(start_date) or normalize_date(start)
    final_end_date = normalize_date(end_date) or normalize_date(end)
    print(f'获取股票K线数据，股票代码：{code}，开始日期：{final_start_date}，结束日期：{final_end_date}，股票名称：{name}，force={force}')

    try:
        result = get_kline_data(code, final_start_date, final_end_date, force=force)

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
async def get_stock_market(marketCode: str, force: bool = False):
    """
    获取指定市场的所有股票列表

    Args:
        marketCode: 市场代码 (a, hk, us)
        force: 是否强制跳过缓存，从数据源重新获取（默认 False）

    Returns:
        股票列表数据
    """
    # 延迟导入
    from service.stocks.stocks import get_stock_by_market

    print(f'获取市场股票列表，市场代码：{marketCode}，force：{force}')

    try:
        # 调用股票市场服务获取数据
        result = get_stock_by_market(marketCode, force=force)

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
