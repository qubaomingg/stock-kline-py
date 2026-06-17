"""优质低价分析 Flow。

工作流（所有 log 集中在 quality-value 主 flow run 中，不产生子 flow run）：
  1. 合并 AI 预设股票池 + 数据库 StarStock 关注股票，去重
  2. 清空 StockQualityValue 集合
  3. 逐只触发分析（每只 log 包含 URL/参数/结果）
"""
import asyncio
import logging
from datetime import datetime

import httpx
from prefect import flow, task, get_run_logger

from flows.config import RAILWAY_API, QUALITY_CONCURRENCY
from flows.stocks_from_ai import all_quality_value_stocks
from flows.db import get_db
from flows.notify import send_text_message

logger = logging.getLogger(__name__)

# 单只股票的重试配置
_QV_MAX_RETRIES = 1
_QV_RETRY_DELAY = 5
_QV_TIMEOUT = 120


@task(retries=2, retry_delay_seconds=5)
def get_stared_stocks() -> list[dict]:
    """从数据库 StarStock 集合获取用户关注的股票。"""
    db = get_db()
    docs = db["StarStock"].find({}, {"stockCode": 1, "stockName": 1, "_id": 0})
    return [
        {"code": d.get("stockCode"), "name": d.get("stockName") or d.get("stockCode")}
        for d in docs
        if d.get("stockCode")
    ]


@task
def clear_quality_value_collection() -> int:
    """清空 StockQualityValue 集合。"""
    db = get_db()
    result = db["StockQualityValue"].delete_many({})
    return result.deleted_count


# ───────── 单只股票处理（不产生独立 flow run，log 集中到主 flow run）

async def send_quality_request(stock: dict) -> bool:
    """触发单只股票的优质低价分析。

    注意：不使用 @flow 装饰器，所有 log 直接写入主 flow run 的日志中。
    手动实现重试/超时。

    该下游接口同步处理单只分析，耗时常 >60s，会被服务端 nginx 60s 切断返回 504，
    但分析在连接期间已执行。复刻原 JS 行为：保持连接让下游完成工作，但把 504 /
    读超时都视为"已触发成功"，不当失败处理。
    """
    run_logger = get_run_logger()
    code = stock["code"]
    name = stock.get("name", code)

    url = f"{RAILWAY_API}/api/emit/quality-value"
    params = {"stockCode": code, "stockName": name}
    run_logger.info("【触发】GET %s  (code=%s, name=%s)", url, code, name)

    timeout = httpx.Timeout(connect=10.0, read=75.0, write=10.0, pool=10.0)
    success = False

    for attempt in range(_QV_MAX_RETRIES + 1):
        attempt_info = f"(第 {attempt + 1}/{_QV_MAX_RETRIES + 1} 次尝试)"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
                try:
                    await asyncio.wait_for(client.get(url, params=params), timeout=_QV_TIMEOUT)
                    run_logger.info("【完成】%s(%s) %s", name, code, attempt_info)
                    success = True
                    break
                except (asyncio.TimeoutError, httpx.ReadTimeout):
                    run_logger.info(
                        "【超时】%s(%s) 读超时（%s），下游仍在后台处理，视为已触发: %s",
                        name, code, attempt_info, url,
                    )
                    success = True
                    break
                except httpx.HTTPStatusError as exc:
                    run_logger.warning("【HTTP 异常】%s(%s) %s: %s", name, code, attempt_info, exc)
                    if attempt < _QV_MAX_RETRIES:
                        await asyncio.sleep(_QV_RETRY_DELAY)
                        continue
                    break
        except httpx.ConnectError as exc:
            run_logger.warning("【网络异常】%s(%s) %s: %s", name, code, attempt_info, exc)
            if attempt < _QV_MAX_RETRIES:
                await asyncio.sleep(_QV_RETRY_DELAY)
                continue
            break
        except Exception as exc:  # noqa: BLE001 — 兜底
            run_logger.warning("【请求异常】%s(%s) %s: %s", name, code, attempt_info, exc)
            if attempt < _QV_MAX_RETRIES:
                await asyncio.sleep(_QV_RETRY_DELAY)
                continue
            break

    if not success:
        run_logger.error("【失败】%s(%s) 所有重试失败: %s", name, code, url)
        return False

    # 入库（为该股票生成一条 StockQualityValue 记录）
    now = datetime.now().isoformat()
    doc = {
        "code": code,
        "name": name,
        "createdAt": now,
        "updatedAt": now,
        "triggerUrl": url,
    }
    db = get_db()
    coll = db["StockQualityValue"]
    coll.update_one({"code": code}, {"$set": doc}, upsert=True)

    return True


# ───────── 主 flow

@flow(
    name="quality-value",
)
async def process_quality_value() -> dict:
    run_logger = get_run_logger()
    ai_stocks = all_quality_value_stocks()
    stared = get_stared_stocks()

    merged = {s["code"]: s for s in [*ai_stocks, *stared]}
    all_stocks = list(merged.values())
    total = len(all_stocks)
    run_logger.info("优质低价：去重后共 %d 只股票", total)

    deleted = clear_quality_value_collection()
    run_logger.info("已清空 StockQualityValue，删除 %d 条", deleted)

    run_logger.info("优质低价：开始触发分析，共 %d 只（并发数 %d）", total, QUALITY_CONCURRENCY)

    sem = asyncio.Semaphore(QUALITY_CONCURRENCY)
    done = 0
    success_count = 0
    lock = asyncio.Lock()

    async def _run(stock: dict) -> bool:
        nonlocal done, success_count
        async with sem:
            try:
                ok = await send_quality_request(stock)
            except Exception as exc:  # noqa: BLE001 — 单只失败不影响其它
                ok = False
                code = stock.get("code", "")
                name = stock.get("name", code)
                run_logger.error("优质低价处理异常 %s(%s): %s", name, code, exc)
        async with lock:
            done += 1
            if ok:
                success_count += 1
            code = stock.get("code", "")
            name = stock.get("name", code)
            run_logger.info(
                "优质低价进度：%d/%d（成功 %d，失败 %d）当前 %s(%s)",
                done, total, success_count, done - success_count, name, code,
            )
        return ok

    outcomes = await asyncio.gather(
        *(_run(stock) for stock in all_stocks),
        return_exceptions=True,
    )
    success = sum(1 for r in outcomes if r is True)
    failed = total - success

    await send_text_message(f"策略：优质低价 任务完成，成功 {success} 只，失败 {failed} 只")
    run_logger.info("优质低价完成：成功 %d，失败 %d", success, failed)
    return {"total": total, "success": success, "failed": failed}
