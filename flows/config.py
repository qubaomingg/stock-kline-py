"""Flow 运行时配置：集中读取环境变量，避免散落在各处。"""
import os
from dotenv import load_dotenv

load_dotenv()

# 下游高频分析服务（Railway），负责实际的 AI 分析逻辑
RAILWAY_API = os.environ.get("RAIL_WAY_API", "http://frequent-api.lanren.site")

# Python 股票数据服务（本服务自身），用于获取全市场股票列表
PYTHON_API_URL = os.environ.get("PYTHON_API_URL", "https://kline-aliyun.lanren.site")

# MongoDB 连接串
MONGO_URI = os.environ.get("DIRECT_URL")

# 飞书通知
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")
FEISHU_DEFAULT_RECEIVE_ID = os.environ.get("FEISHU_DEFAULT_RECEIVE_ID", "37637e1f")

# 全市场趋势分析：每个市场列表
MARKET_CODES = ["a", "hk", "us"]
MARKET_NAMES = {"a": "A股", "hk": "港股", "us": "美股"}

# 并发与重试调优
# 趋势分析：单市场内部并发处理。三市场之间保持串行，避免叠加压力
TREND_CONCURRENCY = int(os.environ.get("TREND_CONCURRENCY", "5"))
QUALITY_CONCURRENCY = int(os.environ.get("QUALITY_CONCURRENCY", "3"))
HTTP_TIMEOUT = float(os.environ.get("FLOW_HTTP_TIMEOUT", "60"))
# trend 单只分析耗时长，给更宽松的超时
TREND_HTTP_TIMEOUT = float(os.environ.get("TREND_HTTP_TIMEOUT", "120"))
