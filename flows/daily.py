"""每日任务编排 Flow（轻量级调度器：仅负责串行调用三个子 Flow）。

用法：
  # 立即跑一次（完整三个任务）
  ./start-prefect.sh run

  # 立即跑一次（只跑某个类型）
  ./start-prefect.sh run newbee   # 优质次新
  ./start-prefect.sh run value    # 优质低价
  ./start-prefect.sh run trend    # 全市场趋势

  # 启动常驻调度（每天凌晨 1 点北京时间执行）
  ./start-prefect.sh start

  # 直接用 Python 调用（调试）
  ./venv/bin/python -m flows.daily run
  ./venv/bin/python -m flows.daily run newbee
"""
import asyncio
import logging
import sys

from prefect import flow, get_run_logger
from prefect.schedules import Cron

from flows.quality_newbee import process_quality_newbee
from flows.quality_value import process_quality_value
from flows.stock_trend import process_all_markets_stock_trend
from flows.notify import send_text_message

logging.basicConfig(level=logging.INFO)

# 任务类型映射：类型关键字 → (显示名, flow 函数, 描述)
TASK_TYPES = {
    "newbee": ("优质次新", process_quality_newbee, "次新股抓取+分析"),
    "value":  ("优质低价", process_quality_value, "优质低价股分析"),
    "trend": ("全市场趋势", process_all_markets_stock_trend, "a/hk/us 全市场趋势分析"),
}


@flow(name="daily-scheduler")
async def daily_flow(task_types: list[str] | None = None) -> dict:
    """每日任务调度器：按类型串行执行。

    Args:
        task_types: 要运行的任务类型关键字列表，可选值 newbee/value/trend；
                    None 表示全量（三个任务都跑）。

    必须串行：三者都直接打同一个下游 frequent-api，若并发执行会叠加压力，
    把单只本就慢的 trend 接口拖到 nginx 60s 超时（504）。
    """
    run_logger = get_run_logger()

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

    results = {}
    for key in selected:
        name, fn, _ = TASK_TYPES[key]
        try:
            results[name] = await fn()
        except Exception as exc:  # noqa: BLE001 — 单任务失败不影响其它
            run_logger.error("%s 任务失败: %s", name, exc)
            await send_text_message(f"策略：{name} 任务失败 : {exc}")
            results[name] = {"error": str(exc)}

    run_logger.info("调度结束")
    return {k: str(v) for k, v in results.items()}


def _parse_types(args: list[str]) -> tuple[str, list[str] | None]:
    """解析命令行参数，返回 (mode, task_types)。

    规则：
      run                → mode="run", types=None (全量)
      run newbee           → mode="run", types=["newbee"]
      run newbee value     → mode="run", types=["newbee","value"]
      serve                → mode="serve", types=None (全量调度)
    """
    if not args:
        return ("run", None)

    mode = args[0]

    rest = args[1:]
    if not rest:
        return (mode, None)

    types = []
    for t in rest:
        if t not in TASK_TYPES:
            print(f"警告: 未知类型 '{t}' 不在可选类型 {list(TASK_TYPES.keys())}")
            continue
        types.append(t)
    return (mode, types if types else None)


def main():
    mode, task_types = _parse_types(sys.argv[1:])

    if mode == "serve":
        daily_flow.serve(
            name="daily-stock-analysis",
            schedule=Cron("0 1 * * *", timezone="Asia/Shanghai"),
        )
    else:
        asyncio.run(daily_flow(task_types))


if __name__ == "__main__":
    main()
