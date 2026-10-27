/**
 * API Client for Food Delivery Information System
 */
const API = {
    base: '',  // Same origin

    async request(method, path, data = null) {
        const token = localStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const opts = { method, headers };
        if (data && method !== 'GET') opts.body = JSON.stringify(data);

        try {
            const res = await fetch(`${this.base}${path}`, opts);
            if (res.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user');
                window.location.reload();
                throw new Error('Session expired');
            }
            const json = await res.json();
            if (!res.ok) throw new Error(json.detail || 'Request failed');
            return json;
        } catch (e) {
            if (e.message !== 'Session expired') throw e;
            return null;
        }
    },

    get(path) { return this.request('GET', path); },
    post(path, data) { return this.request('POST', path, data); },
    put(path, data) { return this.request('PUT', path, data); },
    del(path) { return this.request('DELETE', path); },

    // ===== Auth =====
    login(username, password) { return this.post('/api/auth/login', { username, password }); },
    register(data) { return this.post('/api/auth/register', data); },
    forgotPassword(email) { return this.post('/api/auth/forgot-password', { email }); },
    resetPassword(token, new_password) { return this.post('/api/auth/reset-password', { token, new_password }); },
    wechatLogin(code) { return this.post('/api/auth/wechat-login', { code }); },
    getProfile() { return this.get('/api/auth/me'); },
    setup2FA() { return this.post('/api/auth/2fa/setup'); },

    // ===== Merchants =====
    getMerchants() { return this.get('/api/merchants/all'); },
    getMerchant(id) { return this.get(`/api/merchants/${id}`); },
    getMenu(merchantId) { return this.get(`/api/merchants/${merchantId}/menu`); },
    registerMerchant(data) { return this.post('/api/merchants/register', data); },
    getMerchantProfile() { return this.get('/api/merchants/profile'); },
    addMenuItem(data) { return this.post('/api/merchants/menu', data); },
    getMerchantOrders() { return this.get('/api/merchants/orders/all'); },
    updateOrderStatus(orderId, status) { return this.put(`/api/merchants/orders/${orderId}/status?status=${status}`); },

    // ===== Orders =====
    placeOrder(data) { return this.post('/api/orders/place', data); },
    getMyOrders() { return this.get('/api/orders/my'); },
    getAvailableOrders() { return this.get('/api/orders/available'); },
    acceptOrder(orderId) { return this.post(`/api/orders/${orderId}/accept`); },
    updateRiderOrderStatus(orderId, status) { return this.post(`/api/orders/${orderId}/status?status=${status}`); },
    cancelOrder(orderId) { return this.post(`/api/orders/${orderId}/cancel`); },
    submitReview(data) { return this.post('/api/orders/review', data); },

    // ===== Analytics =====
    getOverview() { return this.get('/api/analytics/overview'); },
    getSales(merchantId, days) {
        let q = `?days=${days}`;
        if (merchantId) q += `&merchant_id=${merchantId}`;
        return this.get(`/api/analytics/sales${q}`);
    },
    getCuisineDist() { return this.get('/api/analytics/cuisine-distribution'); },
    getRiderPerf(days = 7) { return this.get(`/api/analytics/rider-performance?days=${days}`); },
    getCustomerAnalysis() { return this.get('/api/analytics/customer-analysis'); },
    getHourlyDist() { return this.get('/api/analytics/hourly-distribution'); },
    getPaymentAnalysis(days = 30) { return this.get(`/api/analytics/payment-analysis?days=${days}`); },
    getRatingDist() { return this.get('/api/analytics/rating-distribution'); },
    trainModel(merchantId) {
        let q = '';
        if (merchantId) q = `?merchant_id=${merchantId}`;
        return this.post(`/api/analytics/ai/train${q}`);
    },
    getPredictions(merchantId, days = 7) {
        let q = `?days=${days}`;
        if (merchantId) q += `&merchant_id=${merchantId}`;
        return this.get(`/api/analytics/ai/predict-sales${q}`);
    },
    getRecommendations(n = 5) { return this.get(`/api/analytics/ai/recommendations?top_n=${n}`); },

    // ===== GPS =====
    reportLocation(data) { return this.post('/api/gps/report', data); },
    trackOrder(orderId) { return this.get(`/api/gps/track/${orderId}`); },

    // ===== Ethical =====
    getEnvImpact(days = 30) { return this.get(`/api/ethical/environmental-impact?days=${days}`); },
    getTrafficImpact() { return this.get('/api/ethical/traffic-impact'); },
    getFoodWaste() { return this.get('/api/ethical/food-waste-reduction'); },

    // ===== Admin =====
    getUsers() { return this.get('/api/admin/users'); },
    getUsersByRole(role) { return this.get(`/api/admin/users?role=${role}`); },
    toggleUserStatus(userId) { return this.put(`/api/admin/users/${userId}/status`); },
    changeUserRole(userId, role) { return this.put(`/api/admin/users/${userId}/role?new_role=${role}`); },
    getAuditLogs(limit = 50) { return this.get(`/api/admin/audit-logs?limit=${limit}`); },
    getAdminDashboard() { return this.get('/api/admin/dashboard'); },
};
