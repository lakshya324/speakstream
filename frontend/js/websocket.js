/**
 * WebSocketClient - Handles WebSocket communication with the backend
 */
class WebSocketClient {
    constructor(audioPlayer) {
        this.ws = null;
        this.audioPlayer = audioPlayer;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageHandlers = new Map();
        this.responseStartTime = null;
        this.currentResponse = {
            chunks: [],
            audioChunks: [],
            startTime: null
        };
        
        // Set up event handlers
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Handle connection status changes
        this.on('connected', () => {
            this.connected = true;
            this.reconnectAttempts = 0;
            console.log('✅ WebSocket connected');
            this.updateConnectionStatus(true);
        });
        
        this.on('disconnected', () => {
            this.connected = false;
            console.log('❌ WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        });
        
        this.on('error', (error) => {
            console.error('❌ WebSocket error:', error);
            this.updateConnectionStatus(false, error);
        });
        
        // Handle different message types
        this.on('response_start', (data) => {
            this.currentResponse = {
                chunks: [],
                audioChunks: [],
                startTime: Date.now()
            };
            console.log('📤 Response generation started');
        });
        
        this.on('chunk', (data) => {
            this.handleChunk(data.data);
        });
        
        this.on('response_complete', (data) => {
            const duration = Date.now() - this.currentResponse.startTime;
            console.log(`✅ Response completed in ${duration}ms`);
            this.updateResponseTime(duration);
        });
        
        this.on('pong', () => {
            console.log('🏓 Pong received');
        });
    }
    
    connect() {
        if (this.connected) {
            return Promise.resolve();
        }
        
        return new Promise((resolve, reject) => {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                console.log(`🔌 Connecting to ${wsUrl}`);
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onopen = () => {
                    this.emit('connected');
                    resolve();
                };
                
                this.ws.onclose = (event) => {
                    this.emit('disconnected', event);
                };
                
                this.ws.onerror = (error) => {
                    this.emit('error', error);
                    reject(error);
                };
                
                this.ws.onmessage = (event) => {
                    this.handleMessage(event.data);
                };
                
            } catch (error) {
                console.error('❌ Failed to create WebSocket:', error);
                reject(error);
            }
        });
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }
    
    sendMessage(message) {
        if (!this.connected || !this.ws) {
            console.error('❌ Cannot send message: not connected');
            return false;
        }
        
        try {
            const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
            this.ws.send(messageStr);
            return true;
        } catch (error) {
            console.error('❌ Failed to send message:', error);
            return false;
        }
    }
    
    sendChatMessage(text) {
        return this.sendMessage({
            type: 'chat',
            message: text
        });
    }
    
    sendPing() {
        return this.sendMessage({
            type: 'ping'
        });
    }
    
    handleMessage(messageStr) {
        try {
            const message = JSON.parse(messageStr);
            const messageType = message.type || 'unknown';
            
            console.log(`📨 Received ${messageType} message`);
            
            // Emit event for this message type
            this.emit(messageType, message);
            
        } catch (error) {
            console.error('❌ Failed to parse message:', error);
        }
    }
    
    handleChunk(chunkData) {
        if (!chunkData) return;
        
        const chunkType = chunkData.type;
        
        if (chunkType === 'text') {
            // Handle text chunk
            this.currentResponse.chunks.push(chunkData.data);
            this.emit('textChunk', chunkData);
            
        } else if (chunkType === 'audio') {
            // Handle audio chunk
            this.currentResponse.audioChunks.push(chunkData);
            this.audioPlayer.playAudioChunk(chunkData.data, chunkData.chunk_id);
            this.emit('audioChunk', chunkData);
            
        } else if (chunkType === 'error') {
            console.error('❌ Server error:', chunkData.data);
            this.emit('serverError', chunkData);
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ Max reconnection attempts reached');
            return;
        }
        
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;
        
        console.log(`🔄 Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.connected) {
                this.connect().catch(error => {
                    console.error('❌ Reconnection failed:', error);
                });
            }
        }, delay);
    }
    
    updateConnectionStatus(connected, error = null) {
        const statusDot = document.getElementById('connection-status');
        const statusText = document.getElementById('connection-text');
        
        if (statusDot && statusText) {
            if (connected) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Connected';
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = error ? `Error: ${error.message}` : 'Disconnected';
            }
        }
    }
    
    updateResponseTime(duration) {
        const responseTimeInfo = document.getElementById('response-time-info');
        if (responseTimeInfo) {
            responseTimeInfo.textContent = `Response Time: ${duration}ms`;
        }
    }
    
    // Event emitter methods
    on(event, handler) {
        if (!this.messageHandlers.has(event)) {
            this.messageHandlers.set(event, []);
        }
        this.messageHandlers.get(event).push(handler);
    }
    
    off(event, handler) {
        if (this.messageHandlers.has(event)) {
            const handlers = this.messageHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emit(event, ...args) {
        if (this.messageHandlers.has(event)) {
            this.messageHandlers.get(event).forEach(handler => {
                try {
                    handler(...args);
                } catch (error) {
                    console.error(`❌ Error in event handler for ${event}:`, error);
                }
            });
        }
    }
    
    isConnected() {
        return this.connected;
    }
    
    getState() {
        return {
            connected: this.connected,
            reconnectAttempts: this.reconnectAttempts,
            wsState: this.ws ? this.ws.readyState : 'none',
            currentResponse: {
                chunks: this.currentResponse.chunks.length,
                audioChunks: this.currentResponse.audioChunks.length,
                duration: this.currentResponse.startTime ? Date.now() - this.currentResponse.startTime : 0
            }
        };
    }
}
