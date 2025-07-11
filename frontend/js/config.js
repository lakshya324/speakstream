/**
 * Configuration loader for SpeakStream frontend
 * Loads configuration from the backend API
 */
class ConfigLoader {
    constructor() {
        this.config = null;
        this.defaultConfig = {
            websocket_url: "ws://localhost:8000/ws",
            default_volume: 0.8,
            auto_scroll: true,
            save_chat_history: true,
            max_chat_history: 100,
            chunk_size: 1024,
            max_queue_size: 10
        };
    }

    async loadConfig() {
        try {
            const response = await fetch('/config');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.config = await response.json();
            console.log('✅ Configuration loaded:', this.config);
            return this.config;
            
        } catch (error) {
            console.warn('⚠️ Failed to load config from server, using defaults:', error.message);
            this.config = { ...this.defaultConfig };
            return this.config;
        }
    }

    get(key) {
        if (!this.config) {
            console.warn('⚠️ Config not loaded yet, using default for:', key);
            return this.defaultConfig[key];
        }
        return this.config[key] ?? this.defaultConfig[key];
    }

    getWebSocketUrl() {
        return this.get('websocket_url');
    }

    getDefaultVolume() {
        return this.get('default_volume');
    }

    shouldAutoScroll() {
        return this.get('auto_scroll');
    }

    shouldSaveChatHistory() {
        return this.get('save_chat_history');
    }

    getMaxChatHistory() {
        return this.get('max_chat_history');
    }

    getChunkSize() {
        return this.get('chunk_size');
    }

    getMaxQueueSize() {
        return this.get('max_queue_size');
    }
}

// Create global config instance
window.appConfig = new ConfigLoader();
