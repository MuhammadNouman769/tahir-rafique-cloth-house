/* Tahir Rafique Cloth House — AJAX interactions.
   Everything here avoids full page reloads: add-to-cart, cart quantity/
   remove, product filtering/sorting/pagination, and newsletter signup all
   happen via fetch() and swap just the relevant part of the page. */

(function () {
  'use strict';

  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
    return match ? decodeURIComponent(match[2]) : null;
  }

  const CSRF_TOKEN = getCookie('csrftoken');

  function ajaxHeaders(extra) {
    return Object.assign({
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': CSRF_TOKEN,
    }, extra || {});
  }

  function toast(message, type) {
    let wrap = document.getElementById('flash-messages');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'flash-messages';
      wrap.className = 'fixed top-20 left-1/2 -translate-x-1/2 z-[60] w-full max-w-md px-4 space-y-2';
      document.body.appendChild(wrap);
    }
    const bg = type === 'error' ? 'bg-maroon' : (type === 'warning' ? 'bg-golddark' : 'bg-green-600');
    const el = document.createElement('div');
    el.className = `fade-in px-4 py-3 rounded shadow-lg text-sm font-medium text-white flex items-start justify-between gap-3 ${bg}`;
    el.innerHTML = `<span></span><button aria-label="Close">&times;</button>`;
    el.querySelector('span').textContent = message;
    el.querySelector('button').addEventListener('click', () => el.remove());
    wrap.appendChild(el);
    setTimeout(() => el.remove(), 4000);
  }

  function updateCartBadge(count) {
    document.querySelectorAll('.js-cart-count').forEach((el) => {
      el.textContent = count;
    });
  }

  // ---------------------------------------------------------------
  // Add to cart (product cards + product detail page)
  // ---------------------------------------------------------------
  function bindAddToCartForms(scope) {
    (scope || document).querySelectorAll('form.js-add-to-cart').forEach((form) => {
      if (form.dataset.bound) return;
      form.dataset.bound = '1';
      form.addEventListener('submit', function (e) {
        const submitter = e.submitter;
        // "Buy Now" performs a real navigation to checkout, so let it submit normally.
        if (submitter && submitter.name === 'buy_now') return;

        e.preventDefault();
        const formData = new FormData(form);
        fetch(form.action, {
          method: 'POST',
          headers: ajaxHeaders(),
          body: formData,
        })
          .then((r) => r.json())
          .then((data) => {
            if (data.ok) {
              updateCartBadge(data.cart_count);
              toast(data.message, 'success');
            } else {
              toast(data.message || 'Something went wrong.', 'error');
            }
          })
          .catch(() => toast('Could not add to cart. Please try again.', 'error'));
      });
    });
  }

  // ---------------------------------------------------------------
  // Cart page: quantity +/- and remove, without reloading
  // ---------------------------------------------------------------
  function bindCartBody() {
    const cartBody = document.getElementById('cart-body');
    if (!cartBody) return;

    cartBody.addEventListener('click', function (e) {
      const qtyBtn = e.target.closest('.js-cart-qty');
      const removeBtn = e.target.closest('.js-cart-remove');

      if (qtyBtn) {
        const key = qtyBtn.dataset.key;
        const quantity = qtyBtn.dataset.quantity;
        postCartAction(`/cart/update/${key}/`, { quantity });
      } else if (removeBtn) {
        const key = removeBtn.dataset.key;
        postCartAction(`/cart/remove/${key}/`, {});
      }
    });

    function postCartAction(url, body) {
      const formData = new FormData();
      Object.keys(body).forEach((k) => formData.append(k, body[k]));
      fetch(url, { method: 'POST', headers: ajaxHeaders(), body: formData })
        .then((r) => r.json())
        .then((data) => {
          if (data.ok) {
            cartBody.innerHTML = data.html;
            updateCartBadge(data.cart_count);
          }
        })
        .catch(() => toast('Could not update your cart. Please try again.', 'error'));
    }
  }

  // ---------------------------------------------------------------
  // Product listing: AJAX filters, sorting, and pagination
  // ---------------------------------------------------------------
  function bindProductListing() {
    const listing = document.getElementById('product-listing');
    const filterForm = document.getElementById('filter-form');
    if (!listing || !filterForm) return;

    function loadListing(url, pushHistory) {
      listing.classList.add('opacity-50');
      fetch(url, { headers: ajaxHeaders() })
        .then((r) => r.text())
        .then((html) => {
          listing.innerHTML = html;
          listing.classList.remove('opacity-50');
          if (pushHistory !== false) {
            window.history.pushState({ ajaxListing: true }, '', url);
          }
          bindListingLinks();
          bindAddToCartForms(listing);
          const countEl = document.getElementById('result-count');
          // Result count is server-rendered outside the swapped area, so we
          // leave it be; it only matters for the very first load.
        })
        .catch(() => {
          listing.classList.remove('opacity-50');
        });
      window.scrollTo({ top: listing.offsetTop - 100, behavior: 'smooth' });
    }

    function currentListingUrl() {
      const params = new URLSearchParams(new FormData(filterForm));
      const qs = params.toString();
      return window.location.pathname + (qs ? '?' + qs : '');
    }

    filterForm.addEventListener('change', () => loadListing(currentListingUrl()));
    filterForm.addEventListener('submit', (e) => {
      e.preventDefault();
      loadListing(currentListingUrl());
    });

    function bindListingLinks() {
      listing.querySelectorAll('a[href]').forEach((a) => {
        const href = a.getAttribute('href');
        if (a.classList.contains('js-clear-filters') || href.startsWith('?') || href === window.location.pathname) {
          a.addEventListener('click', (e) => {
            e.preventDefault();
            loadListing(a.href);
          });
        }
      });
    }
    bindListingLinks();

    // "Clear all filters" link lives inside the filter form's sidebar,
    // outside #product-listing, so bind it separately.
    document.querySelectorAll('.js-clear-filters').forEach((a) => {
      if (a.dataset.bound) return;
      a.dataset.bound = '1';
      a.addEventListener('click', (e) => {
        e.preventDefault();
        filterForm.reset();
        loadListing(window.location.pathname);
      });
    });

    window.addEventListener('popstate', () => {
      loadListing(window.location.href, false);
    });
  }

  // ---------------------------------------------------------------
  // Newsletter signup
  // ---------------------------------------------------------------
  function bindNewsletterForm() {
    document.querySelectorAll('form.js-newsletter-form').forEach((form) => {
      if (form.dataset.bound) return;
      form.dataset.bound = '1';
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        fetch(form.action, {
          method: 'POST',
          headers: ajaxHeaders(),
          body: new FormData(form),
        })
          .then((r) => r.json())
          .then((data) => {
            toast(data.message, data.ok ? 'success' : 'error');
            if (data.ok) form.reset();
          })
          .catch(() => toast('Could not subscribe right now. Please try again.', 'error'));
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    bindAddToCartForms(document);
    bindCartBody();
    bindProductListing();
    bindNewsletterForm();
  });
})();
