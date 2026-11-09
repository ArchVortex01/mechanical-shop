/* ==========================================================================
   MahtoMech Admin Panel — Products Module
   GET /api/products  |  POST /api/products  |  PUT /api/products/:id  |  DELETE /api/products/:id
   ========================================================================== */

let productsPage = 1;
let productsSearch = '';
let productsCatFilter = '';
let allCategories = [];

// ── Load Products ─────────────────────────────────────────────────────────────
async function loadProducts() {
    tableLoading('productsBody', 6);
    const res = await API.products.list({
        search: productsSearch,
        category: productsCatFilter,
        page: productsPage,
        limit: 15
    });

    if (!res || !res.ok) {
        tableError('productsBody', 6, res?.data?.message || 'Failed to load products.');
        return;
    }

    const { data } = res.data;
    const products  = data?.products || data?.items || data || [];
    const total     = data?.total || data?.count || products.length;
    const totalPages = data?.total_pages || Math.ceil(total / 15) || 1;

    if (!products.length) {
        tableEmpty('productsBody', 6, '📦', 'No products found.');
        buildPagination('productsPagination', 'productsPaginInfo', 1, 1, 0, () => {});
        return;
    }

    document.getElementById('productsBody').innerHTML = products.map(p => `
        <tr>
            <td>
                <div style="display:flex;align-items:center;gap:10px">
                    ${p.image_url ? `<img src="${escHtml(p.image_url)}" style="width:36px;height:36px;object-fit:cover;border-radius:6px;border:1px solid var(--border-card)" onerror="this.style.display='none'">` : '<div style="width:36px;height:36px;background:var(--bg-surface);border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:1.2rem">📦</div>'}
                    <div>
                        <div class="table-cell-bold">${escHtml(p.name)}</div>
                        <div style="font-size:0.75rem;color:var(--text-muted)">${escHtml(p.sku || '—')}</div>
                    </div>
                </div>
            </td>
            <td>${escHtml(p.category_name || p.category || '—')}</td>
            <td class="table-cell-bold">${fmtCurrency(p.price)}</td>
            <td>
                <span style="font-weight:600;color:${(p.stock_quantity||0) === 0 ? 'var(--status-danger)' : (p.stock_quantity||0) < 10 ? 'var(--status-warning)' : 'var(--status-success)'}">
                    ${p.stock_quantity ?? 0}
                </span>
            </td>
            <td>${statusBadge(p.is_active || p.status === 'active' ? 'active' : 'inactive')}</td>
            <td>
                <div class="table-actions">
                    <button class="btn btn-secondary btn-icon btn-sm" title="Edit" onclick="editProduct(${p.id})">✏️</button>
                    <button class="btn btn-danger btn-icon btn-sm" title="Delete" onclick="deleteProduct(${p.id}, '${escHtml(p.name)}')">🗑️</button>
                </div>
            </td>
        </tr>
    `).join('');

    buildPagination('productsPagination', 'productsPaginInfo', productsPage, totalPages, total, (pg) => {
        productsPage = pg;
        loadProducts();
    });
}

// ── Load categories for dropdowns ─────────────────────────────────────────────
async function loadCategoriesForDropdown() {
    if (allCategories.length) return;
    const res = await API.categories.list();
    if (!res || !res.ok) return;
    allCategories = res.data.data || res.data.categories || res.data || [];
    populateCategoryDropdowns();
}

function populateCategoryDropdowns() {
    // Filter dropdown
    const filterSel = document.getElementById('productCatFilter');
    if (filterSel && filterSel.options.length <= 1) {
        allCategories.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name;
            filterSel.appendChild(opt);
        });
    }
    // Modal dropdown
    const modalSel = document.getElementById('pCategory');
    if (modalSel) {
        modalSel.innerHTML = '<option value="">Select category...</option>';
        allCategories.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = c.name;
            modalSel.appendChild(opt);
        });
    }
}

// ── Add Product ───────────────────────────────────────────────────────────────
document.getElementById('addProductBtn')?.addEventListener('click', () => {
    document.getElementById('productModalTitle').textContent = 'Add Product';
    document.getElementById('productForm').reset();
    document.getElementById('productId').value = '';
    document.getElementById('pIsActive').checked = true;
    loadCategoriesForDropdown().then(populateCategoryDropdowns);
    openModal('productModal');
});

// ── Edit Product ──────────────────────────────────────────────────────────────
async function editProduct(id) {
    // Find product in current table data or fetch
    document.getElementById('productModalTitle').textContent = 'Edit Product';
    document.getElementById('productId').value = id;
    await loadCategoriesForDropdown();
    populateCategoryDropdowns();

    // Fetch product details
    const res = await API.get(`/products/${id}`);
    if (!res || !res.ok) { toast.error('Error', 'Could not load product details.'); return; }
    const p = res.data.data || res.data.product || res.data;

    document.getElementById('pName').value        = p.name || '';
    document.getElementById('pCategory').value    = p.category_id || '';
    document.getElementById('pDescription').value = p.description || '';
    document.getElementById('pPrice').value       = p.price || '';
    document.getElementById('pStock').value       = p.stock_quantity ?? 0;
    document.getElementById('pSku').value         = p.sku || '';
    document.getElementById('pBrand').value       = p.brand || '';
    document.getElementById('pImage').value       = p.image_url || '';
    document.getElementById('pIsActive').checked  = p.is_active !== false;

    openModal('productModal');
}

// ── Save Product (Add/Edit) ───────────────────────────────────────────────────
document.getElementById('saveProductBtn')?.addEventListener('click', async () => {
    const id   = document.getElementById('productId').value;
    const name = document.getElementById('pName').value.trim();
    const cat  = document.getElementById('pCategory').value;
    const price = parseFloat(document.getElementById('pPrice').value);

    if (!name)          { toast.warning('Validation', 'Product name is required.'); return; }
    if (!cat)           { toast.warning('Validation', 'Please select a category.'); return; }
    if (isNaN(price))   { toast.warning('Validation', 'Valid price is required.'); return; }

    const body = {
        name,
        category_id:     parseInt(cat),
        description:     document.getElementById('pDescription').value.trim(),
        price,
        stock_quantity:  parseInt(document.getElementById('pStock').value) || 0,
        sku:             document.getElementById('pSku').value.trim(),
        brand:           document.getElementById('pBrand').value.trim(),
        image_url:       document.getElementById('pImage').value.trim(),
        is_active:       document.getElementById('pIsActive').checked
    };

    const btn = document.getElementById('saveProductBtn');
    btn.disabled = true; btn.textContent = 'Saving…';

    const res = id
        ? await API.products.update(id, body)
        : await API.products.create(body);

    btn.disabled = false; btn.textContent = 'Save Product';

    if (!res || !res.ok) {
        toast.error('Save Failed', res?.data?.message || 'Could not save product.');
        return;
    }
    toast.success('Success', `Product ${id ? 'updated' : 'created'} successfully.`);
    closeModal('productModal');
    loadProducts();
});

// ── Delete Product ────────────────────────────────────────────────────────────
function deleteProduct(id, name) {
    confirmAction('Delete Product', `Are you sure you want to delete "${name}"? This cannot be undone.`, async () => {
        const res = await API.products.remove(id);
        if (!res || !res.ok) { toast.error('Delete Failed', res?.data?.message || 'Could not delete product.'); return; }
        toast.success('Deleted', `"${name}" has been removed.`);
        loadProducts();
    });
}

// ── Search & Filter ───────────────────────────────────────────────────────────
document.getElementById('productSearch')?.addEventListener('input', debounce((e) => {
    productsSearch = e.target.value.trim();
    productsPage   = 1;
    loadProducts();
}));

document.getElementById('productCatFilter')?.addEventListener('change', (e) => {
    productsCatFilter = e.target.value;
    productsPage      = 1;
    loadProducts();
});

// ── Register ─────────────────────────────────────────────────────────────────
SECTION_LOADERS['products'] = () => {
    loadCategoriesForDropdown();
    loadProducts();
};

