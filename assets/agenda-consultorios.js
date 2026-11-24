/* Agenda de alquiler de consultorios · KAIROS Salud
   Lee la disponibilidad de window.KAIROS_AGENDA (generada desde src/disponibilidad.json).
   No reserva nada: arma un mensaje de WhatsApp con consultorio, fecha y horarios elegidos. */
(function () {
  const A = window.KAIROS_AGENDA, WA = window.KAIROS_WA;
  if (!A) return;
  const $ = id => document.getElementById(id);
  const DIAS = ['dom', 'lun', 'mar', 'mie', 'jue', 'vie', 'sab'];
  const CUALQUIERA = 'Cualquier consultorio';
  const pad = n => String(n).padStart(2, '0');
  const key = d => d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
  const parse = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d, 12); };
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const fmtDia = d => new Intl.DateTimeFormat('es-AR', { weekday: 'long', day: 'numeric', month: 'long' }).format(d);

  const hoy = new Date(); hoy.setHours(12, 0, 0, 0);
  const desde = A.desde && parse(A.desde) > hoy ? parse(A.desde) : hoy;
  const hasta = new Date(desde); hasta.setDate(hasta.getDate() + 7 * (A.semanas_visibles || 8));

  let room = '', day = null, chosen = [], month = new Date(desde.getFullYear(), desde.getMonth(), 1);

  function horas(rango) {
    if (!rango) return [];
    const [a, b] = rango.map(h => parseInt(h, 10)), out = [];
    for (let h = a; h < b; h++) out.push(pad(h) + ':00');
    return out;
  }
  function libres(r, d) {
    if (d < desde || d > hasta || (A.cerrado || []).includes(key(d))) return [];
    const dow = DIAS[d.getDay()], base = horas(A.horario[dow]);
    const sem = ((A.ocupado_semanal || {})[r] || {})[dow] || [];
    const fec = ((A.ocupado_fechas || {})[r] || {})[key(d)] || [];
    return base.filter(h => !sem.includes(h) && !fec.includes(h));
  }
  function slots(d) {
    if (!room) return [];
    if (room !== CUALQUIERA) return libres(room, d);
    const set = new Set(); A.consultorios.forEach(r => libres(r, d).forEach(h => set.add(h)));
    return [...set].sort();
  }
  function rangos(list) {
    const hs = list.map(h => parseInt(h, 10)).sort((a, b) => a - b), out = [];
    hs.forEach(h => { const last = out[out.length - 1]; if (last && last[1] === h) last[1] = h + 1; else out.push([h, h + 1]); });
    return out.map(([a, b]) => pad(a) + ':00 a ' + pad(b) + ':00').join(', ');
  }

  function renderRooms() {
    document.querySelectorAll('[data-room]').forEach(b => {
      const on = b.dataset.room === room;
      b.classList.toggle('chosen', on); b.setAttribute('aria-pressed', String(on));
    });
  }
  function renderCalendar() {
    $('agMonth').textContent = cap(new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(month));
    const g = $('agDays'); g.replaceChildren();
    ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'].forEach(w => { const e = document.createElement('div'); e.className = 'ag-weekday'; e.textContent = w; g.append(e); });
    const y = month.getFullYear(), m = month.getMonth();
    for (let i = 0; i < new Date(y, m, 1).getDay(); i++) { const s = document.createElement('span'); s.className = 'ag-cell empty'; g.append(s); }
    for (let n = 1; n <= new Date(y, m + 1, 0).getDate(); n++) {
      const d = new Date(y, m, n, 12), free = slots(d), open = !!A.horario[DIAS[d.getDay()]] && d >= desde && d <= hasta;
      const b = document.createElement('button'); b.type = 'button'; b.textContent = n;
      b.className = 'ag-cell' + (room && open ? (free.length ? ' available' : ' full') : '');
      if (day && key(d) === key(day)) b.classList.add('selected');
      b.disabled = !room || !free.length;
      b.setAttribute('aria-label', fmtDia(d) + (b.disabled ? ', sin horarios disponibles' : ', ' + free.length + ' horarios libres'));
      if (!b.disabled) b.onclick = () => chooseDay(d);
      g.append(b);
    }
    $('agPrev').disabled = y === desde.getFullYear() && m === desde.getMonth();
    $('agNext').disabled = new Date(y, m + 1, 1) > hasta;
    $('agHint').textContent = !room ? 'Primero elegí un consultorio.' : 'Verde: días con horarios libres. Rosa: día completo. Gris: sin atención.';
  }
  function renderSlots() {
    const box = $('agSlots'); box.replaceChildren();
    if (!day) { box.innerHTML = '<p class="notice">Elegí un día del calendario para ver los horarios.</p>'; return; }
    slots(day).forEach(h => {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'ag-slot';
      b.textContent = h + ' – ' + pad(parseInt(h, 10) + 1) + ':00';
      const on = chosen.includes(h); b.classList.toggle('chosen', on); b.setAttribute('aria-pressed', String(on));
      b.onclick = () => { chosen = on ? chosen.filter(x => x !== h) : [...chosen, h]; renderSlots(); };
      box.append(b);
    });
    $('agSummary').textContent = chosen.length ? room + ' · ' + fmtDia(day) + ' · ' + rangos(chosen) : 'Podés elegir uno o varios bloques de una hora.';
    $('rentForm').hidden = !chosen.length;
  }
  function chooseDay(d) { day = d; chosen = []; $('agDayTitle').textContent = cap(fmtDia(d)); renderCalendar(); renderSlots(); }
  function chooseRoom(r) {
    room = r; day = null; chosen = []; $('rentForm').hidden = true;
    $('agDayTitle').textContent = 'Elegí un día'; $('agSummary').textContent = '';
    renderRooms(); renderCalendar(); renderSlots();
  }

  document.querySelectorAll('[data-room]').forEach(b => b.addEventListener('click', () => chooseRoom(b.dataset.room)));
  document.querySelectorAll('.consultorio-select').forEach(l => l.addEventListener('click', () => chooseRoom(l.dataset.consultorio)));
  $('agPrev').onclick = () => { month = new Date(month.getFullYear(), month.getMonth() - 1, 1); renderCalendar(); };
  $('agNext').onclick = () => { month = new Date(month.getFullYear(), month.getMonth() + 1, 1); renderCalendar(); };

  $('rentForm').addEventListener('submit', e => {
    e.preventDefault();
    if (!room || !day || !chosen.length) return;
    const v = id => $(id).value.trim();
    const msg = 'Hola KAIROS Salud. CONSULTA: ALQUILER DE CONSULTORIO\n' +
      'Consultorio: ' + room + '\nDía: ' + fmtDia(day) + '\nHorario: ' + rangos(chosen) +
      '\nModalidad: ' + v('rentMode') + '\nNombre: ' + v('rentName') + '\nEspecialidad: ' + v('rentSpec') + '\nWhatsApp: ' + v('rentPhone');
    $('rentStatus').classList.remove('hidden');
    $('rentStatus').textContent = 'Se abrirá WhatsApp con tu consulta. El horario queda sujeto a confirmación de KAIROS.';
    window.open('https://wa.me/' + WA + '?text=' + encodeURIComponent(msg), '_blank', 'noopener,noreferrer');
  });

  renderRooms(); renderCalendar(); renderSlots();
})();
