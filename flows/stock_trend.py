"""全市场趋势分析 Flow。

工作流：
  - market_trend_flow(market_code) → @flow（每市场一个独立 run，flow name 含市场代码）
  - process_single_stock(stock)     → 普通 async 函数（在主 flow run 中输出 log，无独立 run）

每个市场的 flow run 中会输出该市场全部股票的处理 log（URL/参数/结果/重试/失败/进度）。
"""
import asyncio
import logging

import httpx
from prefect import flow, task, get_run_logger

from flows.config import (
    PYTHON_API_URL,
    RAILWAY_API,
    MARKET_CODES,
    MARKET_NAMES,
    TREND_CONCURRENCY,
    TREND_HTTP_TIMEOUT,
)
from flows.notify import send_text_message

logger = logging.getLogger(__name__)
_TREND_TIMEOUT = 120


@task(retries=2, retry_delay_seconds=5, timeout_seconds=360)
async def fetch_market_stocks(market_code: str) -> list[dict]:
    """获取指定市场全部股票列表（调用本服务的 /api/stock/market）。"""
    run_logger = get_run_logger()
    url = f"{PYTHON_API_URL}/api/stock/market?marketCode={market_code}"
    run_logger.info("获取市场 %s 股票列表: %s", market_code, url)
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    stocks = data.get("stocks", []) or []
    run_logger.info("市场 %s 共 %d 只股票", market_code, len(stocks))
    return stocks


# ───────── 单只股票处理（不产生独立 flow run，log 集中到所在市场的 flow run）

async def process_single_stock(stock: dict) -> bool:
    """对单只股票触发趋势分析（无重试，失败即记为失败）。

    不使用 @flow 装饰器，所有 log 直接写入当前 flow run 的日志中。
    """
    run_logger = get_run_logger()
    code = stock.get("code")
    name = stock.get("name", code)

    url = f"{RAILWAY_API}/api/emit/trend"
    params = {"stockCode": code, "stockName": name}
    run_logger.info("【请求】GET %s  (code=%s, name=%s)", url, code, name)

    try:
        async with httpx.AsyncClient(timeout=TREND_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await asyncio.wait_for(client.get(url, params=params), timeout=_TREND_TIMEOUT)
            # HTTP 状态检查
            resp.raise_for_status()

            # JSON 解析 + success 检查
            result = resp.json()
            if not result.get("success"):
                run_logger.warning("【返回失败】%s(%s): success=False, 完整响应=%s", name, code, result)
                return False
            run_logger.info("【成功】%s(%s)", name, code)
            return True

    except httpx.HTTPStatusError as exc:
        run_logger.warning("【HTTP 异常】%s(%s): %s", name, code, exc)
    except (asyncio.TimeoutError, httpx.TimeoutException) as exc:
        run_logger.warning("【超时】%s(%s): %s", name, code, exc)
    except httpx.ConnectError as exc:
        run_logger.warning("【网络异常】%s(%s): %s", name, code, exc)
    except (ValueError, KeyError) as exc:
        run_logger.warning("【JSON 解析异常】%s(%s): %s", name, code, exc)
    except Exception as exc:  # noqa: BLE001 — 兜底
        run_logger.warning("【请求异常】%s(%s): %s", name, code, exc)

    run_logger.error("【失败】%s(%s): %s", name, code, url)
    return False


# ───────── 单市场 Flow（每市场一个独立 flow run）

@flow(name="market-trend-{market_code}")
async def market_trend_flow(market_code: str) -> dict:
    """处理单个市场。每市场一个独立 flow run。

    Flow name 中 {market_code} 会被 Prefect 自动替换为实际参数值，
    在 UI 中可直接看到 "market-trend-a"、"market-trend-hk"、"market-trend-us" 三个独立 run。
    """
    run_logger = get_run_logger()
    market_name = MARKET_NAMES.get(market_code, market_code)
    run_logger.info("开始处理市场 %s (%s)", market_code, market_name)

    stocks = await fetch_market_stocks(market_code)
    if not stocks:
        run_logger.warning("市场 %s 无股票数据，跳过", market_name)
        return {"market": market_code, "total": 0, "success": 0, "failed": 0}

    sem = asyncio.Semaphore(TREND_CONCURRENCY)
    total = len(stocks)
    done = 0
    success_count = 0
    lock = asyncio.Lock()

    async def _run(stock: dict) -> bool:
        nonlocal done, success_count
        async with sem:
            code = stock.get("code")
            name = stock.get("name", code)
            try:
                ok = await process_single_stock(stock)
            except Exception as exc:  # noqa: BLE001 — 单只失败不影响其它
                ok = False
                run_logger.error("【异常】股票 %s(%s) 处理失败: %s", code, name, exc)
            async with lock:
                done += 1
                if ok:
                    success_count += 1
                run_logger.info(
                    "【%s】进度：%d/%d（成功 %d，失败 %d）当前 %s(%s)",
                    market_name, done, total, success_count, done - success_count, name, code,
                )
            return ok

    run_logger.info("【%s】开始处理 %d 只股票（并发数 %d）", market_name, total, TREND_CONCURRENCY)

    outcomes = await asyncio.gather(*(_run(s) for s in stocks), return_exceptions=True)
    success = sum(1 for r in outcomes if r is True)
    failed = total - success

    run_logger.info(
        "【%s】完成：成功 %d，失败 %d，共 %d",
        market_name, success, failed, total,
    )
    return {"market": market_code, "total": total, "success": success, "failed": failed}


# ───────── 全市场调度（不产生独立 flow run，只在 daily-scheduler 的 run 中记录）

async def process_all_markets_stock_trend(markets: list[str] | None = None) -> list[dict]:
    """全市场趋势分析调度器：串行触发 a/hk/us 三个 market-trend-{code} flow。

    Args:
        markets: 要处理的市场列表，None 或 ["a","hk","us"；
                 None 表示全量（a/hk/us）。

    注意：本函数不是 @flow 装饰的，不会产生独立 flow run。
    它直接由 daily_flow 调用，每个 market 的处理会各自产生独立 run。
    """
    run_logger = get_run_logger()
    if not markets:
        selected_markets = list(MARKET_CODES)
    else:
        selected_markets = [m for m in markets if m in MARKET_CODES]
    run_logger.info("开始全市场趋势分析，市场: %s", selected_markets)

    if not selected_markets:
        run_logger.warning("没有合法的市场代码，跳过 trend 不执行")
        return []

    results = []
    for market_code in selected_markets:
        try:
            results.append(await market_trend_flow(market_code))
        except Exception as exc:  # noqa: BLE001 — 单市场失败不应中断其它
            run_logger.error("市场 %s 处理失败: %s", market_code, exc)
            results.append(
                {"market": market_code, "total": 0, "success": 0, "failed": 0, "error": str(exc)}
            )

    total = sum(r["total"] for r in results)
    success = sum(r["success"] for r in results)
    failed = sum(r["failed"] for r in results)
    summary = (
        f"策略：股票趋势分析完成，"
        f"共 {total} 只（成功 {success}，失败 {failed}），"
        f"市场：{'、'.join(MARKET_NAMES.get(c, c) for c in selected_markets)}"
    )
    await send_text_message(summary)
    run_logger.info(summary)
    return results
