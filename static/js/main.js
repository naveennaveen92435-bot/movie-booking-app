/**
 * CinéAI — Main JavaScript
 * Live search, dark mode, notifications, voice booking, hero slider
 */

// ─── Live Search ─────────────────────────────────────────────────────────────
(function () {
  const input = document.getElementById('liveSearch');
  const dropdown = document.getElementById('searchDropdown');
  if (!input || !dropdown) return;

  let debounceTimer;

  input.addEventListener('input', function () {
    clearTimeout(debounceTimer);
    const q = this.value.trim();
    if (q.length < 2) { dropdown.classList.add('d-none'); return; }

    debounceTimer = setTimeout(() => {
      fetch(`/api/search/?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.results.length) {
            dropdown.innerHTML = '<div class="search-item"><span style="color:var(--text-muted);font-size:.85rem;">No results found</span></div>';
          } else {
            dropdown.innerHTML = data.results.map(m => `
              <div class="search-item" onclick="location.href='/movie/${m.slug}/'">
                <img src="${m.poster}" alt="${m.title}" onerror="this.src='/static/images/default_poster.jpg'">
                <div class="movie-info">
                  <div class="movie-title">${m.title}</div>
                  <div class="movie-meta">⭐ ${m.rating} &nbsp;·&nbsp; ${m.genre}</div>
                </div>
              </div>
            `).join('');
          }
          dropdown.classList.remove('d-none');
        }).catch(() => dropdown.classList.add('d-none'));
    }, 300);
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.classList.add('d-none');
    }
  });
})();


// ─── Dark Mode Toggle ────────────────────────────────────────────────────────
(function () {
  const btn = document.getElementById('darkModeToggle');
  if (!btn) return;

  btn.addEventListener('click', function () {
    fetch('/accounts/api/toggle-dark-mode/', {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'Content-Type': 'application/json' },
    })
      .then(r => r.json())
      .then(data => {
        const html = document.documentElement;
        html.setAttribute('data-theme', data.dark_mode ? 'dark' : 'light');
        const label = document.getElementById('darkModeLabel');
        if (label) label.textContent = data.dark_mode ? 'Light Mode' : 'Dark Mode';
      });
  });
})();


// ─── Load Notifications ──────────────────────────────────────────────────────
(function () {
  const list = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  if (!list) return;

  // Fetch notifications on dropdown open
  const dropdownEl = document.querySelector('.notif-dropdown')?.closest('.dropdown');
  if (!dropdownEl) return;

  dropdownEl.addEventListener('show.bs.dropdown', function () {
    fetch('/accounts/api/notifications/')
      .then(r => r.json())
      .then(data => {
        if (!data.notifications || !data.notifications.length) {
          list.innerHTML = '<li><span class="dropdown-item-text text-muted small">No notifications</span></li>';
          return;
        }
        list.innerHTML = data.notifications.map(n => `
          <li class="notif-item ${n.is_read ? '' : 'unread'}">
            <div style="font-weight:${n.is_read ? '400' : '600'};font-size:.85rem">${n.title}</div>
            <div style="font-size:.78rem;color:var(--text-muted);margin-top:2px">${n.message.substring(0, 80)}…</div>
            <div style="font-size:.72rem;color:var(--text-dim);margin-top:4px">${n.created_at}</div>
          </li>
        `).join('');

        if (data.unread > 0) {
          if (badge) { badge.style.display = 'block'; badge.textContent = data.unread; }
        }

        // Mark as read
        fetch('/accounts/api/mark-notifications-read/', {
          method: 'POST',
          headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
      });
  });
})();


// ─── Hero Slider ─────────────────────────────────────────────────────────────
(function () {
  const slides = document.querySelectorAll('.hero-slide');
  const dots = document.querySelectorAll('.hero-dot');
  if (!slides.length) return;

  let current = 0;
  let timer;

  function goTo(idx) {
    slides[current].classList.remove('active');
    if (dots[current]) dots[current].classList.remove('active');
    current = (idx + slides.length) % slides.length;
    slides[current].classList.add('active');
    if (dots[current]) dots[current].classList.add('active');
  }

  function autoPlay() {
    timer = setInterval(() => goTo(current + 1), 5000);
  }

  dots.forEach((dot, i) => {
    dot.addEventListener('click', () => { clearInterval(timer); goTo(i); autoPlay(); });
  });

  if (slides.length > 1) autoPlay();
})();


// ─── Voice Booking ────────────────────────────────────────────────────────────
(function () {
  const voiceBtns = document.querySelectorAll('[id$="VoiceBtn"], #footerVoiceBtn');
  const transcript = document.getElementById('voiceTranscript');

  if (!voiceBtns.length) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    voiceBtns.forEach(b => b.addEventListener('click', () =>
      alert('Voice recognition not supported in this browser. Try Chrome.')));
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = 'en-IN';
  recognition.interimResults = true;

  recognition.onresult = function (e) {
    const text = Array.from(e.results).map(r => r[0].transcript).join('');
    if (transcript) transcript.textContent = `Heard: "${text}"`;
    if (e.results[0].isFinal) processVoiceCommand(text);
  };

  recognition.onend = function () {
    const modal = bootstrap.Modal.getInstance(document.getElementById('voiceModal'));
    if (modal) modal.hide();
  };

  voiceBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = new bootstrap.Modal(document.getElementById('voiceModal'));
      modal.show();
      setTimeout(() => recognition.start(), 300);
    });
  });

  function processVoiceCommand(text) {
    const lower = text.toLowerCase();
    // Simple NLP: extract movie name and redirect to search
    const searchQuery = lower.replace(/book|tickets?|for|movie|show|tonight|today/g, '').trim();
    if (searchQuery.length > 2) {
      window.location.href = `/?q=${encodeURIComponent(searchQuery)}`;
    }
  }
})();


// ─── Auto-dismiss Toasts ─────────────────────────────────────────────────────
document.querySelectorAll('.toast').forEach(el => {
  setTimeout(() => {
    const t = bootstrap.Toast.getInstance(el) || new bootstrap.Toast(el);
    t.hide();
  }, 4000);
});


// ─── Utility: Get CSRF Cookie ────────────────────────────────────────────────
function getCookie(name) {
  const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : null;
}

// ─── Navbar shrink on scroll ─────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  nav.style.boxShadow = window.scrollY > 30
    ? '0 4px 20px rgba(0,0,0,0.4)'
    : 'none';
});
