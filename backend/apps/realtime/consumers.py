import json

from channels.generic.websocket import AsyncWebsocketConsumer


class RealtimeConsumer(AsyncWebsocketConsumer):
    """
    One real-time WebSocket connection per authenticated user.

    Group name:
    user_<user_id>
    """

    async def connect(self):
        user = self.scope.get("user")

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        self.user = user
        self.group_name = f"user_{user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        await self.send_json(
            {
                "type": "connected",
                "message": "Realtime connection established.",
                "user_id": user.id,
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name,
            )

    async def receive(self, text_data=None, bytes_data=None):
        """
        Optional ping/pong support.
        """

        try:
            data = json.loads(text_data or "{}")
        except Exception:
            data = {}

        event_type = data.get("type")

        if event_type == "ping":
            await self.send_json(
                {
                    "type": "pong",
                    "message": "ok",
                }
            )

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data, default=str))

    async def realtime_event(self, event):
        """
        Receive event from channel layer and send to WebSocket.
        """

        payload = event.get("payload", {})

        await self.send_json(payload)