/**
 * AudioPlayer - Handles Web Audio API for real-time audio playback
 */
class AudioPlayer {
    constructor() {
        this.audioContext = null;
        this.audioQueue = [];
        this.isPlaying = false;
        this.isMuted = false;
        this.volume = 0.8;
        this.currentSource = null;
        this.nextPlayTime = 0;
        
        // Initialize audio context on user interaction
        this.initialized = false;
        this.setupAudioContext();
    }
    
    async setupAudioContext() {
        try {
            // Create AudioContext
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create gain node for volume control
            this.gainNode = this.audioContext.createGain();
            this.gainNode.connect(this.audioContext.destination);
            this.gainNode.gain.value = this.volume;
            
            console.log('🔊 Audio context initialized');
            this.initialized = true;
            
        } catch (error) {
            console.error('❌ Failed to initialize audio context:', error);
        }
    }
    
    async ensureAudioContext() {
        if (!this.initialized || this.audioContext.state === 'suspended') {
            try {
                await this.audioContext.resume();
                console.log('🔊 Audio context resumed');
            } catch (error) {
                console.error('❌ Failed to resume audio context:', error);
            }
        }
    }
    
    async playAudioChunk(base64Audio, chunkId) {
        if (!this.initialized || this.isMuted) {
            return;
        }
        
        try {
            await this.ensureAudioContext();
            
            // Decode base64 to ArrayBuffer
            const audioData = this.base64ToArrayBuffer(base64Audio);
            
            // Decode audio data
            const audioBuffer = await this.audioContext.decodeAudioData(audioData);
            
            // Calculate when to play this chunk
            const currentTime = this.audioContext.currentTime;
            const playTime = Math.max(currentTime, this.nextPlayTime);
            
            // Create and configure audio source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.gainNode);
            
            // Start playing
            source.start(playTime);
            
            // Update next play time
            this.nextPlayTime = playTime + audioBuffer.duration;
            
            // Add to queue for tracking
            this.audioQueue.push({
                chunkId,
                duration: audioBuffer.duration,
                playTime,
                source
            });
            
            console.log(`🔊 Playing audio chunk ${chunkId} at ${playTime.toFixed(2)}s (duration: ${audioBuffer.duration.toFixed(2)}s)`);
            
            // Clean up old chunks
            this.cleanupOldChunks();
            
            // Handle source end
            source.onended = () => {
                this.removeFromQueue(chunkId);
            };
            
            this.updatePlayingState();
            
        } catch (error) {
            console.error(`❌ Error playing audio chunk ${chunkId}:`, error);
        }
    }
    
    base64ToArrayBuffer(base64) {
        // Remove data URL prefix if present
        const base64Data = base64.includes(',') ? base64.split(',')[1] : base64;
        
        // Decode base64
        const binaryString = window.atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        return bytes.buffer;
    }
    
    stopAllAudio() {
        try {
            // Stop all playing sources
            this.audioQueue.forEach(chunk => {
                if (chunk.source) {
                    chunk.source.stop();
                }
            });
            
            // Clear queue
            this.audioQueue = [];
            this.nextPlayTime = this.audioContext ? this.audioContext.currentTime : 0;
            this.isPlaying = false;
            
            console.log('⏹️ All audio stopped');
            this.updatePlayingState();
            
        } catch (error) {
            console.error('❌ Error stopping audio:', error);
        }
    }
    
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.gainNode) {
            this.gainNode.gain.value = this.volume;
        }
        console.log(`🔊 Volume set to ${(this.volume * 100).toFixed(0)}%`);
    }
    
    setMuted(muted) {
        this.isMuted = muted;
        if (muted) {
            this.stopAllAudio();
        }
        console.log(`🔊 Audio ${muted ? 'muted' : 'unmuted'}`);
    }
    
    isMuted() {
        return this.isMuted;
    }
    
    getQueueLength() {
        return this.audioQueue.length;
    }
    
    getQueueDuration() {
        const currentTime = this.audioContext ? this.audioContext.currentTime : 0;
        return Math.max(0, this.nextPlayTime - currentTime);
    }
    
    cleanupOldChunks() {
        const currentTime = this.audioContext ? this.audioContext.currentTime : 0;
        const bufferTime = 1.0; // Keep 1 second buffer
        
        this.audioQueue = this.audioQueue.filter(chunk => {
            const chunkEndTime = chunk.playTime + chunk.duration;
            return chunkEndTime > (currentTime - bufferTime);
        });
    }
    
    removeFromQueue(chunkId) {
        this.audioQueue = this.audioQueue.filter(chunk => chunk.chunkId !== chunkId);
        this.updatePlayingState();
    }
    
    updatePlayingState() {
        const wasPlaying = this.isPlaying;
        this.isPlaying = this.audioQueue.length > 0;
        
        if (wasPlaying !== this.isPlaying) {
            // Dispatch custom event for UI updates
            const event = new CustomEvent('audioStateChanged', {
                detail: { isPlaying: this.isPlaying, queueLength: this.audioQueue.length }
            });
            window.dispatchEvent(event);
        }
    }
    
    // Get audio context state for debugging
    getState() {
        return {
            initialized: this.initialized,
            contextState: this.audioContext ? this.audioContext.state : 'none',
            queueLength: this.audioQueue.length,
            isPlaying: this.isPlaying,
            volume: this.volume,
            muted: this.isMuted,
            queueDuration: this.getQueueDuration()
        };
    }
    
    // Force initialization (call on user interaction)
    async forceInitialize() {
        if (!this.initialized) {
            await this.setupAudioContext();
        }
        await this.ensureAudioContext();
    }
}
