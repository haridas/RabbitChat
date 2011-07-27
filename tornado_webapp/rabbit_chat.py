# -*- coding: utf-8 -*-
'''
	RabbitChat - A simple webbased chat sytem based on RabbitMQ + Tornado + Websocket.

	Copyright (C) 2011,  Haridas N <haridas.nss@gmail.com>

	Check RabbitChat/LICENSE file for full copyright notice.

'''
import json
import os
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.options import options, define

import pika
from pika.adapters.tornado_connection import TornadoConnection



# Define available options
define("port", default=8888, type=int, help="run on the given port")
define("cookie_secret", help="random cookie secret")
define("queue_host", default="127.0.0.1", help="Host for amqp daemon")
define("queue_user", default="guest", help="User for amqp daemon")
define("queue_password", default="guest", help="Password for amqp daemon")

PORT = 8888


class PikaClient(object):

    def __init__(self):
        # Construct a queue name we'll use for this instance only
              
        #Giving unique queue for each consumer under a channel.
        self.queue_name = "queue-%s" % (id(self),)
	
	# Default values
        self.connected = False
        self.connecting = False
        self.connection = None
        self.channel = None

	#Webscoket object.
	self.websocket = None
	
        
    def connect(self):
    
	if self.connecting:
            pika.log.info('PikaClient: Already connecting to RabbitMQ')
            return
        
        pika.log.info('PikaClient: Connecting to RabbitMQ on localhost:5672, Object: %s' % (self,))
        
        self.connecting = True

        credentials = pika.PlainCredentials('guest', 'guest')
        param = pika.ConnectionParameters(host='localhost',
                                          port=5672,
                                          virtual_host="/",
                                          credentials=credentials)
        self.connection = TornadoConnection(param,
                                            on_open_callback=self.on_connected)
        
        #Currently this will close tornado ioloop.
        #self.connection.add_on_close_callback(self.on_closed)

    def on_connected(self, connection):
        pika.log.info('PikaClient: Connected to RabbitMQ on localhost:5672')
        self.connected = True
        self.connection = connection
        self.connection.channel(self.on_channel_open)

    def on_channel_open(self, channel):
        pika.log.info('PikaClient: Channel Open, Declaring Exchange, Channel ID: %s' % (channel,))
        self.channel = channel
        
        self.channel.exchange_declare(exchange='tornado',
                                      type="direct",
                                      auto_delete=True,
                                      durable=False,
                                      callback=self.on_exchange_declared)

    def on_exchange_declared(self, frame):
        pika.log.info('PikaClient: Exchange Declared, Declaring Queue')
        self.channel.queue_declare(auto_delete=True,
        			   queue = self.queue_name,
         		           durable=False,
                		   exclusive=True,
                		   callback=self.on_queue_declared)
       	
       

    def on_queue_declared(self, frame):
    
        pika.log.info('PikaClient: Queue Declared, Binding Queue')
        self.channel.queue_bind(exchange='tornado',
                                queue=self.queue_name,
                                routing_key='tornado.*',
                                callback=self.on_queue_bound)
	
    def on_queue_bound(self, frame):
        pika.log.info('PikaClient: Queue Bound, Issuing Basic Consume')
        self.channel.basic_consume(consumer_callback=self.on_pika_message,
                                   queue=self.queue_name,
                                   no_ack=True)
        
    def on_pika_message(self, channel, method, header, body):
        pika.log.info('PikaCient: Message receive, delivery tag #%i' % \
                     method.delivery_tag)
     
        #Send the Cosumed message via Websocket to browser.
        self.websocket.write_message(body)
        
        

    def on_basic_cancel(self, frame):
        pika.log.info('PikaClient: Basic Cancel Ok')
        # If we don't have any more consumer processes running close
        self.connection.close()

    def on_closed(self, connection):
        # We've closed our pika connection so stop the demo
        tornado.ioloop.IOLoop.instance().stop()
	
	
    def sample_message(self, ws_msg):
  	#Publish the message from Websocket to RabbitMQ
       	properties = pika.BasicProperties(content_type="text/plain",delivery_mode=1)
        
        self.channel.basic_publish(exchange='tornado',
                                   routing_key='tornado.*',
                                   body = ws_msg,
                                   properties=properties)
       


class LiveChat(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self):
        
        # Send our main document
        self.render("demo_chat.html",
                    connected=self.application.pika.connected)




class WebSocketServer(tornado.websocket.WebSocketHandler):
	'WebSocket Handler, Which handle new websocket connection.'
			
	def open(self):
		'Websocket Connection opened.'
		
		#Initialize new pika client object for this websocket.
		self.pika_client = PikaClient()
		
		#Assign websocket object to a Pika client object attribute.
		self.pika_client.websocket = self
		
		ioloop.add_timeout(1000, self.pika_client.connect)
		
	def on_message(self,msg):
		'A message on the Webscoket.'
		
		#Publish the received message on the RabbitMQ
		self.pika_client.sample_message(msg)
		
		
	def on_close(self):
		'Closing the websocket..'
		print "WebSocket Closed"
		
		#close the RabbiMQ connection...
		self.pika_client.connection.close()


class TornadoWebServer(tornado.web.Application):
	' Tornado Webserver Application...'
	def __init__(self):

		#Url to its handler mapping.
		handlers = [
	
		        (r"/ws_channel",WebSocketServer),
	        	(r"/chat",LiveChat)
		]
	
		#Other Basic Settings..
		settings = dict(
			cookie_secret = options.cookie_secret,
                	login_url = "/signin",
	                template_path = os.path.join(os.path.dirname(__file__),"templates"),
        	        static_path = os.path.join(os.path.dirname(__file__),"static"),
                	xsrf_cookies = True,
	                debug = True

		)
	
		#Initialize Base class also.
		tornado.web.Application.__init__(self,handlers,**settings)
	


if __name__ == '__main__':
    
    # Set our pika.log options
    pika.log.setup(color=True)
 	
    #Tornado Application
    pika.log.info("Initializing Tornado Webapplications settings...")
    application = TornadoWebServer()
    
    # Helper class PikaClient makes coding async Pika apps in tornado easy
    pc = PikaClient()
    application.pika = pc  # We want a shortcut for below for easier typing

    
    
    # Start the HTTP Server
    pika.log.info("Starting Tornado HTTPServer on port %i" % PORT)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(PORT)

    # Get a handle to the instance of IOLoop
    ioloop = tornado.ioloop.IOLoop.instance()

    # Add our Pika connect to the IOLoop since we loop on ioloop.start
    #ioloop.add_timeout(1000, application.pika.connect)

    # Start the IOLoop
    ioloop.start()
