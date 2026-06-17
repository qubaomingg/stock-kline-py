"""优质次新分析 Flow。

工作流（所有 log 集中在 quality-newbee 主 flow run 中，不产生子 flow run）：
  1. process_quality_newbee()    —— 主 flow：抓取 IPO 列表 → 汇总 → 逐只处理
  2. newbee_ipo_single(stock)    —— 单只股票的处理（3 步 log 全部在主 flow run 中）
     【1/3 IPO 数据】→ 【2/3 触发分析】→ 【3/3 入库】
"""
import asyncio
import logging
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from prefect import flow, task, get_run_logger

from flows.config import RAILWAY_API, QUALITY_CONCURRENCY, HTTP_TIMEOUT
from flows.db import get_db
from flows.notify import send_text_message

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 单只股票的重试配置
_NEWBEE_MAX_RETRIES = 1
_NEWBEE_RETRY_DELAY = 5
_NEWBEE_TIMEOUT = 120


def _parse_listing_date(s: str) -> datetime | None:
    """解析富途上市日期。富途返回格式为 2026/06/12，也兼容 ISO 横杠格式。"""
    s = (s or "").strip()
    if not s:
        return None
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _parse_futu_ipo(html: str, market: str) -> list[dict]:
    """解析富途 IPO 页面，仅保留最近两周上市的新股。"""
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".list-item")
    two_weeks_ago = datetime.now() - timedelta(days=14)
    result = []
    for item in items:
        def text(sel: str) -> str:
            el = item.select_one(sel)
            return el.get_text(strip=True) if el else ""

        symbol = text(".code")
        name = text(".name")
        listing_date_str = text(".value-listingDate")
        if not symbol or not name:
            continue
        listing_date = _parse_listing_date(listing_date_str)
        if listing_date is None or listing_date < two_weeks_ago:
            continue
        result.append(
            {
                "symbol": symbol,
                "name": name,
                "price": text(".value-price"),
                "firstDayChange": text(".value-firstDayPcr"),
                "totalChange": text(".value-ipoPriceChangeRatio"),
                "listingDate": listing_date_str,
                "market": market,
                "extractedAt": datetime.now().isoformat(),
            }
        )
    return result


@task(retries=2, retry_delay_seconds=5, timeout_seconds=120)
async def scrape_ipo(market: str) -> list[dict]:
    """抓取指定市场（us/hk）的 IPO 列表。"""
    run_logger = get_run_logger()
    url = f"https://www.futunn.com/quote/{market}/ipo"
    run_logger.info("抓取 %s IPO 列表: %s", market, url)
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=_HEADERS, verify=False, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text
    stocks = _parse_futu_ipo(html, market)
    run_logger.info("市场 %s 抓取到 %d 只次新股", market, len(stocks))
    return stocks


# ───────── 单只次新股处理（不产生独立 flow run，log 集中到主 flow run）

async def newbee_ipo_single(stock: dict) -> bool:
    """单只次新股处理：记录 IPO 数据 → 触发分析 → 单条入库。

    注意：不使用 @flow 装饰器，所有 log 直接写入主 flow run 的日志中。
    手动实现重试/超时。
    """
    run_logger = get_run_logger()
    symbol = stock["symbol"]
    name = stock.get("name", symbol)
    market = stock.get("market", "")
    listing_date = stock.get("listingDate", "")
    price = stock.get("price", "")
    first_day_change = stock.get("firstDayChange", "")
    total_change = stock.get("totalChange", "")

    # Step 1: 记录该股票的 IPO 数据
    run_logger.info(
        "【1/3 IPO 数据】%s(%s) 市场=%s 上市=%s 价格=%s 首日涨跌幅=%s 累计涨跌幅=%s",
        name, symbol, market, listing_date, price, first_day_change, total_change,
    )

    # Step 2: 触发分析（手动重试）
    url = f"{RAILWAY_API}/api/emit/newbee?code={symbol}"
    run_logger.info(
        "【2/3 触发分析】GET %s  (symbol=%s, name=%s)",
        url, symbol, name,
    )
    timeout = httpx.Timeout(connect=10.0, read=75.0, write=10.0, pool=10.0)

    success = False
    for attempt in range(_NEWBEE_MAX_RETRIES + 1):
        attempt_info = f"(第 {attempt + 1}/{_NEWBEE_MAX_RETRIES + 1} 次尝试)"
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False, follow_redirects=True) as client:
                try:
                    await asyncio.wait_for(client.get(url), timeout=_NEWBEE_TIMEOUT)
                    run_logger.info("【2/3 触发分析】完成 %s %s", url, attempt_info)
                    success = True
                    break
                except asyncio.TimeoutError:
                    run_logger.info(
                        "【2/3 触发分析】读超时（%s），下游仍在后台处理，视为已触发: %s",
                        attempt_info, url,
                    )
                    success = True
                    break
                except httpx.ReadTimeout:
                    run_logger.info(
                        "【2/3 触发分析】读超时（%s），下游仍在后台处理，视为已触发: %s",
                        attempt_info, url,
                    )
                    success = True
                    break
                except httpx.HTTPStatusError as exc:
                    run_logger.warning("【2/3 触发分析】HTTP 状态异常 %s: %s", attempt_info, exc)
                    if attempt < _NEWBEE_MAX_RETRIES:
                        await asyncio.sleep(_NEWBEE_RETRY_DELAY)
                        continue
                    break
        except httpx.ConnectError as exc:
            run_logger.warning("【2/3 触发分析】网络连接失败 %s: %s", attempt_info, exc)
            if attempt < _NEWBEE_MAX_RETRIES:
                await asyncio.sleep(_NEWBEE_RETRY_DELAY)
                continue
            break
        except Exception as exc:  # noqa: BLE001 — 兜底
            run_logger.warning("【2/3 触发分析】请求异常 %s: %s", attempt_info, exc)
            if attempt < _NEWBEE_MAX_RETRIES:
                await asyncio.sleep(_NEWBEE_RETRY_DELAY)
                continue
            break

    if not success:
        run_logger.error("【2/3 触发分析】所有重试失败: %s", url)
        return False

    # Step 3: 单条写入 StockNewBee
    run_logger.info("【3/3 入库】写入 StockNewBee 集合 (%s)", symbol)
    now = datetime.now().isoformat()
    doc = {
        **stock,
        "createdAt": now,
        "updatedAt": now,
    }
    db = get_db()
    coll = db["StockNewBee"]
    coll.update_one(
        {"symbol": symbol},
        {"$set": doc},
        upsert=True,
    )
    run_logger.info("【3/3 入库】完成: %s(%s)", name, symbol)
    return True


# ───────── 主 flow

@flow(
    name="quality-newbee",
)
async def process_quality_newbee() -> dict:
    run_logger = get_run_logger()

    # Step 1: 批量抓取 US / HK 两个市场的 IPO 列表
    run_logger.info("次新股开始抓取：拉取 US / HK 两个市场的 IPO 列表")
    us_stocks, hk_stocks = await asyncio.gather(scrape_ipo("us"), scrape_ipo("hk"))
    all_stocks = [*us_stocks, *hk_stocks]
    total = len(all_stocks)
    run_logger.info(
        "抓取完成：共 %d 只次新股（美股 %d，港股 %d），开始分发分析",
        total, len(us_stocks), len(hk_stocks),
    )

    # Step 2: 清理旧数据（为了确保数据新鲜，先清空；每只负责自己的 upsert）
    db = get_db()
    coll = db["StockNewBee"]
    deleted = coll.delete_many({})
    run_logger.info("已清空 StockNewBee，删除 %d 条", deleted.deleted_count if hasattr(deleted, 'deleted_count') else 0)

    # Step 3: 逐只处理（并发控制，进度 log 输出到主 flow run）
    sem = asyncio.Semaphore(QUALITY_CONCURRENCY)
    done = 0
    success_count = 0
    lock = asyncio.Lock()

    async def _run(stock: dict) -> bool:
        nonlocal done, success_count
        async with sem:
            try:
                ok = await newbee_ipo_single(stock)
            except Exception as exc:  # noqa: BLE001 — 单只失败不影响其它
                ok = False
                symbol = stock.get("symbol", "")
                name = stock.get("name", symbol)
                run_logger.error("次新股处理异常 %s(%s): %s", name, symbol, exc)
        async with lock:
            done += 1
            if ok:
                success_count += 1
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            run_logger.info(
                "次新股进度：%d/%d（成功 %d，失败 %d）当前 %s(%s)",
                done, total, success_count, done - success_count, name, symbol,
            )
        return ok

    outcomes = await asyncio.gather(
        *(_run(stock) for stock in all_stocks),
        return_exceptions=True,
    )
    success = sum(1 for r in outcomes if r is True)
    failed = total - success

    await send_text_message(
        f"策略：优质次新完成 : 美股 {len(us_stocks)} 条，港股 {len(hk_stocks)} 条，"
        f"共计 {total} 条IPO数据已保存到数据库"
    )
    run_logger.info("优质次新完成：共 %d 只，触发成功 %d，失败 %d", total, success, failed)
    return {"us": len(us_stocks), "hk": len(hk_stocks), "total": total, "success": success, "failed": failed}
