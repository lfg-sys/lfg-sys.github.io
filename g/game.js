// Loads YouTube only when the visitor presses play.
document.querySelectorAll('.video').forEach(function (box) {
  box.addEventListener('click', function () {
    var f = document.createElement('iframe');
    f.src = box.dataset.src;
    f.allow = 'autoplay; encrypted-media; picture-in-picture';
    f.allowFullscreen = true;
    f.title = 'Gameplay video';
    box.replaceChildren(f);
  }, { once: true });
});
