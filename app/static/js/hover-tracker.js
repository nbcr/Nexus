/**
 * DEPRECATED: Hover Tracker Module
 * 
 * This file has been split into two separate modules for better maintainability:
 * - HoverTracker.js - Advanced hover interest tracking for individual cards
 * - GlobalScrollTracker.js - Global scroll velocity coordination
 * 
 * The code below is kept for reference only. Use HoverTracker.js and GlobalScrollTracker.js instead.
 * 
 * See app/static/js/HoverTracker.js and app/static/js/GlobalScrollTracker.js
 * Updated: December 4, 2024
 */

console.warn('⚠️ hover-tracker.js is deprecated. Please use HoverTracker.js and GlobalScrollTracker.js instead.');

// Import the new modules (they are already loaded in index.html)
// window.HoverTracker comes from HoverTracker.js
// window.GlobalScrollTracker comes from GlobalScrollTracker.js

// Original implementation reference below (kept for historical reference only)
// ==================================================================================

class HoverTrackerDeprecated {
    constructor(element, contentId, options = {}) {
        this.element = element;
        this.contentId = contentId;

        // Configuration
        this.config = {
            // Minimum hover time to consider as interest (milliseconds)
            minHoverDuration: options.minHoverDuration || 1500,

            // Time window for detecting AFK (milliseconds)
            afkThreshold: options.afkThreshold || 5000,

            // Movement threshold to consider as "active" (pixels)
            movementThreshold: options.movementThreshold || 5,

            // Micro-movement threshold for repositioning (pixels)
            microMovementThreshold: options.microMovementThreshold || 20,

            // Velocity threshold for "slowdown" detection (pixels/ms)
            slowdownVelocityThreshold: options.slowdownVelocityThreshold || 0.3,

            // Sample rate for velocity calculation (milliseconds)
            velocitySampleRate: options.velocitySampleRate || 100,

            // Interest score threshold to consider as "interested"
            interestScoreThreshold: options.interestScoreThreshold || 50,

            // Scroll velocity threshold (pixels/ms) - lower = slower = more interested
            scrollSlowdownThreshold: options.scrollSlowdownThreshold || 2,
        };

        // State tracking
        this.state = {
            isHovering: false,
            isInViewport: false,
            hoverStartTime: null,
            totalHoverTime: 0,
            lastMousePosition: null,
            lastMouseMoveTime: null,
            mousePositions: [], // Track positions for velocity calculation
            afkStartTime: null,
            isAfk: false,
            movementDetected: false,
            slowdownsDetected: 0,
            microMovementsDetected: 0,
            clicksDetected: 0,
            interestScore: 0,
            lastScrollVelocity: 0,
            scrollSlowdowns: 0,
        };

        // Timers
        this.velocityTimer = null;
        this.afkCheckTimer = null;
        this.reportTimer = null;

        // Bind event handlers
        this.handleMouseEnter = this.handleMouseEnter.bind(this);
        this.handleMouseLeave = this.handleMouseLeave.bind(this);
        this.handleMouseMove = this.handleMouseMove.bind(this);
        this.handleClick = this.handleClick.bind(this);
        this.handleTouchStart = this.handleTouchStart.bind(this);
        this.handleTouchEnd = this.handleTouchEnd.bind(this);

        // Initialize
        this.attachEventListeners();
    }

    attachEventListeners() {
        this.element.addEventListener('mouseenter', this.handleMouseEnter);
        this.element.addEventListener('mouseleave', this.handleMouseLeave);
        this.element.addEventListener('mousemove', this.handleMouseMove);
        this.element.addEventListener('click', this.handleClick);
        this.element.addEventListener('touchstart', this.handleTouchStart, { passive: true });
        this.element.addEventListener('touchend', this.handleTouchEnd, { passive: true });
    }

    detachEventListeners() {
        this.element.removeEventListener('mouseenter', this.handleMouseEnter);
        this.element.removeEventListener('mouseleave', this.handleMouseLeave);
        this.element.removeEventListener('mousemove', this.handleMouseMove);
        this.element.removeEventListener('click', this.handleClick);
        this.element.removeEventListener('touchstart', this.handleTouchStart);
        this.element.removeEventListener('touchend', this.handleTouchEnd);

        this.stopTracking();
    }

    handleMouseEnter(e) {
        this.startHover(e.clientX, e.clientY);
    }

    handleMouseLeave(e) {
        this.endHover();
    }

    handleMouseMove(e) {
        this.trackMouseMovement(e.clientX, e.clientY);
    }

    handleClick(e) {
        this.state.clicksDetected++;
        this.state.interestScore += 30; // Clicks are strong interest signals
        if (window.nexusDebugMode) {
            console.log(`🖱️ Click detected on card ${this.contentId}. Interest score: ${this.state.interestScore}`);
        }
        this.reportInterest('click');
    }

    handleTouchStart(e) {
        if (e.touches.length > 0) {
            const touch = e.touches[0];
            this.startHover(touch.clientX, touch.clientY);
        }
    }

    handleTouchEnd(e) {
        this.endHover();
    }

    startHover(x, y) {
        if (this.state.isHovering) return;

        this.state.isHovering = true;
        this.state.hoverStartTime = Date.now();
        this.state.lastMousePosition = { x, y };
        this.state.lastMouseMoveTime = Date.now();
        this.state.mousePositions = [{ x, y, time: Date.now() }];
        this.state.afkStartTime = null;
        this.state.isAfk = false;
        this.state.movementDetected = false;

        // Add visual indicator only in debug mode
        if (window.nexusDebugMode) {
            this.element.classList.add('tracking-interest');
            this.addDebugOverlay();
        }

        // Start velocity tracking
        this.startVelocityTracking();

        // Start AFK checking
        this.startAfkChecking();

        if (window.nexusDebugMode) {
            console.log(`👆 Hover started on card ${this.contentId}`);
        }
    }

    endHover() {
        if (!this.state.isHovering) return;

        this.state.isHovering = false;
        const hoverDuration = Date.now() - this.state.hoverStartTime;
        this.state.totalHoverTime += hoverDuration;

        // Remove visual indicator and debug overlay
        this.element.classList.remove('tracking-interest');
        if (window.nexusDebugMode) {
            this.removeDebugOverlay();
        }

        this.stopTracking();

        // Calculate final interest score
        this.calculateInterestScore();

        if (window.nexusDebugMode) {
            console.log(`👋 Hover ended on card ${this.contentId}. Duration: ${hoverDuration}ms, Total: ${this.state.totalHoverTime}ms, Interest Score: ${this.state.interestScore}`);
        }

        // Report if interest threshold is met
        if (this.state.interestScore >= this.config.interestScoreThreshold) {
            this.reportInterest('hover');
        }
    }

    trackMouseMovement(x, y) {
        if (!this.state.isHovering) return;

        const now = Date.now();
        const lastPos = this.state.lastMousePosition;

        if (!lastPos) {
            this.state.lastMousePosition = { x, y };
            this.state.lastMouseMoveTime = now;
            return;
        }

        // Calculate distance moved
        const distance = Math.sqrt(
            Math.pow(x - lastPos.x, 2) + Math.pow(y - lastPos.y, 2)
        );

        // Detect micro-movements (repositioning)
        if (distance > 0 && distance < this.config.microMovementThreshold) {
            this.state.microMovementsDetected++;
        }

        // Detect meaningful movement
        if (distance >= this.config.movementThreshold) {
            this.state.movementDetected = true;
            this.state.afkStartTime = null; // Reset AFK timer
            this.state.isAfk = false;

            // Add to position history for velocity calculation
            this.state.mousePositions.push({ x, y, time: now });

            // Keep only recent positions (last 1 second)
            this.state.mousePositions = this.state.mousePositions.filter(
                pos => now - pos.time < 1000
            );
        }

        this.state.lastMousePosition = { x, y };
        this.state.lastMouseMoveTime = now;
    }

    startVelocityTracking() {
        this.velocityTimer = setInterval(() => {
            this.checkVelocity();
        }, this.config.velocitySampleRate);
    }

    startAfkChecking() {
        this.afkCheckTimer = setInterval(() => {
            this.checkAfk();
        }, 1000);
    }

    stopTracking() {
        if (this.velocityTimer) {
            clearInterval(this.velocityTimer);
            this.velocityTimer = null;
        }

        if (this.afkCheckTimer) {
            clearInterval(this.afkCheckTimer);
            this.afkCheckTimer = null;
        }

        if (this.reportTimer) {
            clearInterval(this.reportTimer);
            this.reportTimer = null;
        }
    }

    checkVelocity() {
        if (this.state.mousePositions.length < 2) return;

        const positions = this.state.mousePositions;
        const recentPos = positions.at(-1);
        const olderPos = positions.at(Math.max(-positions.length, -5)); // Compare with position from ~500ms ago

        const distance = Math.sqrt(
            Math.pow(recentPos.x - olderPos.x, 2) +
            Math.pow(recentPos.y - olderPos.y, 2)
        );

        const timeDelta = recentPos.time - olderPos.time;
        const velocity = timeDelta > 0 ? distance / timeDelta : 0;

        // Detect slowdown (user getting interested)
        if (velocity < this.config.slowdownVelocityThreshold && this.state.movementDetected) {
            this.state.slowdownsDetected++;
            this.state.interestScore += 5; // Slowdowns indicate reading/interest
            if (window.nexusDebugMode) {
                console.log(`🐌 Slowdown detected on card ${this.contentId}. Velocity: ${velocity.toFixed(3)} px/ms`);
            }
        }
    }

    checkAfk() {
        if (!this.state.isHovering) return;

        const now = Date.now();
        const timeSinceLastMove = now - this.state.lastMouseMoveTime;

        // If no movement for afkThreshold, mark as AFK
        if (timeSinceLastMove >= this.config.afkThreshold) {
            if (!this.state.isAfk) {
                this.state.isAfk = true;
                this.state.afkStartTime = now;
                if (window.nexusDebugMode) {
                    console.log(`😴 AFK detected on card ${this.contentId}`);
                }

                // Reduce interest score for AFK
                this.state.interestScore = Math.max(0, this.state.interestScore - 20);
            }
        }
    }

    calculateInterestScore() {
        let score = 0;

        // Base score from hover duration (capped to avoid AFK inflation)
        const effectiveHoverTime = Math.min(this.state.totalHoverTime, 30000); // Cap at 30 seconds
        score += (effectiveHoverTime / 1000) * 2; // 2 points per second

        // Bonus for movement (indicates active reading, not AFK)
        if (this.state.movementDetected && !this.state.isAfk) {
            score += 10;
        }

        // Bonus for slowdowns (user is reading carefully)
        score += this.state.slowdownsDetected * 5;

        // Bonus for clicks (strong interest signal)
        score += this.state.clicksDetected * 30;

        // Bonus for scroll slowdowns
        score += this.state.scrollSlowdowns * 3;

        // Penalty for excessive micro-movements (probably just repositioning)
        if (this.state.microMovementsDetected > 10) {
            score -= 5;
        }

        // Penalty for AFK
        if (this.state.isAfk) {
            const afkDuration = Date.now() - this.state.afkStartTime;
            score -= (afkDuration / 1000) * 3; // -3 points per second of AFK
        }

        // Penalty for very short hover with no movement (accidental hover)
        if (this.state.totalHoverTime < this.config.minHoverDuration && !this.state.movementDetected) {
            score -= 10;
        }

        this.state.interestScore = Math.max(0, Math.round(score));
    }

    updateScrollVelocity(velocity) {
        // Track scroll velocity changes
        if (this.state.lastScrollVelocity > this.config.scrollSlowdownThreshold &&
            velocity < this.config.scrollSlowdownThreshold) {
            this.state.scrollSlowdowns++;
            this.state.interestScore += 3;
            if (window.nexusDebugMode) {
                console.log(`📜 Scroll slowdown detected near card ${this.contentId}. Interest score: ${this.state.interestScore}`);
            }
        }

        this.state.lastScrollVelocity = velocity;
    }

    async reportInterest(trigger = 'hover') {
        const data = {
            content_id: this.contentId,
            interest_score: this.state.interestScore,
            hover_duration_ms: this.state.totalHoverTime,
            movement_detected: this.state.movementDetected,
            slowdowns_detected: this.state.slowdownsDetected,
            clicks_detected: this.state.clicksDetected,
            was_afk: this.state.isAfk,
            trigger: trigger,
            timestamp: new Date().toISOString()
        };

        try {
            const response = await fetch('/api/v1/session/track-interest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(data)
            });

            if (response.ok) {
                if (window.nexusDebugMode) {
                    console.log(`✅ Interest reported for card ${this.contentId}:`, data);
                }
            } else {
                if (window.nexusDebugMode) {
                    console.warn(`⚠️ Failed to report interest for card ${this.contentId}`);
                }
            }
        } catch (error) {
            if (window.nexusDebugMode) {
                console.error(`❌ Error reporting interest for card ${this.contentId}:`, error);
            }
        }
    }

    // Public method to manually report interest (e.g., on viewport exit)
    forceReport() {
        if (this.state.isHovering) {
            this.endHover();
            return;
        }
        if (this.state.interestScore >= this.config.interestScoreThreshold) {
            this.reportInterest('viewport_exit');
        }
    }

    // Get current state for debugging
    getState() {
        return { ...this.state };
    }

    // Add debug overlay to show live interest score
    addDebugOverlay() {
        if (this.debugOverlay) return; // Already exists

        this.debugOverlay = document.createElement('div');
        this.debugOverlay.className = 'hover-debug-overlay';
        this.debugOverlay.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.85);
            color: #0f0;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
            z-index: 9999;
            pointer-events: none;
            border: 1px solid #0f0;
        `;

        this.element.style.position = 'relative';
        this.element.appendChild(this.debugOverlay);

        // Update overlay every 100ms
        this.debugOverlayInterval = setInterval(() => {
            if (this.debugOverlay && this.state.isHovering) {
                const duration = ((Date.now() - this.state.hoverStartTime) / 1000).toFixed(1);
                this.debugOverlay.innerHTML = `
                    Score: ${this.state.interestScore}<br>
                    Time: ${duration}s<br>
                    Slowdowns: ${this.state.slowdownsDetected}<br>
                    Clicks: ${this.state.clicksDetected}<br>
                    ${this.state.isAfk ? '😴 AFK' : '👀 Active'}
                `;
            }
        }, 100);
    }

    // Remove debug overlay
    removeDebugOverlay() {
        if (this.debugOverlay) {
            this.debugOverlay.remove();
            this.debugOverlay = null;
        }
        if (this.debugOverlayInterval) {
            clearInterval(this.debugOverlayInterval);
            this.debugOverlayInterval = null;
        }
    }

    // Cleanup
    destroy() {
        this.detachEventListeners();
        this.stopTracking();
        this.removeDebugOverlay();
    }
}

// Global scroll velocity tracker for all cards
class GlobalScrollTracker {
    constructor() {
        this.lastScrollPosition = window.scrollY;
        this.lastScrollTime = Date.now();
        this.scrollVelocity = 0;
        this.hoverTrackers = new Set();

        // Bind and attach scroll listener
        this.handleScroll = this.handleScroll.bind(this);
        window.addEventListener('scroll', this.handleScroll, { passive: true });
    }

    handleScroll() {
        const now = Date.now();
        const currentScroll = window.scrollY;

        const distance = Math.abs(currentScroll - this.lastScrollPosition);
        const timeDelta = now - this.lastScrollTime;

        if (timeDelta > 0) {
            this.scrollVelocity = distance / timeDelta; // pixels per millisecond

            // Notify all active hover trackers about scroll velocity
            this.hoverTrackers.forEach(tracker => {
                if (tracker.state.isHovering) {
                    tracker.updateScrollVelocity(this.scrollVelocity);
                }
            });
        }

        this.lastScrollPosition = currentScroll;
        this.lastScrollTime = now;
    }

    registerTracker(tracker) {
        this.hoverTrackers.add(tracker);
    }

    unregisterTracker(tracker) {
        this.hoverTrackers.delete(tracker);
    }

    destroy() {
        window.removeEventListener('scroll', this.handleScroll);
    }
}

// DEPRECATED EXPORTS - Do not use. Use HoverTracker.js and GlobalScrollTracker.js instead.
// For backward compatibility only:
// window.HoverTracker and window.GlobalScrollTracker are now exported from their respective modules

