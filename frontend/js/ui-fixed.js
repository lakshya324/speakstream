/**
 * UIController - Manages the user interface and user interactions
 */
class UIController {
    constructor(wsClient, audioPlayer) {
        this.wsClient = wsClient;
        this.audioPlayer = audioPlayer;
        this.currentBotMessage = null;
        this.messageCount = 0;
        this.chatHistory = [];
        
        // Initialize config-dependent properties
        this.initializeFromConfig();
        
        // Get DOM elements
        this.elements = {
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            connectButton: document.getElementById('connect-button'),
            clearButton: document.getElementById('clear-button'),
            muteButton: document.getElementById('mute-button'),
            volumeSlider: document.getElementById('volume-slider'),
            volumeDisplay: document.getElementById('volume-display'),
            stopAudioButton: document.getElementById('stop-audio-button'),
            chatMessages: document.getElementById('chat-messages'),
            audioQueueInfo: document.getElementById('audio-queue-info'),
            responseTimeInfo: document.getElementById('response-time-info'),
            tokensInfo: document.getElementById('tokens-info')
        };
        
        this.setupEventListeners();
        this.setupWebSocketEvents();
        this.loadChatHistory();
        this.updateUI();
    }

    initializeFromConfig() {
        // Set default values from config or fallbacks
        this.maxHistorySize = window.appConfig ? 
            window.appConfig.getMaxChatHistory() : 
            parseInt(localStorage.getItem('maxChatHistory') || '100');
        
        this.autoScroll = window.appConfig ? 
            window.appConfig.shouldAutoScroll() : 
            localStorage.getItem('autoScroll') !== 'false';
        
        this.shouldSaveChatHistory = window.appConfig ? 
            window.appConfig.shouldSaveChatHistory() : 
            localStorage.getItem('saveChatHistory') !== 'false';
    }
    
    setupEventListeners() {
        // Connect/Disconnect button
        this.elements.connectButton.addEventListener('click', () => {
            if (this.wsClient.isConnected()) {
                this.disconnect();
            } else {
                this.connect();
            }
        });
        
        // Send message
        this.elements.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key to send message
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Update send button state when input changes
        this.elements.messageInput.addEventListener('input', () => {
            this.updateUI();
        });
        
        // Clear chat
        this.elements.clearButton.addEventListener('click', () => {
            this.clearChat();
        });
        
        // Audio controls
        this.elements.muteButton.addEventListener('click', () => {
            this.toggleMute();
        });
        
        this.elements.volumeSlider.addEventListener('input', (e) => {
            this.setVolume(e.target.value);
        });
        
        this.elements.stopAudioButton.addEventListener('click', () => {
            this.stopAudio();
        });
        
        // Audio state changes
        window.addEventListener('audioStateChanged', (e) => {
            this.updateAudioInfo(e.detail);
            this.updateAudioIndicators(e.detail);
        });
        
        // Initialize audio on first user interaction
        document.addEventListener('click', async () => {
            console.log('👆 User clicked - initializing audio...');
            await this.audioPlayer.forceInitialize();
        }, { once: true });
        
        // Update debug info periodically
        setInterval(() => {
            this.updateDebugInfo();
        }, 1000);
    }
    
    setupWebSocketEvents() {
        // Handle text chunks
        this.wsClient.on('textChunk', (chunkData) => {
            console.log('📝 UI received text chunk:', chunkData);
            this.appendTextToCurrentBotMessage(chunkData.data);
        });
        
        // Handle audio chunks
        this.wsClient.on('audioChunk', (chunkData) => {
            console.log('🔊 UI received audio chunk:', chunkData);
            this.showAudioIndicator(chunkData);
        });
        
        // Handle response start
        this.wsClient.on('response_start', () => {
            this.createNewBotMessage();
        });
        
        // Handle response complete
        this.wsClient.on('response_complete', (data) => {
            this.finalizeBotMessage();
        });
        
        // Handle errors
        this.wsClient.on('serverError', (errorData) => {
            this.showError(`Server error: ${errorData.data}`);
        });
        
        // Handle connection events
        this.wsClient.on('connected', () => {
            this.showSuccess('Connected to SpeakStream server!');
            this.updateUI();
        });
        
        this.wsClient.on('disconnected', () => {
            this.showError('Disconnected from server');
            this.updateUI();
        });
    }
    
    async connect() {
        try {
            this.elements.connectButton.textContent = 'Connecting...';
            this.elements.connectButton.disabled = true;
            
            // Ensure audio is initialized before connecting
            await this.audioPlayer.forceInitialize();
            
            await this.wsClient.connect();
            
        } catch (error) {
            this.showError(`Failed to connect: ${error.message}`);
        } finally {
            this.updateUI();
        }
    }
    
    disconnect() {
        this.wsClient.disconnect();
        this.audioPlayer.stopAllAudio();
        this.updateUI();
    }
    
    sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.wsClient.isConnected()) {
            return;
        }
        
        // Add user message to chat
        this.addUserMessage(message);
        
        // Send to server
        this.wsClient.sendChatMessage(message);
        
        // Clear input
        this.elements.messageInput.value = '';
        this.updateUI();
    }
    
    addUserMessage(text) {
        const messageDiv = this.createMessageElement('user', text);
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        this.messageCount++;
        
        // Add to chat history
        this.addToHistory('user', text);
    }
    
    createNewBotMessage() {
        this.currentBotMessage = this.createMessageElement('bot', '', true);
        this.elements.chatMessages.appendChild(this.currentBotMessage);
        this.scrollToBottom();
    }
    
    appendTextToCurrentBotMessage(text) {
        if (!this.currentBotMessage) {
            this.createNewBotMessage();
        }
        
        const textElement = this.currentBotMessage.querySelector('.message-text');
        if (textElement) {
            textElement.textContent += text;
            this.scrollToBottom();
        }
    }
    
    finalizeBotMessage() {
        if (this.currentBotMessage) {
            this.currentBotMessage.classList.remove('streaming-message');
            
            // Add final bot message to history
            const textElement = this.currentBotMessage.querySelector('.message-text');
            if (textElement) {
                this.addToHistory('bot', textElement.textContent);
            }
            
            this.currentBotMessage = null;
            this.messageCount++;
        }
    }
    
    createMessageElement(type, text, isStreaming = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}${isStreaming ? ' streaming-message' : ''}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = type === 'user' ? '👤' : '🤖';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const textElement = document.createElement('p');
        textElement.className = 'message-text';
        textElement.textContent = text;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = new Date().toLocaleTimeString();
        
        content.appendChild(textElement);
        content.appendChild(timeElement);
        
        if (type === 'bot') {
            const audioIndicator = document.createElement('div');
            audioIndicator.className = 'audio-indicator';
            audioIndicator.innerHTML = '🔊 <span class="audio-wave"><span></span><span></span><span></span></span> Generating audio...';
            content.appendChild(audioIndicator);
        }
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        
        return messageDiv;
    }
    
    showAudioIndicator(chunkData) {
        if (!this.currentBotMessage) return;
        
        const audioIndicator = this.currentBotMessage.querySelector('.audio-indicator');
        if (audioIndicator) {
            audioIndicator.className = 'audio-indicator playing';
            audioIndicator.innerHTML = '🔊 <span class="audio-wave"><span></span><span></span><span></span></span> Playing audio...';
        }
    }
    
    clearChat() {
        this.elements.chatMessages.innerHTML = '';
        this.currentBotMessage = null;
        this.messageCount = 0;
        this.clearChatHistory();
        this.audioPlayer.stopAllAudio();
        this.showSuccess('Chat cleared');
    }
    
    toggleMute() {
        const isMuted = !this.audioPlayer.isMuted();
        this.audioPlayer.setMuted(isMuted);
        
        this.elements.muteButton.textContent = isMuted ? '🔇 Audio Off' : '🔊 Audio On';
        
        if (isMuted) {
            this.showSuccess('Audio muted');
        } else {
            this.showSuccess('Audio unmuted');
        }
    }
    
    setVolume(value) {
        const volume = parseInt(value) / 100;
        this.audioPlayer.setVolume(volume);
        this.elements.volumeDisplay.textContent = `${value}%`;
    }
    
    stopAudio() {
        this.audioPlayer.stopAllAudio();
        this.showSuccess('Audio stopped');
    }
    
    updateUI() {
        const connected = this.wsClient.isConnected();
        const hasMessage = this.elements.messageInput.value.trim().length > 0;
        
        // Update connect button
        this.elements.connectButton.textContent = connected ? 'Disconnect' : 'Connect';
        this.elements.connectButton.className = connected ? 'connect-btn connected' : 'connect-btn';
        this.elements.connectButton.disabled = false;
        
        // Update input and send button
        this.elements.messageInput.disabled = !connected;
        this.elements.sendButton.disabled = !connected || !hasMessage;
        
        // Update placeholder
        this.elements.messageInput.placeholder = connected ? 
            'Type your message here...' : 
            'Connect to start chatting...';
    }
    
    updateAudioInfo(audioState) {
        if (this.elements.audioQueueInfo) {
            this.elements.audioQueueInfo.textContent = `Audio Queue: ${audioState.queueLength} chunks`;
        }
    }
    
    updateAudioIndicators(audioState) {
        // Update audio indicators based on current audio state
        const audioIndicators = document.querySelectorAll('.audio-indicator');
        audioIndicators.forEach(indicator => {
            if (audioState.isPlaying && audioState.queueLength > 0) {
                indicator.className = 'audio-indicator playing';
                indicator.innerHTML = '🔊 <span class="audio-wave"><span></span><span></span><span></span></span> Playing audio...';
            } else {
                // Audio has finished playing
                indicator.className = 'audio-indicator';
                indicator.innerHTML = '🔊 Audio complete';
            }
        });
    }
    
    updateDebugInfo() {
        const wsState = this.wsClient.getState();
        const audioState = this.audioPlayer.getState();
        
        if (this.elements.tokensInfo) {
            this.elements.tokensInfo.textContent = `Messages: ${this.messageCount} | Queue: ${audioState.queueLength}`;
        }
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `${type}-message`;
        notification.textContent = message;
        
        // Add to chat area
        this.elements.chatMessages.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
        
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        if (this.autoScroll) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }

    // Chat History Management
    addToHistory(type, text) {
        const historyItem = {
            type: type,
            text: text,
            timestamp: Date.now()
        };
        
        this.chatHistory.push(historyItem);
        
        // Keep history within limits
        if (this.chatHistory.length > this.maxHistorySize) {
            this.chatHistory = this.chatHistory.slice(-this.maxHistorySize);
        }
        
        // Save to localStorage if enabled
        if (this.shouldSaveChatHistory) {
            this.saveChatHistory();
        }
    }

    loadChatHistory() {
        try {
            const saved = localStorage.getItem('speakstream_chat_history');
            if (saved) {
                this.chatHistory = JSON.parse(saved);
                this.restoreChatFromHistory();
            }
        } catch (error) {
            console.warn('Failed to load chat history:', error);
            this.chatHistory = [];
        }
    }

    saveChatHistory() {
        try {
            localStorage.setItem('speakstream_chat_history', JSON.stringify(this.chatHistory));
        } catch (error) {
            console.warn('Failed to save chat history:', error);
        }
    }

    restoreChatFromHistory() {
        // Clear current chat
        this.elements.chatMessages.innerHTML = '';
        
        // Restore messages from history
        this.chatHistory.forEach(item => {
            if (item.type === 'user') {
                const messageDiv = this.createMessageElement('user', item.text);
                this.elements.chatMessages.appendChild(messageDiv);
            } else if (item.type === 'bot') {
                const messageDiv = this.createMessageElement('bot', item.text);
                // Remove audio indicator for historical messages
                const audioIndicator = messageDiv.querySelector('.audio-indicator');
                if (audioIndicator) {
                    audioIndicator.remove();
                }
                this.elements.chatMessages.appendChild(messageDiv);
            }
        });
        
        this.messageCount = this.chatHistory.length;
        this.scrollToBottom();
    }

    clearChatHistory() {
        this.chatHistory = [];
        localStorage.removeItem('speakstream_chat_history');
    }
}
