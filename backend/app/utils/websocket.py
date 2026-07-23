"""WebSocket管理器 - 实时推送工单更新"""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # user_id -> set of websocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """接受WebSocket连接"""
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
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
        dead = set()
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.add(ws)
        # 清理断开的连接
        for ws in dead:
            connections.discard(ws)

    async def broadcast(self, message: dict):
        """广播消息给所有连接的用户"""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)

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
        await self.broadcast({
            "type": "new_ticket",
            "data": ticket_data,
        })

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# 全局单例
ws_manager = ConnectionManager()
