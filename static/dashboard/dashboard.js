(function () {
  // theme
  var saved = localStorage.getItem('dash-theme');
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-action]');
    if (!t) return;
    var a = t.dataset.action;
    if (a === 'theme') {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('dash-theme', next);
      if (window.renderCharts) window.renderCharts();
    }
    if (a === 'menu') document.querySelector('.sidebar').classList.toggle('open');
    if (a === 'dismiss') t.closest('.alert').remove();
    if (a === 'confirm' && !confirm(t.dataset.message || 'Are you sure?')) e.preventDefault();
  });
  // confirm on forms with data-confirm
  document.addEventListener('submit', function (e) {
    var m = e.target.dataset.confirm;
    if (m && !confirm(m)) e.preventDefault();
  });
  // auto-submit filter selects
  document.querySelectorAll('[data-autosubmit]').forEach(function (el) {
    el.addEventListener('change', function () { el.form.submit(); });
  });
  // bulk selection
  document.querySelectorAll('[data-bulk]').forEach(function (scope) {
    var master = scope.querySelector('[data-check-all]');
    var boxes = function () { return scope.querySelectorAll('[data-row-check]'); };
    var bar = scope.querySelector('.bulk');
    function sync() {
      var n = 0; boxes().forEach(function (b) { if (b.checked) n++; });
      if (bar) { bar.classList.toggle('show', n > 0); var c = bar.querySelector('[data-count]'); if (c) c.textContent = n; }
      if (master) master.checked = n > 0 && n === boxes().length;
    }
    if (master) master.addEventListener('change', function () { boxes().forEach(function (b) { b.checked = master.checked; }); sync(); });
    scope.addEventListener('change', function (e) { if (e.target.matches('[data-row-check]')) sync(); });
  });
  // formset: reveal image preview on pick
  document.querySelectorAll('input[type=file][data-preview]').forEach(function (inp) {
    inp.addEventListener('change', function () {
      var img = document.getElementById(inp.dataset.preview);
      if (img && inp.files[0]) { img.src = URL.createObjectURL(inp.files[0]); img.style.display = 'block'; }
    });
  });

  // ───── charts ─────
  function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  function data(id) { var el = document.getElementById(id); return el ? JSON.parse(el.textContent) : null; }
  var instances = [];
  var PALETTE = ['#b8925a', '#1a1512', '#7a1f2b', '#2f6f73', '#c9a227', '#6d5a8c', '#8a8f98', '#d9825b'];
  var STATUS = { pending: '#d97706', confirmed: '#2563eb', processing: '#7c3aed', shipped: '#0891b2', delivered: '#16a34a', cancelled: '#dc2626' };
  var money = function (v) { return 'Rs. ' + Number(v).toLocaleString('en-PK', { maximumFractionDigits: 0 }); };
  var short = function (v) { return v >= 1e6 ? (v / 1e6).toFixed(1) + 'M' : v >= 1e3 ? (v / 1e3).toFixed(0) + 'k' : v; };

  window.renderCharts = function () {
    if (!window.Chart) return;
    instances.forEach(function (c) { c.destroy(); }); instances = [];
    var text = css('--muted'), grid = css('--line'), panel = css('--panel');
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
    Chart.defaults.color = text;
    function mk(id, cfg) { var el = document.getElementById(id); if (el) instances.push(new Chart(el, cfg)); }
    var scales = function (yfmt) {
      return { x: { grid: { display: false }, ticks: { maxTicksLimit: 10, maxRotation: 0 } },
               y: { beginAtZero: true, grid: { color: grid }, border: { display: false }, ticks: { callback: yfmt || short } } };
    };

    var d = data('d-daily');
    if (d && d.labels.length) mk('c-daily', {
      type: 'line',
      data: { labels: d.labels, datasets: [
        { label: 'Revenue', data: d.revenue, borderColor: '#b8925a', backgroundColor: 'rgba(184,146,90,.16)', fill: true, tension: .35, pointRadius: 0, pointHoverRadius: 5, borderWidth: 2.5, yAxisID: 'y' },
        { label: 'Orders', data: d.orders, borderColor: css('--text'), borderDash: [5, 4], tension: .35, pointRadius: 0, borderWidth: 1.5, yAxisID: 'y1' }] },
      options: { maintainAspectRatio: false, interaction: { mode: 'index', intersect: false },
        plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } },
                   tooltip: { callbacks: { label: function (c) { return c.dataset.label + ': ' + (c.datasetIndex === 0 ? money(c.parsed.y) : c.parsed.y); } } } },
        scales: { x: scales().x, y: scales().y, y1: { position: 'right', beginAtZero: true, grid: { display: false }, border: { display: false }, ticks: { precision: 0 } } } }
    });

    var m = data('d-monthly');
    if (m && m.labels.length) mk('c-monthly', {
      type: 'bar',
      data: { labels: m.labels, datasets: [{ label: 'Revenue', data: m.revenue, backgroundColor: '#b8925a', borderRadius: 6, maxBarThickness: 44 }] },
      options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return money(c.parsed.y); } } } }, scales: scales() }
    });

    function doughnut(id, key, colors) {
      var s = data(key); if (!s || !s.data.some(function (x) { return x > 0; })) return;
      mk(id, { type: 'doughnut',
        data: { labels: s.labels, datasets: [{ data: s.data, backgroundColor: colors ? colors(s) : PALETTE, borderColor: panel, borderWidth: 3 }] },
        options: { maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, padding: 14 } },
          tooltip: { callbacks: { label: function (c) { return ' ' + c.label + ': ' + (key === 'd-status' ? c.parsed : money(c.parsed)); } } } } } });
    }
    doughnut('c-status', 'd-status', function (s) { return s.keys.map(function (k) { return STATUS[k]; }); });
    doughnut('c-category', 'd-category');

    function hbar(id, key, isMoney) {
      var s = data(key); if (!s || !s.labels.length) return;
      mk(id, { type: 'bar', data: { labels: s.labels, datasets: [{ data: s.data, backgroundColor: '#b8925a', borderRadius: 6, maxBarThickness: 22 }] },
        options: { indexAxis: 'y', maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (c) { return isMoney ? money(c.parsed.x) : c.parsed.x + ' orders'; } } } },
          scales: { x: { beginAtZero: true, grid: { color: grid }, border: { display: false }, ticks: { callback: isMoney ? short : null, precision: 0 } }, y: { grid: { display: false } } } } });
    }
    hbar('c-city', 'd-city', true);
    function vbar(id, key) {
      var s = data(key); if (!s) return;
      mk(id, { type: 'bar', data: { labels: s.labels, datasets: [{ data: s.data, backgroundColor: '#1a1512', borderRadius: 5, maxBarThickness: 30 }] },
        options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
          scales: { x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12 } }, y: { beginAtZero: true, grid: { color: grid }, border: { display: false }, ticks: { precision: 0 } } } } });
    }
    vbar('c-weekday', 'd-weekday'); vbar('c-hour', 'd-hour');
  };
  if (window.Chart) window.renderCharts(); else window.addEventListener('load', function () { window.renderCharts && window.renderCharts(); });
})();
