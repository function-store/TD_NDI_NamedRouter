
import json
from TDStoreTools import DependDict, StorageManager
from collections import namedtuple

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
###

def debug(message):
	if parent.NDIInfo.par.Debugmessages.eval():
		tdu.debug.debug(message)

class NDINamedRouterInfoExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.webSocket : websocketDAT = self.ownerComp.op('websocket1')
		self.timer = self.ownerComp.op('timer1')
		# # Plural handling configuration
		# self.enablePluralHandling = True

		self.reconnectTimer = self.ownerComp.op('timer3')

		# Connection settings
		self.autoReconnect = True
		
		# Current state data
		self.currentState = {}

		self.resetSocket()
		
		storedItems = [
			{'name': 'Info', 'readOnly': True, 'property': True, 'dependable': True}
		]

		self.stored = StorageManager(self, ownerComp, storedItems)
		
		# Create a named tuple for output info
		self._outputInfo = namedtuple('OutputInfo', ['resx', 'resy'])
		
		debug('[NDI Info Ext] NDI Named Router Info Extension initialized')

		run(
			"args[0].postInit() if args[0] "
			"and hasattr(args[0], 'postInit') else None",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)

	def postInit(self):
		# Create the Outputs attribute directly on the component
		self.Outputs = OutputWrapper(self.ownerComp.Info, self._outputInfo)

		if self.isPeriodicUpdate or self.isUpdateOnStart:
			self.timerActive = True
			self.timer.par.start.pulse()
		
		if _timer := self.ownerComp.op('timer2'):
			_timer.par.start.pulse()
		
	@property
	def seqSwitch(self):
		return self.ownerComp.seq.Switch

	@property
	def isPeriodicUpdate(self):
		return self.ownerComp.par.Update.eval()

	@property
	def isUpdateOnStart(self):
		return self.ownerComp.par.Updateonstart.eval()
	
	@property
	def timerActive(self):
		return self.timer.par.play.eval()
	
	@timerActive.setter#####
	def timerActive(self, value):
		self.timer.par.play.val = value
		if value:
			self.timer.par.start.pulse()

	def onParUpdate(self, val):
		if not self.isUpdateOnStart and not val:
			self.timerActive = False
		elif val:
			self.timerActive = True
		
		# Update auto-update preference with bridge when parameter changes
		if self.isConnected():
			self.sendMessage({
				'action': 'register_client',
				'client_type': 'info',
				'auto_update': val
			})
	
	def onParUpdateonstart(self, val):
		if not self.isPeriodicUpdate and not val:
			self.timerActive = False
		elif val:
			self.timerActive = True

	def onParRequest(self):
		self.requestState()

	def onTimerCycle(self):
		self.refreshSources()

	def _updateOutputsProperty(self):
		"""Update the Outputs attribute on the component"""
		# Simply reassign the wrapper - this will refresh with current Info data
		self.Outputs = OutputWrapper(self.ownerComp.Info, self._outputInfo)

	def _setOutputInfo(self, block_idx, output_name, current_source, resolution):
		"""Set output information for a specific output block"""
		_block = self.seqSwitch[block_idx]
		_block.par.Outputname.val = output_name
		_block.par.Currentsource.val = current_source
		_block.par.Resx.val = resolution[0]
		_block.par.Resy.val = resolution[1]
		
		# Store as dictionary (for pickling compatibility) with output name as key
		output_info = {
			'resx': resolution[0],
			'resy': resolution[1]
		}
		self.stored['Info'][output_name] = output_info
		
		# Update the Outputs property wrapper
		self._updateOutputsProperty()
		
		debug(f'[NDI Info Ext] Updated block {block_idx}: {output_name} -> {current_source} @ {resolution[0]}x{resolution[1]}')
	
	def isConnected(self):
		"""Check if connected to server"""
		if not self.webSocket:
			return False
		# WebSocketDAT is connected if it's active and has established connection
		return self.webSocket.par.active.eval() and self.webSocket.numRows > 0
	
	def resetSocket(self):
		self.webSocket.par.reset.pulse()
	
	def requestState(self):
		"""Request current state from the server"""
		return self._requestState()
	
	def refreshSources(self):
		"""Request server to refresh its sources"""
		return self._refreshSources()
	
	def setSource(self, block_idx, source_name):
		"""Set a source for a specific output block"""
		return self._setSource(block_idx, source_name)
	
	def sendPing(self):
		"""Send ping to server"""
		return self._sendPing()
	
	def sendMessage(self, message_dict):
		"""Send a JSON message to the server"""
		if self.webSocket and self.isConnected():
			try:
				message = json.dumps(message_dict)
				self.webSocket.sendText(message)  # Use WebSocketDAT method
				debug(f'[NDI Info Ext] Message sent: {message_dict.get("action", "unknown")}')
				return True
			except Exception as e:
				debug(f'[NDI Info Ext] Error sending message: {e}')
				return False
		else:
			debug('[NDI Info Ext] Cannot send message: not connected')
			return False
	
	def _requestState(self):
		"""Internal method to request current state from the server"""
		return self.sendMessage({'action': 'request_state'})
	
	def _refreshSources(self):
		"""Internal method to request server to refresh its sources"""
		return self.sendMessage({'action': 'refresh_sources'})
	
	def _setSource(self, block_idx, source_name):
		"""Internal method to request server to set a source for a specific block"""
		return self.sendMessage({
			'action': 'set_source',
			'block_idx': block_idx,
			'source_name': source_name
		})
	
	def _sendPing(self):
		"""Internal method to send ping to server"""
		return self.sendMessage({'action': 'ping'})

	def onReconnectTimerTrigger(self):
		"""TouchDesigner callback when reconnect timer done"""
		self.ownerComp.par.Restart.pulse()
	
	# WebSocket event handlers (called from websocket callbacks)
	def onWebSocketConnect(self, dat):
		"""Called when WebSocket connection is established"""
		debug('[NDI Info Ext] Connected to NDI Named Router server')
		# Register as info-only client with auto-update preference
		self.sendMessage({
			'action': 'register_client',
			'client_type': 'info',
			'auto_update': self.isPeriodicUpdate  # Only get broadcasts if periodic updates are enabled
		})
		# Request initial state from server
		self.reconnectTimer.par.initialize.pulse()
		self._requestState()
	
	def onWebSocketDisconnect(self, dat):
		"""Called when WebSocket connection is closed"""
		debug('[NDI Info Ext] Disconnected from NDI Named Router server')
		self.reconnectTimer.par.start.pulse()
	
	def onWebSocketReceiveText(self, dat, message):
		"""Called when text message is received from server"""
		debug(f'[NDI Info Ext] Received WebSocket message: {message[:100]}...')
		
		try:
			data = json.loads(message)
			action = data.get('action', 'unknown')
			
			debug(f'[NDI Info Ext] Processing action: {action}')
			
			if action == 'state_update':
				# Handle state update from server
				self.handleStateUpdate(data.get('state', {}))
				
			elif action == 'source_changed':
				# Handle individual source change notifications
				block_idx = data.get('block_idx')
				source_name = data.get('source_name')
				self.handleSourceChange(block_idx, source_name)
				
			elif action == 'pong':
				debug('[NDI Info Ext] Received pong response')
				
			elif action == 'error':
				error_msg = data.get('message', 'Unknown error')
				debug(f'[NDI Info Ext] Server error: {error_msg}')
				
			else:
				debug(f'[NDI Info Ext] Unknown action received: {action}')
				
		except json.JSONDecodeError as e:
			debug(f'[NDI Info Ext] Error parsing JSON message: {e}')
		except Exception as e:
			debug(f'[NDI Info Ext] Error processing message: {e}')
	
	def onWebSocketReceiveBinary(self, dat, contents):
		"""Called when binary message is received"""
		debug(f'[NDI Info Ext] Binary message received: {len(contents)} bytes (not implemented)')
	
	def onWebSocketReceivePing(self, dat, contents):
		"""Called when ping is received"""
		debug('[NDI Info Ext] Ping received, sending pong')
		dat.sendPong(contents)
	
	def onWebSocketReceivePong(self, dat, contents):
		"""Called when pong is received"""
		debug('[NDI Info Ext] Pong received')
	
	def onWebSocketMonitorMessage(self, dat, message):
		"""Called for WebSocket status messages"""
		debug(f'[NDI Info Ext] Monitor message: {message}')
	
	def handleStateUpdate(self, state):
		"""Handle state update from server"""
		debug(f'[NDI Info Ext] Handling state update with {len(state)} keys')
		
		try:
			# Store the current state
			self.currentState = state.copy()
			
			# Extract data from state
			output_names = state.get('output_names', [])
			current_sources = state.get('current_sources', [])
			output_resolutions = state.get('output_resolutions', [])
			
			debug(f'[NDI Info Ext] State data - Outputs: {len(output_names)}, Sources: {len(current_sources)}, Resolutions: {len(output_resolutions)}')
			
			# Update each output with the received information
			if output_names:
				self.seqSwitch.numBlocks = len(output_names)
				self.stored['Info'] = {}
			for i in range(len(output_names)):
				output_name = output_names[i] if i < len(output_names) else f'Output {i+1}'
				current_source = current_sources[i] if i < len(current_sources) else ''
				resolution = output_resolutions[i] if i < len(output_resolutions) else [0, 0]
				
				# Call the extension method to set the output info
				self._setOutputInfo(i, output_name, current_source, resolution)
			
			# Final update of Outputs property after all outputs are processed
			self._updateOutputsProperty()
			if not self.isPeriodicUpdate and self.isUpdateOnStart:
				self.timerActive = False
			
			debug('[NDI Info Ext] State update completed')
			
		except Exception as e:
			debug(f'[NDI Info Ext] Error handling state update: {e}')
	
	def handleSourceChange(self, block_idx, source_name):
		"""Handle individual source change notification"""
		debug(f'[NDI Info Ext] Source changed: Block {block_idx} -> {source_name}')
		# You can add additional logic here if needed for individual source changes
		self.seqSwitch[block_idx].par.Currentsource.val = source_name
	
	# def onTimer(self):
	# 	"""Called periodically for auto-reconnect functionality"""
	# 	if self.autoReconnect and not self.isConnected():
	# 		self.reconnectTimer += 1
	# 		if self.reconnectTimer >= self.reconnectInterval:
	# 			debug('Auto-reconnecting to server...')
	# 			self.connectToServer()
	# 			self.reconnectTimer = 0
	# 	else:
	# 		self.reconnectTimer = 0
	
	# Parameter callbacks
	
	def onParRequeststate(self):
		"""Called when Request State parameter is pulsed"""
		debug('Request State parameter triggered')
		self._requestState()
	
	def onParRefreshsources(self):
		"""Called when Refresh Sources parameter is pulsed"""
		debug('Refresh Sources parameter triggered')
		self._refreshSources()
	
	def onParSendping(self):
		"""Called when Send Ping parameter is pulsed"""
		debug('Send Ping parameter triggered')
		self._sendPing()
	
	
	# Data getter methods
	def getCurrentState(self):
		"""Get the current state data"""
		return self.currentState.copy()
	
	def getConnectionStatus(self):
		"""Get connection status string"""
		return 'connected' if self.isConnected() else 'disconnected'
	
	def getNumOutputs(self):
		"""Get number of outputs"""
		return len(self.currentState.get('output_names', []))
	
	def getOutputNames(self):
		"""Get list of output names"""
		return self.currentState.get('output_names', [])
	
	def getCurrentSources(self):
		"""Get list of current sources for each output"""
		return self.currentState.get('current_sources', [])
	
	def getOutputResolutions(self):
		"""Get list of output resolutions"""
		return self.currentState.get('output_resolutions', [])
	
	def getAvailableSources(self):
		"""Get list of available NDI sources"""
		return self.currentState.get('sources', [])


class OutputWrapper:
	"""Wrapper that provides attribute access to Info DependDict"""
	def __init__(self, info_dict, output_info_factory):
		self._info_dict = info_dict
		self._output_info_factory = output_info_factory
	
	def __getattr__(self, name):
		# Convert attribute name to match stored keys (handle spaces, special chars)
		# Try exact match first
		if name in self._info_dict:
			return self._dictToNamedTuple(self._info_dict[name])
		
		# Try with spaces (e.g. projector -> "Projector")
		formatted_name = name.replace('_', ' ').title()
		if formatted_name in self._info_dict:
			return self._dictToNamedTuple(self._info_dict[formatted_name])
		
		# Try common variations
		for key in self._info_dict.keys():
			# Remove spaces and special chars, lowercase for comparison
			clean_key = ''.join(c.lower() for c in key if c.isalnum())
			clean_attr = ''.join(c.lower() for c in name if c.isalnum())
			if clean_key == clean_attr:
				return self._dictToNamedTuple(self._info_dict[key])
		
		# If not found, raise AttributeError with helpful message
		raise AttributeError(f"Output '{name}' not found. Available outputs: {list(self._info_dict.keys())}")
	
	def _dictToNamedTuple(self, data_dict):
		"""Convert dictionary to named tuple for clean interface"""
		if isinstance(data_dict, DependDict):
			# Extract values from Dependency objects if present
			resx_val = data_dict.get('resx', 0)
			resy_val = data_dict.get('resy', 0)
			
			# Handle Dependency objects
			if hasattr(resx_val, 'val'):
				resx_val = resx_val.val
			if hasattr(resy_val, 'val'):
				resy_val = resy_val.val
			
			return self._output_info_factory(
				resx=resx_val,
				resy=resy_val
			)
		else:
			# If it's already a named tuple (shouldn't happen now, but safety)
			return data_dict
	
	def __dir__(self):
		# For autocomplete/introspection - convert keys to valid attribute names
		return [self._keyToAttr(key) for key in self._info_dict.keys()]
	
	def _keyToAttr(self, key):
		"""Convert output name to valid attribute name"""
		# Replace spaces and special chars with underscores, lowercase
		return ''.join(c.lower() if c.isalnum() else '_' for c in key).strip('_')

