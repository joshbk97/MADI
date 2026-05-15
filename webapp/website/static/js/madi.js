/**
 * MADI — Interactive UI Layer
 * Scroll animations, navbar behavior, form UX, and micro-interactions.
 */
(function () {
  'use strict';

  /* ───────────────────────────────────────────────
   *  1.  PAGE LOAD ANIMATION
   * ─────────────────────────────────────────────── */
  document.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('madi-loaded');
    initScrollAnimations();
    initNavbarScroll();
    initFormValidation();
    initFormProgress();
    initDragDrop();
    initFlashAutoDismiss();
    initBackToTop();
    initPasswordToggle();
    initCountUpAnimations();
    initParallaxHero();
    initSmoothAnchorScroll();
  });

  /* ───────────────────────────────────────────────
   *  2.  INTERSECTION OBSERVER — SCROLL ANIMATIONS
   * ─────────────────────────────────────────────── */
  function initScrollAnimations() {
    var animEls = document.querySelectorAll('.madi-animate');
    if (!animEls.length) return;

    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var el = entry.target;
            var delay = el.getAttribute('data-delay') || 0;
            setTimeout(function () {
              el.classList.add('madi-visible');
            }, parseInt(delay, 10));
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    animEls.forEach(function (el) {
      observer.observe(el);
    });
  }

  /* ───────────────────────────────────────────────
   *  3.  NAVBAR SCROLL BEHAVIOR
   * ─────────────────────────────────────────────── */
  function initNavbarScroll() {
    var navbar = document.querySelector('.navbar-fixed-top');
    if (!navbar) return;

    var scrollThreshold = 50;
    var ticking = false;

    function onScroll() {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          if (window.scrollY > scrollThreshold) {
            navbar.classList.add('navbar-scrolled');
          } else {
            navbar.classList.remove('navbar-scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // run once on load
  }

  /* ───────────────────────────────────────────────
   *  4.  REAL-TIME FORM VALIDATION
   * ─────────────────────────────────────────────── */
  function initFormValidation() {
    var forms = document.querySelectorAll('.glass-panel form');
    forms.forEach(function (form) {
      var inputs = form.querySelectorAll('input.form-control, select.form-control');
      inputs.forEach(function (input) {
        input.addEventListener('input', validateField);
        input.addEventListener('change', validateField);
        input.addEventListener('blur', validateField);
      });
    });
  }

  function validateField(e) {
    var el = e.target;
    // Don't validate hidden or file inputs
    if (el.type === 'hidden' || el.type === 'file') return;

    var wrapper = el.closest('.form-group');
    if (!wrapper) return;

    // Remove previous state
    wrapper.classList.remove('has-success', 'has-error');

    // Only show state if field has been interacted with
    if (el.value === '' && !el.required) return;

    if (el.value !== '') {
      if (el.checkValidity()) {
        wrapper.classList.add('has-success');
      } else {
        wrapper.classList.add('has-error');
      }
    }
  }

  /* ───────────────────────────────────────────────
   *  5.  FORM PROGRESS BAR
   * ─────────────────────────────────────────────── */
  function initFormProgress() {
    var progressBar = document.getElementById('formProgressBar');
    var progressText = document.getElementById('formProgressText');
    if (!progressBar) return;

    var form = progressBar.closest('.glass-panel').querySelector('form');
    if (!form) return;

    var fields = form.querySelectorAll(
      'input[required], select[required]'
    );

    function updateProgress() {
      var filled = 0;
      fields.forEach(function (f) {
        if (f.type === 'hidden') { filled++; return; }
        if (f.value !== '' && f.value !== null) filled++;
      });

      var total = fields.length;
      var hidden = form.querySelectorAll('input[type="hidden"][required]').length;
      var visibleTotal = total - hidden;
      var visibleFilled = filled - hidden;

      var pct = visibleTotal > 0 ? Math.round((visibleFilled / visibleTotal) * 100) : 0;
      progressBar.style.width = pct + '%';

      if (progressText) {
        progressText.textContent = pct + '% Complete';
      }

      // Change color based on completion
      if (pct === 100) {
        progressBar.style.background = 'var(--success)';
        progressBar.style.boxShadow = '0 0 12px rgba(16, 185, 129, 0.4)';
      } else {
        progressBar.style.background = 'linear-gradient(90deg, var(--accent-primary), var(--accent-secondary))';
        progressBar.style.boxShadow = 'none';
      }
    }

    fields.forEach(function (f) {
      f.addEventListener('input', updateProgress);
      f.addEventListener('change', updateProgress);
    });

    updateProgress();
  }

  /* ───────────────────────────────────────────────
   *  6.  DRAG AND DROP UPLOAD (Pneumonia page)
   * ─────────────────────────────────────────────── */
  function initDragDrop() {
    var uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;

    var fileInput = document.getElementById('formFile');

    ['dragenter', 'dragover'].forEach(function (evt) {
      uploadArea.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.add('upload-area--dragover');
      });
    });

    ['dragleave', 'drop'].forEach(function (evt) {
      uploadArea.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        uploadArea.classList.remove('upload-area--dragover');
      });
    });

    uploadArea.addEventListener('drop', function (e) {
      var files = e.dataTransfer.files;
      if (files.length && fileInput) {
        // Validate file type
        var file = files[0];
        if (!file.type.startsWith('image/')) {
          showToast('Please upload an image file (JPG, PNG).', 'error');
          return;
        }
        // Validate file size (max 10 MB)
        if (file.size > 10 * 1024 * 1024) {
          showToast('File is too large. Maximum size is 10 MB.', 'error');
          return;
        }
        fileInput.files = files;
        // Trigger the preview
        if (typeof window.preview_image === 'function') {
          window.preview_image({ target: fileInput });
        }
      }
    });
  }

  /* ───────────────────────────────────────────────
   *  7.  FLASH MESSAGE AUTO-DISMISS
   * ─────────────────────────────────────────────── */
  function initFlashAutoDismiss() {
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
      // Entrance animation
      alert.classList.add('madi-flash-enter');

      setTimeout(function () {
        alert.classList.add('madi-flash-exit');
        setTimeout(function () {
          if (alert.parentNode) alert.parentNode.removeChild(alert);
        }, 400);
      }, 5000);
    });
  }

  /* ───────────────────────────────────────────────
   *  8.  BACK TO TOP BUTTON
   * ─────────────────────────────────────────────── */
  function initBackToTop() {
    var btn = document.getElementById('backToTop');
    if (!btn) return;

    var ticking = false;

    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          if (window.scrollY > 300) {
            btn.classList.add('madi-btt-visible');
          } else {
            btn.classList.remove('madi-btt-visible');
          }
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });

    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ───────────────────────────────────────────────
   *  9.  PASSWORD SHOW/HIDE TOGGLE
   * ─────────────────────────────────────────────── */
  function initPasswordToggle() {
    var toggles = document.querySelectorAll('.madi-password-toggle');
    toggles.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var input = this.parentElement.querySelector('input');
        var icon = this.querySelector('i');
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          input.type = 'password';
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      });
    });
  }

  /* ───────────────────────────────────────────────
   *  10. COUNT-UP ANIMATION (Confidence bars, etc)
   * ─────────────────────────────────────────────── */
  function initCountUpAnimations() {
    var countEls = document.querySelectorAll('[data-countup]');
    if (!countEls.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCountUp(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    countEls.forEach(function (el) { observer.observe(el); });
  }

  function animateCountUp(el) {
    var target = parseFloat(el.getAttribute('data-countup'));
    var suffix = el.getAttribute('data-suffix') || '';
    var duration = 1200;
    var start = 0;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      // Ease-out cubic
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = Math.round(eased * target);
      el.textContent = current + suffix;
      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.textContent = target + suffix;
      }
    }

    requestAnimationFrame(step);
  }

  /* ───────────────────────────────────────────────
   *  11. PARALLAX-LIKE HERO FLOAT
   * ─────────────────────────────────────────────── */
  function initParallaxHero() {
    var heroImg = document.querySelector('#home .img-responsive');
    if (!heroImg) return;

    var ticking = false;

    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          var scrolled = window.scrollY;
          var rate = scrolled * 0.15;
          heroImg.style.transform = 'translateY(' + rate + 'px)';
          ticking = false;
        });
        ticking = true;
      }
    }, { passive: true });
  }

  /* ───────────────────────────────────────────────
   *  12. SMOOTH ANCHOR SCROLL (replaces legacy custom.js)
   * ─────────────────────────────────────────────── */
  function initSmoothAnchorScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        var targetId = this.getAttribute('href');
        if (targetId === '#' || targetId.length <= 1) return;

        var target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          var offset = 70; // navbar height
          var top = target.getBoundingClientRect().top + window.scrollY - offset;
          window.scrollTo({ top: top, behavior: 'smooth' });

          // Collapse mobile menu if open
          var navCollapse = document.querySelector('.navbar-collapse.in');
          if (navCollapse && typeof $ !== 'undefined') {
            $(navCollapse).collapse('hide');
          }
        }
      });
    });
  }

  /* ───────────────────────────────────────────────
   *  UTILITY: Toast notification
   * ─────────────────────────────────────────────── */
  function showToast(message, type) {
    var toast = document.createElement('div');
    toast.className = 'madi-toast madi-toast--' + (type || 'info');
    toast.textContent = message;
    document.body.appendChild(toast);

    // Trigger reflow
    toast.offsetHeight;
    toast.classList.add('madi-toast--show');

    setTimeout(function () {
      toast.classList.remove('madi-toast--show');
      setTimeout(function () {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, 3000);
  }

})();
