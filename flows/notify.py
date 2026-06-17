"""飞书文本通知：移植自 lanren-bg-api/utils/feishu.js 的 sendTextMessage。"""
import json
import logging
import httpx

from flows.config import (
    FEISHU_APP_ID,
    FEISHU_APP_SECRET,
    FEISHU_DEFAULT_RECEIVE_ID,
)

logger = logging.getLogger(__name__)


async def _get_access_token() -> str:
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
        resp = await client.post(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            json={"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET},
        )
        resp.raise_for_status()
        return resp.json()["tenant_access_token"]


async def send_text_message(
    text: str,
    receive_id: str = FEISHU_DEFAULT_RECEIVE_ID,
    receive_id_type: str = "user_id",
) -> bool:
    """发送飞书文本消息，失败时仅记录日志、不抛出（通知不应影响主流程）。"""
    try:
        token = await _get_access_token()
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.post(
                f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "receive_id": receive_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text}, ensure_ascii=False),
                },
            )
            resp.raise_for_status()
        logger.info("飞书通知已发送: %s", text)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("发送飞书通知失败: %s", exc)
        return False
