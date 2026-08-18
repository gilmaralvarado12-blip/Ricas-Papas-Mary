(function () {
    'use strict';

    function injectStyles() {
        if (document.getElementById('rpm-inline-dnd-styles')) {
            return;
        }
        var style = document.createElement('style');
        style.id = 'rpm-inline-dnd-styles';
        style.textContent = '' +
            '.rpm-row-dragging { opacity: 0.65; }' +
            '.rpm-row-drop-target { outline: 2px dashed #b21e29; background: rgba(255, 244, 210, 0.55); }' +
            '.rpm-drag-handle { user-select: none; font-weight: 700; color: #6b7280; }' +
            '.rpm-drag-disabled { cursor: not-allowed !important; opacity: 0.45; }';
        document.head.appendChild(style);
    }

    function asArray(nodeList) {
        return Array.prototype.slice.call(nodeList || []);
    }

    function getInlineRows(group) {
        return asArray(group.querySelectorAll('tr.form-row')).filter(function (row) {
            return !row.classList.contains('empty-form');
        });
    }

    function getProductoValue(row) {
        var input = row.querySelector('input[name$="-producto"]');
        return input ? (input.value || '').trim() : '';
    }

    function isRowSortable(row) {
        var markedForDeletion = row.querySelector('input[name$="-DELETE"]');
        if (markedForDeletion && markedForDeletion.checked) {
            return false;
        }
        return getProductoValue(row) !== '';
    }

    function setOrderValues(group) {
        var rows = getInlineRows(group).filter(function (row) {
            return row.style.display !== 'none';
        });

        rows.forEach(function (row, index) {
            var orderInput = row.querySelector('input[name$="-orden"]');
            if (orderInput) {
                orderInput.value = String(index + 1);
            }
        });
    }

    function enableDragAndDrop(group) {
        var tbody = group.querySelector('tbody');
        if (!tbody) {
            return;
        }

        var draggingRow = null;

        getInlineRows(group).forEach(function (row) {
            var handle = row.querySelector('.rpm-drag-handle');
            if (!handle) {
                return;
            }

            var sortable = isRowSortable(row);
            row.draggable = sortable;
            handle.classList.toggle('rpm-drag-disabled', !sortable);
            handle.style.cursor = sortable ? 'grab' : 'not-allowed';
            handle.setAttribute('aria-label', 'Arrastrar fila para ordenar');

            if (!sortable) {
                return;
            }

            row.addEventListener('dragstart', function (event) {
                draggingRow = row;
                row.classList.add('rpm-row-dragging');
                if (event.dataTransfer) {
                    event.dataTransfer.effectAllowed = 'move';
                    event.dataTransfer.setData('text/plain', 'dragging');
                }
            });

            row.addEventListener('dragend', function () {
                row.classList.remove('rpm-row-dragging');
                getInlineRows(group).forEach(function (targetRow) {
                    targetRow.classList.remove('rpm-row-drop-target');
                });
                draggingRow = null;
                setOrderValues(group);
            });

            row.addEventListener('dragover', function (event) {
                if (!draggingRow || draggingRow === row) {
                    return;
                }
                if (!isRowSortable(row)) {
                    return;
                }
                event.preventDefault();
                getInlineRows(group).forEach(function (targetRow) {
                    targetRow.classList.remove('rpm-row-drop-target');
                });
                row.classList.add('rpm-row-drop-target');
                var rect = row.getBoundingClientRect();
                var insertBefore = event.clientY < (rect.top + rect.height / 2);
                if (insertBefore) {
                    tbody.insertBefore(draggingRow, row);
                } else {
                    tbody.insertBefore(draggingRow, row.nextSibling);
                }
            });

            row.addEventListener('drop', function (event) {
                event.preventDefault();
                row.classList.remove('rpm-row-drop-target');
                setOrderValues(group);
            });
        });

        setOrderValues(group);
    }

    function init() {
        injectStyles();
        var group = document.getElementById('destacados_portada-group');
        if (!group) {
            return;
        }

        enableDragAndDrop(group);

        document.addEventListener('click', function (event) {
            var target = event.target;
            if (!target) {
                return;
            }
            if (target.closest('.add-row a')) {
                window.setTimeout(function () {
                    enableDragAndDrop(group);
                }, 60);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
