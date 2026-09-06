---
---
/**
 * De Witte Raaf - Interactive Site Scripts
 * High performance, zero dependencies, modern ES6+
 */

document.addEventListener('DOMContentLoaded', () => {
  // Record page load timestamp for form spam velocity gate
  window.__PAGE_LOAD_TIME = Date.now();

  initHeaderScroll();
  initMobileMenu();
  initServicesTabs();
  initContactForm();
  initLazyMap();
});

/**
 * Header shadow on scroll
 */
function initHeaderScroll() {
  const header = document.querySelector('.site-header');
  if (!header) return;

  const handleScroll = () => {
    if (window.scrollY > 20) {
      header.classList.add('is-scrolled');
    } else {
      header.classList.remove('is-scrolled');
    }
  };

  window.addEventListener('scroll', handleScroll, { passive: true });
}

/**
 * Mobile navigation menu toggle
 */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-toggle');
  const siteNav = document.querySelector('.site-nav');
  if (!toggleBtn || !siteNav) return;

  toggleBtn.addEventListener('click', () => {
    const isOpen = siteNav.classList.toggle('is-open');
    toggleBtn.setAttribute('aria-expanded', isOpen);
    toggleBtn.setAttribute('aria-label', isOpen ? 'Menu sluiten' : 'Menu openen');
  });

  // Close menu when clicking outside
  document.addEventListener('click', (e) => {
    if (siteNav.classList.contains('is-open') && !siteNav.contains(e.target) && !toggleBtn.contains(e.target)) {
      siteNav.classList.remove('is-open');
      toggleBtn.setAttribute('aria-expanded', 'false');
    }
  });
}

/**
 * Services Vertical Tabs & Deep Linking
 */
function initServicesTabs() {
  const tabButtons = document.querySelectorAll('.service-tab-btn');
  const tabPanes = document.querySelectorAll('.service-pane');
  if (!tabButtons.length || !tabPanes.length) return;

  function activateTab(slug) {
    let found = false;
    tabButtons.forEach(btn => {
      const match = btn.dataset.serviceSlug === slug;
      btn.classList.toggle('is-active', match);
      btn.setAttribute('aria-selected', match ? 'true' : 'false');
      if (match) found = true;
    });

    tabPanes.forEach(pane => {
      const match = pane.dataset.serviceSlug === slug;
      pane.classList.toggle('is-active', match);
      pane.setAttribute('aria-hidden', match ? 'false' : 'true');
    });

    if (!found && tabButtons.length > 0) {
      tabButtons[0].classList.add('is-active');
      tabButtons[0].setAttribute('aria-selected', 'true');
      tabPanes[0].classList.add('is-active');
      tabPanes[0].setAttribute('aria-hidden', 'false');
    }
  }

  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const slug = btn.dataset.serviceSlug;
      activateTab(slug);
      if (history.pushState) {
        history.pushState(null, null, `#${slug}`);
      } else {
        location.hash = slug;
      }
    });
  });

  // Check URL hash for deep-linking on load
  const hash = window.location.hash.replace('#', '');
  if (hash) {
    activateTab(hash);
  }

  // Handle browser back/forward buttons
  window.addEventListener('hashchange', () => {
    const newHash = window.location.hash.replace('#', '');
    if (newHash) activateTab(newHash);
  });
}

/**
 * Contact Form with Formward & Anti-Spam Velocity/Honeypot
 */
function initContactForm() {
  const form = document.querySelector('#contact-form');
  if (!form) return;

  const statusEl = document.querySelector('#form-status');
  const submitBtn = form.querySelector('button[type="submit"]');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // 1. Anti-Spam Check: Honeypot trap
    const honeypot = form.querySelector('input[name="_gotcha"]');
    if (honeypot && honeypot.value.trim() !== '') {
      console.warn('Spam bot detected via honeypot.');
      // Silently pretend success to fool bots
      if (statusEl) {
        statusEl.className = 'form-status success';
        statusEl.textContent = 'Hartelijk dank voor uw bericht! We nemen spoedig contact met u op.';
      }
      form.reset();
      return;
    }

    // 2. Anti-Spam Check: Time gate (velocity check)
    const timeSpent = Date.now() - (window.__PAGE_LOAD_TIME || 0);
    if (timeSpent < 2500) {
      alert('Het formulier werd te snel verstuurd. Gelieve even te wachten en opnieuw te proberen.');
      return;
    }

    // Prepare payload
    const formData = new FormData(form);
    const endpoint = form.action;

    // Show loading state
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.dataset.origText = submitBtn.innerHTML;
      submitBtn.innerHTML = 'Versturen...';
    }
    if (statusEl) {
      statusEl.style.display = 'none';
      statusEl.className = 'form-status';
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json'
        }
      });

      if (response.ok) {
        if (statusEl) {
          statusEl.className = 'form-status success';
          statusEl.textContent = 'Hartelijk dank voor uw bericht! We nemen spoedig contact met u op.';
        }
        form.reset();
      } else {
        throw new Error('Server antwoordde niet met 200 OK');
      }
    } catch (err) {
      console.error('Contact form submission error:', err);
      if (statusEl) {
        statusEl.className = 'form-status error';
        statusEl.textContent = 'Er trad een fout op bij het verzenden. U kan ons ook rechtstreeks bellen op 09/352.53.54 of mailen naar dac@dewitteraafdierenartsen.be.';
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = submitBtn.dataset.origText || 'Verstuur bericht';
      }
    }
  });
}

/**
 * Lazy-load OpenStreetMap (Leaflet) via Intersection Observer
 * Prevents third-party map script/CSS from degrading FCP or LCP.
 */
function initLazyMap() {
  const mapContainer = document.getElementById('osm-map-view');
  if (!mapContainer) return;

  const lat = parseFloat(mapContainer.dataset.lat || '50.962147');
  const lng = parseFloat(mapContainer.dataset.lng || '3.890904');
  const zoom = parseInt(mapContainer.dataset.zoom || '15', 10);
  const title = mapContainer.dataset.title || 'Dierenartsencentrum De Witte Raaf';

  const loadLeaflet = () => {
    // 1. Inject Leaflet CSS
    if (!document.getElementById('leaflet-css')) {
      const css = document.createElement('link');
      css.id = 'leaflet-css';
      css.rel = 'stylesheet';
      css.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      css.integrity = 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=';
      css.crossOrigin = '';
      document.head.appendChild(css);
    }

    // 2. Inject Leaflet JS
    if (!window.L) {
      const script = document.createElement('script');
      script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      script.integrity = 'sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=';
      script.crossOrigin = '';
      script.onload = () => renderMap(lat, lng, zoom, title, mapContainer);
      document.body.appendChild(script);
    } else {
      renderMap(lat, lng, zoom, title, mapContainer);
    }
  };

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadLeaflet();
          obs.disconnect();
        }
      });
    }, { rootMargin: '300px' });
    observer.observe(mapContainer);
  } else {
    loadLeaflet();
  }
}

function renderMap(lat, lng, zoom, title, container) {
  if (!window.L) return;

  const map = L.map(container.id, {
    scrollWheelZoom: false,
    attributionControl: true
  }).setView([lat, lng], zoom);

  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
  }).addTo(map);

  // Custom marker icon using clinic emblem
  const customIcon = L.icon({
    iconUrl: '{{ site.baseurl }}/assets/branding/logos/dewitteraaf_logo_embleem.svg',
    iconSize: [36, 36],
    iconAnchor: [18, 36],
    popupAnchor: [0, -36]
  });

  const marker = L.marker([lat, lng], { icon: customIcon }).addTo(map);
  marker.bindPopup(`
    <div style="font-family: Montserrat, sans-serif; padding: 4px;">
      <strong style="color: #014F2B; font-size: 14px;">${title}</strong><br>
      Wijde Wereld 2a, 9340 Oordegem<br>
      <a href="https://www.google.com/maps/search/?api=1&query=${lat},${lng}" target="_blank" rel="noopener" style="color: #014F2B; font-weight: 600; text-decoration: underline; display: inline-block; margin-top: 4px;">
        Open in Google Maps &rarr;
      </a>
    </div>
  `);
}
