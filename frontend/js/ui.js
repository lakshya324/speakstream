/**
 * UIController - Manages the user interface and user interactions
 */
class UIController {
    constructor(wsClient, audioPlayer) {
        this.wsClient = wsClient;
        this.audioPlayer = audioPlayer;
        this.currentBotMessage = null;
        this.messageCount = 0;
        
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
        this.updateUI();
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
        });
        
        // Initialize audio on first user interaction
        document.addEventListener('click', () => {
            this.audioPlayer.forceInitialize();
        }, { once: true });
        
        // Update debug info periodically
        setInterval(() => {
            this.updateDebugInfo();
        }, 1000);
    }
    
    setupWebSocketEvents() {
        // Handle text chunks
        this.wsClient.on('textChunk', (chunkData) => {
            this.appendTextToCurrentBotMessage(chunkData.data);
        });
        
        // Handle audio chunks
        this.wsClient.on('audioChunk', (chunkData) => {
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
    }\n    \n    showAudioIndicator(chunkData) {\n        if (!this.currentBotMessage) return;\n        \n        const audioIndicator = this.currentBotMessage.querySelector('.audio-indicator');\n        if (audioIndicator) {\n            audioIndicator.className = 'audio-indicator playing';\n            audioIndicator.innerHTML = '🔊 <span class=\"audio-wave\"><span></span><span></span><span></span></span> Playing audio...';\n        }\n    }\n    \n    clearChat() {\n        this.elements.chatMessages.innerHTML = '';\n        this.currentBotMessage = null;\n        this.messageCount = 0;\n        this.audioPlayer.stopAllAudio();\n        this.showSuccess('Chat cleared');\n    }\n    \n    toggleMute() {\n        const isMuted = !this.audioPlayer.isMuted();\n        this.audioPlayer.setMuted(isMuted);\n        \n        this.elements.muteButton.textContent = isMuted ? '🔇 Audio Off' : '🔊 Audio On';\n        \n        if (isMuted) {\n            this.showSuccess('Audio muted');\n        } else {\n            this.showSuccess('Audio unmuted');\n        }\n    }\n    \n    setVolume(value) {\n        const volume = parseInt(value) / 100;\n        this.audioPlayer.setVolume(volume);\n        this.elements.volumeDisplay.textContent = `${value}%`;\n    }\n    \n    stopAudio() {\n        this.audioPlayer.stopAllAudio();\n        this.showSuccess('Audio stopped');\n    }\n    \n    updateUI() {\n        const connected = this.wsClient.isConnected();\n        \n        // Update connect button\n        this.elements.connectButton.textContent = connected ? 'Disconnect' : 'Connect';\n        this.elements.connectButton.className = connected ? 'connect-btn connected' : 'connect-btn';\n        this.elements.connectButton.disabled = false;\n        \n        // Update input and send button\n        this.elements.messageInput.disabled = !connected;\n        this.elements.sendButton.disabled = !connected || !this.elements.messageInput.value.trim();\n        \n        // Update placeholder\n        this.elements.messageInput.placeholder = connected ? \n            'Type your message here...' : \n            'Connect to start chatting...';\n    }\n    \n    updateAudioInfo(audioState) {\n        if (this.elements.audioQueueInfo) {\n            this.elements.audioQueueInfo.textContent = `Audio Queue: ${audioState.queueLength} chunks`;\n        }\n    }\n    \n    updateDebugInfo() {\n        const wsState = this.wsClient.getState();\n        const audioState = this.audioPlayer.getState();\n        \n        if (this.elements.tokensInfo) {\n            this.elements.tokensInfo.textContent = `Messages: ${this.messageCount} | Queue: ${audioState.queueLength}`;\n        }\n    }\n    \n    showError(message) {\n        this.showNotification(message, 'error');\n    }\n    \n    showSuccess(message) {\n        this.showNotification(message, 'success');\n    }\n    \n    showNotification(message, type = 'info') {\n        // Create notification element\n        const notification = document.createElement('div');\n        notification.className = `${type}-message`;\n        notification.textContent = message;\n        \n        // Add to chat area\n        this.elements.chatMessages.appendChild(notification);\n        \n        // Auto remove after 3 seconds\n        setTimeout(() => {\n            if (notification.parentNode) {\n                notification.parentNode.removeChild(notification);\n            }\n        }, 3000);\n        \n        this.scrollToBottom();\n    }\n    \n    scrollToBottom() {\n        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;\n    }\n}
