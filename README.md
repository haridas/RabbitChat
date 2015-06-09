RabbitChat
=========

****************************************************************************************
 RabbitChat - A simple web based chat sytem based on RabbitMQ + Tornado + Websocket.

 Copyright (C) 2011,  Haridas N <haridas.nss@gmail.com>
 
 Check RabbitChat/LICENSE file for full Copyright notice.
****************************************************************************************



Introduction:-
==============

A simple web based chat system developed by using RabbitMQ + Tornado + Websocket + Pika.

I commited two versions of this chat system, the difference is with the creation of RabbitMQ channel and connection.

In the first version(master branch) we create rabbitMQ connection and channel for each incomming websocket connection. So we do this in the Websocket handler of Tornado application.

In the latest one (The Branch RabbitChat-new)  I used RabbitMQ more effectively by controlling the RabbitMQ channle andconnection creation, so according to this the latest version it use  one connection and one  channel for every websocket request. ie; we reusing the RabbitMQ connection and channels.



In order to test this application you need following packages :

1. Tornado - Python High performence async webserver.
2. Pika - RabbitMQ client that support Tornado IOLoop.
3. Websocket-js - Browser JS package to support websocket API
4. Also you should run a RabbitMQ broker in your system.

To install python packages :- 
=============================
1. To install Tornado use this command: "easy_install tornado" ,

2. Similarly, easy_install pika, 

3. To know more about the Websocket browser implementation, get a copy from https://github.com/stdva/web-socket-js



HOW to RUN
==========

Enter in to tornado application folder and run the python script:

    >cd tornado_app

    >python rabbit_chat.py


Take this URL http://localhost:8888/chat on your browser(Chrome or Firefox 4, the browser should support websocket.)

Enjoy ...:)



 

