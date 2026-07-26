"""WebSocket管理器 - 实时推送工单更新"""
import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

MAX_CONNECTIONS_PER_USER = 5


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # user_id -> set of websocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """接受WebSocket连接，超过每用户上限时拒绝"""
        if user_id not in self._connections:
            self._connections[user_id] = set()
        if len(self._connections[user_id]) >= MAX_CONNECTIONS_PER_USER:
            await websocket.close(code=1008, reason="连接数超限")
            logger.warning(f"用户 {user_id} WebSocket 连接数超限 ({MAX_CONNECTIONS_PER_USER})")
            return
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.info(f"用户 {user_id} 建立WebSocket连接, 当前连接数: {self.total_connections}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        """断开连接"""
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.info(f"用户 {user_id} 断开WebSocket连接, 当前连接数: {self.total_connections}")

    async def send_to_user(self, user_id: int, message: dict):
        """发送消息给指定用户的所有连接"""
        connections = self._connections.get(user_id, set())
        if not connections:
            logger.warning(f"[WS] 用户 {user_id} 无连接, 跳过发送")
            return
        logger.info(f"[WS] 发送消息给用户 {user_id}, 连接数: {len(connections)}")
        results = await asyncio.gather(
            *[ws.send_json(message) for ws in connections],
            return_exceptions=True,
        )
        # 记录失败的发送
        for ws, r in zip(connections, results):
            if isinstance(r, Exception):
                logger.warning(f"[WS] 发送失败给用户 {user_id}: {r}")
        # 清理断开的连接
        dead = {ws for ws, r in zip(connections, results) if isinstance(r, Exception)}
        for ws in dead:
            connections.discard(ws)

    async def broadcast(self, message: dict):
        """广播消息给所有连接的用户"""
        user_ids = list(self._connections.keys())
        logger.info(f"[WS] broadcast 开始: 用户数={len(user_ids)}, ids={user_ids}, msg_type={message.get('type')}")
        if not user_ids:
            logger.warning("[WS] broadcast: 无在线用户，跳过")
            return
        tasks = [self.send_to_user(uid, message) for uid in user_ids]
        logger.info(f"[WS] broadcast: 准备发送 {len(tasks)} 个任务")
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("[WS] broadcast 完成")

    async def notify_ticket_update(self, ticket_data: dict, target_user_ids: list = None):
        """通知工单更新"""
        message = {
            "type": "ticket_update",
            "data": ticket_data,
        }
        if target_user_ids:
            for uid in target_user_ids:
                await self.send_to_user(uid, message)
        else:
            await self.broadcast(message)

    async def notify_new_ticket(self, ticket_data: dict):
        """通知新工单"""
        msg = {"type": "new_ticket", "data": ticket_data}
        user_ids = list(self._connections.keys())
        logger.debug(f"notify_new_ticket: user_ids={user_ids}, total_connections={self.total_connections}")
        if not user_ids:
            logger.debug("无在线用户，跳过广播")
            return
        for uid in user_ids:
            conns = self._connections.get(uid, set())
            for ws in list(conns):
                try:
                    await ws.send_json(msg)
                    logger.debug(f"发送成功: user_id={uid}")
                except Exception as e:
                    logger.debug(f"发送失败: user_id={uid}, error={e}")
                    conns.discard(ws)

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# 全局单例
ws_manager = ConnectionManager()
