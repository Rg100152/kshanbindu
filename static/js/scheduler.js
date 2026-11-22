/* ============================================================
   KshanBindu — Vanilla JS scheduler & reminder engine
   No frameworks, no phone numbers. Built by Raj Gautam.
   ============================================================ */
'use strict';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  let data = null;
  try { data = await response.json(); } catch (_) { /* empty body */ }
  if (!response.ok) {
    throw new Error((data && (data.description || data.error || data.message)) || `Request failed (${response.status})`);
  }
  return data;
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[ch]));
}

function isoDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function toast(message, kind = '') {
  const container = $('#toast-container');
  if (!container) return;
  const node = document.createElement('div');
  node.className = `toast ${kind}`.trim();
  node.textContent = message;
  container.appendChild(node);
  setTimeout(() => node.remove(), 4200);
}

/* ------------------------------------------------------- booking studio */
function initBooking() {
  const list = $('#event-list');
  const grid = $('#calendar-grid');
  if (!list || !grid) return;

  const state = {
    eventId: Number($('.event-card.active')?.dataset.eventId || 0),
    duration: Number($('.event-card.active')?.dataset.duration || 30),
    date: null,
    month: new Date(),
    slot: null,
    availableDates: new Set(),
  };
  state.month = new Date(state.month.getFullYear(), state.month.getMonth(), 1);

  /* ---- event selection ---- */
  $$('.event-card', list).forEach((card) => {
    card.addEventListener('click', () => {
      $$('.event-card', list).forEach((c) => c.classList.remove('active'));
      card.classList.add('active');
      state.eventId = Number(card.dataset.eventId);
      state.duration = Number(card.dataset.duration);
      $('#duration-text').textContent = `${state.duration} minutes`;
      clearSlot();
      hideSuccess();
      loadAvailability();
      if (state.date) loadSlots();
    });
  });

  /* ---- month navigation ---- */
  $('#prev-month').addEventListener('click', () => {
    state.month.setMonth(state.month.getMonth() - 1);
    renderCalendar();
    loadAvailability();
  });
  $('#next-month').addEventListener('click', () => {
    state.month.setMonth(state.month.getMonth() + 1);
    renderCalendar();
    loadAvailability();
  });

  /* ---- calendar grid ---- */
  function renderCalendar() {
    const year = state.month.getFullYear();
    const month = state.month.getMonth();
    $('#calendar-month-label').textContent = state.month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + 90);
    const offset = (new Date(year, month, 1).getDay() + 6) % 7; // Monday-first
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const cells = Math.ceil((offset + daysInMonth) / 7) * 7;
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < cells; i += 1) {
      const cell = document.createElement('div');
      cell.className = 'day-cell';
      const dayNumber = i - offset + 1;

      if (dayNumber < 1 || dayNumber > daysInMonth) {
        cell.classList.add('empty');
        fragment.appendChild(cell);
        continue;
      }

      const day = new Date(year, month, dayNumber);
      const value = isoDate(day);
      const isSunday = day.getDay() === 0;
      const disabled = day < today || day > maxDate || isSunday;
      cell.textContent = String(dayNumber);
      cell.dataset.date = value;
      cell.setAttribute('role', 'gridcell');

      if (disabled) {
        cell.disabled = true;
        cell.classList.add('closed');
        cell.title = isSunday ? 'Studio closed on Sundays' : 'Outside booking window';
      } else {
        cell.classList.add('day-button');
        if (state.availableDates.has(value)) cell.classList.add('available');
        if (value === isoDate(today)) cell.classList.add('today');
        if (value === state.date) cell.classList.add('selected');
        cell.addEventListener('click', () => selectDate(value));
      }
      fragment.appendChild(cell);
    }
    grid.replaceChildren(fragment);
  }

  function selectDate(value) {
    state.date = value;
    state.slot = null;
    $('#booking-form').hidden = true;
    hideSuccess();
    renderCalendar();
    loadSlots();
  }

  async function loadAvailability() {
    try {
      const data = await api(`/api/availability?year=${state.month.getFullYear()}&month=${state.month.getMonth() + 1}&event_type_id=${state.eventId}`);
      state.availableDates = new Set(data.dates);
      renderCalendar();
    } catch (error) {
      /* calendar still works without dots */
      console.warn('Availability:', error.message);
    }
  }

  /* ---- slots ---- */
  async function loadSlots() {
    const slotGrid = $('#slot-grid');
    if (!state.date) {
      $('#selected-date-label').textContent = 'Select a date to see open slots.';
      $('#slot-count').textContent = '—';
      slotGrid.innerHTML = '<div class="empty-state"><span>📅</span><p>Your open moments will appear here.</p></div>';
      return;
    }

    const pretty = new Date(`${state.date}T12:00:00`).toLocaleDateString('en-US', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' });
    $('#selected-date-label').textContent = pretty;
    $('#slots-title').textContent = 'Available moments';
    slotGrid.innerHTML = '<div class="empty-state"><span>⏳</span><p>Checking live availability…</p></div>';

    try {
      const data = await api(`/api/slots?date=${state.date}&event_type_id=${state.eventId}`);
      const open = data.slots.filter((s) => s.status === 'available').length;
      const locked = data.slots.filter((s) => s.status === 'booked').length;
      $('#slot-count').textContent = `${open} open · ${locked} locked`;
      const fragment = document.createDocumentFragment();

      data.slots.forEach((slot) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'slot-button';
        button.innerHTML = `${escapeHtml(slot.label)}<small>${escapeHtml(slot.status === 'booked' ? '🔒 Booked' : slot.status === 'available' ? 'Available' : escapeHtml(slot.reason))}</small>`;
        button.title = slot.reason;

        if (slot.status === 'available') {
          button.dataset.time = slot.time;
          button.dataset.end = slot.end_time;
          button.addEventListener('click', () => chooseSlot(button, slot));
        } else {
          button.classList.add(slot.status);
          button.disabled = true;
        }
        fragment.appendChild(button);
      });
      slotGrid.replaceChildren(fragment);
      if (!data.slots.some((s) => s.status === 'available')) {
        slotGrid.insertAdjacentHTML('beforeend', '<div class="empty-state"><span>🌙</span><p>No open moments left on this date. Try another day.</p></div>');
      }
    } catch (error) {
      slotGrid.innerHTML = `<div class="empty-state"><span>⚠️</span><p>${escapeHtml(error.message)}</p></div>`;
    }
  }

  function chooseSlot(button, slot) {
    state.slot = slot;
    $$('.slot-button', $('#slot-grid')).forEach((b) => b.classList.remove('selected'));
    button.classList.add('selected');
    $('#form-slot').textContent = `${slot.label} IST`;
    $('#booking-form').hidden = false;
    hideSuccess();
  }

  function clearSlot() {
    state.slot = null;
    $$('.slot-button.selected', $('#slot-grid')).forEach((b) => b.classList.remove('selected'));
    $('#booking-form').hidden = true;
  }

  function hideSuccess() { $('#success-panel').hidden = true; }

  /* ---- booking confirmation modal ---- */
  const modal = $('#confirm-modal');
  $('#clear-slot').addEventListener('click', clearSlot);
  $('#book-another').addEventListener('click', () => { clearSlot(); loadSlots(); });

  $('#booking-form').addEventListener('submit', (event) => {
    event.preventDefault();
    if (!state.slot) { toast('Please choose a slot first.', 'warn'); return; }
    const summary = $('#modal-summary');
    summary.innerHTML = `
      <div><span>Session</span><strong>${escapeHtml($('.event-card.active .event-copy strong').textContent)}</strong></div>
      <div><span>Date</span><strong>${escapeHtml($('#selected-date-label').textContent)}</strong></div>
      <div><span>Time</span><strong>${escapeHtml(state.slot.label)} IST</strong></div>
      <div><span>Guest</span><strong>${escapeHtml($('#client-name').value)}</strong></div>
      <div><span>Email</span><strong>${escapeHtml($('#client-email').value)}</strong></div>`;
    modal.hidden = false;
  });

  function closeModal() { modal.hidden = true; }
  $('#modal-close').addEventListener('click', closeModal);
  $('#modal-cancel').addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && !modal.hidden) closeModal(); });

  $('#modal-confirm').addEventListener('click', async () => {
    const button = $('#modal-confirm');
    button.disabled = true;
    button.textContent = 'Reserving…';
    try {
      const result = await api('/api/book', {
        method: 'POST',
        body: JSON.stringify({
          event_type_id: state.eventId,
          client_name: $('#client-name').value.trim(),
          client_email: $('#client-email').value.trim(),
          notes: $('#notes').value.trim(),
          date: state.date,
          time: state.slot.time,
        }),
      });
      closeModal();
      $('#booking-form').hidden = true;
      $('#ics-link').href = result.ics_url;
      $('#ics-link').download = `kshanbindu-${result.booking.id}.ics`;
      $('#jitsi-link').href = result.booking.jitsi_link;
      $('#success-message').textContent = `${result.message} Booking #${result.booking.id}.`;
      $('#success-panel').hidden = false;
      toast('Moment reserved! Your .ics invite is ready.');
      $('#booking-form').reset();
      loadSlots();
      loadAvailability();
    } catch (error) {
      toast(error.message, 'warn');
    } finally {
      button.disabled = false;
      button.innerHTML = 'Yes, book it <span>→</span>';
    }
  });

  renderCalendar();
  loadAvailability();
  if (state.date) loadSlots();
}

/* ------------------------------------------------------ host dashboard */
let nextAppointment = null;
let alertPlayed = false;

function playAlert() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    [0, 0.22, 0.44].forEach((delay, index) => {
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'sine';
      oscillator.frequency.value = index === 2 ? 1046 : 784;
      gain.gain.setValueAtTime(0.0001, ctx.currentTime + delay);
      gain.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + delay + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + delay + 0.18);
      oscillator.connect(gain).connect(ctx.destination);
      oscillator.start(ctx.currentTime + delay);
      oscillator.stop(ctx.currentTime + delay + 0.2);
    });
  } catch (error) {
    console.warn('Audio alert unavailable:', error.message);
  }
  const panel = $('#next-appointment-card');
  panel?.classList.remove('alerting');
  void panel?.offsetWidth;
  panel?.classList.add('alerting');
  toast('🔔 Reminder: your next appointment starts soon!', 'warn');
}

function initDashboard() {
  const tbody = $('#bookings-body');
  if (!tbody) return;

  let bookings = [];
  let filter = 'all';

  /* ---- next appointment + countdown ---- */
  async function loadNext() {
    try {
      const data = await api('/api/next');
      nextAppointment = data.appointment;
      alertPlayed = false;
      if (!nextAppointment) {
        $('#next-title').textContent = 'No upcoming appointments';
        $('#next-meta').textContent = 'New bookings will show up here with a live countdown.';
        ['#cd-days', '#cd-hours', '#cd-mins', '#cd-secs'].forEach((s) => $(s).textContent = '--');
        $('#next-jitsi').style.display = 'none';
        $('#ics-next').style.display = 'none';
        return;
      }
      const when = new Date(nextAppointment.starts_at).toLocaleString('en-IN', {
        timeZone: 'Asia/Kolkata', weekday: 'long', day: 'numeric', month: 'long',
        hour: '2-digit', minute: '2-digit', hour12: true,
      });
      $('#next-title').textContent = `${nextAppointment.event_name} · ${nextAppointment.client_name}`;
      $('#next-meta').textContent = `${when} IST · ${nextAppointment.duration} minutes · Booking #${nextAppointment.id} · ${nextAppointment.status}`;
      $('#next-jitsi').style.display = '';
      $('#next-jitsi').href = nextAppointment.jitsi_link;
      $('#ics-next').style.display = '';
      $('#ics-next').href = `/api/ics/${nextAppointment.id}`;
    } catch (error) {
      toast(error.message, 'warn');
    }
  }

  function tick() {
    if (!nextAppointment) return;
    const target = new Date(nextAppointment.starts_at).getTime();
    const diff = target - Date.now();
    if (diff <= 0) {
      ['#cd-days', '#cd-hours', '#cd-mins', '#cd-secs'].forEach((s) => $(s).textContent = '00');
      return;
    }
    const totalSeconds = Math.floor(diff / 1000);
    const days = Math.floor(totalSeconds / 86400);
    const hours = Math.floor((totalSeconds % 86400) / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = totalSeconds % 60;
    $('#cd-days').textContent = String(days).padStart(2, '0');
    $('#cd-hours').textContent = String(hours).padStart(2, '0');
    $('#cd-mins').textContent = String(mins).padStart(2, '0');
    $('#cd-secs').textContent = String(secs).padStart(2, '0');

    if (diff <= 5 * 60 * 1000 && !alertPlayed && $('#reminder-toggle').checked) {
      alertPlayed = true;
      playAlert();
    }
  }

  $('#reminder-toggle').addEventListener('change', (event) => {
    localStorage.setItem('kshanbindu.reminder', event.target.checked ? 'on' : 'off');
    toast(event.target.checked ? 'Browser reminders enabled.' : 'Browser reminders paused.');
  });
  if (localStorage.getItem('kshanbindu.reminder') === 'on') $('#reminder-toggle').checked = true;
  $('#test-alert').addEventListener('click', playAlert);

  /* ---- bookings table ---- */
  function renderBookings() {
    const visible = bookings.filter((b) => filter === 'all' || b.status === filter);
    if (!visible.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="table-empty">Nothing here yet — nice and calm.</td></tr>';
      return;
    }
    tbody.innerHTML = visible.map((b) => {
      const when = new Date(`${b.appointment_date}T12:00:00`).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
      const canApprove = b.status !== 'approved';
      const canCancel = b.status !== 'cancelled';
      return `<tr>
        <td><div class="client-cell"><strong>${escapeHtml(b.client_name)}</strong><small>${escapeHtml(b.client_email)}</small></div></td>
        <td><span class="event-cell">${escapeHtml(b.event_name)} · ${b.duration} min</span></td>
        <td><span class="date-cell">${b.appointment_date}<small>${when} · ${escapeHtml(b.start_time)} IST</small></span></td>
        <td><span class="status-badge status-${escapeHtml(b.status)}">${escapeHtml(b.status)}</span></td>
        <td><div class="row-actions">
          ${canApprove ? `<button type="button" class="approve" data-action="approve" data-id="${b.id}">Approve</button>` : ''}
          ${canCancel ? `<button type="button" class="cancel" data-action="cancel" data-id="${b.id}">Cancel</button>` : ''}
        </div></td>
      </tr>`;
    }).join('');
  }

  function updateStats() {
    const now = new Date();
    $('#stat-upcoming').textContent = bookings.filter((b) => b.status !== 'cancelled' && new Date(`${b.appointment_date}T${b.start_time}`) >= now).length;
    $('#stat-pending').textContent = bookings.filter((b) => b.status === 'pending').length;
    $('#stat-approved').textContent = bookings.filter((b) => b.status === 'approved').length;
    $('#stat-total').textContent = bookings.length;
  }

  async function loadBookings() {
    try {
      bookings = await api('/api/bookings');
      renderBookings();
      updateStats();
    } catch (error) {
      tbody.innerHTML = `<tr><td colspan="5" class="table-empty">${escapeHtml(error.message)}</td></tr>`;
    }
  }

  $$('.filter').forEach((button) => button.addEventListener('click', () => {
    $$('.filter').forEach((b) => b.classList.remove('active'));
    button.classList.add('active');
    filter = button.dataset.filter;
    renderBookings();
  }));

  tbody.addEventListener('click', async (event) => {
    const button = event.target.closest('button[data-action]');
    if (!button) return;
    button.disabled = true;
    try {
      const result = await api(`/api/bookings/${button.dataset.id}/${button.dataset.action}`, { method: 'POST' });
      toast(`Booking #${result.id} ${result.status}.`);
      await loadBookings();
      await loadNext();
    } catch (error) {
      toast(error.message, 'warn');
    }
  });

  /* ---- event type catalog ---- */
  async function loadEventTypes() {
    try {
      const types = await api('/api/event-types');
      $('#event-type-list').innerHTML = types.map((t) => `<div class="event-type-item">
        <span class="event-type-swatch" style="background:${escapeHtml(t.accent)}"></span>
        <span><strong>${escapeHtml(t.name)}</strong><small>${t.duration} min · ${escapeHtml(t.description || 'No description')}</small></span>
      </div>`).join('');
    } catch (error) {
      toast(error.message, 'warn');
    }
  }

  $('#event-type-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const created = await api('/api/event-types', {
        method: 'POST',
        body: JSON.stringify({
          name: $('#et-name').value.trim(),
          duration: Number($('#et-duration').value),
          accent: $('#et-accent').value,
          description: $('#et-description').value.trim(),
        }),
      });
      toast(`“${created.name}” added to your catalog.`);
      $('#event-type-form').reset();
      $('#et-duration').value = 30;
      $('#et-accent').value = '#4F46E5';
      loadEventTypes();
    } catch (error) {
      toast(error.message, 'warn');
    }
  });

  loadNext();
  loadBookings();
  loadEventTypes();
  tick();
  setInterval(tick, 1000);
  setInterval(loadNext, 60000);
}

/* ------------------------------------------------------------------ boot */
document.addEventListener('DOMContentLoaded', () => {
  initBooking();
  initDashboard();
});
