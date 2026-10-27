/**
 * Food Delivery Information System - Web Client
 */
let currentUser = null;
let charts = {};

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user');
    if (token && userData) {
        currentUser = JSON.parse(userData);
        showDashboard();
    }
});

function getRoleLabel(role) {
    const labels = { customer: 'Customer', rider: 'Rider', merchant: 'Merchant', analyst: 'Analyst', regulator: 'Regulator' };
    return labels[role] || role;
}

// ==================== TOAST ====================
function showToast(msg, type = 'info') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = `toast ${type} show`;
    setTimeout(() => t.classList.remove('show'), 3000);
}

// ==================== MODAL ====================
function openModal(title, html) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = html;
    document.getElementById('modalOverlay').classList.add('active');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

// ==================== LOGIN ====================
function switchLoginTab(tab) {
    document.querySelectorAll('.login-tabs .tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.login-form').forEach(f => f.classList.remove('active'));
    if (tab === 'login') {
        document.querySelector('.login-tabs .tab:first-child').classList.add('active');
        document.getElementById('loginForm').classList.add('active');
    } else {
        document.querySelector('.login-tabs .tab:last-child').classList.add('active');
        document.getElementById('registerForm').classList.add('active');
    }
    document.getElementById('forgotPasswordForm').style.display = 'none';
}

function showForgotPassword() {
    document.getElementById('loginForm').classList.remove('active');
    document.getElementById('forgotPasswordForm').style.display = 'block';
}

function showLoginOnly() {
    document.getElementById('forgotPasswordForm').style.display = 'none';
    document.getElementById('loginForm').classList.add('active');
}

async function login() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    if (!username || !password) { showToast('Please fill in all fields', 'error'); return; }
    try {
        const res = await API.login(username, password);
        if (res.need_2fa) {
            showToast('2FA required - check authenticator app', 'info');
            // Simplified: proceed with 2FA
            const code = prompt('Enter 2FA code:');
            if (code) {
                const res2 = await API.post('/api/auth/login/2fa', { code });
                handleLoginSuccess(res2);
            }
            return;
        }
        handleLoginSuccess(res);
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function register() {
    const data = {
        username: document.getElementById('regUsername').value.trim(),
        email: document.getElementById('regEmail').value.trim(),
        password: document.getElementById('regPassword').value,
        phone: document.getElementById('regPhone').value.trim(),
        role: document.getElementById('regRole').value
    };
    if (!data.username || !data.email || !data.password) { showToast('Please fill in required fields', 'error'); return; }
    try {
        const res = await API.register(data);
        handleLoginSuccess(res);
        showToast('Account created successfully!', 'success');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function forgotPassword() {
    const email = document.getElementById('forgotEmail').value.trim();
    if (!email) { showToast('Please enter your email', 'error'); return; }
    try {
        const res = await API.forgotPassword(email);
        if (res.reset_token) {
            const newPwd = prompt('Enter new password:');
            if (newPwd) {
                await API.resetPassword(res.reset_token, newPwd);
                showToast('Password reset successful!', 'success');
                showLoginOnly();
            }
        } else {
            showToast(res.message, 'info');
        }
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function simulateWechatLogin() {
    const code = prompt('Enter WeChat authorization code (or any text to simulate):') || `wx_code_${Date.now()}`;
    try {
        const res = await API.wechatLogin(code);
        handleLoginSuccess(res);
        showToast('WeChat login successful!', 'success');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function handleLoginSuccess(res) {
    localStorage.setItem('access_token', res.access_token);
    localStorage.setItem('refresh_token', res.refresh_token || '');
    localStorage.setItem('user', JSON.stringify(res.user));
    currentUser = res.user;
    showDashboard();
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    currentUser = null;
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-login').classList.add('active');
    document.getElementById('navbar').classList.add('hidden');
    showToast('Logged out', 'info');
}

// ==================== NAVIGATION ====================
function showDashboard() {
    document.getElementById('page-login').classList.remove('active');
    document.querySelectorAll('.page').forEach(p => {
        if (p.id !== 'page-login') p.classList.remove('active');
    });
    document.getElementById('navbar').classList.remove('hidden');
    document.getElementById('navUserInfo').textContent = `${currentUser.username} (${getRoleLabel(currentUser.role)})`;

    // Build nav links
    const navLinks = document.getElementById('navLinks');
    const links = { customer: ['Browse', 'Orders', 'Profile'], rider: ['Available Orders', 'My Deliveries', 'GPS', 'Profile'],
        merchant: ['Profile', 'Menu', 'Orders', 'Analytics'],
        analyst: ['Overview', 'Charts', 'AI Predictions', 'Environment'],
        regulator: ['Dashboard', 'Users', 'Audit Logs'] };
    const pageMap = { customer: { 'Browse': 'customer', 'Orders': 'customer', 'Profile': 'customer' },
        rider: { 'Available Orders': 'rider', 'My Deliveries': 'rider', 'GPS': 'rider', 'Profile': 'rider' },
        merchant: { 'Profile': 'merchant', 'Menu': 'merchant', 'Orders': 'merchant', 'Analytics': 'merchant' },
        analyst: { 'Overview': 'analyst', 'Charts': 'analyst', 'AI Predictions': 'analyst', 'Environment': 'analyst' },
        regulator: { 'Dashboard': 'regulator', 'Users': 'regulator', 'Audit Logs': 'regulator' } };

    let html = '';
    (links[currentUser.role] || []).forEach(label => {
        html += `<a href="#" onclick="switchSection('${label}')">${label}</a>`;
    });
    navLinks.innerHTML = html;

    // Show role page
    const pageId = `page-${currentUser.role}`;
    document.getElementById(pageId).classList.add('active');
    document.getElementById('navbar').classList.remove('hidden');

    // Load role-specific data
    loadRoleData(currentUser.role);
}

function switchSection(label) {
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    event.target.classList.add('active');
    if (label === 'Profile') {
        showProfile();
    } else {
        loadRoleData(currentUser.role);
    }
}

// ==================== USER PROFILE & SECURITY ====================
function showProfile() {
    const isCustomer = currentUser.role === 'customer';
    const containerId = isCustomer ? 'customerProfile' : 'riderProfile';
    const cardId = isCustomer ? 'customerProfileCard' : 'riderProfileCard';
    const pageId = isCustomer ? '#page-customer' : '#page-rider';

    document.querySelectorAll(pageId + ' .dashboard-grid .card').forEach(c => {
        if (c.id !== cardId) c.style.display = 'none';
    });
    document.getElementById(cardId).style.display = '';

    API.getProfile().then(p => {
        currentUser = Object.assign({}, currentUser, p);
        renderUserProfile(containerId);
    }).catch(e => showToast(e.message, 'error'));
}


function renderUserProfile(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const u = currentUser;
    const twoFAEnabled = u.two_factor_enabled || false;
    container.innerHTML = `
        <div class="profile-info">
            <p><strong>Username:</strong> ${u.username}</p>
            <p><strong>Email:</strong> ${u.email || 'N/A'}</p>
            <p><strong>Role:</strong> ${u.role}</p>
            <p><strong>Phone:</strong> ${u.phone || 'N/A'}</p>
            <hr>
            <div class="security-section">
                <h4><i class="fas fa-shield-alt"></i> Security Settings</h4>
                <p><strong>Two-Factor Authentication:</strong> ${twoFAEnabled ? '✅ Enabled' : '❌ Disabled'}</p>
                ${twoFAEnabled
                    ? '<button class="btn btn-sm btn-danger" onclick="disable2FA()">Disable 2FA</button>'
                    : '<button class="btn btn-sm btn-primary" onclick="setup2FA()">Setup 2FA</button>'}
                <div id="twoFAResult" style="margin-top:10px;"></div>
            </div>
        </div>
    `;
}

async function setup2FA() {
    try {
        const res = await API.setup2FA();
        const div = document.getElementById('twoFAResult');
        if (!div) return;
        div.innerHTML = `
            <div class="alert alert-success">
                <p><strong>✅ 2FA Enabled!</strong></p>
                <p><strong>Secret:</strong> <code>${res.secret}</code></p>
                <p><strong>URI:</strong> <code style="word-break:break-all;">${res.uri}</code></p>
                <p style="margin-top:8px;font-size:0.85rem;color:#666;">
                    Scan the URI with Google Authenticator or enter the secret manually.
                    On next login, you will be prompted for a 6-digit code.
                </p>
                <button class="btn btn-sm btn-outline" onclick="copyToClipboard('${res.secret}')">Copy Secret</button>
            </div>
        `;
        currentUser.two_factor_enabled = true;
        showToast('2FA enabled successfully!', 'success');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function disable2FA() {
    try {
        await API.post('/api/auth/2fa/disable');
        currentUser.two_factor_enabled = false;
        renderUserProfile(currentUser.role === 'customer' ? 'customerProfile' : 'riderProfile');
        showToast('2FA disabled', 'info');
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}


function toggleMobileMenu() {
    document.getElementById('navLinks').classList.toggle('mobile-open');
}

// ==================== LOAD ROLE DATA ====================
async function loadRoleData(role) {
    switch (role) {
        case 'customer': loadCustomerData(); break;
        case 'rider': loadRiderData(); break;
        case 'merchant': loadMerchantData(); break;
        case 'analyst': loadAnalystData(); break;
        case 'regulator': loadRegulatorData(); break;
    }
}

// ==================== CUSTOMER ====================
async function loadCustomerData() {
    document.getElementById('customerName').textContent = currentUser.username;
    document.querySelectorAll('#page-customer .dashboard-grid .card').forEach(c => c.style.display = '');
    document.getElementById('customerProfileCard').style.display = 'none';
    try {
        const [merchants, orders, recs] = await Promise.all([
            API.getMerchants(), API.getMyOrders(), API.getRecommendations(4)
        ]);
        renderMerchants(merchants);
        renderCustomerOrders(orders);
        renderRecommendations(recs);
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function renderMerchants(merchants) {
    const container = document.getElementById('merchantList');
    if (!merchants || merchants.length === 0) {
        container.innerHTML = '<p>No restaurants available.</p>';
        return;
    }
    container.innerHTML = merchants.map(m => `
        <div class="merchant-card" onclick="showMerchantMenu(${m.id}, '${m.name}')">
            <h4>${m.name}</h4>
            <div class="cuisine"><i class="fas fa-tag"></i> ${m.cuisine_type || 'Various'}</div>
            <div class="rating"><i class="fas fa-star"></i> ${m.rating || 'N/A'} ${m.address ? `| ${m.address}` : ''}</div>
        </div>
    `).join('');
}

function renderCustomerOrders(orders) {
    const container = document.getElementById('customerOrders');
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No orders yet. Start ordering!</p>';
        return;
    }
    container.innerHTML = orders.slice(0, 5).map(o => `
        <div class="order-card">
            <div class="order-header">
                <strong>${o.merchant_name}</strong>
                <span class="badge badge-${o.status}">${o.status}</span>
            </div>
            <div class="order-meta">$${o.total_price.toFixed(2)} | ${o.created_at ? new Date(o.created_at).toLocaleDateString() : ''} | ${o.payment_method}</div>
            <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap;">
                ${o.status === 'delivered' ? `<button class="btn btn-sm btn-outline" onclick="showReviewForm(${o.id})">Review</button>` : ''}
                ${['pending','accepted'].includes(o.status) ? `<button class="btn btn-sm btn-danger" onclick="cancelOrder(${o.id})">Cancel</button>` : ''}
                ${['accepted','picked_up','delivering'].includes(o.status) && o.rider_name ? `<button class="btn btn-sm btn-outline" onclick="trackRider(${o.id})">Track Rider</button>` : ''}
            </div>
        </div>
    `).join('');
}

function renderRecommendations(recs) {
    const container = document.getElementById('recommendations');
    if (!recs || recs.length === 0) {
        container.innerHTML = '<p>No recommendations yet. Place some orders first!</p>';
        return;
    }
    container.innerHTML = recs.map(r => `
        <div class="menu-item">
            <div class="name">${r.name}</div>
            <div class="price">$${r.price.toFixed(2)}</div>
            <div class="category">${r.category || ''}</div>
            <div style="font-size:0.8rem;color:var(--text-light)">${r.reason || ''}</div>
        </div>
    `).join('');
}

async function showMerchantMenu(merchantId, name) {
    try {
        const [merchant, menu] = await Promise.all([
            API.getMerchant(merchantId), API.getMenu(merchantId)
        ]);
        let html = `
            <h4>${merchant.name}</h4>
            <p>${merchant.description || ''} | ${merchant.address || ''}</p>
            <hr style="margin:12px 0">
            <div style="display:grid;gap:8px;">
        `;
        menu.forEach(item => {
            html += `
                <div style="display:flex;justify-content:space-between;align-items:center;padding:8px;border:1px solid var(--border);border-radius:8px;">
                    <div><strong>${item.name}</strong><br><small>${item.category || ''}</small></div>
                    <div><strong style="color:var(--primary)">$${item.price.toFixed(2)}</strong>
                        <button class="btn btn-primary btn-sm" onclick="addToOrder(${merchantId}, ${item.id}, '${item.name}', ${item.price})">+</button>
                    </div>
                </div>
            `;
        });
        html += `</div><hr style="margin:12px 0">
            <div id="orderSummary">
                <h4>Your Order</h4>
                <div id="cartItems"></div>
                <p><strong>Total: $<span id="cartTotal">0.00</span></strong></p>
                <div class="form-group"><label>Delivery Address</label><input type="text" id="deliveryAddr" placeholder="Your address"></div>
                <div class="form-group"><label>Note</label><textarea id="orderNote" rows="2"></textarea></div>
                <div class="form-group"><label>Payment</label>
                    <select id="paymentMethod"><option value="cash">Cash</option><option value="card">Card</option><option value="wechat">WeChat Pay</option></select>
                </div>
                <button class="btn btn-primary btn-full" onclick="placeOrder(${merchantId})">Place Order</button>
            </div>
        `;
        window._currentOrder = { merchantId, items: [] };
        openModal(`Order from ${name}`, html);
    } catch (e) {
        showToast(e.message, 'error');
    }
}

function addToOrder(merchantId, itemId, name, price) {
    if (!window._currentOrder) window._currentOrder = { merchantId, items: [] };
    const existing = window._currentOrder.items.find(i => i.id === itemId);
    if (existing) existing.qty++;
    else window._currentOrder.items.push({ id: itemId, name, price, qty: 1 });
    renderCart();
}

function renderCart() {
    const cart = document.getElementById('cartItems');
    const total = document.getElementById('cartTotal');
    if (!window._currentOrder || window._currentOrder.items.length === 0) {
        cart.innerHTML = '<p>Cart is empty. Add items from the menu.</p>';
        total.textContent = '0.00';
        return;
    }
    const items = window._currentOrder.items;
    let html = '';
    let sum = 0;
    items.forEach((item, i) => {
        const subtotal = item.price * item.qty;
        sum += subtotal;
        html += `<div style="display:flex;justify-content:space-between;padding:4px 0;">
            <span>${item.name} x${item.qty}</span>
            <span>$${subtotal.toFixed(2)} <button class="btn btn-sm btn-danger" onclick="removeFromOrder(${i})" style="padding:2px 6px;">x</button></span>
        </div>`;
    });
    cart.innerHTML = html;
    total.textContent = sum.toFixed(2);
}

function removeFromOrder(idx) {
    window._currentOrder.items.splice(idx, 1);
    renderCart();
}

async function placeOrder(merchantId) {
    const addr = document.getElementById('deliveryAddr').value.trim();
    if (!addr) { showToast('Please enter delivery address', 'error'); return; }
    const items = window._currentOrder.items;
    if (items.length === 0) { showToast('Cart is empty', 'error'); return; }

    try {
        const res = await API.placeOrder({
            merchant_id: merchantId,
            items: items.map(i => ({ menu_item_id: i.id, quantity: i.qty })),
            delivery_address: addr,
            note: document.getElementById('orderNote').value,
            payment_method: document.getElementById('paymentMethod').value
        });
        showToast(`Order placed! Order #${res.order_id}`, 'success');
        closeModal();
        loadCustomerData();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function cancelOrder(orderId) {
    if (!confirm('Cancel this order?')) return;
    try {
        await API.cancelOrder(orderId);
        showToast('Order cancelled', 'info');
        loadCustomerData();
    } catch (e) { showToast(e.message, 'error'); }
}

async function trackRider(orderId) {
    try {
        const res = await API.trackOrder(orderId);
        if (res.latitude) {
            openModal('Rider Tracking', `
                <p><strong>Rider:</strong> ${res.rider_name}</p>
                <p><strong>Location:</strong> ${res.latitude.toFixed(6)}, ${res.longitude.toFixed(6)}</p>
                <p><strong>Speed:</strong> ${res.speed || 'N/A'} km/h</p>
                <p><strong>Last Updated:</strong> ${new Date(res.last_updated).toLocaleString()}</p>
                <p><i class="fas fa-map-marked-alt" style="font-size:3rem;color:var(--primary);display:block;text-align:center;margin:20px 0;"></i></p>
                <p style="text-align:center;color:var(--text-light);">Your rider is on the way! 🏍️</p>
            `);
        } else {
            showToast('No location data yet', 'info');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function showReviewForm(orderId) {
    openModal('Rate Your Order', `
        <div class="form-group"><label>Rating (1-5)</label>
            <select id="reviewRating">
                <option value="5">⭐ 5 - Excellent</option>
                <option value="4">⭐ 4 - Good</option>
                <option value="3">⭐ 3 - Average</option>
                <option value="2">⭐ 2 - Poor</option>
                <option value="1">⭐ 1 - Terrible</option>
            </select></div>
        <div class="form-group"><label>Comment</label><textarea id="reviewContent" rows="3" placeholder="How was your experience?"></textarea></div>
        <button class="btn btn-primary btn-full" onclick="submitReview(${orderId})">Submit Review</button>
    `);
}

async function submitReview(orderId) {
    try {
        await API.submitReview({
            order_id: orderId,
            rating: parseInt(document.getElementById('reviewRating').value),
            content: document.getElementById('reviewContent').value
        });
        showToast('Review submitted!', 'success');
        closeModal();
        loadCustomerData();
    } catch (e) { showToast(e.message, 'error'); }
}

// ==================== RIDER ====================
async function loadRiderData() {
    document.querySelectorAll('#page-rider .dashboard-grid .card').forEach(c => c.style.display = '');
    document.getElementById('riderProfileCard').style.display = 'none';
    try {
        const [available, myOrders] = await Promise.all([
            API.getAvailableOrders(), API.getMyOrders()
        ]);
        renderAvailableOrders(available);
        renderRiderOrders(myOrders);
    } catch (e) { showToast(e.message, 'error'); }
}

function renderAvailableOrders(orders) {
    const container = document.getElementById('availableOrders');
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No available orders right now.</p>';
        return;
    }
    container.innerHTML = orders.slice(0, 10).map(o => `
        <div class="order-card">
            <div class="order-header">
                <strong>${o.merchant_name}</strong>
                <span class="badge badge-pending">$${o.total_price.toFixed(2)}</span>
            </div>
            <div class="order-meta">To: ${o.delivery_address} | ${o.customer_name}</div>
            <button class="btn btn-success btn-sm" onclick="acceptOrder(${o.id})" style="margin-top:8px;">
                <i class="fas fa-check"></i> Accept Order
            </button>
        </div>
    `).join('');
}

async function acceptOrder(orderId) {
    try {
        await API.acceptOrder(orderId);
        showToast('Order accepted!', 'success');
        loadRiderData();
    } catch (e) { showToast(e.message, 'error'); }
}

function renderRiderOrders(orders) {
    const container = document.getElementById('riderDeliveries');
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No orders in progress.</p>';
        return;
    }
    container.innerHTML = orders.filter(o => o.status !== 'delivered' && o.status !== 'cancelled').map(o => `
        <div class="order-card" style="border-left-color:${o.status === 'delivered' ? 'var(--success)' : o.status === 'picked_up' ? 'var(--info)' : 'var(--warning)'}">
            <div class="order-header">
                <strong>${o.merchant_name}</strong>
                <span class="badge badge-${o.status}">${o.status}</span>
            </div>
            <div class="order-meta">$${o.total_price.toFixed(2)} | ${o.delivery_address}</div>
            <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
                ${o.status === 'accepted' || o.status === 'preparing' ? `<button class="btn btn-sm btn-primary" onclick="updateRiderStatus(${o.id}, 'picked_up')">Picked Up</button>` : ''}
                ${o.status === 'picked_up' ? `<button class="btn btn-sm btn-primary" onclick="updateRiderStatus(${o.id}, 'delivering')">Delivering</button>` : ''}
                ${o.status === 'delivering' ? `<button class="btn btn-sm btn-success" onclick="updateRiderStatus(${o.id}, 'delivered')">Delivered ✅</button>` : ''}
            </div>
        </div>
    `).join('') || '<p>No active deliveries.</p>';
}

async function updateRiderStatus(orderId, status) {
    try {
        await API.updateRiderOrderStatus(orderId, status);
        showToast(`Order updated to ${status}`, 'success');
        loadRiderData();
    } catch (e) { showToast(e.message, 'error'); }
}

let gpsInterval = null;
function startGPS() {
    if (gpsInterval) { clearInterval(gpsInterval); gpsInterval = null; showToast('GPS stopped', 'info'); return; }
    if (!navigator.geolocation) { showToast('GPS not available', 'error'); return; }

    gpsInterval = setInterval(async () => {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            document.getElementById('gpsLat').textContent = pos.coords.latitude.toFixed(6);
            document.getElementById('gpsLng').textContent = pos.coords.longitude.toFixed(6);
            try {
                await API.reportLocation({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                    accuracy: pos.coords.accuracy,
                    speed: pos.coords.speed,
                    extra_data: { battery: navigator.battery ? navigator.battery.level : null }
                });
            } catch (e) { /* silently retry next interval */ }
        }, () => {}, { enableHighAccuracy: true });
    }, 10000);

    showToast('GPS tracking started!', 'success');
    document.querySelector('#gpsStatus .btn').textContent = 'Stop GPS';
}

// ==================== MERCHANT ====================
async function loadMerchantData() {
    try {
        const profile = await API.getMerchantProfile().catch(() => null);
        renderMerchantProfile(profile);
        if (profile) {
            const [menu, orders] = await Promise.all([
                API.getMenu(profile.id), API.getMerchantOrders()
            ]);
            renderMerchantMenu(menu);
            renderMerchantOrders(orders);
            loadMerchantAnalytics(profile.id);
        }
    } catch (e) { /* showToast(e.message, 'error'); */ }
}

function renderMerchantProfile(profile) {
    const container = document.getElementById('merchantProfile');
    const btn = document.getElementById('createMerchantBtn');
    if (!profile) {
        container.innerHTML = '<p>You haven\'t registered as a merchant yet.</p>';
        btn.style.display = 'block';
        return;
    }
    btn.style.display = 'none';
    container.innerHTML = `
        <p><strong>${profile.name}</strong></p>
        <p>${profile.description || ''}</p>
        <p>${profile.address || ''} | ${profile.cuisine_type || ''}</p>
        <p><i class="fas fa-star" style="color:#FFC107"></i> ${profile.rating || 'N/A'}</p>
    `;
}

function showCreateMerchant() {
    openModal('Register as Merchant', `
        <div class="form-group"><label>Restaurant Name</label><input type="text" id="mName"></div>
        <div class="form-group"><label>Description</label><textarea id="mDesc" rows="2"></textarea></div>
        <div class="form-group"><label>Address</label><input type="text" id="mAddr"></div>
        <div class="form-group"><label>Cuisine Type</label><input type="text" id="mCuisine" placeholder="e.g. Italian, Chinese"></div>
        <button class="btn btn-primary btn-full" onclick="createMerchant()">Register</button>
    `);
}

async function createMerchant() {
    try {
        await API.registerMerchant({
            name: document.getElementById('mName').value,
            description: document.getElementById('mDesc').value,
            address: document.getElementById('mAddr').value,
            cuisine_type: document.getElementById('mCuisine').value
        });
        showToast('Merchant registered!', 'success');
        closeModal();
        loadMerchantData();
    } catch (e) { showToast(e.message, 'error'); }
}

function renderMerchantMenu(items) {
    const container = document.getElementById('merchantMenu');
    if (!items || items.length === 0) {
        container.innerHTML = '<p>No menu items. Add your first item!</p>';
        return;
    }
    container.innerHTML = items.map(item => `
        <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border);">
            <div><strong>${item.name}</strong><br><small>${item.category || ''}</small></div>
            <div><strong>$${item.price.toFixed(2)}</strong> <small>Stock: ${item.stock}</small></div>
        </div>
    `).join('');
}

function showAddMenuItem() {
    openModal('Add Menu Item', `
        <div class="form-group"><label>Name</label><input type="text" id="miName"></div>
        <div class="form-group"><label>Price</label><input type="number" id="miPrice" step="0.01"></div>
        <div class="form-group"><label>Category</label><input type="text" id="miCategory"></div>
        <div class="form-group"><label>Stock</label><input type="number" id="miStock" value="999"></div>
        <div class="form-group"><label>Description</label><textarea id="miDesc" rows="2"></textarea></div>
        <button class="btn btn-primary btn-full" onclick="addMenuItem()">Add Item</button>
    `);
}

async function addMenuItem() {
    try {
        await API.addMenuItem({
            name: document.getElementById('miName').value,
            price: parseFloat(document.getElementById('miPrice').value),
            category: document.getElementById('miCategory').value,
            stock: parseInt(document.getElementById('miStock').value) || 999,
            description: document.getElementById('miDesc').value
        });
        showToast('Item added!', 'success');
        closeModal();
        loadMerchantData();
    } catch (e) { showToast(e.message, 'error'); }
}

function renderMerchantOrders(orders) {
    const container = document.getElementById('merchantOrders');
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No orders yet.</p>';
        return;
    }
    container.innerHTML = orders.slice(0, 5).map(o => `
        <div class="order-card">
            <div class="order-header">
                <strong>Order #${o.id}</strong>
                <span class="badge badge-${o.status}">${o.status}</span>
            </div>
            <div class="order-meta">${o.customer_name} | $${o.total_price.toFixed(2)}</div>
            <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap;">
                ${o.status === 'pending' ? `<button class="btn btn-sm btn-success" onclick="merchantUpdateOrder(${o.id}, 'accepted')">Accept</button>
                    <button class="btn btn-sm btn-danger" onclick="merchantUpdateOrder(${o.id}, 'cancelled')">Reject</button>` : ''}
                ${o.status === 'accepted' ? `<button class="btn btn-sm btn-primary" onclick="merchantUpdateOrder(${o.id}, 'preparing')">Start Preparing</button>` : ''}
            </div>
        </div>
    `).join('');
}

async function merchantUpdateOrder(orderId, status) {
    try { await API.updateOrderStatus(orderId, status);
        showToast(`Order #${orderId}: ${status}`, 'success');
        loadMerchantData();
    } catch (e) { showToast(e.message, 'error'); }
}

async function loadMerchantAnalytics(merchantId) {
    try {
        const sales = await API.getSales(merchantId, 30);
        if (sales && sales.length > 0 && document.getElementById('salesChart')) {
            renderChart('salesChart', 'line', {
                labels: sales.map(s => s.date),
                datasets: [{
                    label: 'Daily Sales ($)',
                    data: sales.map(s => s.total_sales),
                    borderColor: '#FF5722',
                    backgroundColor: 'rgba(255,87,34,0.1)',
                    fill: true,
                    tension: 0.4
                }]
            });
        }
    } catch (e) {}
}

// ==================== ANALYST ====================
async function loadAnalystData() {
    try {
        const [overview, sales, cuisine, hourly, ratings, payment, env] = await Promise.all([
            API.getOverview(), API.getSales(null, 30), API.getCuisineDist(),
            API.getHourlyDist(), API.getRatingDist(), API.getPaymentAnalysis(30),
            API.getEnvImpact(30)
        ]);

        // Overview stats
        if (overview) {
            document.getElementById('analystOverview').innerHTML = `
                <div class="stat-item"><div class="stat-value">${overview.total_users}</div><div class="stat-label">Users</div></div>
                <div class="stat-item"><div class="stat-value">${overview.total_orders}</div><div class="stat-label">Orders</div></div>
                <div class="stat-item"><div class="stat-value">${overview.total_merchants}</div><div class="stat-label">Merchants</div></div>
                <div class="stat-item"><div class="stat-value">$${overview.total_revenue.toLocaleString()}</div><div class="stat-label">Revenue</div></div>
                <div class="stat-item"><div class="stat-value">${overview.average_rating}</div><div class="stat-label">Avg Rating</div></div>
            `;
        }

        // Charts
        if (sales && sales.length > 0) {
            renderChart('analystSalesChart', 'line', {
                labels: sales.map(s => s.date.slice(5)),
                datasets: [{
                    label: 'Sales ($)',
                    data: sales.map(s => s.total_sales),
                    borderColor: '#FF5722',
                    backgroundColor: 'rgba(255,87,34,0.1)',
                    fill: true, tension: 0.4
                }, {
                    label: 'Orders',
                    data: sales.map(s => s.order_count),
                    borderColor: '#2196F3',
                    backgroundColor: 'rgba(33,150,243,0.1)',
                    fill: true, tension: 0.4,
                    yAxisID: 'y1'
                }]
            }, { scales: { y1: { position: 'right', grid: { drawOnChartArea: false } } } });
        }

        if (cuisine && cuisine.length > 0) {
            renderChart('cuisineChart', 'doughnut', {
                labels: cuisine.map(c => c.cuisine),
                datasets: [{ data: cuisine.map(c => c.order_count),
                    backgroundColor: ['#FF5722','#4CAF50','#2196F3','#FF9800','#9C27B0','#607D8B'] }]
            });
        }

        if (hourly && hourly.length > 0) {
            renderChart('hourlyChart', 'bar', {
                labels: hourly.map(h => `${h.hour}:00`),
                datasets: [{ label: 'Orders', data: hourly.map(h => h.order_count),
                    backgroundColor: '#FF9800' }]
            });
        }

        if (ratings && ratings.length > 0) {
            renderChart('ratingChart', 'bar', {
                labels: ratings.map(r => `⭐${r.rating}`),
                datasets: [{ label: 'Count', data: ratings.map(r => r.count),
                    backgroundColor: ['#f44336','#FF9800','#FFC107','#8BC34A','#4CAF50'] }]
            });
        }

        if (payment && payment.length > 0) {
            renderChart('paymentChart', 'pie', {
                labels: payment.map(p => p.method),
                datasets: [{ data: payment.map(p => p.total),
                    backgroundColor: ['#4CAF50','#2196F3','#FF9800','#9C27B0'] }]
            });
        }

        // Environment
        if (env) {
            document.getElementById('envImpact').innerHTML = `
                <div class="stats-row">
                    <div class="stat-item"><div class="stat-value">${env.total_deliveries}</div><div class="stat-label">Deliveries</div></div>
                    <div class="stat-item"><div class="stat-value">${env.estimated_co2_kg}kg</div><div class="stat-label">CO2</div></div>
                    <div class="stat-item"><div class="stat-value">${env.trees_needed_for_offset}</div><div class="stat-label">Trees to Offset</div></div>
                </div>
                <ul style="margin-top:10px;font-size:0.9rem;color:var(--text-light);">
                    ${(env.eco_tips || []).map(t => `<li>🌱 ${t}</li>`).join('')}
                </ul>
            `;
        }
    } catch (e) { showToast('Error loading analytics: ' + e.message, 'error'); }
}

async function trainModel() {
    try {
        const res = await API.trainModel();
        showToast(`Model trained! R² score: ${res.r2_score}`, 'success');
        loadPredictions();
    } catch (e) { showToast(e.message, 'error'); }
}

async function loadPredictions() {
    try {
        const preds = await API.getPredictions(null, 7);
        if (!preds || preds.error) {
            showToast(preds?.error || 'No predictions available', 'info');
            return;
        }
        renderChart('predictionChart', 'bar', {
            labels: preds.map(p => p.date.slice(5)),
            datasets: [{
                label: `Predicted Sales (conf: ${preds[0]?.confidence || 'N/A'})`,
                data: preds.map(p => p.predicted_sales),
                backgroundColor: '#4CAF50'
            }]
        });
        showToast('Predictions loaded!', 'success');
    } catch (e) { showToast(e.message, 'error'); }
}

// ==================== REGULATOR ====================
async function loadRegulatorData() {
    try {
        const [dashboard, users, logs] = await Promise.all([
            API.getAdminDashboard(), API.getUsers(), API.getAuditLogs(30)
        ]);

        if (dashboard) {
            document.getElementById('regulatorOverview').innerHTML = `
                <div class="stat-item"><div class="stat-value">${dashboard.total_users}</div><div class="stat-label">Total Users</div></div>
                <div class="stat-item"><div class="stat-value">${dashboard.active_users}</div><div class="stat-label">Active</div></div>
                <div class="stat-item"><div class="stat-value">${dashboard.total_orders}</div><div class="stat-label">Orders</div></div>
                <div class="stat-item"><div class="stat-value">${dashboard.total_merchants}</div><div class="stat-label">Merchants</div></div>
                <div class="stat-item"><div class="stat-value" style="color:var(--success)">${dashboard.system_status}</div><div class="stat-label">System</div></div>
            `;
        }

        if (users) {
            document.getElementById('userManagement').innerHTML = `
                <div class="table-wrap"><table>
                    <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Email</th><th>2FA</th><th>Active</th><th>Actions</th></tr></thead>
                    <tbody>${users.map(u => `
                        <tr>
                            <td>${u.id}</td>
                            <td>${u.username}</td>
                            <td><span class="badge badge-${u.role}">${u.role}</span></td>
                            <td>${u.email}</td>
                            <td>${u.two_factor_enabled ? '✅' : '❌'}</td>
                            <td>${u.is_active ? '✅' : '❌'}</td>
                            <td>
                                <button class="btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleUser(${u.id})">${u.is_active ? 'Deactivate' : 'Activate'}</button>
                                <select onchange="changeRole(${u.id}, this.value)" style="padding:4px;font-size:0.8rem;">
                                    <option value="">Change role...</option>
                                    <option value="customer">Customer</option>
                                    <option value="rider">Rider</option>
                                    <option value="merchant">Merchant</option>
                                    <option value="analyst">Analyst</option>
                                    <option value="regulator">Regulator</option>
                                </select>
                            </td>
                        </tr>
                    `).join('')}</tbody>
                </table></div>
            `;
        }

        if (logs) {
            document.getElementById('auditLogs').innerHTML = `
                <div class="table-wrap"><table>
                    <thead><tr><th>Time</th><th>User ID</th><th>Action</th><th>Resource</th><th>Details</th></tr></thead>
                    <tbody>${logs.slice(0, 20).map(l => `
                        <tr>
                            <td>${new Date(l.created_at).toLocaleString()}</td>
                            <td>${l.user_id || '-'}</td>
                            <td>${l.action}</td>
                            <td>${l.resource_type || '-'} #${l.resource_id || '-'}</td>
                            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${l.details ? JSON.stringify(l.details).slice(0, 60) : '-'}</td>
                        </tr>
                    `).join('')}</tbody>
                </table></div>
            `;
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function toggleUser(userId) {
    try {
        await API.toggleUserStatus(userId);
        showToast('User status toggled', 'success');
        loadRegulatorData();
    } catch (e) { showToast(e.message, 'error'); }
}

async function changeRole(userId, role) {
    if (!role) return;
    try {
        await API.changeUserRole(userId, role);
        showToast(`Role changed to ${role}`, 'success');
        loadRegulatorData();
    } catch (e) { showToast(e.message, 'error'); }
}

// ==================== CHART HELPER ====================
function renderChart(canvasId, type, data, extraOpts = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (charts[canvasId]) {
        charts[canvasId].destroy();
        delete charts[canvasId];
    }
    const ctx = canvas.getContext('2d');
    charts[canvasId] = new Chart(ctx, {
        type,
        data,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: type !== 'bar' || true, position: 'bottom', labels: { boxWidth: 12, padding: 8 } } },
            ...extraOpts
        }
    });
}
