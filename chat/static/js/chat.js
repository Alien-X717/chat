/*
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
    along with Chat.  If not, see <https://www.gnu.org/licenses/>.
*/
var activeContact;
var userid;
var username;
var contactList = Object();
var srchactive= false;
var ws_scheme = window.location.protocol == "https:" ? "wss" : "ws";
var socket = new ReconnectingWebSocket(ws_scheme + '://'+host+'/ws/chat/');  //remember to change this


socket.onopen = function(e)
{    
   socket.send(JSON.stringify({
       "command":"CACHE_CHAT"
   }));
}
 
socket.onmessage = function(e)
{
    var data = JSON.parse(e.data);
    switch(data['command'])
    {   
        case 'PING':socket.send(JSON.stringify({"command": "PONG"}));  
                    break;
        case 'NEW_MSG':var cls; 
                        var ID;
                        var name;
                        var status="";
                        if(data.message.sid===userid)
                        {
                            ID=activeContact;
                            name=contactList[activeContact].name;                                  
                        }
                        else
                        {   ID=data.message.sid;    
                            name=data.message.sender;
                            status="online";
                            img=data.message.pic;
                        }
                        createContact(ID,name,data.message.content,status,false,img);
                        $("#chat-log"+ID).append(createMessage(data.message));
			scrollToEnd(ID);                   
            	break;
        case 'LOAD_MSGS':var msg_list=data['msg_list'];

                        for(var i=0;i<msg_list.length;i++)
                        {   
                            if(!contactList[msg_list[i].contact])
                            {                            
                            var cid=msg_list[i].contact;
                            var cname = msg_list[i].name;
                            var msgs = msg_list[i].messages;
                            len = msgs.length;
                            var img=msg_list[i].pic;
                            createContact(cid,cname,msgs[0].content,msg_list[i].status,true,img);
                            for(var j=0;j<len;j++)
                            {           
                              $("#chat-log"+String(cid)).prepend(createMessage(msgs[j]));
                            }
			    scrollToEnd(cid);   
                            }
                        }
            break;
        case 'SEARCH': list=data["result"];
                        if(list.length>0){
                            $("#search-list").empty();
                            for(i=0;i<list.length;i++){
                                var uname=list[i].uname;
                                var id = list[i].id;
                                var name = list[i].name;
                                var img = list[i].pic;
                                createresults(id,name,img,uname);
                            }
                            }
                        
                        
            break;    
        case 'MAR': id=data["message"]                        
                    $(".msg"+userid+"_"+id).removeClass("un");                       
            break;    
        case 'ONLINE': id=data["message"]                     
                       toggleStatus(id,"offline","online");                            
            break;
        case 'OFFLINE':id=data["message"]
                       toggleStatus(id,"online","offline"); 
             break; 
        case 'NEW_CONT': createContact(data["id"],data["name"],"",data["status"],false,data["pic"]);          
    
            }
}

function scrollToEnd(id)
{
    var tab = document.getElementById("chat-tab"+id);
    tab.scrollTop = tab.scrollHeight;
}

function createresults(id,name,pic,uname){
    contact = $('<li id="tcontact'+id+'" class="contact"><div class="wrap"><img src="'+pic+'" alt="" /><div class="meta"><p class="name">'+name+'</p><p class="preview'+id+'">'+uname+'</p></div></div></li>');                           
    $("#search-list").append(contact);
    $("#tcontact"+id).click(function()
    {
    $("#search-bar").val("");
    stopsearch();
    var preview="";
    if(contactList[id]){
        preview="already added,start chating!"
        createContact(id,uname,preview,"",false,pic)
    }
    else{
        socket.send(JSON.stringify({
            "command":"NEW_CONTACT",
            "id":id
        }));
    }
    });                     
}
$("#chat-input-box").on("keyup",function(e){
    if(e.keyCode === 13){
        $("#chat-submit").click();
    }
});

$("#chat-submit").on("click",function(e)
{   
    var txt = $("#chat-input-box").val();
    var recipient = contactList[activeContact];
    if(!activeContact){
        return false;
    }
    if($.trim(txt) === '' ) {
		return false;
	}
    socket.send(JSON.stringify({
        "command":"NEW_MSG",
        "message":{
            'sender':username,
            'recipient':contactList[activeContact].name,
            'content':txt
        }
    }));
    $("#chat-input-box").val(null);
});

function toggleStatus(sid,from,to){
    $(".contact-status"+sid).removeClass(from);
    $(".contact-status"+sid).addClass(to);
    contactList[sid].status=to;

}

function createContact(sid,name,preview,status,mode,img)
{      
    var contact;
    if(preview===""){
        preview="No Message";
    }
     if(contactList[sid])
     {
        $("#contact"+sid).remove();    
    }
    else{
        createChattab(sid);
        contactList[sid]={
            'name':name,
            'status':status,
            'pic':img
         };
        
    }
    var stat=contactList[sid].status;
    var imgurl = contactList[sid].pic;
    contact = $('<li style="display:none;" id="contact'+String(sid)+'" class="contact"><div class="wrap"><span class="contact-status'+sid+' '+stat+'"></span><img src="'+imgurl+'" alt="" /><div class="meta"><p class="name">'+name+'</p><p class="preview'+sid+'">'+preview+'</p></div></div></li>');
    if(mode===true){
        $("#contact-list").append(contact); 
    }
    else{    
    $("#contact-list").prepend(contact);
    }
    if(activeContact===sid){
        $("#contact"+sid).css("display","block");
    }else{
    $("#contact"+sid).slideDown("fast");
    }
    $("#contact"+sid).click(function()
    {
      $("#chat-tab"+activeContact).css("display","none"); 
      $("#contact"+activeContact).removeClass("active");
      
      activeContact=sid;
      $("#active-contact").text(contactList[activeContact].name);
      $("#active-contact-img").attr("src",contactList[activeContact].pic);
      $("#chat-tab"+activeContact).css("display","block");
      $("#contact"+activeContact).addClass("active");  
      
          if($(".msg"+sid).hasClass("un"))
          {
              sendMAR(sid);
          }
        $(".msg"+sid).removeClass("un");
    });
}

function sendMAR(sid){
    socket.send(JSON.stringify({
        "command":"MAR",
        "message":sid
    }));
}

function createChattab(id)
{
  var tab = '<ul id="chat-log'+id+'"></ul>';  
  tab=$('<div id="chat-tab'+id+'" class="messages"></div>').html(tab);
 
  $("#chat-parent").append(tab);
  $("#chat-tab"+id).css("display","none");
}

function createMessage(msg)
{  
   var cls; 
   if(msg.sid===userid){
       cls="replies msg"+msg.sid+"_"+msg.rid;
       if(msg.is_readed===false){
           cls=cls+" un";
       }
   }else{
       cls="sent msg"+msg.sid;
      if(msg.is_readed===false) 
      {
        if(activeContact===msg.sid){
           sendMAR(activeContact);
        }
        else{
           cls = cls+" un";
       }
    }
   }
  return '<li class="'+String(cls)+'"><p>'+String(msg.content)+'<br><span class="custom-msg-date">'+String(msg.time_stamp)+'</span></p></li>';    
}

$(document).ready(function(e){

    
});

$("#search-bar").on("keyup",function(e){
    var search = $("#search-bar").val();
    search=$.trim(search);    
    if(search !== ''){
        socket.send(JSON.stringify({
            "command":"SEARCH",
            "text":search
        }));
        if(srchactive===false){
            startsearch();
        }
    }
    else if(srchactive===true){
        stopsearch();
    } 
});

function stopsearch(){
    $("#search-list").empty();
    srchactive=false;
    $("#search-list").css("display","none");
    $("#contact-list").css("display","block");
}
function startsearch(){
    srchactive=true;
    $('#contact-list').css("display","none");
    $("#search-list").css("display","block");
    
}


