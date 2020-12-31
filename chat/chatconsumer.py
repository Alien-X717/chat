'''
    Copyright (C) 2020  Jayesh Karkare Alien-X717

    This file is part of Chat

    Chat is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Chat is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Chat.  If not, see <https://www.gnu.org/licenses/>.'''

from django.conf import settings
import json
from django.db.models.query_utils import Q
from .models import Message,contact
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from channels.exceptions import StopConsumer
import threading,time
 
User = get_user_model()

class ChatConsumer(WebsocketConsumer):

    def connect(self): 
        self.user = User.objects.get(username=self.scope['user'])
        contact.objects.filter(contact_id=self.user).delete()
        contact.objects.create(channel_name = self.channel_name,contact_id=self.user)
        self.accept()
        self.PING_ACK=True
        pinger = threading.Thread(target=self.ping)
        pinger.start()
    
    def send_to_socket(self,data):
        self.send(json.dumps(data))
        
    def cache_chat(self):
        try:
            msgs = Message.objects.values('sender','recipient').filter(Q(recipient=self.user) | Q(sender=self.user)).order_by('timestamp')
            self.user_list= list()
            msg_list=list()
            for msg in msgs:
                sid = msg['sender']
                if sid==self.user.id:
                    sid=msg['recipient']
                
                if sid not in self.user_list:
                    self.user_list.append(sid)                
                    msg_list.append(self.chat_load(data={'user':sid}))

            self.send_to_socket({
                'command':'LOAD_MSGS',
                'msg_list':msg_list
            })
        except Exception as e:
            print("exception in cahcing chat" + str(e))
            pass

       

    def disconnect(self, code):

        contact.objects.filter(channel_name=self.channel_name).delete()
        try:
            contact.objects.get(contact_id=self.user)
        except contact.DoesNotExist as e: 
            for item in self.user_list:
                rec = User.objects.get(pk=item)
                self.send_chat_msg(msg=self.user.id,type="status.OFF",reciever=rec)
        raise StopConsumer() 
            

       
    #this recieves msg from other channel and sends to the current user    
    def chat_message(self,event):
        msg=event["message"]
        self.send_to_socket({
            'command': 'NEW_MSG',
            'message': msg
        })
        if(msg["sid"] not in self.user_list and msg['sid']!=self.user.id):
            self.user_list.append(msg["sid"])
            rec = User.objects.get(pk=msg["sid"])
            self.send_chat_msg(msg=self.user.id,type="status.ON",reciever=rec)
            

    def ping(self):
        while True:
            time.sleep(4)
            if self.PING_ACK == True:
                self.PING_ACK=False
                self.send_to_socket({'command':'PING'})
            else:
                self.disconnect(code=1001)
    
    def pong(self,event):
        self.PING_ACK = True
       
    def status_OFF(self,event):
        id=event["message"]
        if id in self.user_list:
            self.user_list.remove(id)
            self.send_to_socket({
                "command":"OFFLINE",
                "message":id
            })
        
    def status_ON(self,event):
        id= event["message"]
        if id not in self.user_list:
            self.user_list.append(id)
        self.send_to_socket({
                "command":"ONLINE",
                "message":id
            })

    def chat_load(self,data):
        
        recipient = User.objects.get(id=data['user'])
        msg_set=Message.objects.filter((Q(sender=self.user) & Q(recipient=recipient)) | (Q(sender = recipient) & Q(recipient=self.user))).order_by('-timestamp').all()             
        chname=self.get_channel_name(recipient=recipient)
        
        status=''
        if chname is None:
            status="offline"
        else:
            status="online"
            self.send_chat_msg(msg=self.user.id,type="status.ON",reciever=recipient)

        ctx={
            'contact': data['user'],
            'name':recipient.username,
            'messages':self.to_json_msgs(msg_set),
            'status':status,
            'pic':recipient.profile_pic.url
        }
        return ctx
    
    def new_msg(self, recv_data):
        data=recv_data["message"]
        try:
            sender_user = User.objects.filter(username=data['sender'])[0]
            recipient_user = User.objects.filter(username=data['recipient'])[0]
            msg = Message.objects.create(
                sender=sender_user,
                recipient=recipient_user,
                content = data["content"],   
                )
            self.send_to_socket({
                "command": "NEW_MSG",
                "message": self.to_json_msg(msg)
            })

            self.send_chat_msg(msg=self.to_json_msg(msg),type="chat.message",reciever=recipient_user)
            
        except Exception as e:
            print("exception in new_msg()" + str(e))   

    def get_channel_name(self,recipient):
        try:
            chanel= contact.objects.get(contact_id=recipient)
            return chanel.channel_name
        except contact.DoesNotExist:
            return None    
    
    #for sending msg to another channel(to recipient's channel)
    def send_chat_msg(self,msg,type,reciever):       
        try:
            ch_name = self.get_channel_name(recipient=reciever)    
            if ch_name is not None:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(ch_name, {
                    "type":type,   
                    "message":msg
                })
        except Exception as e:
            print("error while sending"+str(e))

    def search_result(self,data):
        try:
            result_set=User.objects.values('id','username','profile_pic').filter(username__contains=data["text"]).exclude(id=self.user.id)[:10]
            contact_list=list()
            for item in result_set:
                #if not item['username'] == self.user.username:
                    contact_list.append({
                        "id":item["id"],
                        "name":item['username'],
                        "uname":item['username'],
                        "pic":settings.MEDIA_URL+item['profile_pic']

                    })

            self.send_to_socket({
                "command":"SEARCH",
                "result":contact_list
            })
        except Exception as e:
            print(e)        

    def add_new_contact(self,data):
        contact = User.objects.get(pk=data['id'])
        if data['id'] not in self.user_list:
            self.user_list.append(data['id'])

        chname=self.get_channel_name(recipient=data['id'])    
        status=''
        if chname is None:
            status="offline"
        else:
            status="online"     
        self.send_to_socket({
            "command":"NEW_CONT",
            "id":contact.id,
            "name":contact.username,
            "pic":contact.profile_pic.url,
            "status":status
        })

    def chat_MAR(self,event):     
        self.send_to_socket({
            "command":"MAR",
            "message":event["message"]
        })
    
    #if user reads the messages of sender
    def mark_as_read(self,data):       
        sen = User.objects.get(pk=data["message"])
        un_read_msgs = Message.objects.values("id").filter(sender=sen,recipient=self.user,is_readed=False)
        for unread in un_read_msgs:
            msg = Message.objects.get(pk=unread["id"])
            msg.is_readed=True
            msg.save()
        self.send_chat_msg(msg=self.user.id,type="chat.MAR",reciever=sen)

    def to_json_msgs(self, msgs):
        msg_list = []
        for msg in msgs:
            msg_list.append(self.to_json_msg(msg))
        return msg_list
    
    def to_json_msg(self, msg):
        return{
            'sid':msg.sender.id,
            'rid':msg.recipient.id,            
            'sender': msg.sender.username,
            'recipient':msg.recipient.username,
            'content': msg.content,
            'time_stamp':str(msg.timestamp).split('.')[0],
            'is_readed':msg.is_readed,
            'pic':msg.sender.profile_pic.url
            }    
             
   
    #this recieves from socket
    def receive(self, text_data):
        recv_data = json.loads(text_data)
        #print(recv_data)
       
        if recv_data['command'] == 'PONG':
            self.pong(recv_data)
        elif recv_data['command'] == 'NEW_MSG':
            self.new_msg(recv_data)
        elif recv_data['command'] == 'CACHE_CHAT':
            self.cache_chat()    
        elif recv_data['command'] == 'SEARCH':
            self.search_result(recv_data)        
        elif recv_data['command'] == 'NEW_CONTACT':
            self.add_new_contact(recv_data)
        elif recv_data['command'] == 'MAR':
            self.mark_as_read(recv_data)
        else:
            pass  
    
    
        