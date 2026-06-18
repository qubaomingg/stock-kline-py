"""每日任务编排 Flow（轻量级调度器：仅负责串行调用三个子 Flow）。

工作流（每日 00:00 Asia/Shanghai 自动触发）：
  1. 优质次新分析 (quality-newbee)    —— 抓取新股 IPO 列表 + 触发分析
  2. 优质低价分析 (quality-value)      —— AI 预设池 + 关注股票
  3. 全市场趋势分析 (market-trend-*)   —— A股/港股/美股 三市场串行执行

所有任务按顺序串行，避免并发叠加打挂下游服务。

用法：
  # 立即跑一次（完整三个任务）
  ./start-prefect.sh run

  # 立即跑一次（只跑某个类型）
  ./start-prefect.sh run newbee   # 优质次新
  ./start-prefect.sh run value    # 优质低价
  ./start-prefect.sh run trend    # 全市场趋势（a/hk/us）

  # trend 支持指定市场：trend 后跟 a/hk/us 任一组合
  ./start-prefect.sh run trend us       # 只跑美股趋势
  ./start-prefect.sh run trend hk       # 只跑港股趋势
  ./start-prefect.sh run trend a        # 只跑 A 股趋势
  ./start-prefect.sh run trend hk us    # 港股 + 美股趋势
  ./start-prefect.sh run trend us newbee  # 美股趋势 + 优质次新

  # 启动常驻调度（每天 00:00 北京时间执行）
  ./start-prefect.sh start

  # 直接用 Python 调用（调试）
  ./venv/bin/python -m flows.daily run
  ./venv/bin/python -m flows.daily run trend us
"""
import asyncio
import logging
import sys
from datetime import datetime

from prefect import flow, get_run_logger
from prefect.schedules import Cron

from flows.quality_newbee import process_quality_newbee
from flows.quality_value import process_quality_value
from flows.stock_trend import process_all_markets_stock_trend
from flows.notify import send_text_message
from flows.config import MARKET_CODES

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# 任务类型映射：类型关键字 → (显示名, flow 函数, 描述)
TASK_TYPES = {
    "newbee": ("优质次新", process_quality_newbee, "次新股抓取+分析"),
    "value":  ("优质低价", process_quality_value, "优质低价股分析"),
    "trend": ("全市场趋势", process_all_markets_stock_trend, "a/hk/us 全市场趋势分析"),
}


@flow(name="daily-scheduler")
async def daily_flow(task_types=None, trend_markets=None):
    """每日任务调度器：按类型串行执行。

    Args:
        task_types: 要运行的任务类型关键字列表，可选值 newbee/value/trend；
                    None 表示全量（三个任务都跑）。
        trend_markets: trend 任务要处理的市场列表（a/hk/us）；
                       None 表示全量市场（a/hk/us）。

    必须串行：三者都直接打同一个下游 frequent-api，若并发执行会叠加压力，
    把单只本就慢的 trend 接口拖到 nginx 60s 超时（504）。
    """
    run_logger = get_run_logger()
    start_time = datetime.now()

    if not task_types:
        selected = list(TASK_TYPES.keys())  # 全量
    else:
        # 去重、保留用户指定顺序
        selected = []
        for t in task_types:
            if t not in selected:
                selected.append(t)

    run_logger.info(
        "开始调度: %s",
        ", ".join(f"{TASK_TYPES[t][0]}({t})" for t in selected),
    )
    if "trend" in selected and trend_markets:
        run_logger.info("趋势市场过滤: %s", ", ".join(trend_markets))

    results = {}
    failed_tasks = []

    for i, key in enumerate(selected, 1):
        name, fn, _ = TASK_TYPES[key]
        task_start = datetime.now()
        run_logger.info("=" * 60)
        run_logger.info("任务 %d/%d: %s 开始", i, len(selected), name)
        run_logger.info("=" * 60)

        try:
            if key == "trend":
                result = await fn(trend_markets)
            else:
                result = await fn()
            results[name] = result
            task_elapsed = (datetime.now() - task_start).total_seconds()
            run_logger.info("✓ %s 完成，耗时 %.1fs", name, task_elapsed)

        except Exception as exc:
            run_logger.error("✗ %s 任务失败: %s", name, exc, exc_info=True)
            await send_text_message(f"策略：{name} 任务失败 : {exc}")
            results[name] = {"error": str(exc)}
            failed_tasks.append(name)

    # 最终汇总
    total_elapsed = (datetime.now() - start_time).total_seconds()
    run_logger.info("=" * 60)
    run_logger.info(
        "调度结束：成功 %d/%d，失败 %d，总耗时 %.1fs",
        len(selected) - len(failed_tasks), len(selected), len(failed_tasks), total_elapsed,
    )
    if failed_tasks:
        run_logger.info("失败任务: %s", ", ".join(failed_tasks))
    run_logger.info("=" * 60)

    return {k: str(v) for k, v in results.items()}


def _parse_types(args):
    """解析命令行参数，返回 (mode, task_types, trend_markets)。

    规则：
      run                    → mode="run", types=None, markets=None（全量）
      run trend              → mode="run", types=["trend"], markets=None（trend 全市场）
      run trend us           → mode="run", types=["trend"], markets=["us"]
      run trend hk a         → mode="run", types=["trend"], markets=["hk","a"]
      run trend us newbee    → mode="run", types=["trend","newbee"], markets=["us"]
      run newbee value       → mode="run", types=["newbee","value"], markets=None
      serve                  → mode="serve", types=None, markets=None（全量调度）

    解析规则：
      - 如果 arg 在 TASK_TYPES 中 → 任务类型
      - 如果 arg 在 MARKET_CODES 中 → trend 的市场过滤参数（必须紧跟 trend 或其他 market code）
      - 其他 → 警告并跳过
    """
    if not args:
        return ("run", None, None)

    mode = args[0]

    rest = args[1:]
    if not rest:
        return (mode, None, None)

    types = []
    trend_markets = []

    for t in rest:
        if t in TASK_TYPES:
            types.append(t)
        elif t in MARKET_CODES:
            # 市场代码：作为 trend 的市场过滤参数
            if t not in trend_markets:
                trend_markets.append(t)
        else:
            print(f"警告: 未知参数 '{t}' 不在可选类型 {list(TASK_TYPES.keys())} 或市场 {MARKET_CODES}")

    task_types = types if types else None
    markets = trend_markets if trend_markets else None
    return (mode, task_types, markets)


def main():
    mode, task_types, trend_markets = _parse_types(sys.argv[1:])

    if mode == "serve":
        import os
        cron_expr = os.environ.get("PREFECT_CRON", "0 0 * * *")
        cron_tz = os.environ.get("PREFECT_CRON_TZ", "Asia/Shanghai")
        logger.info(
            "启动 daily-scheduler，注册到 Prefect Server: 部署名=lanren-daily-scheduler, cron=%s, timezone=%s",
            cron_expr, cron_tz,
        )
        daily_flow.serve(
            name="lanren-daily-scheduler",
            schedule=Cron(cron_expr, timezone=cron_tz),  # 带时区的 Cron 对象
        )
    else:
        # 立即手动跑一次
        logger.info("立即执行 daily_flow，任务=%s，趋势市场=%s", task_types, trend_markets)
        asyncio.run(daily_flow(task_types, trend_markets))


if __name__ == "__main__":
    main()
