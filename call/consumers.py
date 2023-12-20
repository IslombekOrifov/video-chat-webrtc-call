# call/consumers.py
import json
from asgiref.sync import async_to_sync

from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async


from accounts.models import ActiveUser


class CallConsumer(WebsocketConsumer):
    groups_info = {}
    def connect(self):
        self.accept()
        admin =  self.scope['url_route']['kwargs'].get('not_user', False)
        if (admin and admin == 'translator'):
            self.main_user = self.scope['url_route']['kwargs']['username']
            ActiveUser.objects.get_or_create(username=f"{self.scope['url_route']['kwargs']['username']}", is_translator=True)
            self.notify_translator_disconnected()
        elif (admin and admin == 'lawyer'):
            ActiveUser.objects.get_or_create(username=f"{self.scope['url_route']['kwargs']['username']}", is_lawyer=True)
            self.notify_lawyer_disconnected()
        else:
            ActiveUser.objects.get_or_create(username=f"{self.scope['url_route']['kwargs']['username']}")
        
        
        # filtering sending active users data for each users
        active_translators = ActiveUser.objects.filter(is_translator=True).values_list('username', flat=True)
        active_lawyers = ActiveUser.objects.filter(is_lawyer=True).values_list('username', flat=True)
        active_data = (list(active_lawyers) if self.scope['url_route']['kwargs'].get('not_user', False) and self.scope['url_route']['kwargs'].get('not_user') == 'translator' else
          [] if self.scope['url_route']['kwargs'].get('not_user', False) and self.scope['url_route']['kwargs'].get('not_user') == 'lawyer' else
          list(active_translators))

        print(CallConsumer.groups_info)
        # response to client, that we are connected.
        self.send(text_data=json.dumps({
            'type': 'connection',
            'data': {
                'message': "Connected",
                'active_admins': active_data,
            }
        }))


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.my_name,
            self.channel_name
        )
        if hasattr(self, 'main_user'):
            if CallConsumer.groups_info.get(self.main_user, False):
                if self.main_user == self.my_name:
                    second_user = CallConsumer.groups_info[self.main_user].get('second_user', False)
                    third_user = CallConsumer.groups_info[self.main_user].get('third_user', False)
                    if second_user and third_user:
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            second_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            second_user,
                            self.my_name
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            third_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            third_user,
                            self.my_name
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            third_user,
                            second_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            second_user,
                            third_user
                        )
                    elif second_user:
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            second_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            second_user,
                            self.my_name
                        )
                    elif third_user:
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            third_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            third_user,
                            self.my_name
                        )
                    CallConsumer.groups_info.pop(self.main_user)
                elif CallConsumer.groups_info[self.main_user].get('second_user', False) == self.my_name:
                    if CallConsumer.groups_info[self.main_user].get('third_user', False):
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            self.main_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            self.main_user,
                            self.my_name
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            CallConsumer.groups_info[self.main_user].get('third_user')
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            CallConsumer.groups_info[self.main_user].get('third_user'),
                            self.my_name
                        )
                        CallConsumer.groups_info[self.main_user]['second_user'] == CallConsumer.groups_info[self.main_user]['third_user']
                        CallConsumer.groups_info[self.main_user].pop('third_user')
                    else:
                        CallConsumer.groups_info[self.main_user].pop('second_user')
                        async_to_sync(self.channel_layer.group_discard)(
                            self.my_name,
                            self.main_user
                        )
                        async_to_sync(self.channel_layer.group_discard)(
                            self.main_user,
                            self.my_name
                        )
                elif CallConsumer.groups_info[self.main_user].get('third_user', False) == self.my_name:
                    CallConsumer.groups_info[self.main_user].pop('third_user')
                    async_to_sync(self.channel_layer.group_discard)(
                        self.my_name,
                        self.main_user
                    )
                    async_to_sync(self.channel_layer.group_discard)(
                        self.main_user,
                        self.my_name
                    )
                    async_to_sync(self.channel_layer.group_discard)(
                        self.my_name,
                        CallConsumer.groups_info[self.main_user].get('second_user')
                    )
                    async_to_sync(self.channel_layer.group_discard)(
                        CallConsumer.groups_info[self.main_user].get('second_user'),
                        self.my_name
                    )
                
        user = ActiveUser.objects.filter(username=self.my_name).last()
        if user.is_translator:
            user.delete()
            self.notify_translator_disconnected()
        if user.is_lawyer:
            user.delete()
            self.notify_lawyer_disconnected()
        
        
        
    # Receive message from client WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        eventType = text_data_json['type']

        if eventType == 'login':
            name = text_data_json['data']['name']

            # we will use this as room name as well
            self.my_name = name

            # Join room
            async_to_sync(self.channel_layer.group_add)(
                self.my_name,
                self.channel_name
            )
        
        if eventType == 'call':
            name = text_data_json['data']['name']
            print(self.my_name, "is calling", name);
            if not self.scope['url_route']['kwargs'].get('not_user', False):
                self.main_user = name
            async_to_sync(self.channel_layer.group_send)(
                name,
                {
                    'type': 'call_received',
                    'data': {
                        'caller': self.my_name,
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )
        if eventType == 'extra_call':
            name = text_data_json['data']['name']
            print(self.my_name, "is calling", name);
 
            async_to_sync(self.channel_layer.group_send)(
                name,
                {
                    'type': 'extra_call_received',
                    'data': {
                        'caller': self.my_name,
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )

        if eventType == 'answer_call':
            caller = text_data_json['data']['caller']
            caller_room = self.scope['url_route']['kwargs']['username']

            async_to_sync(self.channel_layer.group_add)(caller_room, self.channel_name)
            async_to_sync(self.channel_layer.group_add)(caller, caller_room)

            async_to_sync(self.channel_layer.group_send)(
                caller,
                {
                    'type': 'call_answered',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )
            if self.scope['url_route']['kwargs'].get('not_user', False) == 'translator':
                self.main_user = caller_room
                if CallConsumer.groups_info.get(caller_room, False) and not CallConsumer.groups_info[caller_room].get('third_user', False):
                    CallConsumer.groups_info[caller_room]['third_user'] = caller
                    s_user_username = CallConsumer.groups_info[caller]['second_user']

                    async_to_sync(self.channel_layer.group_add)(caller, s_user_username)
                    async_to_sync(self.channel_layer.group_add)(s_user_username, caller)

                    async_to_sync(self.channel_layer.group_send)(
                        s_user_username,
                        {
                            'type': 'new_call',
                            'data': {
                                'to_user': caller
                            }
                        }
                    )
                    print('Third user worked')
                elif not self.groups_info.get(caller_room, False):
                    CallConsumer.groups_info[self.my_name] = {}
                    CallConsumer.groups_info[self.my_name]['second_user'] = caller
                   
                    
            elif self.scope['url_route']['kwargs'].get('not_user', False) == 'lawyer':
                if hasattr(self, 'main_user'):
                    pass
                else: self.main_user = caller
                if CallConsumer.groups_info.get(self.main_user, False) and not CallConsumer.groups_info[self.main_user].get('third_user', False):
                    CallConsumer.groups_info[self.main_user]['third_user'] = caller_room
                    s_user_username = CallConsumer.groups_info[self.main_user]['second_user']

                    async_to_sync(self.channel_layer.group_add)(caller_room, s_user_username)
                    async_to_sync(self.channel_layer.group_add)(s_user_username, caller_room)

                    async_to_sync(self.channel_layer.group_send)(
                        s_user_username,
                        {
                            'type': 'new_call',
                            'data': {
                                'to_user': caller_room
                            }
                        }
                    )
                    print('Third user worked')
                elif not self.groups_info.get(self.main_user, False):
                    CallConsumer.groups_info[self.main_user] = {}
                    CallConsumer.groups_info[self.main_user]['second_user'] = caller_room
                    
        
        if eventType == 'extra_answer_call':
            caller = text_data_json['data']['caller']
            caller_room = self.scope['url_route']['kwargs']['username']

            async_to_sync(self.channel_layer.group_add)(caller_room, self.channel_name)
            async_to_sync(self.channel_layer.group_add)(caller, caller_room)

            async_to_sync(self.channel_layer.group_send)(
                caller,
                {
                    'type': 'extracall_answered',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )
            
        if eventType == 'ICEcandidate':

            user = text_data_json['data']['user']

            async_to_sync(self.channel_layer.group_send)(
                user,
                {
                    'type': 'ICEcandidate',
                    'data': {
                        'rtcMessage': text_data_json['data']['rtcMessage']
                    }
                }
            )
            
        if eventType == 'admin_connected':
            users = ActiveUser.objects.all()
            active_admins = users.filter(is_admin=True).values_list('username', flat=True)
            active_users = users.filter(is_admin=False).values_list('username', flat=True)
            for user in active_users:
                async_to_sync(self.channel_layer.group_send)(
                    user,
                    {
                        'type': 'admin_connected',
                        'data': {
                            'active_admins': list(active_admins)
                        }
                    }
                )
        if eventType == 'admin_disconnected':
            users = ActiveUser.objects.all()
            active_admins = users.filter(is_admin=True).values_list('username', flat=True)
            active_users = users.filter(is_admin=False).values_list('username', flat=True)
            for user in active_users:
                async_to_sync(self.channel_layer.group_send)(
                    user,
                    {
                        'type': 'admin_disconnected',
                        'data': {
                            'active_admins': list(active_admins)
                        }
                    }
                )
                

    def call_received(self, event):
        print('Call received by ', self.my_name )
        self.send(text_data=json.dumps({
            'type': 'call_received',
            'data': event['data']
        }))
        
    def extra_call_received(self, event):
        print('Call received by ', self.my_name )
        self.send(text_data=json.dumps({
            'type': 'extra_call_received',
            'data': event['data']
        }))
        
    def new_call(self, event):
        print('Call received by ', self.my_name )
        self.send(text_data=json.dumps({
            'type': 'new_call',
            'data': event['data']
        }))


    def call_answered(self, event):
        print(self.my_name, "'s call answered")
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))
    def extracall_answered(self, event):
        self.send(text_data=json.dumps({
            'type': 'call_answered',
            'data': event['data']
        }))

    def ICEcandidate(self, event):
        self.send(text_data=json.dumps({
            'type': 'ICEcandidate',
            'data': event['data']
        }))
        
    def admin_connected(self, event):
        self.send(text_data=json.dumps({
            'type': 'admin_connected',
            'data': event['data']
        }))
        
    def admin_disconnected(self, event):
        self.send(text_data=json.dumps({
            'type': 'admin_disconnected',
            'data': event['data']
        }))
    
    
    def notify_other_users_connected(self):
        users = ActiveUser.objects.all()
        active_admins = users.filter(is_admin=True).values_list('username', flat=True)
        active_users = users.filter(is_admin=False).values_list('username', flat=True)
        for user in active_users:
            async_to_sync(self.channel_layer.send)(
                user,
                {
                    'type': 'admin_connected',
                    'data': {
                        'active_admins': list(active_admins)
                    }
                }
            )

    def notify_other_users_disconnected(self):
        users = ActiveUser.objects.all()
        active_admins = users.filter(is_admin=True).values_list('username', flat=True)
        active_users = users.filter(is_admin=False).values_list('username', flat=True)
        for user in active_users:
            async_to_sync(self.channel_layer.group_send)(
                user,
                {
                    'type': 'admin_disconnected',
                    'data': {
                        'active_admins': list(active_admins)
                    }
                }
            )
            
    def notify_translator_disconnected(self):
        users = ActiveUser.objects.all()
        active_translators = users.filter(is_translator=True).values_list('username', flat=True)
        active_users = users.filter(is_admin=False, is_translator=False, is_lawyer=False).values_list('username', flat=True)
        for user in active_users:
            async_to_sync(self.channel_layer.group_send)(
                user,
                {
                    'type': 'admin_disconnected',
                    'data': {
                        'active_admins': list(active_translators)
                    }
                }
            )
            
    def notify_lawyer_disconnected(self):
        users = ActiveUser.objects.all()
        active_lawyers = users.filter(is_lawyer=True).values_list('username', flat=True)
        active_translators = users.filter(is_translator=True).values_list('username', flat=True)
        for user in active_translators:
            async_to_sync(self.channel_layer.group_send)(
                user,
                {
                    'type': 'admin_disconnected',
                    'data': {
                        'active_admins': list(active_lawyers)
                    }
                }
            )
            