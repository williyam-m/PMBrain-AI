/**
 * PMBrain AI — Landing Page Animations
 * GPU-accelerated CSS animations + IntersectionObserver reveals
 */

const LandingAnimations = {
    observers: [],

    init() {
        this.setupScrollReveal();
        this.setupNavbarScroll();
        this.setupParallax();
        this.animateScoreBars();
    },

    // Reveal elements as they enter viewport
    setupScrollReveal() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    // If this is a stagger parent, delay-reveal children
                    if (entry.target.classList.contains('stagger-children')) {
                        const children = entry.target.querySelectorAll('.fade-in-up');
                        children.forEach((child, i) => {
                            setTimeout(() => child.classList.add('visible'), i * 120);
                        });
                    }
                }
            });
        }, {
            threshold: 0.12,
            rootMargin: '0px 0px -60px 0px'
        });

        document.querySelectorAll('.fade-in-up, .stagger-children').forEach(el => {
            observer.observe(el);
        });

        this.observers.push(observer);
    },

    // Navbar background on scroll
    setupNavbarScroll() {
        const nav = document.querySelector('.landing-nav');
        if (!nav) return;

        const onScroll = () => {
            if (window.scrollY > 40) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        };

        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    },

    // Subtle parallax on orbs
    setupParallax() {
        const orbs = document.querySelectorAll('.hero-orb');
        if (!orbs.length) return;

        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    const scrollY = window.scrollY;
                    orbs.forEach((orb, i) => {
                        const speed = (i + 1) * 0.03;
                        orb.style.transform = `translateY(${scrollY * speed}px)`;
                    });
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
    },

    // Animate score bars when visible
    animateScoreBars() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const fills = entry.target.querySelectorAll('.demo-score-fill, .score-graph-fill');
                    fills.forEach(fill => {
                        const targetWidth = fill.getAttribute('data-width');
                        if (targetWidth) {
                            setTimeout(() => {
                                fill.style.width = targetWidth + '%';
                            }, 200);
                        }
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.3 });

        // Observe score containers when they exist
        setTimeout(() => {
            document.querySelectorAll('.demo-scores, .score-graph').forEach(el => {
                observer.observe(el);
            });
        }, 500);

        this.observers.push(observer);
    },

    // Clean up
    destroy() {
        this.observers.forEach(obs => obs.disconnect());
        this.observers = [];
    }
};
