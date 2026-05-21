(function () {
    'use strict';

    var toggle = document.querySelector('[data-nav-toggle]');
    var menuWrap = document.querySelector('[data-nav-menu]');
    if (toggle && menuWrap) {
        toggle.addEventListener('click', function () {
            menuWrap.classList.toggle('is-open');
        });
    }

    document.querySelectorAll('[data-dismiss="alert"]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var alert = btn.closest('.alert');
            if (alert) alert.remove();
        });
    });

    document.querySelectorAll('[data-tabs]').forEach(function (root) {
        var buttons = root.querySelectorAll('[data-tab-target]');
        var panes = root.querySelectorAll('[data-tab-pane]');
        buttons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var target = btn.getAttribute('data-tab-target');
                buttons.forEach(function (b) { b.classList.remove('active'); });
                btn.classList.add('active');
                panes.forEach(function (pane) {
                    pane.classList.toggle('active', pane.id === target);
                });
            });
        });
    });
})();
