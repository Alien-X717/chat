
from AskOn.settings import CHANNEL_LAYERS
from concurrent.futures import thread
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
        
        print("connect started")
        #self.room_name = self.scope['url_route']['kwargs']['room_name']
       
        self.user = User.objects.get(username=self.scope['user'])
        print(self.channel_name)
        #print(self.room_name)
        #print(self.user)
        self.room_group_name = str(self.user.id)
        #contact.objects.filter(contact_id=self.user).delete()
        contact.objects.create(channel_name = self.channel_name,contact_id=self.user)
        # Join room group
        self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.PING_ACK=True
        pinger = threading.Thread(target=self.ping)
        pinger.start()
    
    def send_to_socket(self,data):
        self.send(json.dumps(data))
        
    def send_to_group(self,data,type):
        print("grp data")
        print(data)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':type,
                'message':self.to_json_msg(data)
            }
        )

    def grp_msg(self,event):
        
        self.send_to_socket({
            'command':event['command'],
            'message':event['message']
        })


    def cache_chat(self, recv_data):
        print("chat_cache chala")
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
            print(self.user_list)
        except Exception as e:
            print("exception in cahcing chat" + str(e))
            pass

       

    def disconnect(self, code):
        print(code)
        contact.objects.filter(channel_name=self.channel_name).delete()
        try:
            contact.objects.filter(contact_id=self.user).all()
        except contact.DoesNotExist as e: 
            for item in self.user_list:
                rec = User.objects.get(pk=item)
                self.send_chat_msg(msg=self.user.id,type="status.OFF",reciever=rec)
            
        
        self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name)
        
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )    
        raise StopConsumer() 
            

        
        

    #this recieves msg from other channel and sends to the current user    
    def chat_message(self,event):
        print("data recieved from other channel")
        #print(event["message"])
        msg=event["message"]
        
        #self.send_to_socket({
        #    'command': 'NEW_MSG',
        #    'message': msg
        #})
        self.send_to_group(data=msg)
        if(msg["sid"] not in self.user_list and msg['sid']!=self.user.id):
            self.user_list.append(msg["sid"])
            rec = User.objects.get(pk=msg["sid"])
            self.send_chat_msg(msg=self.user.id,type="status.ON",reciever=rec)
            #print(self.user_list)

    def ping(self):
        print("ping started")
        while True:
            time.sleep(4)
            if self.PING_ACK == True:
                self.PING_ACK=False
                self.send_to_socket({
                    'command':'PING'
                })
                #print(f"ping sended{self.scope['user']}")
                
                
            else:
                print(f"got disconnected {self.user}")
                self.disconnect(code=1001)
    
    def pong(self,event):
        
        self.PING_ACK = True
        #print(f"ping ack recieved{self.scope['user']}")
    
    def status_OFF(self,event):
        id=event["message"]
        #print(str(id)+"got offline")
        if id in self.user_list:
            self.user_list.remove(id)
            self.send_to_socket({
                "command":"OFFLINE",
                "message":id
            })
        
    def status_ON(self,event):
        id= event["message"]
        #print(str(id)+"got online")
        if id not in self.user_list:
            self.user_list.append(id)
        self.send_to_socket({
                "command":"ONLINE",
                "message":id
            })

    def chat_load(self,data):
        
        recipient = User.objects.get(id=data['user'])
        
        #new_msg_count= Message.objects.filter(recipient=5,is_readed=False).count()
        #if new_msg_count > (ul-ll):
         #   ul=new_msg_count

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
        print(recv_data)
        data=recv_data["message"]
        try:
            sender_user = User.objects.filter(username=data['sender'])[0]
            recipient_user = User.objects.filter(username=data['recipient'])[0]
            msg = Message.objects.create(
                sender=sender_user,
                recipient=recipient_user,
                content = data["content"],
                    
                )
            #async_to_sync(self.channel_layer.group_send)(
            #    self.room_group_name,
            #    {
            #    'type': 'chat.message',
            #    'message':self.to_json_msg(msg)
            #    })
            #self.send_to_socket({
            #    "command": "NEW_MSG",
            #    "message": self.to_json_msg(msg)
            #})
            
            self.send_to_group(data=msg,type='NEW_MSG')
            self.send_chat_msg(msg=self.to_json_msg(msg),type="chat.message",reciever=recipient_user)
            
        except Exception as e:
            print("exception in new_msg()")
            print(e)    

    def get_channel_name(self,recipient):
        chanel_name = None
        try:
            print("fetching channel")
            chanel= contact.objects.filter(contact_id=recipient).all()[:1]
            print("channel got")
            for ch in chanel:
                chanel_name = ch.channel_name
                print(ch)
        except contact.DoesNotExist or Exception as e :
            print(e)
        return chanel_name        
    
    #for sending msg to another channel(to recipient's channel)
    def send_chat_msg(self,msg,type,reciever):       
        try:
            ch_name = self.get_channel_name(recipient=reciever)    
    #        print("data to be sent to")
            if ch_name is not None:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(ch_name, {
                    "type":type,   
                    "message":msg
                })
        except Exception as e:
            print("error while sending"+str(e))
            pass
   
    #this recieves from socket
    def receive(self, text_data):
        recv_data = json.loads(text_data)
        #print("recieved data")
        #print(recv_data)
        self.commands[recv_data['command']](self,recv_data)

    def search_result(self,data):
        
        try:
            result_set=User.objects.values('id','username','profile_pic','first_name','last_name').filter(Q(first_name__contains=data["text"]) | Q(last_name__contains=data["text"])).exclude(id=self.user.id)[:10]
            
            contact_list=list()
            for item in result_set:
                #if not item['username'] == self.user.username:
                    contact_list.append({
                        "id":item["id"],
                        "name":item['first_name']+" "+item['last_name'],
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
       # print(str(data['id']) + "has been selected")
        contact = User.objects.get(pk=data['id'])
        if data['id'] not in self.user_list:
            self.user_list.append(data['id'])
            print("new contact added " + contact.profile_pic.url)

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
     #   print("message is readed by " + str(event["message"]))        
        self.send_to_socket({
            "command":"MAR",
            "message":event["message"]
        })
    
    #if user reads the messages of sender
    def mark_as_read(self,data):       
        sen = User.objects.get(pk=data["message"])
        un_read_msgs = Message.objects.values("id").filter(sender=sen,recipient=self.user,is_readed=False)
        for unread in un_read_msgs:
      #      print(unread)
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
    
    
    commands={
        'PONG':pong,
        'NEW_MSG':new_msg,
        'MAR':mark_as_read,
        'CACHE_CHAT':cache_chat,
        'SEARCH':search_result,
        'NEW_CONTACT':add_new_contact,             
    }
        