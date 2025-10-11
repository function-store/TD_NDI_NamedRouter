'''Info Header Start
Name : NDINamedRouterExt
Author : Dan@DAN-4090
Saveorigin : NDI_NamedRouter.58.toe
Saveversion : 2023.11880
Info Header End'''
import re
import json
import time
from TDStoreTools import StorageManager

CustomParHelper: CustomParHelper = next(d for d in me.docked if 'ExtUtils' in d.tags).mod('CustomParHelper').CustomParHelper # import
####

def debug(message):
	if parent.NDINamedRouter.par.Debugmessages.eval():
		tdu.debug.debug(message)

class NDINamedRouterExt:
	def __init__(self, ownerComp):
		CustomParHelper.Init(self, ownerComp, enable_properties=True, enable_callbacks=True)
		self.ownerComp = ownerComp
		self.ndiTable : ndiDAT = self.ownerComp.op('ndi_watcher')
		
		# Component identification for multi-instance support
		self.componentId = self.ownerComp.par.Componentid.eval() if hasattr(self.ownerComp.par, 'Componentid') else self.ownerComp.name
		
		# Plural handling configuration
		self.enablePluralHandling = True
		
		# Initialize the WebSocket handler
		self.webHandler = WebHandler(self)

		
		self.seqSwitch[0].par.Currentsource.menuLabels = self.sources
		self.seqSwitch[0].par.Currentsource.menuNames = self.sources

		debug(f'NDI Named Switcher Extension initialized with {len(self.sources)} sources')
		debug(f'Plural handling: {"enabled" if self.enablePluralHandling else "disabled"}')

		storedItems = [{'name': 'savedSources', 'readOnly': True}]
		self.stored = StorageManager(self, ownerComp, storedItems)

		run(
			"args[0].updateSourceMapping()",
			self,
			endFrame=True,
			delayRef=op.TDResources
		)

		if self.ownerComp.par.Recalllast.eval():
			run(
				"args[0]._recallSavedSources()",
				self,
				delayMilliSeconds = 1000,
				delayRef=op.TDResources
			)



	def transformPatternForPlurals(self, pattern):
		"""Transform a regex pattern to handle both singular and plural forms
		
		This method adds 's?' to word endings when plural handling is enabled.
		It's designed to be conservative and only modify simple word patterns.
		"""
		if not self.enablePluralHandling:
			return pattern + '\)'
		
		# Only apply to simple patterns that end with word characters
		# This avoids breaking complex regex patterns
		if re.match(r'^[a-zA-Z0-9_.*]+$', pattern):
			# Look for word endings and add s? if they don't already have it
			# This handles patterns like 'projector' -> 'projectors?'
			# But leaves patterns like 'projector.*' or 'projectors?' unchanged
			if re.search(r'[a-zA-Z0-9_]$', pattern) and not pattern.endswith('s?'):
				transformed = pattern + 's?\)'
				return transformed
		
		return pattern + '\)'

	@property#
	def seqSwitch(self):
		return self.ownerComp.seq.Switch

	@property
	def regexPatterns(self):
		patterns = []
		for _block in self.seqSwitch:
			patterns.append(_block.par.Sourceregex.eval())
		return patterns

	@property
	def effectiveRegexPatterns(self):
		"""Get the actual patterns used for matching (after plural transformation)"""
		patterns = []
		for pattern in self.regexPatterns:
			patterns.append(self.transformPatternForPlurals(pattern))
		return patterns

	@property
	def outputNames(self):
		outputNames = []
		for _block in self.seqSwitch:
			outputNames.append(_block.par.Outputname.eval())
		return outputNames

	@property
	def sources(self):
		# list comprehension for backwards compatibility
		return [_cell.val for _cell in self.ndiTable.col('sourceName')[1:]]
	
	@property
	def currentSources(self):
		return [_block.par.Currentsource.eval() for _block in self.seqSwitch]

	@currentSources.setter
	def currentSources(self, values):
		for _block, _source in zip(self.seqSwitch, values):
			_block.par.Currentsource.val = _source

	@property
	def outputResolutions(self):
		"""Get resolution for each output block"""
		resolutions = []
		for i in range(len(self.seqSwitch)):
			try:
				resx = self.seqSwitch[i].par.Resx.eval()
				resy = self.seqSwitch[i].par.Resy.eval()
				resolutions.append((resx, resy))
			except Exception as e:
				debug(f'Error getting resolution for block {i}: {e}')
				resolutions.append((0, 0))  # Default fallback
		return resolutions


	def _saveCurrentSources(self):
		savedSources = []
		for _block in self.seqSwitch:
			savedSources.append({'source': _block.par.Currentsource.eval(), 'showPlaceholder': _block.par.Showplaceholder.eval()})
		self.stored['savedSources'] = savedSources
		debug(f'Saved current sources: {savedSources}')

	def _recallSavedSources(self):
		savedSources = self.stored['savedSources']
		for _block, _source in zip(self.seqSwitch, savedSources):
			if _source['source'] in self.seqSwitch[0].par.Currentsource.menuNames:
				_block.par.Currentsource.val = _source['source']
				_block.par.Showplaceholder.val = _source['showPlaceholder']
			else:
				_block.par.Showplaceholder.val = True
		debug(f'Recalled saved sources: {savedSources}')

	def onProjectPreSave(self):
		# save sources
		#self._saveCurrentSources()
		pass

	def onParSavecurrent(self):
		self._saveCurrentSources()
		if self.ownerComp.par.enableexternaltox.eval():
			self.ownerComp.saveExternalTox()
		project.save()

	def onParLockglobal(self, val):
		"""Called when global lock parameter changes"""
		debug(f'Global lock changed to: {val}')
		# Broadcast state update to web interface
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()



	def onParRecallsaved(self):
		self._recallSavedSources()

	def getCurrentState(self):
		"""Get current state for WebSocket communication"""
		try:
			state = {
				'component_id': self.componentId,
				'component_name': self.ownerComp.name,
				'sources': self.sources,
				'output_names': self.outputNames,
				'current_sources': [block.par.Currentsource.val for block in self.seqSwitch],
				'regex_patterns': self.regexPatterns,
				'effective_regex_patterns': self.effectiveRegexPatterns,
				'plural_handling_enabled': self.enablePluralHandling,
				'output_resolutions': self.outputResolutions,
				'lock_global': self.ownerComp.par.Lockglobal.eval(),
				'locks': [block.par.Lock.eval() for block in self.seqSwitch],
				'last_update': time.time()
			}
			return state
		except Exception as e:
			debug(f'Error getting current state: {e}')
			return {}

	def handleSetSource(self, block_idx, source_name):
		"""Handle source selection from web interface"""
		try:
			if block_idx is not None and block_idx < len(self.seqSwitch):
				self.seqSwitch[block_idx].par.Currentsource.val = source_name
				debug(f'Set source for block {block_idx}: {source_name}')
				
				# Broadcast the change to all connected clients
				# Note: onSeqSwitchNCurrentsource callback will also call broadcastSourceChange
				# but we also broadcast here to ensure immediate sync
				if hasattr(self, 'webHandler'):
					self.webHandler.broadcastSourceChange(block_idx, source_name)
				return True
			else:
				debug(f'Invalid block index: {block_idx}')
				return False
		except Exception as e:
			debug(f'Error setting source: {e}')
			return False

	def handleRefreshSources(self):
		"""Handle refresh sources request from web interface"""
		try:
			debug('Refreshing sources from web interface')
			self.RefreshSourceMapping()
			return True
		except Exception as e:
			debug(f'Error refreshing sources: {e}')
			return False

	def handleSaveConfiguration(self):
		"""Handle save configuration request from web interface"""
		try:
			debug('Saving current configuration from web interface')
			self.onParSavecurrent()
			return True
		except Exception as e:
			debug(f'Error saving configuration: {e}')
			return False

	def handleRecallConfiguration(self):
		"""Handle recall configuration request from web interface"""
		try:
			debug('Recalling saved configuration from web interface')
			self._recallSavedSources()
			return True
		except Exception as e:
			debug(f'Error recalling configuration: {e}')
			return False

	def onSeqSwitchNSourceregex(self, idx, val):
		debug(f'onSeqSwitchNSourceregex: {idx} {val}')
		return

	def onSeqSwitchNCurrentsource(self, idx, val):
		_comp = self.ownerComp.op(f'ndi{idx}')
		_op = _comp.op('ndiin1')
		_op.par.name = val
		#self.seqSwitch[idx].par.Showplaceholder.val = False
		
		# Notify web clients of source change
		debug(f'Source changed for block {idx}: {val}')
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastSourceChange(idx, val)

	def onSeqSwitchNResx(self, idx, val):
		"""Called when resolution X changes for a block"""
		debug(f'Resolution X for block {idx} changed to: {val}')
		# Broadcast state update to web interface
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()
	
	def onSeqSwitchNResy(self, idx, val):
		"""Called when resolution Y changes for a block"""
		debug(f'Resolution Y for block {idx} changed to: {val}')
		# Broadcast state update to web interface
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()

	def onSeqSwitchNLock(self, idx, val):
		"""Called when individual block lock parameter changes"""
		debug(f'Lock for block {idx} changed to: {val}')
		# Broadcast state update to web interface
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()

	def updateSourceMapping(self, latestSourceName=None):
		"""Update source mapping based on current sources and regex patterns
		
		Note: All regex matching and source name comparisons are case-insensitive
		Respects lock states - locked outputs won't be automatically updated
		"""
		# Check global lock - if enabled, skip all auto-routing
		if self.ownerComp.par.Lockglobal.eval():
			debug('Global lock enabled - skipping auto-routing')
			return
		
		sources = self.sources
		if not isinstance(sources, list):
			sources = [sources]
		
		matched_idxs = []
		
		if latestSourceName:
			# When latestSourceName is provided: Only update blocks whose regex patterns match this latest source
			debug(f'Updating only blocks that match latest source: {latestSourceName}')
			
			for blockIdx, pattern in enumerate(self.regexPatterns):
				# Check if this specific block is locked
				if self.seqSwitch[blockIdx].par.Lock.eval():
					debug(f'Block {blockIdx} is locked - skipping auto-routing')
					continue
				
				# Apply plural handling transformation if enabled
				transformedPattern = self.transformPatternForPlurals(pattern)
				
				debug(f'Checking block {blockIdx} with pattern {transformedPattern} for latest source {latestSourceName}')
				# Check if the latest source matches this block's pattern
				if re.fullmatch(transformedPattern, latestSourceName, re.IGNORECASE):
					debug(f'Latest source {latestSourceName} matches pattern {blockIdx}: {transformedPattern}')
					
					# Use the full source name directly
					self.seqSwitch[blockIdx].par.Currentsource.val = latestSourceName
					matched_idxs.append(blockIdx)
					debug(f'Updated block {blockIdx} to use latest source: {latestSourceName}')
				else:
					# Check if current source is still valid for this block (don't change it)
					currentSource = self.seqSwitch[blockIdx].par.Currentsource.val
					if currentSource:
						if re.fullmatch(transformedPattern, currentSource, re.IGNORECASE):
							matched_idxs.append(blockIdx)
							debug(f'Block {blockIdx} keeping current source: {currentSource}')
		else:
			# When not using latest source: For each block, if current output matches regex, keep it. Otherwise find a matching one.
			debug('Updating all blocks based on current state')
			for blockIdx, pattern in enumerate(self.regexPatterns):
				# Check if this specific block is locked
				if self.seqSwitch[blockIdx].par.Lock.eval():
					debug(f'Block {blockIdx} is locked - skipping auto-routing')
					continue
				
				# this is to prevent overriding a manual source change
				if self.seqSwitch[blockIdx].par.Currentsource.eval() in sources:
					debug(f'current source is already in prev sources, nothing to do really')
					matched_idxs.append(blockIdx)
					continue

				# Apply plural handling transformation if enabled
				transformedPattern = self.transformPatternForPlurals(pattern)
				debug(f'Checking block {blockIdx} with pattern: {pattern} -> {transformedPattern}')
				
				# First check if current source still matches the pattern
				currentSource = self.seqSwitch[blockIdx].par.Currentsource.val
				currentStillMatches = False
				
				if currentSource:
					if re.fullmatch(transformedPattern, currentSource, re.IGNORECASE):
						# Current source still matches, keep it
						currentStillMatches = True
						matched_idxs.append(blockIdx)
						debug(f'Block {blockIdx} keeping current source: {currentSource} (still matches pattern)')
				
				# If current source doesn't match, find a new matching source
				if not currentStillMatches:
					matchingSource = None
					
					# Find first source that matches this pattern
					for source in sources:
						if re.fullmatch(transformedPattern, source, re.IGNORECASE):
							matchingSource = source
							debug(f'Source {source} matches pattern {transformedPattern} (case-insensitive)')
							break
					
					# Use the matching source if found
					if matchingSource:
						self.seqSwitch[blockIdx].par.Currentsource.val = matchingSource
						matched_idxs.append(blockIdx)
						debug(f'Updated block {blockIdx} to new matching source: {matchingSource}')
					else:
						debug(f'No sources match pattern {blockIdx}: {transformedPattern}')
		
		debug(f"Updated source mapping {self.seqSwitch}")
		if latestSourceName is not None and matched_idxs:
			for _idx in matched_idxs:
				self.seqSwitch[_idx].par.Showplaceholder.val = False
		
		# Notify web clients of state changes
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()
		
	def onSourceAppeared(self, dat, _sources):
	
		latestSource = _sources[0].sourceName
		sources = [_source.sourceName for _source in _sources]
		for _source in sources:
			if _source not in self.seqSwitch[0].par.Currentsource.menuLabels:
				labels = self.seqSwitch[0].par.Currentsource.menuLabels
				names = self.seqSwitch[0].par.Currentsource.menuNames
				labels.append(_source)
				names.append(_source)
				self.seqSwitch[0].par.Currentsource.menuLabels = labels
				self.seqSwitch[0].par.Currentsource.menuNames = names
		debug(f'updating menus with {sources} cause they appeared')

		for _source in sources:
			# Update source mapping with the latest source having priority
			debug(f'updating source mapping for {_source} because it appeared')
			self.updateSourceMapping(_source)
		
		# Note: updateSourceMapping already calls broadcastStateUpdate()


	def onSourceDisappeared(self, dat, sources):
		for _source in sources:
			_source = _source.sourceName
			if _source in self.seqSwitch[0].par.Currentsource.menuLabels:
				labels = self.seqSwitch[0].par.Currentsource.menuLabels
				names = self.seqSwitch[0].par.Currentsource.menuNames
				saved_sources = self.currentSources
				labels.remove(_source)
				names.remove(_source)
				self.seqSwitch[0].par.Currentsource.menuLabels = labels
				self.seqSwitch[0].par.Currentsource.menuNames = names
				self.currentSources = saved_sources
		debug(f'updating menus after sources disappeared')
		
		# Update source mapping after sources disappeared
		self.updateSourceMapping()
		
		# Note: updateSourceMapping already calls broadcastStateUpdate()


	def RefreshSourceMapping(self):
		"""Call this method to manually refresh the source mapping"""
		debug('Manually refreshing source mapping')
		self.updateSourceMapping()
		# Broadcast state update after refresh
		if hasattr(self, 'webHandler'):
			self.webHandler.broadcastStateUpdate()

	def onReconnectTimerTrigger(self):
		"""TouchDesigner callback when reconnect timer done"""
		self.ownerComp.par.Restart.pulse()

class WebHandler:
	"""Handler class for WebSocket communication with bridge server"""
	
	def __init__(self, extension):
		self.extension = extension
		self.webSocketDAT : webSocketDAT = self.extension.ownerComp.op('websocket1')
		self.reconnectTimer = self.extension.ownerComp.op('timer1')
		

	def onConnect(self, webSocketDat ):
		"""Called when bridge server connects"""
		debug(f'Bridge server connected to DAT: {webSocketDat.name}')
		# Send initial state to bridge when it connects
		self.reconnectTimer.par.initialize.pulse()
		self.sendInitialState(webSocketDat)
		debug(f'Initial state sent to bridge')
		return

	def onDisconnect(self, webSocketDat):
		"""Called when bridge server disconnects"""
		debug(f'Bridge server disconnected from DAT: {webSocketDat.name}')
		self.reconnectTimer.par.start.pulse()
		return

	def sendToBridge(self, message, webSocketDAT=None):
		"""Send message to bridge server (which broadcasts to all browsers)"""
		if webSocketDAT is None:
			webSocketDAT = self.webSocketDAT
			
		if not webSocketDAT:
			debug('ERROR: No WebSocket DAT available for sending')
			return
			
		try:
			webSocketDAT.sendText(message)
			debug(f'Message sent to bridge')
		except Exception as e:
			debug(f'Failed to send to bridge: {e}')
		
	def broadcastStateUpdate(self, webSocketDAT=None):
		"""Send current state to bridge (which broadcasts to all browsers)"""
		debug('Sending state update to bridge')
		
		if self.extension:
			state = self.extension.getCurrentState()
			debug(f'Current state: {len(state)} keys')
			response = {
				'action': 'state_update',
				'state': state
			}
			message = json.dumps(response)
			debug(f'Sending state: {message[:200]}...')
			self.sendToBridge(message, webSocketDAT)
			debug('State sent to bridge')
		else:
			debug('WARNING: Extension not found')
			
	def broadcastSourceChange(self, block_idx, source_name, webSocketDAT=None):
		"""Send source change to bridge (which broadcasts to all browsers)"""
		debug(f'Sending source change to bridge: block_idx={block_idx}, source_name={source_name}')
		
		response = {
			'action': 'source_changed',
			'block_idx': block_idx,
			'source_name': source_name
		}
		message = json.dumps(response)
		debug(f'Source change message: {response}')
		self.sendToBridge(message, webSocketDAT)
		debug('Source change sent to bridge')
		
	def sendInitialState(self, webSocketDAT):
		"""Send initial state to bridge (bridge will forward to requesting browser)"""
		debug('Sending initial state to bridge')
		
		if self.extension:
			debug('Extension found, getting current state...')
			state = self.extension.getCurrentState()
			debug(f'Current state retrieved: {len(state)} keys')
			response = {
				'action': 'state_update',
				'state': state
			}
			debug(f'Sending state response: {json.dumps(response)[:200]}...')
			webSocketDAT.sendText(json.dumps(response))
			debug('Initial state sent to bridge')
		else:
			debug('WARNING: Extension not found, cannot send initial state')
			
	def handleMessage(self, webSocketDAT, client, message):
		"""Handle incoming WebSocket messages"""
		#debug(f'Handling message: {message}')
		
		try:
			data = json.loads(message)
			#debug(f'JSON parsed successfully: {data}')
			action = data.get('action')
			#debug(f'Action extracted: {action}')
			
			if not self.extension:
				debug('ERROR: Extension not found, sending error response')
				error_response = {
					'action': 'error',
					'message': 'NDI Named Switcher extension not found'
				}
				webSocketDAT.sendText( json.dumps(error_response))
				return
			
			if action == 'request_state':
				debug('Processing request_state action')
				state = self.extension.getCurrentState()
				debug(f'Retrieved state for request: {len(state)} keys')
				response = {
					'action': 'state_update',
					'state': state
				}
				debug(f'Sending state response for request: {json.dumps(response)[:200]}...')
				webSocketDAT.sendText( json.dumps(response))
				debug('State response sent successfully')
				
			elif action == 'set_source':
				debug('Processing set_source action')
				block_idx = data.get('block_idx')
				source_name = data.get('source_name')
				debug(f'Set source parameters: block_idx={block_idx}, source_name={source_name}')
				
				if block_idx is not None and source_name is not None:
					debug('Valid set_source parameters, calling extension handler')
					success = self.extension.handleSetSource(block_idx, source_name)
					debug(f'Extension handleSetSource result: {success}')
					
					if success:
						debug('Set source successful, getting updated state')
						state = self.extension.getCurrentState()
						debug(f'Updated state retrieved: {len(state)} keys')
						response = {
							'action': 'state_update',
							'state': state
						}
						debug(f'Sending updated state: {json.dumps(response)[:200]}...')
						webSocketDAT.sendText( json.dumps(response))
						debug('Updated state sent successfully')
					else:
						debug('Set source failed, sending error response')
						error_response = {
							'action': 'error',
							'message': f'Failed to set source for block {block_idx}'
						}
						webSocketDAT.sendText( json.dumps(error_response))
				else:
					debug('Invalid set_source parameters, sending error response')
					error_response = {
						'action': 'error',
						'message': 'Invalid set_source parameters'
					}
					webSocketDAT.sendText( json.dumps(error_response))
			
			elif action == 'refresh_sources':
				debug('Processing refresh_sources action')
				success = self.extension.handleRefreshSources()
				debug(f'Extension handleRefreshSources result: {success}')
				
				if success:
					debug('Refresh sources successful, getting updated state')
					state = self.extension.getCurrentState()
					debug(f'Updated state after refresh: {len(state)} keys')
					response = {
						'action': 'state_update',
						'state': state
					}
					debug(f'Sending refreshed state: {json.dumps(response)[:200]}...')
					webSocketDAT.sendText( json.dumps(response))
					debug('Refreshed state sent successfully')
				else:
					debug('Refresh sources failed, sending error response')
					error_response = {
						'action': 'error',
						'message': 'Failed to refresh sources'
					}
					webSocketDAT.sendText( json.dumps(error_response))
			
			elif action == 'set_lock':
				debug('Processing set_lock action')
				block_idx = data.get('block_idx')
				locked = data.get('locked')
				debug(f'Set lock parameters: block_idx={block_idx}, locked={locked}')
				
				if block_idx is not None and locked is not None:
					if block_idx < len(self.extension.seqSwitch):
						self.extension.seqSwitch[block_idx].par.Lock.val = locked
						debug(f'Set lock for block {block_idx}: {locked}')
						
						# Send updated state
						state = self.extension.getCurrentState()
						response = {
							'action': 'state_update',
							'state': state
						}
						webSocketDAT.sendText(json.dumps(response))
						debug('Lock state updated successfully')
					else:
						error_response = {
							'action': 'error',
							'message': f'Invalid block index: {block_idx}'
						}
						webSocketDAT.sendText(json.dumps(error_response))
				else:
					error_response = {
						'action': 'error',
						'message': 'Invalid set_lock parameters'
					}
					webSocketDAT.sendText(json.dumps(error_response))
			
			elif action == 'set_lock_global':
				debug('Processing set_lock_global action')
				locked = data.get('locked')
				debug(f'Set global lock: {locked}')
				
				if locked is not None:
					self.extension.ownerComp.par.Lockglobal.val = locked
					debug(f'Set global lock: {locked}')
					
					# Send updated state
					state = self.extension.getCurrentState()
					response = {
						'action': 'state_update',
						'state': state
					}
					webSocketDAT.sendText(json.dumps(response))
					debug('Global lock state updated successfully')
				else:
					error_response = {
						'action': 'error',
						'message': 'Invalid set_lock_global parameters'
					}
					webSocketDAT.sendText(json.dumps(error_response))
			
			elif action == 'save_configuration':
				debug('Processing save_configuration action')
				success = self.extension.handleSaveConfiguration()
				debug(f'Extension handleSaveConfiguration result: {success}')
				
				if success:
					debug('Save configuration successful, getting updated state')
					state = self.extension.getCurrentState()
					response = {
						'action': 'configuration_saved',
						'state': state,
						'message': 'Configuration saved successfully'
					}
					debug('Sending configuration saved response')
					webSocketDAT.sendText( json.dumps(response))
					debug('Configuration saved response sent successfully')
				else:
					debug('Save configuration failed, sending error response')
					error_response = {
						'action': 'error',
						'message': 'Failed to save configuration'
					}
					webSocketDAT.sendText( json.dumps(error_response))
			
			elif action == 'recall_configuration':
				debug('Processing recall_configuration action')
				success = self.extension.handleRecallConfiguration()
				debug(f'Extension handleRecallConfiguration result: {success}')
				
				if success:
					debug('Recall configuration successful, getting updated state')
					state = self.extension.getCurrentState()
					response = {
						'action': 'configuration_recalled',
						'state': state,
						'message': 'Configuration recalled successfully'
					}
					debug('Sending configuration recalled response')
					webSocketDAT.sendText( json.dumps(response))
					debug('Configuration recalled response sent successfully')
				else:
					debug('Recall configuration failed, sending error response')
					error_response = {
						'action': 'error',
						'message': 'Failed to recall configuration'
					}
					webSocketDAT.sendText( json.dumps(error_response))
			
			elif action == 'ping':
				#debug('Processing ping action')
				pong_response = {
					'action': 'pong',
					'timestamp': time.time()
				}
				#debug('Sending pong response')
				webSocketDAT.sendText( json.dumps(pong_response))
				#debug('Pong response sent')
			
			elif action == 'error':
				# Ignore error messages (they're informational only, don't respond)
				debug(f'Error message received: {data.get("message")}')
			
			elif action == 'state_update':
				# Ignore state updates from other components (we only send these, not receive)
				debug('Received state_update from another component (ignoring)')
			
			elif action == 'source_changed':
				# Ignore source change notifications from other components
				debug('Received source_changed from another component (ignoring)')
			
			elif action == 'configuration_saved':
				# Ignore configuration saved notifications from other components
				debug('Received configuration_saved from another component (ignoring)')
			
			elif action == 'configuration_recalled':
				# Ignore configuration recalled notifications from other components
				debug('Received configuration_recalled from another component (ignoring)')
			
			else:
				debug(f'Unknown action received: {action}')
				error_response = {
					'action': 'error',
					'message': f'Unknown action: {action}'
				}
				webSocketDAT.sendText( json.dumps(error_response))
		
		except Exception as e:
			debug(f'Exception in handleMessage: {e}')
			error_response = {
				'action': 'error',
				'message': f'Error processing message: {str(e)}'
			}
			webSocketDAT.sendText( json.dumps(error_response))

	def _outputResolution(self, block_idx):
		return self.mapping[block_idx].par.Resx.eval(), self.mapping[block_idx].par.Resy.eval()