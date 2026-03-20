// ─────────────────────────────────────────────────────────────────────────────
// Config
// ─────────────────────────────────────────────────────────────────────────────
const API = '';          // Same origin
let ADMIN_PW = '';       // Set on login

// ─────────────────────────────────────────────────────────────────────────────
// Auth
// ─────────────────────────────────────────────────────────────────────────────
function doLogin() {
  const pw = document.getElementById('auth-input').value.trim();
  if (!pw) return;
  ADMIN_PW = pw;
  // Verify by hitting a protected endpoint
  apiFetch('/admin/hotel')
    .then(() => {
      document.getElementById('auth-gate').style.display = 'none';
      loadAll();
    })
    .catch(() => {
      document.getElementById('auth-error').style.display = 'block';
      ADMIN_PW = '';
    });
}

document.getElementById('auth-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

function doLogout() {
  ADMIN_PW = '';
  document.getElementById('auth-gate').style.display = 'flex';
  document.getElementById('auth-input').value = '';
  document.getElementById('auth-error').style.display = 'none';
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared API helper
// ─────────────────────────────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const res = await fetch(API + path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'x-admin-password': ADMIN_PW,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Toast
// ─────────────────────────────────────────────────────────────────────────────
let toastTimer;
function toast(msg, type = 'info') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.display = 'block';
  el.style.borderColor = type === 'error' ? 'rgba(252,129,129,0.4)' : 'rgba(104,211,145,0.3)';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab switching
// ─────────────────────────────────────────────────────────────────────────────
const TABS = ['overview', 'bookings', 'rooms', 'faqs', 'logs', 'test'];

function switchTab(tab) {
  TABS.forEach(t => {
    document.getElementById(`tab-${t}`).classList.toggle('active', t === tab);
    document.getElementById(`content-${t}`).classList.toggle('active', t === tab);
  });
  if (tab === 'logs') loadLogs();
  if (tab === 'rooms') loadRooms();
  if (tab === 'faqs') loadFaqs();
  if (tab === 'bookings') loadBookings();
}

// ─────────────────────────────────────────────────────────────────────────────
// Load Everything (overview)
// ─────────────────────────────────────────────────────────────────────────────
async function loadAll() {
  try {
    const [hotel, rooms, logs] = await Promise.all([
      apiFetch('/admin/hotel'),
      apiFetch('/admin/rooms'),
      apiFetch('/admin/logs'),
    ]);

    // Header hotel name
    document.getElementById('hotel-name-header').textContent = hotel.name || 'Hotel Bot';

    // Stats
    const avail = rooms.filter(r => r.status === 'available').length;
    const occ = rooms.filter(r => r.status === 'occupied').length;
    const maint = rooms.filter(r => r.status === 'maintenance').length;
    document.getElementById('stat-total').textContent = rooms.length;
    document.getElementById('stat-available').textContent = avail;
    document.getElementById('stat-occupied').textContent = occ;
    document.getElementById('stat-maintenance').textContent = maint;
    document.getElementById('stat-convs').textContent = logs.length;
    document.getElementById('logs-badge').textContent = logs.length;

    // Hotel info card
    document.getElementById('hotel-info-body').innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
        <div><strong style="color:var(--text)">📍 Address</strong><br>${hotel.address}</div>
        <div><strong style="color:var(--text)">📞 Phone</strong><br>${hotel.phone}</div>
        <div><strong style="color:var(--text)">📧 Email</strong><br>${hotel.email}</div>
        <div><strong style="color:var(--text)">🌐 Website</strong><br>${hotel.website}</div>
        <div><strong style="color:var(--text)">🕑 Check-in</strong><br>${hotel.check_in_time}</div>
        <div><strong style="color:var(--text)">🕛 Check-out</strong><br>${hotel.check_out_time}</div>
        <div style="grid-column:span 2"><strong style="color:var(--text)">✨ Amenities</strong><br>${hotel.amenities.join(' · ')}</div>
        <div style="grid-column:span 2"><strong style="color:var(--text)">📋 Cancellation</strong><br>${hotel.cancellation_policy}</div>
      </div>
    `;

    // Also populate rooms/faqs tables while we're at it
    renderRooms(rooms);
  } catch (e) {
    toast('Failed to load data: ' + e.message, 'error');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Rooms
// ─────────────────────────────────────────────────────────────────────────────
async function loadRooms() {
  try {
    const rooms = await apiFetch('/admin/rooms');
    renderRooms(rooms);
  } catch (e) {
    toast('Failed to load rooms', 'error');
  }
}

function renderRooms(rooms) {
  const tbody = document.getElementById('rooms-tbody');
  if (!rooms.length) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--text-muted)">No rooms yet. Click "Add Room" to get started.</td></tr>`;
    return;
  }

  tbody.innerHTML = rooms.map(r => {
    const badgeClass = { available: 'badge-available', occupied: 'badge-occupied', maintenance: 'badge-maintenance' }[r.status] || '';
    const statusLabel = { available: '✅ Available', occupied: '🔴 Occupied', maintenance: '🔧 Maintenance' }[r.status] || r.status;
    return `
      <tr>
        <td><strong>${r.id}</strong></td>
        <td>${r.type}</td>
        <td>₹${Number(r.price_per_night).toLocaleString('en-IN')}</td>
        <td>${r.bed_type}</td>
        <td>${r.view || '—'}</td>
        <td>${r.max_occupancy}</td>
        <td><span class="badge-pill ${badgeClass}">${statusLabel}</span></td>
        <td>${r.available_from}</td>
        <td style="display:flex;gap:6px;">
          <button class="btn btn-ghost btn-sm" onclick="openEditRoom('${r.id}')">✏️ Edit</button>
          <button class="btn btn-danger btn-sm" onclick="deleteRoom('${r.id}')">🗑</button>
        </td>
      </tr>
    `;
  }).join('');
}

// Room modal state
let editingRoomId = null;

function openAddRoom() {
  editingRoomId = null;
  document.getElementById('room-modal-title').textContent = 'Add Room';
  document.getElementById('room-form').reset();
  document.getElementById('r-date').value = new Date().toISOString().split('T')[0];
  openModal('room-modal');
}

async function openEditRoom(roomId) {
  editingRoomId = roomId;
  document.getElementById('room-modal-title').textContent = `Edit Room ${roomId}`;
  try {
    const rooms = await apiFetch('/admin/rooms');
    const room = rooms.find(r => r.id === roomId);
    if (!room) return;
    document.getElementById('r-id').value = room.id;
    document.getElementById('r-id').disabled = true;
    document.getElementById('r-type').value = room.type;
    document.getElementById('r-price').value = room.price_per_night;
    document.getElementById('r-occupancy').value = room.max_occupancy;
    document.getElementById('r-bed').value = room.bed_type;
    document.getElementById('r-view').value = room.view || '';
    document.getElementById('r-status').value = room.status;
    document.getElementById('r-date').value = room.available_from;
    document.getElementById('r-features').value = (room.features || []).join(', ');
    openModal('room-modal');
  } catch (e) {
    toast('Could not load room data', 'error');
  }
}

async function submitRoom(e) {
  e.preventDefault();
  const payload = {
    id: document.getElementById('r-id').value.trim(),
    type: document.getElementById('r-type').value,
    price_per_night: Number(document.getElementById('r-price').value),
    max_occupancy: Number(document.getElementById('r-occupancy').value),
    bed_type: document.getElementById('r-bed').value.trim(),
    view: document.getElementById('r-view').value.trim(),
    status: document.getElementById('r-status').value,
    available_from: document.getElementById('r-date').value,
    features: document.getElementById('r-features').value.split(',').map(f => f.trim()).filter(Boolean),
  };

  try {
    if (editingRoomId) {
      await apiFetch(`/admin/rooms/${editingRoomId}`, { method: 'PUT', body: JSON.stringify(payload) });
      toast('✅ Room updated');
    } else {
      await apiFetch('/admin/rooms', { method: 'POST', body: JSON.stringify(payload) });
      toast('✅ Room added');
    }
    document.getElementById('r-id').disabled = false;
    closeModal('room-modal');
    loadRooms();
    updateStats();
  } catch (e) {
    toast('Failed to save room: ' + e.message, 'error');
  }
}

async function deleteRoom(roomId) {
  if (!confirm(`Delete room ${roomId}? This cannot be undone.`)) return;
  try {
    await apiFetch(`/admin/rooms/${roomId}`, { method: 'DELETE' });
    toast('🗑 Room deleted');
    loadRooms();
    updateStats();
  } catch (e) {
    toast('Failed to delete room', 'error');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// FAQs
// ─────────────────────────────────────────────────────────────────────────────
async function loadFaqs() {
  try {
    const faqs = await apiFetch('/admin/faqs');
    renderFaqs(faqs);
  } catch (e) {
    toast('Failed to load FAQs', 'error');
  }
}

function renderFaqs(faqs) {
  const container = document.getElementById('faqs-list');
  if (!faqs.length) {
    container.innerHTML = `<div class="empty-state"><div class="icon">❓</div><p>No FAQs yet. Add one to improve the bot's answers.</p></div>`;
    return;
  }
  container.innerHTML = faqs.map(f => `
    <div class="glass-card" style="display:flex;gap:16px;align-items:flex-start;">
      <div style="flex:1;">
        <div style="font-weight:600;margin-bottom:6px;">❓ ${escHtml(f.question)}</div>
        <div style="color:var(--text-muted);font-size:14px;line-height:1.6;">${escHtml(f.answer)}</div>
      </div>
      <button class="btn btn-danger btn-sm" onclick="deleteFaq('${f.id}')">🗑</button>
    </div>
  `).join('');
}

function openAddFaq() {
  document.getElementById('faq-q').value = '';
  document.getElementById('faq-a').value = '';
  openModal('faq-modal');
}

async function submitFaq(e) {
  e.preventDefault();
  const payload = {
    question: document.getElementById('faq-q').value.trim(),
    answer: document.getElementById('faq-a').value.trim(),
  };
  try {
    await apiFetch('/admin/faqs', { method: 'POST', body: JSON.stringify(payload) });
    toast('✅ FAQ added');
    closeModal('faq-modal');
    loadFaqs();
  } catch (e) {
    toast('Failed to add FAQ', 'error');
  }
}

async function deleteFaq(faqId) {
  if (!confirm('Delete this FAQ?')) return;
  try {
    await apiFetch(`/admin/faqs/${faqId}`, { method: 'DELETE' });
    toast('🗑 FAQ deleted');
    loadFaqs();
  } catch (e) {
    toast('Failed to delete FAQ', 'error');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Conversation logs
// ─────────────────────────────────────────────────────────────────────────────
async function loadLogs() {
  try {
    const logs = await apiFetch('/admin/logs');
    renderLogs(logs);
    document.getElementById('logs-badge').textContent = logs.length;
  } catch (e) {
    toast('Failed to load logs', 'error');
  }
}

function renderLogs(logs) {
  const container = document.getElementById('logs-container');
  if (!logs.length) {
    container.innerHTML = `<div class="empty-state"><div class="icon">💬</div><p>No conversations yet. Test the bot or connect Twilio to see messages here.</p></div>`;
    return;
  }

  // Group by phone
  const grouped = {};
  logs.forEach(entry => {
    if (!grouped[entry.phone]) grouped[entry.phone] = [];
    grouped[entry.phone].push(entry);
  });

  container.innerHTML = Object.entries(grouped).map(([phone, entries]) => `
    <div class="glass-card conv-group">
      <div class="conv-phone">
        📱 ${escHtml(phone)}
        <span style="color:var(--text-subtle);font-weight:400;font-size:12px;">${entries.length} message${entries.length > 1 ? 's' : ''}</span>
      </div>
      ${[...entries].reverse().map(e => `
        <div class="conv-row">
          <div style="display:flex;justify-content:flex-end;">
            <div>
              <div class="conv-bubble user">${escHtml(e.user)}</div>
              <div class="conv-time" style="text-align:right;">${formatTime(e.timestamp)}</div>
            </div>
          </div>
          <div class="conv-bubble bot" style="margin-top:4px;">${escHtml(e.bot)}</div>
        </div>
      `).join('')}
    </div>
  `).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
// Test Bot
// ─────────────────────────────────────────────────────────────────────────────
async function sendTestMsg() {
  const phone = document.getElementById('test-phone').value.trim() || '+919999999999';
  const msgEl = document.getElementById('test-msg');
  const msg = msgEl.value.trim();
  if (!msg) return;
  msgEl.value = '';

  const chat = document.getElementById('test-chat');

  // Add user bubble
  chat.innerHTML += `
    <div style="display:flex;justify-content:flex-end;">
      <div>
        <div class="conv-bubble user">${escHtml(msg)}</div>
        <div class="conv-time" style="text-align:right;">You · now</div>
      </div>
    </div>`;
  chat.scrollTop = chat.scrollHeight;

  // Typing indicator
  const typingId = 'typing-' + Date.now();
  chat.innerHTML += `<div id="${typingId}" class="conv-bubble bot" style="color:var(--text-muted);">⌛ Thinking…</div>`;
  chat.scrollTop = chat.scrollHeight;

  try {
    const res = await fetch('/webhook/test', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, message: msg }),
    });
    const data = await res.json();
    document.getElementById(typingId)?.remove();
    chat.innerHTML += `
      <div>
        <div class="conv-bubble bot">${escHtml(data.reply)}</div>
        <div class="conv-time">Bot · now</div>
      </div>`;
  } catch (e) {
    document.getElementById(typingId)?.remove();
    chat.innerHTML += `<div class="conv-bubble bot" style="color:var(--accent-red);">Error: ${e.message}</div>`;
  }

  chat.scrollTop = chat.scrollHeight;
}

function fillMsg(text) {
  document.getElementById('test-msg').value = text;
  document.getElementById('test-msg').focus();
}

// ─────────────────────────────────────────────────────────────────────────────
// Modals
// ─────────────────────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  document.getElementById('r-id').disabled = false;
}

// Close modal on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) closeModal(overlay.id);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/\n/g, '<br>');
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleString('en-IN', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

async function updateStats() {
  try {
    const [rooms, logs] = await Promise.all([apiFetch('/admin/rooms'), apiFetch('/admin/logs')]);
    document.getElementById('stat-total').textContent = rooms.length;
    document.getElementById('stat-available').textContent = rooms.filter(r => r.status === 'available').length;
    document.getElementById('stat-occupied').textContent = rooms.filter(r => r.status === 'occupied').length;
    document.getElementById('stat-maintenance').textContent = rooms.filter(r => r.status === 'maintenance').length;
    document.getElementById('stat-convs').textContent = logs.length;
    document.getElementById('logs-badge').textContent = logs.length;
  } catch {}
}

// ─────────────────────────────────────────────────────────────────────────────
// Booking Calendar
// ─────────────────────────────────────────────────────────────────────────────

let _calWeekOffset = 0;   // 0 = current week, -1 = last week, +1 = next week
let _allBookings = [];
let _allRooms = [];

function getWeekDates(offset = 0) {
  const now = new Date();
  const day = now.getDay(); // 0=Sun
  const monday = new Date(now);
  monday.setDate(now.getDate() - ((day + 6) % 7) + offset * 7);
  monday.setHours(0, 0, 0, 0);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

function toISO(date) {
  return date.toISOString().split('T')[0];
}

async function loadBookings() {
  try {
    [_allBookings, _allRooms] = await Promise.all([
      apiFetch('/admin/bookings'),
      apiFetch('/admin/rooms'),
    ]);
    renderCalendar();
  } catch (e) {
    toast('Failed to load bookings: ' + e.message, 'error');
  }
}

function shiftWeek(dir) {
  _calWeekOffset += dir;
  renderCalendar();
}

function renderCalendar() {
  const days = getWeekDates(_calWeekOffset);
  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  const today = toISO(new Date());

  // Update label
  const label = `${days[0].toLocaleDateString('en-IN', { day:'2-digit', month:'short' })} – ${days[6].toLocaleDateString('en-IN', { day:'2-digit', month:'short', year:'numeric' })}`;
  document.getElementById('cal-week-label').textContent = label;

  // Build header row
  let html = `<div class="cal-grid" style="grid-template-columns: 180px repeat(7, 1fr);">`;
  html += `<div class="cal-header-cell">Unit</div>`;
  days.forEach((d, i) => {
    const iso = toISO(d);
    const isToday = iso === today;
    html += `<div class="cal-header-cell${isToday ? ' cal-today-header' : ''}">${dayNames[i]}<br><small>${d.getDate()} ${d.toLocaleString('en-IN',{month:'short'})}</small></div>`;
  });

  // Build room rows
  _allRooms.forEach(room => {
    html += `<div class="cal-room-cell">${escHtml(room.name || room.id)}<br><small style="color:var(--text-subtle)">${room.type}</small></div>`;

    days.forEach(d => {
      const iso = toISO(d);
      const isToday = iso === today;
      // Find booking that covers this day for this room
      const booking = _allBookings.find(b =>
        b.room_id === room.id && b.check_in <= iso && b.check_out > iso
      );
      if (booking) {
        html += `<div class="cal-cell cal-booked${isToday ? ' cal-today' : ''}" onclick="openBookingDetail('${booking._id}')" title="${escHtml(booking.guest_name)}">
          <span class="cal-guest">${escHtml(booking.guest_name)}</span>
        </div>`;
      } else {
        const isUnavailable = room.status !== 'available' || room.available_from > iso;
        html += `<div class="cal-cell ${isUnavailable ? 'cal-unavailable' : 'cal-free'}${isToday ? ' cal-today' : ''}"></div>`;
      }
    });
  });

  html += `</div>`;
  document.getElementById('booking-calendar').innerHTML = html;
}

async function openAddBooking() {
  // Populate room dropdown
  const sel = document.getElementById('bk-room');
  sel.innerHTML = _allRooms.map(r => `<option value="${r.id}">${escHtml(r.name || r.id)} (${r.type})</option>`).join('');
  // Default dates to current week start
  const days = getWeekDates(_calWeekOffset);
  document.getElementById('bk-checkin').value = toISO(days[0]);
  const checkout = new Date(days[0]); checkout.setDate(checkout.getDate() + 1);
  document.getElementById('bk-checkout').value = toISO(checkout);
  document.getElementById('bk-name').value = '';
  document.getElementById('bk-phone').value = '';
  document.getElementById('bk-notes').value = '';
  openModal('booking-modal');
}

async function submitBooking(e) {
  e.preventDefault();
  const checkin = document.getElementById('bk-checkin').value;
  const checkout = document.getElementById('bk-checkout').value;
  if (checkout <= checkin) {
    toast('Check-out must be after check-in', 'error');
    return;
  }
  const payload = {
    room_id: document.getElementById('bk-room').value,
    guest_name: document.getElementById('bk-name').value.trim(),
    guest_phone: document.getElementById('bk-phone').value.trim(),
    check_in: checkin,
    check_out: checkout,
    notes: document.getElementById('bk-notes').value.trim(),
  };
  try {
    await apiFetch('/admin/bookings', { method: 'POST', body: JSON.stringify(payload) });
    toast('✅ Booking saved');
    closeModal('booking-modal');
    loadBookings();
  } catch (e) {
    toast('Failed to save booking: ' + e.message, 'error');
  }
}

function openBookingDetail(bookingId) {
  const bk = _allBookings.find(b => b._id === bookingId);
  if (!bk) return;
  const room = _allRooms.find(r => r.id === bk.room_id);
  document.getElementById('booking-detail-body').innerHTML = `
    <div><strong>Unit:</strong> ${escHtml(room ? (room.name || room.id) : bk.room_id)}</div>
    <div><strong>Guest:</strong> ${escHtml(bk.guest_name)}</div>
    <div><strong>Phone:</strong> ${escHtml(bk.guest_phone || '—')}</div>
    <div><strong>Check-in:</strong> ${bk.check_in}</div>
    <div><strong>Check-out:</strong> ${bk.check_out}</div>
    ${bk.notes ? `<div><strong>Notes:</strong> ${escHtml(bk.notes)}</div>` : ''}
    <div style="margin-top:8px;font-size:12px;color:var(--text-subtle)">Booking ID: ${bk._id}</div>
  `;
  document.getElementById('booking-cancel-btn').onclick = () => cancelBooking(bookingId);
  openModal('booking-detail-modal');
}

async function cancelBooking(bookingId) {
  if (!confirm('Cancel this booking? This cannot be undone.')) return;
  try {
    await apiFetch(`/admin/bookings/${bookingId}`, { method: 'DELETE' });
    toast('🗑 Booking cancelled');
    closeModal('booking-detail-modal');
    loadBookings();
  } catch (e) {
    toast('Failed to cancel booking', 'error');
  }
}
