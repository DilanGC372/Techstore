// El menú permanece visible si JavaScript no está disponible.
const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#main-nav');
const mobileScreen = window.matchMedia('(max-width: 700px)');

function setMenuOpen(isOpen) {
    menuButton.setAttribute('aria-expanded', String(isOpen));
    navigation.classList.toggle('is-collapsed', !isOpen);
}

function adaptMenu() {
    setMenuOpen(!mobileScreen.matches);
}

menuButton.hidden = false;
adaptMenu();
mobileScreen.addEventListener('change', adaptMenu);

menuButton.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    setMenuOpen(!isOpen);
});

navigation.addEventListener('click', (event) => {
    if (event.target.closest('a') && mobileScreen.matches) {
        setMenuOpen(false);
    }
});

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && mobileScreen.matches
        && menuButton.getAttribute('aria-expanded') === 'true') {
        setMenuOpen(false);
        menuButton.focus();
    }
});

// Si una imagen falla, muestra la alternativa sin repetir solicitudes fallidas.
document.querySelectorAll('img[data-image-fallback]').forEach((image) => {
    function showFallback() {
        const fallback = image.dataset.imageFallback;
        if (!fallback) return;
        delete image.dataset.imageFallback;
        image.src = fallback;
        image.alt = 'Imagen pendiente';
        const caption = image.closest('figure')?.querySelector('figcaption');
        if (caption) caption.textContent = 'Imagen pendiente';
    }
    image.addEventListener('error', showFallback, { once: true });
    if (image.complete && image.naturalWidth === 0) showFallback();
});
