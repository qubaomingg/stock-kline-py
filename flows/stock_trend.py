"""全市场趋势分析 Flow。

工作流：
  - market_trend_flow(market_code) → @flow（每市场一个独立 run，flow name 含市场代码）
  - process_single_stock(stock)     → 普通 async 函数（在主 flow run 中输出 log，无独立 run）

每个市场的 flow run 中会输出该市场全部股票的处理 log（URL/参数/结果/重试/失败/进度）。
失败股票的名称和代码会写入 logs/failed_stocks_{market}_{timestamp}.json，便于后续分析。
"""
import asyncio
import json
import logging
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

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

async def process_single_stock(stock: dict) -> tuple[bool, str]:
    """对单只股票触发趋势分析（无重试，失败即记为失败）。

    不使用 @flow 装饰器，所有 log 直接写入当前 flow run 的日志中。

    Returns:
        (是否成功, 失败原因)
    """
    run_logger = get_run_logger()
    code = stock.get("code")
    name = stock.get("name", code)

    url = f"{RAILWAY_API}/api/emit/trend"
    params = {"stockCode": code, "stockName": name}
    run_logger.info("【请求】GET %s  (code=%s, name=%s", url, code, name)

    try:
        async with httpx.AsyncClient(timeout=TREND_HTTP_TIMEOUT, follow_redirects=True) as client:
            resp = await asyncio.wait_for(client.get(url, params=params), timeout=_TREND_TIMEOUT)
            resp.raise_for_status()
            result = resp.json()
            if not result.get("success"):
                reason = "HTTP success=False"
                run_logger.warning("【返回失败】%s(%s): %s, 完整响应=%s", name, code, reason, result)
                return False, reason
            run_logger.info("【成功】%s(%s)", name, code)
            return True, ""

    except asyncio.TimeoutError as exc:
        reason = "请求超时"
        run_logger.warning("【超时】%s(%s): %s", name, code, exc)
    except httpx.TimeoutException as exc:
        reason = "HTTP 超时"
        run_logger.warning("【超时】%s(%s): %s", name, code, exc)
    except httpx.ConnectError as exc:
        reason = "网络连接失败"
        run_logger.warning("【网络异常】%s(%s): %s", name, code, exc)
    except httpx.HTTPStatusError as exc:
        reason = f"HTTP {getattr(exc.response, 'status_code', '?')}"
        run_logger.warning("【HTTP 异常】%s(%s): %s", name, code, exc)
    except (ValueError, KeyError) as exc:
        reason = "JSON 解析失败"
        run_logger.warning("【JSON 解析异常】%s(%s): %s", name, code, exc)
    except Exception as exc:  # noqa: BLE001 — 兜底
        reason = f"{type(exc).__name__}: {exc}"
        run_logger.warning("【请求异常】%s(%s): %s", name, code, exc)

    run_logger.error("【失败】%s(%s): %s", name, code, url)
    return False, reason


# ───────── 单市场 Flow（每市场一个独立 flow run）

@flow(name="market-trend-{market_code}")
async def market_trend_flow(market_code: str) -> dict:
    """处理单个市场。每市场一个独立 flow run。

    Flow name 中 {market_code} 会被 Prefect 自动替换为实际参数值，
    在 UI 中可直接看到 "market-trend-a"、"market-trend-hk"、"market-trend-us" 三个独立 run。

    返回结果中额外包含 failed_stocks 列表，便于排查失败原因。
    """
    run_logger = get_run_logger()
    market_name = MARKET_NAMES.get(market_code, market_code)
    run_logger.info("开始处理市场 %s (%s)", market_code, market_name)

    stocks = await fetch_market_stocks(market_code)
    if not stocks:
        run_logger.warning("市场 %s 无股票数据，跳过", market_name)
        return {"market": market_code, "total": 0, "success": 0, "failed": 0, "failed_stocks": []}

    sem = asyncio.Semaphore(TREND_CONCURRENCY)
    total = len(stocks)
    done = 0
    success_count = 0
    failed_stocks: list[dict] = []  # [{name, code, reason}]
    lock = asyncio.Lock()

    async def _run(stock: dict) -> tuple[bool, str]:
        nonlocal done, success_count
        async with sem:
            code = stock.get("code")
            name = stock.get("name", code)
            try:
                ok, reason = await process_single_stock(stock)
            except Exception as exc:  # noqa: BLE001 — 单只失败不影响其它
                ok, reason = False, f"处理异常: {type(exc).__name__}: {exc}"
                run_logger.error("【异常】股票 %s(%s) 处理失败: %s", code, name, exc)
            async with lock:
                done += 1
                if ok:
                    success_count += 1
                else:
                    failed_stocks.append({"name": name, "code": code, "reason": reason})
                run_logger.info(
                    "【%s】进度：%d/%d（成功 %d，失败 %d）当前 %s(%s)",
                    market_name, done, total, success_count, done - success_count, name, code,
                )
            return ok, reason

    run_logger.info("【%s】开始处理 %d 只股票（并发数 %d）", market_name, total, TREND_CONCURRENCY)

    outcomes = await asyncio.gather(*(_run(s) for s in stocks), return_exceptions=True)
    success = sum(1 for r in outcomes if isinstance(r, tuple) and r[0] is True)
    failed = total - success

    run_logger.info(
        "【%s】完成：成功 %d，失败 %d，共 %d",
        market_name, success, failed, total,
    )

    # 打印失败股票（用分隔符突出显示，便于在日志中直接检索）
    if failed_stocks:
        run_logger.info("=" * 80)
        run_logger.info("【%s】失败股票共 %d 只，完整列表:", market_name, failed)
        # 按每 10 只一行打印，便于阅读
        for i in range(0, len(failed_stocks), 10):
            batch = failed_stocks[i:i + 10]
            names_line = ", ".join(f"{s['name']}({s['code']})" for s in batch)
            run_logger.info("  [%d-%d] %s", i + 1, min(i + 10, failed), names_line)
        run_logger.info("=" * 80)

    # 将失败股票写入 JSON 文件（便于后续分析）
    if failed_stocks:
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = logs_dir / f"failed_stocks_{market_code}_{ts}.json"
            with open(output_path, "w", encoding="utf-8") as fp:
                json.dump(
                    {
                        "market": market_code,
                        "market_name": market_name,
                        "total": total,
                        "success": success,
                        "failed": failed,
                        "timestamp": datetime.utcnow().isoformat(),
                        "failed_stocks": failed_stocks,
                        "reason_summary": {
                            reason: sum(1 for s in failed_stocks if s["reason"] == reason)
                            for reason in set(s["reason"] for s in failed_stocks)
                        },
                    },
                    fp,
                    ensure_ascii=False,
                    indent=2,
                )
            # 同时写一份最新的简化版
            latest_path = logs_dir / f"failed_stocks_{market_code}_latest.json"
            with open(latest_path, "w", encoding="utf-8") as fp:
                json.dump(
                    {
                        "market": market_code,
                        "market_name": market_name,
                        "total": total,
                        "success": success,
                        "failed": failed,
                        "timestamp": datetime.utcnow().isoformat(),
                        "failed_stocks": failed_stocks,
                    },
                    fp,
                    ensure_ascii=False,
                    indent=2,
                )
            run_logger.info("【%s】失败股票已保存到: %s", market_name, output_path)
        except Exception as exc:  # noqa: BLE001
            run_logger.warning("写入失败股票文件时出错: %s", exc)

    # 日志中汇总失败原因 Top N
    if failed_stocks:
        reason_counter = Counter(s["reason"] for s in failed_stocks)
        run_logger.info("【%s】失败原因 TOP 5: %s", market_name, reason_counter.most_common(5))
        # 列出前 20 只失败股票
        run_logger.info(
            "【%s】失败股票列表(前 20): %s",
            market_name,
            [f"{s['name']}({s['code']})" for s in failed_stocks[:20]],
        )

    return {
        "market": market_code,
        "market_name": market_name,
        "total": total,
        "success": success,
        "failed": failed,
        "failed_stocks": failed_stocks,
    }


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
                {"market": market_code, "total": 0, "success": 0, "failed": 0, "error": str(exc), "failed_stocks": []}
            )

    total = sum(r["total"] for r in results)
    success = sum(r["success"] for r in results)
    failed = sum(r["failed"] for r in results)

    # 汇总失败股票信息
    all_failed = []
    for r in results:
        failed_list = r.get("failed_stocks", [])
        for s in failed_list:
            all_failed.append({**s, "market": r.get("market", market_code)})

    # 打印所有失败股票（醒目分隔符，便于直接从日志中检索）
    if all_failed:
        run_logger.info("=" * 80)
        run_logger.info("【全市场汇总】失败股票共 %d 只，完整列表:", len(all_failed))
        # 按市场分组打印
        by_market = defaultdict(list)
        for s in all_failed:
            by_market[s.get("market", "unknown")].append(s)
        for mkt, stocks in sorted(by_market.items()):
            mkt_name = MARKET_NAMES.get(mkt, mkt)
            run_logger.info("--- %s (%d 只) ---", mkt_name, len(stocks))
            for i in range(0, len(stocks), 10):
                batch = stocks[i:i + 10]
                names_line = ", ".join(f"{s['name']}({s['code']})" for s in batch)
                run_logger.info("  [%d-%d] %s", i + 1, min(i + 10, len(stocks)), names_line)
        run_logger.info("=" * 80)

    summary_parts = [
        f"策略：股票趋势分析完成，共 {total} 只（成功 {success}，失败 {failed}）",
        f"市场：{'、'.join(MARKET_NAMES.get(c, c) for c in selected_markets)}",
    ]
    if all_failed:
        summary_parts.append(f"失败股票 {len(all_failed)} 只，示例:")
        for s in all_failed[:10]:
            summary_parts.append(f"  - {s.get('name', '')}({s.get('code', '')}) [{s.get('reason', '')}]")
        if len(all_failed) > 10:
            summary_parts.append(f"  ... 还有 {len(all_failed) - 10} 只")
        # 保存全量失败到总文件
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            all_path = logs_dir / f"failed_stocks_all_{ts}.json"
            with open(all_path, "w", encoding="utf-8") as fp:
                json.dump(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "total": total,
                        "success": success,
                        "failed_total": failed,
                        "markets": results,
                        "failed_stocks": all_failed,
                    },
                    fp,
                    ensure_ascii=False,
                    indent=2,
                )
            run_logger.info("全市场失败股票汇总已保存到: %s", all_path)
        except Exception as exc:  # noqa: BLE001
            run_logger.warning("写入全市场失败股票文件时出错: %s", exc)

    summary = "\n".join(summary_parts)
    await send_text_message(summary)
    run_logger.info(summary)
    return results
