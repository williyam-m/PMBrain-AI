"""
WebSocket consumer for real-time updates.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PMBrainConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time updates.
    Handles: AI job status, new insights, scoring updates, spec progress.
    """

    async def connect(self):
        self.project_id = self.scope['url_route']['kwargs'].get('project_id', 'general')
        self.room_group_name = f'project_{self.project_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to PMBrain AI - Project {self.project_id}',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """Handle incoming messages from client."""
        data = json.loads(text_data)
        msg_type = data.get('type', 'message')

        # Broadcast to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'broadcast_message',
                'message': data,
            }
        )

    # Handler methods for different message types
    async def agent_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'agent_update',
            'data': event['message'],
        }))

    async def insight_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'insight_update',
            'data': event['message'],
        }))

    async def opportunity_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'opportunity_update',
            'data': event['message'],
        }))

    async def spec_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'spec_update',
            'data': event['message'],
        }))

    async def notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['message'],
        }))

    async def broadcast_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'broadcast',
            'data': event['message'],
        }))
