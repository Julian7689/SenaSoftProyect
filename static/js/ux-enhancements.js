/**
 * Mejoras globales de UX e interactividad para todas las vistas
 * Incluye efectos de scroll, animaciones y feedback visual
 */

(function() {
    'use strict';

    // ==================== NAVBAR SCROLL EFFECT ====================
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    function handleScroll() {
        const currentScroll = window.pageYOffset;
        
        if (navbar) {
            if (currentScroll > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
        
        lastScroll = currentScroll;
    }
    
    window.addEventListener('scroll', handleScroll, { passive: true });

    // ==================== SMOOTH SCROLL FOR ANCHOR LINKS ====================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // ==================== RIPPLE EFFECT FOR BUTTONS ====================
    function createRipple(event) {
        const button = event.currentTarget;
        const ripple = document.createElement('span');
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple-effect');
        
        button.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }
    

    document.querySelectorAll('.btn-primary, .btn-auth, .btn-primary-enhanced, .refresh-btn').forEach(btn => {
        // Solo agregar si no tiene ya el listener
        if (!btn.dataset.rippleAdded) {
            btn.style.position = 'relative';
            btn.style.overflow = 'hidden';
            btn.addEventListener('click', createRipple);
            btn.dataset.rippleAdded = 'true';
        }
    });

    // Estilos para el efecto ripple
    const style = document.createElement('style');
    style.textContent = `
        .ripple-effect {
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.6);
            transform: scale(0);
            animation: ripple-animation 0.6s ease-out;
            pointer-events: none;
        }
        
        @keyframes ripple-animation {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
        
        /* Animación de entrada para elementos */
        .animate-in {
            animation: fadeInUp 0.6s ease-out;
        }
        
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Loading spinner */
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Pulse animation for important elements */
        .pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: .7;
            }
        }
        
        /* Bounce animation */
        .bounce {
            animation: bounce 1s infinite;
        }
        
        @keyframes bounce {
            0%, 100% {
                transform: translateY(0);
            }
            50% {
                transform: translateY(-10px);
            }
        }
    `;
    document.head.appendChild(style);

    // ==================== INTERSECTION OBSERVER FOR ANIMATIONS ====================
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observar elementos que deben animarse al aparecer
    document.querySelectorAll('.resource-card, .category-card, .stat-card, .case-item, .alarm-item').forEach(el => {
        observer.observe(el);
    });

    // ==================== TOOLTIP FUNCTIONALITY ====================
    document.querySelectorAll('[data-tooltip]').forEach(el => {
        el.addEventListener('mouseenter', function() {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip-custom';
            tooltip.textContent = this.dataset.tooltip;
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.cssText = `
                position: fixed;
                top: ${rect.top - tooltip.offsetHeight - 10}px;
                left: ${rect.left + (rect.width - tooltip.offsetWidth) / 2}px;
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-size: 0.875rem;
                z-index: 9999;
                pointer-events: none;
                animation: fadeIn 0.2s ease;
            `;
            
            this._tooltip = tooltip;
        });
        
        el.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });

    // ==================== FORM VALIDATION FEEDBACK ====================
    document.querySelectorAll('input, textarea').forEach(input => {
        input.addEventListener('invalid', function(e) {
            e.preventDefault();
            this.classList.add('error-shake');
            setTimeout(() => this.classList.remove('error-shake'), 500);
        });
        
        input.addEventListener('input', function() {
            if (this.validity.valid) {
                this.classList.remove('error-shake');
            }
        });
    });

    // Error shake animation
    const shakeStyle = document.createElement('style');
    shakeStyle.textContent = `
        .error-shake {
            animation: shake 0.5s ease-in-out;
            border-color: #ef4444 !important;
        }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            50% { transform: translateX(10px); }
            75% { transform: translateX(-10px); }
        }
    `;
    document.head.appendChild(shakeStyle);

    // ==================== COPY TO CLIPBOARD FUNCTIONALITY ====================
    document.querySelectorAll('[data-copy]').forEach(el => {
        el.style.cursor = 'pointer';
        el.addEventListener('click', async function() {
            const text = this.dataset.copy || this.textContent;
            try {
                await navigator.clipboard.writeText(text);
                
                // Visual feedback
                const originalText = this.innerHTML;
                this.innerHTML = '✓ Copiado';
                this.style.color = '#10b981';
                
                setTimeout(() => {
                    this.innerHTML = originalText;
                    this.style.color = '';
                }, 2000);
            } catch (err) {
                console.error('Error al copiar:', err);
            }
        });
    });

    // ==================== PROGRESSIVE IMAGE LOADING ====================
    document.querySelectorAll('img[data-src]').forEach(img => {
        const loadImage = () => {
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            img.classList.add('loaded');
        };
        
        if ('IntersectionObserver' in window) {
            const imgObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        loadImage();
                        imgObserver.unobserve(img);
                    }
                });
            });
            imgObserver.observe(img);
        } else {
            loadImage();
        }
    });

    // ==================== KEYBOARD SHORTCUTS ====================
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K para focus en búsqueda o input principal
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('#messageInput, input[type="search"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape para cerrar modales o limpiar focus
        if (e.key === 'Escape') {
            document.activeElement?.blur();
            // Cerrar sidebar móvil si está abierto
            const sidebar = document.querySelector('.chat-sidebar.show');
            if (sidebar) {
                sidebar.classList.remove('show');
            }
        }
    });

    // ==================== CONSOLE WELCOME MESSAGE ====================
    if (window.console && console.log) {
        const styles = [
            'color: #6366f1',
            'font-size: 20px',
            'font-weight: bold',
            'text-shadow: 2px 2px 4px rgba(99, 102, 241, 0.3)'
        ].join(';');
        
        console.log('%c🤖 BOTI - Sistema de Apoyo', styles);
        console.log('%cVersión 1.0.0 | Desarrollado con ❤️ para ayudar', 'color: #8b5cf6; font-size: 12px;');
    }

    console.log('✨ Mejoras de UX cargadas correctamente');
})();
