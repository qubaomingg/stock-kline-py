# Prefect Flow 运行架构与使用说明

## 概述

本项目使用 **Prefect 3.x** 作为任务编排引擎，管理三类数据分析任务：

- **优质次新** (newbee) — 扫描最近 14 天上市的新股，触发分析并存库
- **优质低价** (value) — 运行优质低价股策略分析
- **全市场趋势** (trend) — 分别对 A 股/港股/美股三个市场运行趋势分析

所有 Flow **连接线上 Prefect Server** (`https://prefect.lanren.site/api`)，运行记录与日志全部可以在 Prefect UI 中查看。

---

## 架构设计

### Flow 层次结构（当前设计）

```
daily-scheduler                     [顶层调度 Flow, 1 run]
 ├── quality-newbee                 [子 Flow run — 次新主流程]
 ├── quality-value                  [子 Flow run — 优质低价主流程]
 ├── market-trend-a                 [子 Flow run — A 股市场]
 ├── market-trend-hk                [子 Flow run — 港股市场]
 └── market-trend-us                [子 Flow run — 美股市场]
```

### 关键设计决策

| 决策 | 说明 |
|-----|------|
| **单只股票不再产生独立 Flow Run** | 每只股票的处理作为**普通 async 函数**执行，所有日志直接写入其所属主流程 run。避免成千上万只股票产生相同数量的 Flow run 污染 UI。 |
| **趋势按市场拆分为独立 Flow Run** | A 股/港股/美股每个市场一个独立的 `market-trend-{code}` Flow run，便于在 Prefect UI 中按市场查看进度与结果。 |
| **串行执行三类任务** | 优质次新 → 优质低价 → 全市场趋势，**串行执行**。原因：三者都调用下游 `frequent-api`，若并发会叠加压力，导致 nginx 60s 超时 (504)。 |
| **单个市场内部并发可控** | 单个市场内的股票处理用 `asyncio.Semaphore` 控制并发度（见 `QUALITY_CONCURRENCY` / 趋势内部默认串行）。 |
| **PM2 守护常驻 serve 进程** | 本地不再启动 Prefect Server，仅一个 `stock-prefect-serve` 进程连线上 Server 注册 cron 调度并执行 Flow。 |

### 日志设计

- **单只股票**的请求 URL / 参数 / 结果 / 重试信息全部以 INFO / WARNING 级别写入**其所属主流程 run 的日志流**。
- **每只股票**处理结束后，主流程 log 中会出现进度信息，例如：
  ```
  次新股进度：1/28（成功 1，失败 0）当前 阿里巴巴(BABA)
  优质低价进度：5/82（成功 5，失败 0）当前 贵州茅台(600519)
  【A股】进度：123/5527（成功 123，失败 0）当前 浦发银行(600000)
  ```

---

## 运行方式

### 命令总览

使用项目根目录的 `start-prefect.sh`：

```bash
./start-prefect.sh start      # 启动常驻 PM2 守护进程（每天 01:00 自动全量触发）
./start-prefect.sh stop       # 停止 serve 进程
./start-prefect.sh restart    # 重启 serve 进程
./start-prefect.sh status     # 查看 PM2 状态和最近日志
./start-prefect.sh logs       # 查看 serve 进程最近 100 行日志

./start-prefect.sh run              # 立即手动跑一次（全量三类任务）
./start-prefect.sh run newbee       # 立即手动跑一次（只跑优质次新）
./start-prefect.sh run value        # 立即手动跑一次（只跑优质低价）
./start-prefect.sh run trend        # 立即手动跑一次（只跑全市场趋势）
./start-prefect.sh run newbee value # 立即手动跑一次（跑指定多个任务）
```

### 支持的任务类型

| 关键字 | 中文名称 | 说明 |
|-------|---------|------|
| `newbee` | 优质次新 | 抓取最近 14 天 IPO（A 股/港股/美股）→ 触发分析 → 写入 `StockNewBee` 集合 |
| `value` | 优质低价 | 从 `stocks_from_ai` 预定义池 + `StarStock` 关注池 → 去重 → 触发分析 → 写入 `StockQualityValue` 集合 |
| `trend` | 全市场趋势 | 分 `a` / `hk` / `us` 三个市场独立 run：拉股票列表 → 逐只触发趋势分析 |

### 直接用 Python 调用（调试用）

```bash
# 全量
./venv/bin/python -m flows.daily run

# 按类型
./venv/bin/python -m flows.daily run newbee
./venv/bin/python -m flows.daily run value
./venv/bin/python -m flows.daily run trend
./venv/bin/python -m flows.daily run newbee value
```

---

## 文件结构

```
stock-kline-py/
 ├── flows/
 │    ├── daily.py              # 顶层调度 Flow (daily-scheduler)
 │    ├── quality_newbee.py     # 优质次新 Flow + 单只处理
 │    ├── quality_value.py      # 优质低价 Flow + 单只处理
 │    ├── stock_trend.py        # 全市场趋势 Flow（按市场拆分）
 │    ├── config.py             # 配置（API 地址、并发数等）
 │    ├── db.py                 # MongoDB 连接
 │    ├── notify.py             # 飞书通知
 │    └── stocks_from_ai.py     # 次新/低价预定义股票池
 ├── start-prefect.sh           # PM2 进程管理脚本（主入口）
 ├── requirements.txt
 └── README.md
```

### 关键配置项（`flows/config.py`）

| 变量 | 说明 | 默认值 |
|-----|------|--------|
| `RAILWAY_API` | 下游分析 API（frequent-api 部署） | `http://frequent-api.lanren.site`（可被 `RAIL_WAY_API` 环境变量覆盖） |
| `PYTHON_API_URL` | 本地 Python 股票基础数据 API | `http://localhost:8000`（可被环境变量覆盖为 `http://kline-aliyun.lanren.site/api`） |
| `QUALITY_CONCURRENCY` | 次新/低价单只处理并发数 | `3` |
| `TREND_CONCURRENCY` | 趋势单市场内部并发数 | `5`（可通过环境变量调整：`1` 串行、`10` 高并发等） |
| `MARKET_CODES` | 趋势分析覆盖的市场列表 | `["a", "hk", "us"]` |
| `MARKET_NAMES` | 市场代码 → 中文名称映射 | `{a: "A股", hk: "港股", us: "美股"}` |
| `TREND_HTTP_TIMEOUT` | 趋势单请求超时 | `120` 秒 |

---

## 各 Flow 详解

### 1. 优质次新 (`quality-newbee`)

**Flow 入口**：`process_quality_newbee()`

**处理流程**：

```
① 抓取 IPO 列表（US / HK 两个市场，最近 14 天）
   └─ fetch: futunn.com 列表页 → BeautifulSoup 解析
② 清空 `StockNewBee` 集合（确保数据新鲜）
③ 逐只处理（每只一个 newbee-ipo 单元，但不产生独立 Flow Run）：
   ├── 【1/3 IPO 数据】记录股票代码、名称、上市日期、首日涨幅
   ├── 【2/3 触发分析】GET RAILWAY_API + "?code={symbol}"
   │     └─ 504 / 读超时 → 视为成功（下游已在处理）
   │     └─ HTTP 异常 → 进入重试（最多 retries=1，延迟 5 秒）
   └── 【3/3 入库】更新 `StockNewBee` 集合
```

**Prefect UI 可见**：1 个 `quality-newbee` Flow run，内部日志包含所有股票的三步过程。

---

### 2. 优质低价 (`quality-value`)

**Flow 入口**：`process_quality_value()`

**处理流程**：

```
① 合并股票池（预定义池 + StarStock 关注池 → 去重）
② 清空 `StockQualityValue` 集合
③ 逐只触发分析（并发度 QUALITY_CONCURRENCY = 3）：
   ├── 请求: GET RAILWAY_API + "?stockCode={code}&stockName={name}"
   ├── 超时/504 → 视为成功
   └── 每条结果写入 `StockQualityValue` 集合
```

**Prefect UI 可见**：1 个 `quality-value` Flow run。

---

### 3. 全市场趋势 (`market-trend-*`)

**Flow 入口**：`market_trend_flow(market_code)`

每个市场一个独立 Flow run（在 Prefect UI 中可分别查看）：

```
market-trend-a    ← A 股市场
market-trend-hk   ← 港股市场
market-trend-us   ← 美股市场
```

**每市场内部流程**：

```
① 拉股票列表 (GET PYTHON_API_URL/stock/market?marketCode={code})
② 逐只并行触发趋势分析（`TREND_CONCURRENCY=5`，默认 5 路并发。每只一次性尝试，无重试）：
   ├── 【请求】GET RAILWAY_API + "?stockCode={code}&stockName={name}"
   ├── 【超时】读超时或 asyncio timeout → 视为失败，直接跳过
   ├── 【HTTP 异常】非 200 → 视为失败，直接跳过
   ├── 【返回失败】success=False → 视为失败，直接跳过
   └── 【成功】/ 失败 → 记录到主流程进度日志
```

**Prefect UI 可见**：3 个 Flow run（`market-trend-a` / `market-trend-hk` / `market-trend-us`）

---

## 调度与 Cron

**定时任务**：每天 **01:00（Asia/Shanghai）** 自动执行 `daily_flow()` — 即按顺序运行：

```
优质次新 → 优质低价 → 全市场趋势(a/hk/us)
```

**注册位置**：`flows/daily.py` 的 `main()` 中 `daily_flow.serve(...)`：

```python
daily_flow.serve(
    name="daily-stock-analysis",
    schedule=Cron("0 1 * * *", timezone="Asia/Shanghai"),
)
```

**启动 Cron**：运行 `./start-prefect.sh start` 后，PM2 守护的 `stock-prefect-serve` 进程会自动连线上 Prefect Server 注册调度并等待触发。

---

## Prefect Server

- **地址**：`https://prefect.lanren.site/api`
- **UI**：`https://prefect.lanren.site`（用于查看 Flow runs、日志、状态）
- **本地配置**：`PREFECT_HOME` 指向项目 `./.prefect` 目录（独立于系统用户配置）

---

## 故障与排查

### 常见问题

| 现象 | 原因 | 排查 |
|-----|------|------|
| **PM2 进程正常但 Prefect UI 看不到 run** | Prefect API 连通性 | `curl https://prefect.lanren.site/api/health` 确认可达 |
| **趋势分析卡在某只股票很久** | 下游 API 慢，触发 nginx 504 | 检查 `RAILWAY_API` 下游服务健康状态；在日志中搜 "超时" |
| **日志中出现大量 `【HTTP 异常】`** | 下游服务不稳定 | 查看 `lanren-railway-api` / frequent-api 部署状态 |
| **Flow run 状态为 Failed** | 某段代码抛异常未被 `except` 捕获 | 打开失败 run 的日志，搜 `Traceback` / `Error` |
| **数据没有写入 MongoDB** | DB 连接或 upsert 失败 | 检查 `DIRECT_URL` 环境变量；检查集合是否被意外清空 |

### 手动触发单个任务

```bash
cd stock-kline-py
./start-prefect.sh run newbee    # 只跑次新（最快，几分钟内有结果）
./start-prefect.sh run value     # 只跑低价
./start-prefect.sh run trend     # 只跑趋势（耗时最久）
```

---

## 历史架构变更（为何改成现在这样）

| 变更点 | 旧设计 | 新设计 | 原因 |
|-------|--------|--------|------|
| **单只股票 Flow Run** | 每只股票独立 Flow run（newbee-single / trend-single 等） | 普通 async 函数，日志汇总到主流程 run | 5000+ 只股票产生 5000+ Flow run，Prefect UI 被淹没 |
| **趋势市场拆分** | 全市场在一个 `all-markets-trend` run 中 | 每个市场独立 `market-trend-{code}` run | 便于按市场查看进度、单独重跑失败市场 |
| **本地 Prefect Server** | 本地起 `127.0.0.1:4200` server | 直接连线上 `prefect.lanren.site/api` | 简化部署、统一 UI |

---

## 参考文件

| 文件 | 作用 |
|-----|------|
| `flows/daily.py` | 顶层调度 + 命令行参数解析 + serve/cron 注册 |
| `flows/quality_newbee.py` | 次新 Flow + IPO 抓取 + 单只处理 |
| `flows/quality_value.py` | 低价 Flow + 股票池合并 + 单只触发 |
| `flows/stock_trend.py` | 全市场趋势 Flow（每市场独立 run） |
| `flows/config.py` | API 地址、并发数、超时等配置 |
| `start-prefect.sh` | PM2 进程管理 + 手动 run 命令 |
