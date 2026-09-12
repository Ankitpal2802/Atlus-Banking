document.addEventListener('DOMContentLoaded', function () {
    // --- Toast ---
    var toastEl = document.createElement('div');
    toastEl.id = 'toast';
    document.body.appendChild(toastEl);
    var toastTimer = null;

    function showToast(message) {
        toastEl.textContent = message;
        toastEl.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            toastEl.classList.remove('show');
        }, 2600);
    }

    document.querySelectorAll('[data-toast]').forEach(function (el) {
        if (!el.hasAttribute('tabindex') && el.tagName !== 'A' && el.tagName !== 'BUTTON') {
            el.setAttribute('tabindex', '0');
            el.setAttribute('role', 'button');
        }
        el.addEventListener('click', function (e) {
            if (el.tagName === 'A' && (el.getAttribute('href') === '#' || !el.getAttribute('href'))) {
                e.preventDefault();
            }
            showToast(el.getAttribute('data-toast'));
        });
        el.addEventListener('keydown', function (e) {
            if ((e.key === 'Enter' || e.key === ' ') && el.tagName !== 'A' && el.tagName !== 'BUTTON') {
                e.preventDefault();
                el.click();
            }
        });
    });

    // --- "Know More" expands the product card's feature list ---
    document.querySelectorAll('.more-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var card = btn.closest('.card');
            var list = card ? card.querySelector('ul.list') : null;
            if (!list) return;
            var isOpen = list.classList.toggle('open');
            btn.textContent = isOpen ? 'Show Less' : 'Know More';
        });
    });

    // --- Hamburger menu (mobile nav) ---
    var hamburger = document.querySelector('.hamburger');
    var option = document.querySelector('.nav-bar .option');
    if (hamburger && option) {
        hamburger.addEventListener('click', function () {
            var isOpen = option.classList.toggle('open');
            hamburger.classList.toggle('open', isOpen);
            hamburger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
        // Close the menu after tapping a nav link
        option.querySelectorAll('a').forEach(function (link) {
            link.addEventListener('click', function () {
                option.classList.remove('open');
                hamburger.classList.remove('open');
            });
        });
    }
});
