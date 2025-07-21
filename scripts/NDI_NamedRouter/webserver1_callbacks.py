'''Info Header Start
Name : webserver1_callbacks
Author : Dan@DAN-4090
Saveorigin : NDI_NamedRouter.1.toe
Saveversion : 2023.11880
Info Header End'''
# WebServer DAT callbacks for NDI Named Router
# This file should be attached to a WebServer DAT in TouchDesigner
# Configure the WebServer DAT to handle WebSocket connections

import json
import time

# me - this DAT.
# webServerDAT - the connected Web Server DAT
# request - A dictionary of the request fields. The dictionary will always contain the below entries, plus any additional entries dependent on the contents of the request
# 		'method' - The HTTP method of the request (ie. 'GET', 'PUT').
# 		'uri' - The client's requested URI path. If there are parameters in the URI then they will be located under the 'pars' key in the request dictionary.
#		'pars' - The query parameters.
# 		'clientAddress' - The client's address.
# 		'serverAddress' - The server's address.
# 		'data' - The data of the HTTP request.
# response - A dictionary defining the response, to be filled in during the request method. Additional fields not specified below can be added (eg. response['content-type'] = 'application/json').
# 		'statusCode' - A valid HTTP status code integer (ie. 200, 401, 404). Default is 404.
# 		'statusReason' - The reason for the above status code being returned (ie. 'Not Found.').
# 		'data' - The data to send back to the client. If displaying a web-page, any HTML would be put here.

# return the response dictionary

def debug(message):
	if parent.NDINamedRouter.par.Debugmessages.eval():
		tdu.debug.debug(message)

def onHTTPRequest(webServerDAT, request, response):
	response['statusCode'] = 200 # OK
	response['statusReason'] = 'OK'
	response['data'] = '<b>TouchDesigner: </b>' + webServerDAT.name
	return response

def onWebSocketOpen(webServerDAT, client, uri):
	"""Called when a WebSocket client connects"""
	debug(f'Web client connected to WebServer DAT')
	
	# Use the handler to send initial state and track client
	_ext = ext.NDINamedRouterExt
	if _ext and _ext.webHandler:
		_ext.webHandler.addClient(client)
		_ext.webHandler.sendInitialState(webServerDAT, client)
	else:
		debug('WARNING: Extension or WebHandler not found')
	
	return

def onWebSocketClose(webServerDAT, client):
	"""Called when a WebSocket client disconnects"""
	debug('Web client disconnected from WebServer DAT')
	
	# Remove client from handler's tracking
	_ext = ext.NDINamedRouterExt
	if _ext and _ext.webHandler:
		_ext.webHandler.removeClient(client)
	
	return

async def parseJSON(message, webServerDAT, client):
	"""Parse JSON messages from web clients"""
	# Use the handler to process the message
	_ext = ext.NDINamedRouterExt
	if _ext and _ext.webHandler:
		_ext.webHandler.handleMessage(webServerDAT, client, message)
	else:
		debug('WARNING: Extension or WebHandler not found')
		error_response = {
			'action': 'error',
			'message': 'NDI Named Router extension or handler not found'
		}
		webServerDAT.webSocketSendText(client, json.dumps(error_response))

def onWebSocketReceiveText(webServerDAT, client, data):
	"""Called when a text message is received from a WebSocket client"""
	if data == 'ping':
		webServerDAT.webSocketSendText(client, 'pong')
		return
	
	# Handle JSON messages asynchronously
	coroutines = [parseJSON(data, webServerDAT, client)]
	op.TDAsyncIO.Run(coroutines)
	return

def onWebSocketReceiveBinary(webServerDAT, client, data):
	"""Called when a binary message is received"""
	# Not used for this application
	debug(f'Binary message received (not implemented): {len(data)} bytes')
	return

def onWebSocketReceivePing(webServerDAT, client, data):
	"""Called when a ping message is received"""
	webServerDAT.webSocketSendPong(client, data=data)  # Send a reply with same message
	return

def onWebSocketReceivePong(webServerDAT, client, data):
	"""Called when a pong message is received"""
	# Not used for this application
	return

def onServerStart(webServerDAT):
	"""Called when the WebServer starts"""
	debug(f'NDI Named Router WebServer started: {webServerDAT.name}')
	return

def onServerStop(webServerDAT):
	"""Called when the WebServer stops"""
	debug(f'NDI Named Router WebServer stopped: {webServerDAT.name}')
	return
