# WebSocketDAT callbacks for NDI Named Router Info Service
# This file provides minimal bridge callbacks that forward events to the extension

def getExtension():
	"""Get the extension instance"""
	try:
		return ext.NDINamedRouterInfoExt
	except:
		return None

def onConnect(dat):
	"""Called when WebSocket connection is established"""
	ext = getExtension()
	debug(f'onConnect: {ext}')
	if ext:
		ext.onWebSocketConnect(dat)
	return

def onDisconnect(dat):
	"""Called when WebSocket connection is closed"""
	ext = getExtension()
	if ext:
		ext.onWebSocketDisconnect(dat)
	return

def onReceiveText(dat, rowIndex, message):
	"""Called when text message is received from server"""
	ext = getExtension()
	if ext:
		ext.onWebSocketReceiveText(dat, message)
	return

def onReceiveBinary(dat, contents):
	"""Called when binary message is received"""
	ext = getExtension()
	if ext:
		ext.onWebSocketReceiveBinary(dat, contents)
	return

def onReceivePing(dat, contents):
	"""Called when ping is received"""
	ext = getExtension()
	if ext:
		ext.onWebSocketReceivePing(dat, contents)
	else:
		# Fallback: send pong directly
		dat.sendPong(contents)
	return

def onReceivePong(dat, contents):
	"""Called when pong is received"""
	ext = getExtension()
	if ext:
		ext.onWebSocketReceivePong(dat, contents)
	return

def onMonitorMessage(dat, message):
	"""Called for WebSocket status messages"""
	ext = getExtension()
	if ext:
		ext.onWebSocketMonitorMessage(dat, message)
	return

	