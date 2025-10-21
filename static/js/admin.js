
(function(){
  const KEY = 'boti_auth';

  function getAuth(){
    try{
      const ls = localStorage.getItem(KEY);
      const ss = sessionStorage.getItem(KEY);
      const raw = ls || ss;
      return raw ? JSON.parse(raw) : null;
    }catch{ return null; }
  }

  function ensureAdmin(){
    const auth = getAuth();
    if (!auth || auth.role !== 'admin'){
      const guard = document.getElementById('admin-guard');
      if (guard){
        guard.textContent = ' Acceso restringido. Esta vista es solo para administradores.';
        guard.style.display = 'block';
      }
      // Short delay to show the message then redirect
      setTimeout(() => window.location.replace('/'), 1200);
      return false;
    }
    // Display username
    const userNameEl = document.getElementById('user-name');
    if (userNameEl && auth.username) {
      userNameEl.textContent = auth.username;
    }
    return true;
  }

  function fakeFetchData(){
    const now = new Date();
    const iso = now.toISOString();

    const cases = [
      { 
        id: 'CAS-001', 
        categoria: 'Salud Mental', 
        estado: 'abierto', 
        riesgo: 'medio', 
        fecha: new Date(Date.now() - 2*60*60*1000).toISOString(), 
        resumen: 'Usuario reporta ansiedad persistente y busca recursos de apoyo psicológico.' 
      },
      { 
        id: 'CAS-002', 
        categoria: ' Violencia Doméstica', 
        estado: 'abierto', 
        riesgo: 'alto', 
        fecha: new Date(Date.now() - 4*60*60*1000).toISOString(), 
        resumen: 'Reporte de agresión física reciente. Requiere intervención inmediata.' 
      },
      { 
        id: 'CAS-003', 
        categoria: 'Acoso', 
        estado: 'cerrado', 
        riesgo: 'bajo', 
        fecha: new Date(Date.now() - 24*60*60*1000).toISOString(), 
        resumen: 'Consejería brindada sobre acoso laboral. Seguimiento programado.' 
      },
      { 
        id: 'CAS-004', 
        categoria: ' Ayuda Social', 
        estado: 'abierto', 
        riesgo: 'medio', 
        fecha: new Date(Date.now() - 6*60*60*1000).toISOString(), 
        resumen: 'Solicitud de información sobre recursos comunitarios disponibles.' 
      },
      { 
        id: 'CAS-005', 
        categoria: ' Salud Mental', 
        estado: 'abierto', 
        riesgo: 'alto', 
        fecha: new Date(Date.now() - 1*60*60*1000).toISOString(), 
        resumen: 'Pensamientos suicidas detectados. En proceso de derivación a línea 106.' 
      },
    ];

    const alarms = [
      { 
        id: 'ALR-100', 
        tipo: ' Emergencia Crítica', 
        nivel: 'crítico', 
        detalle: 'Palabras clave de peligro inmediato detectadas en conversación activa', 
        fecha: new Date(Date.now() - 15*60*1000).toISOString()
      },
      { 
        id: 'ALR-101', 
        tipo: ' Seguimiento Urgente', 
        nivel: 'alto', 
        detalle: 'Usuario con señales de recaída después de tratamiento previo', 
        fecha: new Date(Date.now() - 45*60*1000).toISOString()
      },
      { 
        id: 'ALR-102', 
        tipo: ' Alerta Preventiva', 
        nivel: 'alto', 
        detalle: 'Patrón de mensajes nocturnos con contenido preocupante detectado', 
        fecha: new Date(Date.now() - 120*60*1000).toISOString()
      },
    ];

    return { cases, alarms, lastUpdate: iso };
  }

  function formatTimeAgo(dateStr){
    const now = Date.now();
    const past = new Date(dateStr).getTime();
    const diff = Math.floor((now - past) / 1000); // seconds
    
    if (diff < 60) return 'Hace un momento';
    if (diff < 3600) return `Hace ${Math.floor(diff/60)} min`;
    if (diff < 86400) return `Hace ${Math.floor(diff/3600)} h`;
    return `Hace ${Math.floor(diff/86400)} días`;
  }

  function render(){
    const { cases, alarms, lastUpdate } = fakeFetchData();
    const casesCount = document.getElementById('cases-count');
    const alarmsCount = document.getElementById('alarms-count');
    const last = document.getElementById('last-update');
    const casesList = document.getElementById('cases-list');
    const alarmsList = document.getElementById('alarms-list');

    // Animar contadores
    if (casesCount) {
      animateCounter(casesCount, 0, cases.length, 800);
    }
    if (alarmsCount) {
      animateCounter(alarmsCount, 0, alarms.length, 800);
    }
    
    if (last) {
      last.textContent = new Date(lastUpdate).toLocaleString('es-CO', {
        dateStyle: 'short',
        timeStyle: 'short'
      });
    }

    if (casesList){
      casesList.innerHTML = '';
      cases.forEach((c, idx) => {
        const item = document.createElement('div');
        item.className = 'case-item';
        item.style.animationDelay = `${idx * 0.1}s`;
        item.style.opacity = '0';
        item.style.animation = 'fadeInUp 0.5s ease-out forwards';
        
        const riskColor = c.riesgo === 'alto' ? '#ef4444' : c.riesgo === 'medio' ? '#f59e0b' : '#10b981';
        
        item.innerHTML = `
          <div class="item-content">
            <div class="item-main">
              <div class="item-id">${c.id}</div>
              <div class="item-summary">${c.resumen}</div>
              <div class="item-meta">
                <span class="meta-tag">${c.categoria}</span>
                <span class="meta-tag"> ${formatTimeAgo(c.fecha)}</span>
              </div>
            </div>
            <div class="item-aside">
              <span class="status-badge ${c.estado === 'abierto' ? 'badge-open' : 'badge-closed'}">
                ${c.estado === 'abierto' ? 'Abierto' : ' Cerrado'}
              </span>
              <div class="risk-label">
                Riesgo: <strong style="color:${riskColor};">${c.riesgo.toUpperCase()}</strong>
              </div>
            </div>
          </div>
        `;
        
        // Añadir efecto hover de sonido (simulado con escala)
        item.addEventListener('mouseenter', () => {
          item.style.transform = 'translateX(8px) scale(1.01)';
        });
        item.addEventListener('mouseleave', () => {
          item.style.transform = '';
        });
        
        casesList.appendChild(item);
      });
    }

    if (alarmsList){
      alarmsList.innerHTML = '';
      alarms.forEach((a, idx) => {
        const item = document.createElement('div');
        item.className = 'alarm-item';
        item.style.animationDelay = `${idx * 0.1}s`;
        item.style.opacity = '0';
        item.style.animation = 'fadeInUp 0.5s ease-out forwards';
        
        item.innerHTML = `
          <div class="item-content">
            <div class="item-main">
              <div class="item-id">${a.id}</div>
              <div class="item-summary">${a.detalle}</div>
              <div class="item-meta">
                <span class="meta-tag">${a.tipo}</span>

              </div>
            </div>
            <div class="item-aside">
              <span class="status-badge ${a.nivel === 'crítico' ? 'badge-critical' : 'badge-high'}">
                ${a.nivel === 'crítico' ? ' CRÍTICO' : ' ALTO'}
              </span>
            </div>
          </div>
        `;
        
        item.addEventListener('mouseenter', () => {
          item.style.transform = 'translateX(8px) scale(1.01)';
        });
        item.addEventListener('mouseleave', () => {
          item.style.transform = '';
        });
        
        alarmsList.appendChild(item);
      });
    }
  }

  function animateCounter(element, start, end, duration) {
    const startTime = performance.now();
    
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (end - start) * easeOut);
      
      element.textContent = current;
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = end;
      }
    }
    
    requestAnimationFrame(update);
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (!ensureAdmin()) return;

    const refresh = document.getElementById('refresh-btn');
    if (refresh) {
      refresh.addEventListener('click', () => {
        // Animación de rotación del botón
        const svg = refresh.querySelector('svg');
        if (svg) {
          svg.style.transform = 'rotate(360deg)';
          setTimeout(() => {
            svg.style.transform = '';
          }, 500);
        }
        render();
      });
    }

    render();
  });
})();
