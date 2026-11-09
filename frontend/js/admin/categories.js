/* ==========================================================================
   MahtoMech Admin Panel — Categories Module
   GET /api/categories  |  POST /api/categories  |  PUT /api/categories/:id  |  DELETE /api/categories/:id
   ========================================================================== */

async function loadCategories() {
    tableLoading('categoriesBody', 5);
    const res = await API.categories.list();

    if (!res || !res.ok) {
        tableError('categoriesBody', 5, res?.data?.message || 'Failed to load categories.');
        return;
    }

    const cats = res.data.data || res.data.categories || res.data || [];

    if (!cats.length) {
        tableEmpty('categoriesBody', 5, '🏷️', 'No categories found. Add your first category.');
        return;
    }

    document.getElementById('categoriesBody').innerHTML = cats.map(c => `
        <tr>
            <td class="table-cell-bold">${escHtml(c.name)}</td>
            <td><code style="font-size:0.78rem;color:var(--text-muted)">${escHtml(c.slug || '—')}</code></td>
            <td style="color:var(--text-muted);font-size:0.85rem">${escHtml(c.description || '—')}</td>
            <td>
                <span class="badge badge-info">${c.product_count ?? 0} products</span>
            </td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-secondary btn-icon btn-sm" title="Edit" onclick="editCategory(${c.id}, '${escHtml(c.name)}', '${escHtml(c.slug||'')}', '${escHtml(c.description||'')}')">✏️</button>
                    <button class="btn btn-danger btn-icon btn-sm" title="Delete" onclick="deleteCategory(${c.id}, '${escHtml(c.name)}', ${c.product_count||0})">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');

    // Also refresh the allCategories cache used by products module
    allCategories = cats;
}

// ── Add Category ──────────────────────────────────────────────────────────────
document.getElementById('addCategoryBtn')?.addEventListener('click', () => {
    document.getElementById('categoryModalTitle').textContent = 'Add Category';
    document.getElementById('categoryForm').reset();
    document.getElementById('categoryId').value = '';
    openModal('categoryModal');
});

// ── Auto-generate slug ────────────────────────────────────────────────────────
document.getElementById('catName')?.addEventListener('input', (e) => {
    const slugField = document.getElementById('catSlug');
    if (slugField && !slugField.dataset.manuallyEdited) {
        slugField.value = e.target.value.trim().toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    }
});

document.getElementById('catSlug')?.addEventListener('input', (e) => {
    e.target.dataset.manuallyEdited = e.target.value ? 'true' : '';
});

// ── Edit Category ─────────────────────────────────────────────────────────────
function editCategory(id, name, slug, description) {
    document.getElementById('categoryModalTitle').textContent = 'Edit Category';
    document.getElementById('categoryId').value   = id;
    document.getElementById('catName').value      = name;
    document.getElementById('catSlug').value      = slug;
    document.getElementById('catDescription').value = description;
    openModal('categoryModal');
}

// ── Save Category ─────────────────────────────────────────────────────────────
document.getElementById('saveCategoryBtn')?.addEventListener('click', async () => {
    const id   = document.getElementById('categoryId').value;
    const name = document.getElementById('catName').value.trim();
    if (!name) { toast.warning('Validation', 'Category name is required.'); return; }

    const body = {
        name,
        slug:        document.getElementById('catSlug').value.trim(),
        description: document.getElementById('catDescription').value.trim()
    };

    const btn = document.getElementById('saveCategoryBtn');
    btn.disabled = true; btn.textContent = 'Saving…';

    const res = id
        ? await API.categories.update(id, body)
        : await API.categories.create(body);

    btn.disabled = false; btn.textContent = 'Save Category';

    if (!res || !res.ok) {
        toast.error('Save Failed', res?.data?.message || 'Could not save category.');
        return;
    }
    toast.success('Success', `Category ${id ? 'updated' : 'created'} successfully.`);
    closeModal('categoryModal');
    allCategories = []; // reset cache
    loadCategories();
});

// ── Delete Category ───────────────────────────────────────────────────────────
function deleteCategory(id, name, productCount) {
    if (productCount > 0) {
        toast.warning('Cannot Delete', `"${name}" has ${productCount} product(s). Reassign or remove them first.`);
        return;
    }
    confirmAction('Delete Category', `Delete category "${name}"? This cannot be undone.`, async () => {
        const res = await API.categories.remove(id);
        if (!res || !res.ok) { toast.error('Delete Failed', res?.data?.message || 'Could not delete category.'); return; }
        toast.success('Deleted', `Category "${name}" removed.`);
        allCategories = [];
        loadCategories();
    });
}

// ── Register ──────────────────────────────────────────────────────────────────
SECTION_LOADERS['categories'] = loadCategories;

