# WebSocket DAT callbacks for NDI Named Router
# This file should be attached to a WebSocket DAT in TouchDesigner
# Configure the WebSocket DAT to handle WebSocket connections

import json
import time

# me - this DAT
# dat - the WebSocket DAT

def debug(message):
	if parent.NDINamedRouter.par.Debugmessages.eval():
		tdu.debug.debug(message)

def onConnect(dat):
	"""Called when bridge server connects"""
	debug(f'Bridge server connected to DAT: {dat.name}')
	
	# Send initial state to bridge when it connects
	_ext = ext.NDINamedRouterExt
	if _ext and _ext.webHandler:
		debug(f'Sending initial state to bridge')
		_ext.webHandler.sendInitialState(dat, dat)
	else:
		debug('WARNING: Extension or WebHandler not found')
	
	return

def onDisconnect(dat):
	"""Called when bridge server disconnects"""
	debug('Bridge server disconnected from DAT')
	
	# Could add reconnection logic here if needed
	
	return

# me - this DAT
# dat - the DAT that received a message
# rowIndex - the row number the message was placed into
# message - a unicode representation of the text
# 
# Only text frame messages will be handled in this function.

def onReceiveText(dat, rowIndex, message):
	"""Called when a text message is received from a WebSocket client"""
	debug(f'Received text message: {message}')
	
	if message == 'ping':
		dat.sendText('pong')
		return
	
	# Handle JSON messages asynchronously
	coroutines = [parseJSON(message, dat)]
	op.TDAsyncIO.Run(coroutines)
	return

async def parseJSON(message, dat):
	"""Parse JSON messages from web clients"""
	# Use the handler to process the message
	debug(f'Parsing JSON message: {message}')
	_ext = ext.NDINamedRouterExt
	if _ext and _ext.webHandler:
		_ext.webHandler.handleMessage(dat, dat, message)
	else:
		debug('WARNING: Extension or WebHandler not found')
		error_response = {
			'action': 'error',
			'message': 'NDI Named Router extension or handler not found'
		}
		dat.sendText(json.dumps(error_response))

# me - this DAT
# dat - the DAT that received a message
# contents - a byte array of the message contents
# 
# Only binary frame messages will be handled in this function.

def onReceiveBinary(dat, contents):
	"""Called when a binary message is received"""
	debug(f'Binary message received (not implemented): {len(contents)} bytes')
	# Not used for this application
	return

# me - this DAT
# dat - the DAT that received a message
# contents - a byte array of the message contents
# 
# Only ping messages will be handled in this function.

def onReceivePing(dat, contents):
	"""Called when a ping message is received"""
	debug(f'Ping message received: {contents}')
	dat.sendPong(contents) # send a reply with same message
	return

# me - this DAT
# dat - the DAT that received a message
# contents - a byte array of the message content
# 
# Only pong messages will be handled in this function.

def onReceivePong(dat, contents):
	"""Called when a pong message is received"""
	debug(f'Pong message received: {contents}')
	# Not used for this application
	return

# me - this DAT
# dat - the DAT that received a message
# message - a unicode representation of the message
#
# Use this method to monitor the websocket status messages

def onMonitorMessage(dat, message):
	"""Called when WebSocket status messages are received"""
	debug(f'WebSocket monitor message: {message}')
	return