*******************************************************************************
    Realtime Chat Application using django channels,websockets and javascript
    
    Copyright (C) 2020  Jayesh Karkare Alien-X717

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

***************************
contributor : Jayesh Karkare karkarejayesh@gmail.com

chat template taken from bootsnipp.com made by emilcarlsson

Features:
*   p2p realtime chat
*   live online/offline status
*   live read receipts

cons:
*   can only run on a single tab as of now.Don't open it on multiple tabs with same session.
*   if you logout on some other tab, the chat will work till the connection persists.

required python libs:
*    Django
*    channels==2.4.0

if you want to use redis as a channel layer
*   pip install channels-redis

redis is required to be running in the background

for linux:
*    sudo apt-get install redis
*    redis-server
*    redis-cli ping (if it prints "PONG" then redis is succesfully running )

for windows:
get it from here : https://github.com/tporadowski/redis/releases/tag/v5.0.9 and run redis-server.exe

************************************************************************************
for production use :
Additional configuration will be required depending on your server and hosting enviroment. Check official django channels documentation https://channels.readthedocs.io/en/2.x/ 

************************************************************************************

 
