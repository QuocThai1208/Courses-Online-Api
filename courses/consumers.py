import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import CommentTopic, Topic

class ForumConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.topic_id = self.scope['url_route']['kwargs']['topic_id']
        self.topic_group_name = f'topic_{self.topic_id}'
        
        # Join topic group
        await self.channel_layer.group_add(
            self.topic_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave topic group
        await self.channel_layer.group_discard(
            self.topic_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'comment')
        
        if message_type == 'new_comment':
            # Broadcast new comment to all users in topic
            await self.channel_layer.group_send(
                self.topic_group_name,
                {
                    'type': 'new_comment_notification',
                    'comment_id': data['comment_id'],
                    'user_name': data['user_name'],
                    'content': data['content'][:100] + '...' if len(data['content']) > 100 else data['content']
                }
            )
    
    async def new_comment_notification(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_comment',
            'comment_id': event['comment_id'],
            'user_name': event['user_name'],
            'content': event['content'],
            'timestamp': event.get('timestamp')
        }))