#!/usr/bin/env python3
"""Genera la web pública de KAIROS Salud en dist/.

Uso:
  python3 build.py                 -> versión de prueba (noindex, URL de GitHub Pages)
  python3 build.py --produccion    -> versión final con dominio propio (indexable)

Para cambiar datos de contacto o el dominio, editá solo el bloque DATOS.
"""
import json, os, shutil, sys, html
from datetime import date

# ======================= DATOS =======================
DATOS = {
    "marca": "KAIROS Salud",
    "whatsapp": "5491135798229",           # formato internacional sin "+"
    "whatsapp_visible": "11 3579-8229",
    "direccion": "Calle 158 esquina 53",
    "localidad": "Hudson",
    "partido": "Berazategui",
    "provincia": "Buenos Aires",
    "dominio_final": "https://www.kairossalud.com.ar",   # cambiar si se compra otro
    "url_prueba": "https://kairossalud.github.io",       # se ajusta al nombre real de la cuenta
    "zonas": ["Hudson", "Berazategui", "Plátanos", "Ranelagh", "Gutiérrez", "El Pato",
              "Villa España", "Ezpeleta", "Quilmes", "Florencio Varela", "Avellaneda"],
    "habilitacion_aprobada": False,
    "ga4_id": "G-DR2GCEQM6F",             # Google Analytics 4 (vacío = sin medición)       # pasar a True cuando el Ministerio la apruebe
}
# =====================================================

PROD = "--produccion" in sys.argv
BASE = (DATOS["dominio_final"] if PROD else DATOS["url_prueba"]).rstrip("/")
ROBOTS_META = "index,follow" if PROD else "noindex,nofollow"
SRC, DIST = "src", "dist"
HOY = date.today().isoformat()
WA = DATOS["whatsapp"]
DIR_COMPLETA = f'{DATOS["direccion"]}, {DATOS["localidad"]}, {DATOS["partido"]}'
MAPS = "https://www.google.com/maps/search/?api=1&query=" + "Calle+158+y+53+Hudson+Berazategui"


def wa_link(texto):
    from urllib.parse import quote
    return f"https://wa.me/{WA}?text={quote(texto)}"


def rel(depth):
    return "../" * depth


def head_extra(path, title, desc, depth, schema):
    r = rel(depth)
    url = BASE + "/" + path
    return f'''<meta name="robots" content="{ROBOTS_META}"/>
<link rel="canonical" href="{url}"/>
<link rel="icon" href="{r}assets/brand/favicon.ico" sizes="any"/>
<link rel="icon" type="image/png" href="{r}assets/brand/favicon-32.png"/>
<link rel="apple-touch-icon" href="{r}assets/brand/apple-touch-icon.png"/>
<meta property="og:type" content="website"/><meta property="og:locale" content="es_AR"/>
<meta property="og:site_name" content="{DATOS['marca']}"/>
<meta property="og:title" content="{html.escape(title)}"/>
<meta property="og:description" content="{html.escape(desc)}"/>
<meta property="og:url" content="{url}"/>
<meta property="og:image" content="{BASE}/assets/brand/og-kairos.jpg"/>
<meta name="twitter:card" content="summary_large_image"/>
<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>
<noscript><style>.reveal{{opacity:1!important;transform:none!important}}</style></noscript>
{ga4_snippet()}'''


def ga4_snippet():
    """GA4 sin datos personales: solo se envían nombres de evento y la página.
    Nunca se mandan valores de formularios (nombre, teléfono, situación, etc.)."""
    gid = DATOS.get("ga4_id")
    if not gid:
        return ""
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>'
            "<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments)}"
            f"gtag('js',new Date());gtag('config','{gid}',{{anonymize_ip:true,allow_google_signals:false,allow_ad_personalization_signals:false}});"
            "document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a');if(!a)return;var h=a.getAttribute('href')||'';"
            "if(h.indexOf('wa.me')>-1){gtag('event','whatsapp_click',{ubicacion:location.pathname,boton:(a.className||'link').split(' ')[0]})}"
            "else if(h.indexOf('#turnos')>-1){gtag('event','turno_click',{ubicacion:location.pathname})}"
            "else if(h.indexOf('maps')>-1){gtag('event','como_llegar_click',{ubicacion:location.pathname})}},true);"
            "document.addEventListener('submit',function(e){var f=e.target;if(!f||!f.id)return;"
            "var n={careForm:'consulta_domicilio',rentForm:'consulta_alquiler',bookingForm:'solicitud_turno'}[f.id];"
            "if(n)gtag('event','formulario_enviado',{formulario:n,ubicacion:location.pathname})},true);</script>")


def org_schema():
    tipo = "MedicalClinic" if DATOS["habilitacion_aprobada"] else "MedicalBusiness"
    return {
        "@type": tipo,
        "@id": BASE + "/#organizacion",
        "name": DATOS["marca"],
        "url": BASE + "/",
        "logo": BASE + "/assets/brand/kairos-logo.png",
        "image": BASE + "/assets/brand/og-kairos.jpg",
        "telephone": "+" + WA,
        "address": {"@type": "PostalAddress", "streetAddress": DATOS["direccion"],
                    "addressLocality": DATOS["localidad"], "addressRegion": DATOS["provincia"],
                    "addressCountry": "AR"},
        "areaServed": [{"@type": "City", "name": z} for z in DATOS["zonas"]],
        "contactPoint": {"@type": "ContactPoint", "telephone": "+" + WA,
                         "contactType": "customer service", "availableLanguage": "es"},
    }


def breadcrumb(items):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + "/" + p}
        for i, (n, p) in enumerate(items)]}


def must_replace(text, old, new, count=1):
    if old not in text:
        raise SystemExit(f"No encontrado en plantilla: {old[:70]!r}")
    return text.replace(old, new, count)


# ---------------- Página principal ----------------
def build_index():
    t = open(f"{SRC}/index.html", encoding="utf-8").read()
    title = ("KAIROS Salud · Centro de salud multidisciplinario en Hudson" if DATOS["habilitacion_aprobada"]
             else "KAIROS Salud · Consultorios y salud a domicilio en Hudson")
    desc = ("Consultorios de especialidades en Hudson, Berazategui. Enfermería, cuidadores y "
            "acompañamiento terapéutico a domicilio en Zona Sur. Consultanos por WhatsApp.")
    t = must_replace(t, '<title>KAIROS Salud | Especialistas en Hudson y cuidados a domicilio</title>', f"<title>{title}</title>")
    t = must_replace(t, 'content="KAIROS Salud: consultorios y especialidades médicas en Hudson, Berazategui. Enfermería, cuidadores y acompañamiento terapéutico a domicilio en Zona Sur."', f'content="{desc}"')
    schema = {"@context": "https://schema.org", "@graph": [org_schema(), {
        "@type": "WebSite", "@id": BASE + "/#web", "url": BASE + "/", "name": DATOS["marca"],
        "inLanguage": "es-AR", "publisher": {"@id": BASE + "/#organizacion"}}]}
    t = must_replace(t, "<style>", head_extra("", title, desc, 0, schema) + "<style>")
    # H1 con palabra clave sin cambiar el diseño: la línea chica pasa a ser el H1
    h1 = ("Centro de salud multidisciplinario en Hudson, Berazategui" if DATOS["habilitacion_aprobada"]
          else "Consultorios y salud a domicilio en Hudson, Berazategui")
    t = must_replace(t, '<span class="eyebrow" style="color:#edf1ff">Hudson · Zona Sur</span><h1>Tu salud, <em>en el lugar</em> que necesitás.</h1>',
                     f'<h1 class="eyebrow hero-kicker" style="color:#edf1ff">{h1}</h1><p class="hero-title">Tu salud, <em>en el lugar</em> que necesitás.</p>')
    t = must_replace(t, ".hero h1{margin:26px 0 24px}.hero h1 em{", ".hero .hero-title{margin:26px 0 24px;font-size:clamp(3.35rem,6.6vw,7.1rem);font-weight:700;letter-spacing:-.055em;line-height:1.08}h1.hero-kicker{font-size:12px;line-height:1.5;letter-spacing:.17em;margin:0;max-width:520px}.hero .hero-title em{")
    t = t.replace(".hero h1{font-size:", ".hero .hero-title{font-size:")
    # WhatsApp oficial
    t = must_replace(t, "const CONFIG={whatsapp:''}; // REEMPLAZAR con el número oficial internacional sin '+', ej. 54911... No hay número real configurado.", f"const CONFIG={{whatsapp:'{WA}'}};")
    t = must_replace(t, "WhatsApp oficial pendiente de configurar. El formulario todavía no envía mensajes.", "Al enviar se abre WhatsApp con tu consulta para que la revises antes de mandarla.")
    # Enlaces internos a cada servicio domiciliario
    t = must_replace(t, '<div class="care-clean-footer"><span>¿Trabajás en cuidados domiciliarios?</span>',
                     '<nav aria-label="Servicios a domicilio" class="care-clean-footer"><span>Conocé cada servicio:</span>'
                     '<a href="domicilio/enfermeria/">Enfermería a domicilio</a><a href="domicilio/cuidadores/">Cuidadores a domicilio</a>'
                     '<a href="domicilio/acompanamiento-terapeutico/">Acompañamiento terapéutico</a></nav>'
                     '<div class="care-clean-footer" style="margin-top:12px"><span>¿Trabajás en cuidados domiciliarios?</span>')
    # Dirección real en la sección sede
    t = must_replace(t, '<p><strong>Hudson · Berazategui · Buenos Aires</strong><br/></p><a class="btn btn-outline" href="https://maps.google.com/?q=Hudson%2C%20Berazategui" rel="noopener" target="_blank">Ver Hudson en Maps ↗</a>',
                     f'<p><strong>{DATOS["direccion"]}</strong><br/>{DATOS["localidad"]}, partido de {DATOS["partido"]}, Buenos Aires</p><a class="btn btn-outline" href="{MAPS}" rel="noopener" target="_blank">Cómo llegar ↗</a>')
    # Footer con datos reales
    t = must_replace(t, '<p>Hudson, Berazategui · Zona Sur</p><a href="#domicilio">Consulta domiciliaria</a><a href="#turnos">Consulta por turnos</a><p class="smallnote">Contactos oficiales: a confirmar antes de publicar.</p>',
                     f'<p>{DATOS["direccion"]}<br/>{DATOS["localidad"]}, {DATOS["partido"]}</p><a href="https://wa.me/{WA}" rel="noopener" target="_blank">WhatsApp {DATOS["whatsapp_visible"]}</a><a href="{MAPS}" rel="noopener" target="_blank">Cómo llegar</a><a href="privacidad/">Privacidad</a>')
    t = must_replace(t, '<a href="#domicilio">A domicilio</a><a href="profesionales.html">Para profesionales</a>',
                     '<a href="#domicilio">A domicilio</a><a href="domicilio/">Servicios a domicilio</a><a href="profesionales.html">Para profesionales</a>')
    # Ancho/alto de imágenes (evita saltos de diseño)
    for src, w, h in [("assets/sede-exterior.jpg", 825, 1100), ("assets/hero-clinica.jpg", 825, 1100),
                      ("assets/consultorio-4.jpg", 763, 508), ("assets/equipo.jpg", 1500, 844)]:
        t = t.replace(f'src="{src}"/>', f'src="{src}" width="{w}" height="{h}"/>').replace(f'src="{src}" alt=', f'src="{src}" width="{w}" height="{h}" alt=')
    return t


# ---------------- Para profesionales ----------------
def build_profesionales():
    t = open(f"{SRC}/profesionales.html", encoding="utf-8").read()
    title = "Alquiler de consultorios en Hudson, Berazategui · KAIROS Salud"
    desc = ("Alquilá un consultorio en Hudson por hora, módulo fijo o mensual. Recepción, sala de espera y Wi-Fi. "
            "Además, sumate al equipo de cuidados domiciliarios de Zona Sur.")
    t = must_replace(t, "<title>Profesionales | KAIROS Salud Hudson</title>", f"<title>{title}</title>")
    t = must_replace(t, 'content="Consultorios para profesionales de la salud en Hudson, Berazategui. Consultá por alquiler y postulaciones para cuidados domiciliarios KAIROS."', f'content="{desc}"')
    schema = {"@context": "https://schema.org", "@graph": [org_schema(),
              breadcrumb([("Inicio", ""), ("Para profesionales", "profesionales.html")])]}
    t = must_replace(t, "<style>", head_extra("profesionales.html", title, desc, 0, schema) + "<style>")
    t = must_replace(t, '<h1>Tu espacio para atender, en KAIROS.</h1>', '<h1>Alquiler de consultorios en Hudson, Berazategui.</h1><p class="lead" style="margin-top:14px;font-weight:700">Tu espacio para atender, en KAIROS.</p>')
    t = must_replace(t, "const CONFIG={whatsapp:'',postulationFormUrl:''};", f"const CONFIG={{whatsapp:'{WA}',postulationFormUrl:''}};")
    t = t.replace("[Superficie] · [Ubicación dentro de la sede] · [Equipamiento por confirmar]", "Consultá medidas, equipamiento y horarios disponibles por WhatsApp.")
    t = t.replace('<a href="#modalidades">Modalidades</a>', '<a href="#modalidades">Modalidades</a><a href="#disponibilidad">Agenda</a>')
    t = must_replace(t, "<li>Habilitación provincial del Ministerio de Salud</li>", "<li>Habilitación provincial</li>")
    # Agenda de alquiler de consultorios (reemplaza el formulario de texto)
    import re as _re
    agenda = open(f"{SRC}/disponibilidad.json", encoding="utf-8").read()
    rooms = json.loads(agenda)["consultorios"]
    room_btns = "".join(f'<button type="button" class="ag-room" data-room="{r}" aria-pressed="false">{r}</button>' for r in rooms)
    room_btns += '<button type="button" class="ag-room" data-room="Cualquier consultorio" aria-pressed="false">Cualquiera disponible</button>'
    section = f'''<section id="disponibilidad"><div class="wrap"><div class="section-title"><span class="eyebrow">Agenda de consultorios</span><h2>Elegí consultorio, día y horario.</h2><p>Mirá la disponibilidad de cada espacio y enviános tu solicitud por WhatsApp. Te confirmamos el alquiler y las condiciones de forma personalizada.</p></div>
<div class="ag-layout"><div class="ag-panel">
<div class="ag-step"><span>1</span><div><h3>Consultorio</h3><div class="ag-rooms">{room_btns}</div></div></div>
<div class="ag-step"><span>2</span><div style="min-width:0"><h3>Día</h3><div class="ag-toolbar"><button type="button" class="ag-nav" id="agPrev" aria-label="Mes anterior">‹</button><strong id="agMonth" aria-live="polite"></strong><button type="button" class="ag-nav" id="agNext" aria-label="Mes siguiente">›</button></div><div class="ag-grid" id="agDays" role="group" aria-label="Calendario de disponibilidad"></div><div class="ag-key"><span><i class="ag-dot ok"></i>Con horarios libres</span><span><i class="ag-dot full"></i>Completo</span><span><i class="ag-dot off"></i>Sin atención</span></div><p class="notice" id="agHint"></p></div></div>
</div><div class="ag-panel ag-detail"><div class="ag-head"><span class="eyebrow" style="margin:0">Tu elección</span><h3 id="agDayTitle">Elegí un día</h3><p class="notice" id="agSummary" style="margin:0"></p></div>
<div class="ag-slots" id="agSlots" aria-live="polite"></div>
<form id="rentForm" class="ag-form" hidden><h3>Tus datos</h3><div class="fields"><label class="field full">Modalidad<select id="rentMode" required=""><option value="">Elegí una opción</option><option>Por hora (solo este día)</option><option>Módulo fijo semanal (mismo día y horario todas las semanas)</option><option>Mensual</option><option>Quiero asesoramiento</option></select></label><label class="field full">Nombre y apellido<input autocomplete="name" id="rentName" placeholder="Tu nombre completo" required=""/></label><label class="field">Especialidad<input id="rentSpec" placeholder="Ej. Psicología" required=""/></label><label class="field">WhatsApp<input autocomplete="tel" id="rentPhone" inputmode="tel" placeholder="Código de área + número" required="" type="tel"/></label></div><button class="btn" type="submit">Enviar solicitud por WhatsApp ↗</button><p class="notice">La solicitud no reserva automáticamente: te confirmamos disponibilidad y valores por WhatsApp. No incluyas información de pacientes.</p><p class="status hidden" id="rentStatus" role="status"></p></form>
</div></div></div></section>'''
    t, n = _re.subn(r'<section id="disponibilidad">.*?</section>', lambda m: section, t, count=1, flags=_re.S)
    assert n == 1
    t = _re.sub(r"\$\('rentForm'\)\.addEventListener\('submit'.*?\n", "", t, count=1)
    t = _re.sub(r"document\.querySelectorAll\('\.consultorio-select'\).*?\n", "", t, count=1)
    assert "rentRoom" not in t
    css = open(f"{SRC}/agenda-consultorios.css", encoding="utf-8").read()
    t = must_replace(t, "</style></head>", css + "</style></head>")
    t = must_replace(t, "</body></html>", f'<script>window.KAIROS_AGENDA={json.dumps(json.loads(agenda), ensure_ascii=False)};window.KAIROS_WA="{WA}";</script><script src="assets/agenda-consultorios.js" defer></script></body></html>')
    t = must_replace(t, '<p><strong>KAIROS Salud</strong> · Hudson, Berazategui<br/><small>Consultorios y cuidados a domicilio</small></p>',
                     f'<p><strong>KAIROS Salud</strong> · {DIR_COMPLETA}<br/><small>WhatsApp {DATOS["whatsapp_visible"]} · <a href="privacidad/">Privacidad</a></small></p>')
    return t


# ---------------- Páginas de servicios a domicilio ----------------
NAV = '''<div class="topbar">KAIROS SALUD · <strong>{dir}</strong> · Consultorios + cuidados a domicilio</div>
<header class="header"><div class="nav-inner"><a aria-label="KAIROS Salud, inicio" class="brand" href="{r}"><span class="brand-copy"><span class="brand-name">kairos</span><span class="brand-sub">salud</span></span></a><nav aria-label="Navegación principal" class="nav-links" id="menu"><a href="{r}#especialidades">Especialidades</a><a href="{r}domicilio/">A domicilio</a><a href="{r}profesionales.html">Para profesionales</a><a href="{r}#sede">La sede</a><a class="btn btn-blue" href="{wa}" rel="noopener" target="_blank">Consultar por WhatsApp ↗</a></nav><button aria-controls="menu" aria-expanded="false" aria-label="Abrir menú" class="mobile-toggle" id="menuToggle">☰</button></div></header>'''

FOOTER = '''<footer class="footer"><div class="wrap"><div class="footer-grid"><div><a class="brand" href="{r}"><span class="brand-copy"><span class="brand-name">kairos</span><span class="brand-sub">salud</span></span></a><p style="margin-top:25px">Consultorios en Hudson.<br/>Cuidados en tu casa.</p></div><div><h3>A domicilio</h3><a href="{r}domicilio/enfermeria/">Enfermería a domicilio</a><a href="{r}domicilio/cuidadores/">Cuidadores a domicilio</a><a href="{r}domicilio/acompanamiento-terapeutico/">Acompañamiento terapéutico</a><a href="{r}profesionales.html">Para profesionales</a></div><div><h3>Contacto</h3><p>{dir}</p><a href="https://wa.me/{wa_num}" rel="noopener" target="_blank">WhatsApp {wa_vis}</a><a href="{maps}" rel="noopener" target="_blank">Cómo llegar</a><a href="{r}privacidad/">Privacidad</a></div></div><div class="footer-bottom"><span>© {anio} KAIROS Salud</span><span>Una forma más humana de cuidar.</span></div></div></footer>
<a class="float-wa" href="{wa}" rel="noopener" target="_blank">✆ WhatsApp</a>
<script>const t=document.getElementById('menuToggle'),m=document.getElementById('menu');t.addEventListener('click',()=>{{const o=m.classList.toggle('open');t.setAttribute('aria-expanded',String(o));t.textContent=o?'✕':'☰'}});</script>'''

PAGE_CSS = '''.svc-hero{padding:30px 0 10px}.svc-hero-inner{background:#e6eafd;border-radius:30px;padding:clamp(32px,6vw,80px)}.svc-hero h1{font-size:clamp(2.4rem,5.2vw,5rem);margin:18px 0 20px;max-width:900px}.svc-hero p{max-width:640px;color:#475d79;font-size:1.08rem}.crumbs{font-size:12px;color:var(--muted);margin-bottom:14px}.crumbs a{text-decoration:underline}.svc-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.svc-card{background:#fff;border:1px solid var(--line);border-radius:22px;padding:30px}.svc-card h2{font-size:clamp(1.6rem,2.6vw,2.3rem);margin-bottom:14px}.svc-card p{color:var(--muted)}.zonas{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.zonas span{background:#eef3fd;border-radius:30px;padding:8px 13px;font-size:13px;font-weight:700;color:var(--navy)}.related{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.related a{background:#fff;border:1px solid var(--line);border-radius:18px;padding:22px;font-weight:800;display:flex;justify-content:space-between}.related a span{color:var(--blue)}.notice-box{background:#fff5df;border:1px solid #ecd9b4;color:#634d29;border-radius:15px;padding:17px 21px;font-size:14px;margin-top:22px}.svc-steps{counter-reset:s;list-style:none;padding:0;display:grid;gap:14px}.svc-steps li{counter-increment:s;display:flex;gap:14px;align-items:flex-start}.svc-steps li:before{content:counter(s);flex:none;width:34px;height:34px;border-radius:50%;background:#eaf0ff;color:var(--navy);display:grid;place-items:center;font-weight:800}@media(max-width:850px){.svc-grid,.related{grid-template-columns:1fr}}'''


def page(path, depth, title, desc, h1, kicker, intro, cta_text, body, crumbs, faq=None, service=None):
    r = rel(depth)
    graph = [org_schema(), breadcrumb(crumbs)]
    if service:
        graph.append({"@type": "Service", "name": service, "serviceType": service,
                      "provider": {"@id": BASE + "/#organizacion"},
                      "areaServed": [{"@type": "City", "name": z} for z in DATOS["zonas"]],
                      "url": BASE + "/" + path})
    if faq:
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]})
    schema = {"@context": "https://schema.org", "@graph": graph}
    wa = wa_link(cta_text)
    crumbs_html = " › ".join(f'<a href="{r}{p}">{n}</a>' for n, p in crumbs[:-1]) + f" › {crumbs[-1][0]}"
    faq_html = ""
    if faq:
        faq_html = ('<section class="section" id="preguntas"><div class="wrap faq"><div><span class="eyebrow">Preguntas frecuentes</span>'
                    f'<h2>Lo que más nos consultan.</h2></div><div>'
                    + "".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in faq) + "</div></div></section>")
    return f'''<!DOCTYPE html>
<html lang="es-AR"><head><meta charset="utf-8"/><meta content="width=device-width,initial-scale=1" name="viewport"/><meta content="#567ebd" name="theme-color"/>
<title>{title}</title><meta name="description" content="{html.escape(desc)}"/>
{head_extra(path, title, desc, depth, schema)}
<link href="https://fonts.googleapis.com" rel="preconnect"/><link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect"/><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&amp;family=Nunito:wght@500;600;700;800;900&amp;display=swap" rel="stylesheet"/>
<link rel="stylesheet" href="{r}assets/site.css"/><style>{PAGE_CSS}</style></head><body>
{NAV.format(r=r, wa=wa, dir=DATOS["direccion"] + ", " + DATOS["localidad"])}
<main><section class="svc-hero"><div class="wrap"><div class="svc-hero-inner"><div class="crumbs">{crumbs_html}</div><span class="eyebrow">{kicker}</span><h1>{h1}</h1><p>{intro}</p><div class="hero-actions"><a class="btn btn-navy" href="{wa}" rel="noopener" target="_blank">Consultar por WhatsApp ↗</a><a class="btn btn-white" href="{r}#domicilio">Completar formulario</a></div></div></div></section>
{body}
{faq_html}
</main>
{FOOTER.format(r=r, wa=wa, wa_num=WA, wa_vis=DATOS["whatsapp_visible"], dir=DIR_COMPLETA, maps=MAPS, anio=date.today().year)}
</body></html>'''


def zonas_html():
    return '<div class="zonas">' + "".join(f"<span>{z}</span>" for z in DATOS["zonas"]) + "</div>"


def related(depth, excluir):
    r = rel(depth)
    items = [("domicilio/enfermeria/", "Enfermería a domicilio"), ("domicilio/cuidadores/", "Cuidadores a domicilio"),
             ("domicilio/acompanamiento-terapeutico/", "Acompañamiento terapéutico"), ("profesionales.html", "Consultorios en Hudson")]
    links = "".join(f'<a href="{r}{p}">{n}<span>↗</span></a>' for p, n in items if p != excluir)
    return f'<section class="section soft"><div class="wrap"><span class="eyebrow">También en KAIROS</span><h2 style="margin:14px 0 28px">Otros servicios.</h2><div class="related">{links}</div></div></section>'


AVISO = ('<div class="notice-box"><strong>No es un servicio de emergencias.</strong> Ante una urgencia médica, comunicate con el '
         'sistema de emergencias de tu zona. No envíes diagnósticos ni estudios por WhatsApp: la prestación se define después de evaluar la necesidad.</div>')

COMO = '''<div class="svc-card"><h2>Cómo coordinamos</h2><ol class="svc-steps"><li>Nos escribís por WhatsApp o completás el formulario con tu localidad y lo que necesitás.</li><li>Te contactamos para entender la situación y los horarios.</li><li>Te proponemos la persona y la modalidad indicadas.</li><li>Acordamos el inicio y hacemos seguimiento.</li></ol></div>'''


def build_domicilio():
    pages = {}
    # Hub
    body = f'''<section class="section"><div class="wrap"><div class="svc-grid">
<div class="svc-card"><h2>Servicios a domicilio</h2><p>Coordinamos profesionales y cuidadores para que la atención llegue a tu casa, con orientación personalizada desde el primer contacto.</p>
<ul class="list-check"><li><a href="enfermeria/"><strong>Enfermería a domicilio</strong></a></li><li><a href="cuidadores/"><strong>Cuidadoras y cuidadores a domicilio</strong></a></li><li><a href="acompanamiento-terapeutico/"><strong>Acompañamiento terapéutico</strong></a></li></ul></div>
<div class="svc-card"><h2>Zonas donde trabajamos</h2><p>Berazategui y localidades de Zona Sur. Consultá disponibilidad según tu domicilio.</p>{zonas_html()}</div>
{COMO}<div class="svc-card"><h2>¿No sabés qué servicio necesitás?</h2><p>Es muy común. Contanos la situación —por ejemplo, un alta hospitalaria, un postoperatorio o un adulto mayor que necesita compañía— y te orientamos.</p>{AVISO}</div>
</div></div></section>'''
    pages["domicilio/index.html"] = page(
        "domicilio/", 1, "Salud a domicilio en Berazategui y Zona Sur · KAIROS Salud",
        "Enfermería, cuidadores y acompañamiento terapéutico a domicilio en Berazategui, Hudson, Quilmes, Florencio Varela y Zona Sur.",
        "Salud a domicilio en Berazategui y Zona Sur", "Cuidados en casa",
        "Enfermería, cuidadores y acompañamiento terapéutico para vos o tu familia, coordinados desde nuestra sede en Hudson.",
        "Hola KAIROS Salud, quiero consultar por atención a domicilio.", body,
        [("Inicio", ""), ("A domicilio", "domicilio/")])

    # Enfermería
    faq = [("¿Qué diferencia hay entre una enfermera y una cuidadora?", "La enfermera realiza prestaciones propias de enfermería según su formación e indicación médica. La cuidadora acompaña y asiste en actividades de la vida diaria."),
           ("¿Necesito una indicación médica?", "Las prestaciones de enfermería se realizan según la indicación del médico tratante. Te pedimos esa información al coordinar, no por WhatsApp."),
           ("¿En qué zonas trabajan?", "Berazategui, Hudson y localidades de Zona Sur como Quilmes, Ezpeleta, Florencio Varela y alrededores. Consultá disponibilidad según domicilio."),
           ("¿Atienden urgencias?", "No. Ante una urgencia médica comunicate con el sistema de emergencias de tu zona.")]
    body = f'''<section class="section"><div class="wrap"><div class="svc-grid">
<div class="svc-card"><h2>Cuándo puede ayudarte</h2><ul class="list-check"><li>Después de un alta hospitalaria.</li><li>Postoperatorios y curaciones.</li><li>Prestaciones de enfermería indicadas por el médico tratante.</li><li>Seguimiento en casa de personas mayores.</li></ul></div>
<div class="svc-card"><h2>Zonas de cobertura</h2><p>Enfermería a domicilio en Berazategui y Zona Sur:</p>{zonas_html()}</div>
{COMO}<div class="svc-card"><h2>Antes de consultar</h2><p>Tené a mano la localidad, el tipo de cuidado que necesitás y desde cuándo. Nosotros te orientamos con el resto.</p>{AVISO}</div>
</div></div></section>{related(2, "domicilio/enfermeria/")}'''
    pages["domicilio/enfermeria/index.html"] = page(
        "domicilio/enfermeria/", 2, "Enfermería a domicilio en Berazategui y Zona Sur · KAIROS",
        "Enfermería a domicilio en Berazategui, Hudson, Quilmes, Florencio Varela y Zona Sur. Altas hospitalarias, postoperatorios y curaciones. Consultá disponibilidad.",
        "Enfermería a domicilio en Berazategui y Zona Sur", "Cuidados en casa",
        "Enfermeras y enfermeros que van a tu casa para acompañar una recuperación o un tratamiento, según la indicación de tu médico.",
        "Hola KAIROS Salud, quiero consultar por enfermería a domicilio.", body,
        [("Inicio", ""), ("A domicilio", "domicilio/"), ("Enfermería", "domicilio/enfermeria/")], faq, "Enfermería a domicilio")

    # Cuidadores
    faq = [("¿Qué hace una cuidadora a domicilio?", "Acompaña y asiste a la persona en actividades de la vida diaria: compañía, higiene y confort, alimentación, movilidad y acompañamiento a turnos o salidas."),
           ("¿Puedo contratar unas horas o fines de semana?", "Sí. Coordinamos según la necesidad: algunas horas, fines de semana o acompañamiento diario."),
           ("¿Una cuidadora puede hacer prestaciones de enfermería?", "No. Para prestaciones de enfermería coordinamos una enfermera o enfermero."),
           ("¿En qué zonas trabajan?", "Berazategui, Hudson y localidades de Zona Sur. Consultá disponibilidad según domicilio.")]
    body = f'''<section class="section"><div class="wrap"><div class="svc-grid">
<div class="svc-card"><h2>En qué acompañan</h2><ul class="list-check"><li>Compañía para adultos mayores.</li><li>Higiene, confort y alimentación.</li><li>Movilidad dentro y fuera de casa.</li><li>Acompañamiento a turnos médicos.</li></ul></div>
<div class="svc-card"><h2>Modalidades</h2><ul class="list-check"><li>Unas horas por día.</li><li>Fines de semana.</li><li>Acompañamiento diario.</li></ul><p>Zonas de cobertura:</p>{zonas_html()}</div>
{COMO}<div class="svc-card"><h2>Para vos y tu familia</h2><p>Sabemos que dejar a un ser querido en manos de otra persona no es fácil. Por eso escuchamos la situación antes de proponer a alguien.</p>{AVISO}</div>
</div></div></section>{related(2, "domicilio/cuidadores/")}'''
    pages["domicilio/cuidadores/index.html"] = page(
        "domicilio/cuidadores/", 2, "Cuidadores a domicilio en Berazategui y Zona Sur · KAIROS",
        "Cuidadoras y cuidadores a domicilio para adultos mayores en Berazategui, Hudson y Zona Sur. Por horas, fines de semana o acompañamiento diario.",
        "Cuidadores a domicilio en Berazategui y Zona Sur", "Cuidados en casa",
        "Cuidadoras y cuidadores que acompañan a tu familiar en su casa, con la frecuencia que necesites.",
        "Hola KAIROS Salud, quiero consultar por cuidadores a domicilio.", body,
        [("Inicio", ""), ("A domicilio", "domicilio/"), ("Cuidadores", "domicilio/cuidadores/")], faq, "Cuidadores a domicilio")

    # Acompañamiento terapéutico
    faq = [("¿Qué es el acompañamiento terapéutico?", "Es un dispositivo de apoyo en la vida cotidiana de una persona que está en tratamiento. El acompañante trabaja dentro de la estrategia definida por el profesional tratante."),
           ("¿Necesito una indicación profesional?", "Sí. El acompañamiento terapéutico se coordina con el psicólogo, psiquiatra u otro profesional a cargo del tratamiento."),
           ("¿Dónde se realiza?", "En el domicilio y en los espacios cotidianos de la persona en Berazategui y Zona Sur, según lo que indique el tratamiento.")]
    body = f'''<section class="section"><div class="wrap"><div class="svc-grid">
<div class="svc-card"><h2>Cómo trabaja un acompañante terapéutico</h2><ul class="list-check"><li>Acompaña en la rutina diaria y en los espacios cotidianos.</li><li>Trabaja articulado con el profesional tratante.</li><li>Favorece la autonomía y la integración social.</li></ul></div>
<div class="svc-card"><h2>Zonas de cobertura</h2><p>Acompañantes terapéuticos en Berazategui y Zona Sur:</p>{zonas_html()}</div>
{COMO}<div class="svc-card"><h2>Confidencialidad</h2><p>Por WhatsApp solo te pedimos datos de contacto y el tipo de servicio. La información del tratamiento se conversa luego, de forma reservada.</p>{AVISO}</div>
</div></div></section>{related(2, "domicilio/acompanamiento-terapeutico/")}'''
    pages["domicilio/acompanamiento-terapeutico/index.html"] = page(
        "domicilio/acompanamiento-terapeutico/", 2, "Acompañamiento terapéutico en Berazategui y Zona Sur · KAIROS",
        "Acompañantes terapéuticos a domicilio en Berazategui, Hudson y Zona Sur, articulados con el profesional tratante. Consultá por WhatsApp.",
        "Acompañamiento terapéutico en Berazategui y Zona Sur", "Salud mental · A domicilio",
        "Acompañantes terapéuticos que trabajan junto al profesional tratante, en la casa y la vida cotidiana de la persona.",
        "Hola KAIROS Salud, quiero consultar por acompañamiento terapéutico.", body,
        [("Inicio", ""), ("A domicilio", "domicilio/"), ("Acompañamiento terapéutico", "domicilio/acompanamiento-terapeutico/")], faq, "Acompañamiento terapéutico")

    # Privacidad
    body = f'''<section class="section"><div class="wrap" style="max-width:820px"><div class="svc-card">
<h2>Qué datos usamos</h2><p>Cuando nos escribís por WhatsApp o completás un formulario, usamos tu nombre, número de contacto, localidad y el servicio consultado únicamente para responderte y coordinar la atención.</p>
<h2 style="margin-top:28px">Qué no pedimos por la web</h2><p>No pedimos ni guardamos diagnósticos, estudios ni historia clínica a través de este sitio. Esa información se trata luego, de forma reservada, con el equipo que te atienda.</p>
<h2 style="margin-top:28px">Formularios de la web</h2><p>Los formularios no envían datos a un servidor: arman un mensaje que vos revisás y enviás desde tu WhatsApp. La agenda de turnos de la web está en fase de prueba y guarda la información solo en tu navegador.</p>
<h2 style="margin-top:28px">Estadísticas de visitas</h2><p>Usamos Google Analytics para saber cuántas personas visitan la web y qué secciones usan. No enviamos a Google nombres, teléfonos ni información de salud: solo datos agregados de navegación, como la página visitada o el tipo de dispositivo.</p>
<h2 style="margin-top:28px">Tus derechos</h2><p>Podés pedir acceso, rectificación o supresión de tus datos escribiéndonos por WhatsApp, conforme a la Ley 25.326 de Protección de Datos Personales.</p>
<p class="smallnote" style="margin-top:22px">Responsable: KAIROS Salud · {DIR_COMPLETA}. Última actualización: {HOY}.</p></div></div></section>'''
    pages["privacidad/index.html"] = page(
        "privacidad/", 1, "Política de privacidad · KAIROS Salud",
        "Cómo usa KAIROS Salud los datos que nos enviás por la web y WhatsApp.",
        "Política de privacidad", "KAIROS Salud",
        "Cuidamos tu información con el mismo criterio con el que cuidamos tu salud.",
        "Hola KAIROS Salud, tengo una consulta sobre mis datos.", body,
        [("Inicio", ""), ("Privacidad", "privacidad/")])
    return pages


def build_404():
    t = page("404.html", 0, "Página no encontrada · KAIROS Salud", "La página que buscás no existe.",
             "No encontramos esta página", "Error 404",
             "Puede que el enlace haya cambiado. Te dejamos los accesos principales.",
             "Hola KAIROS Salud, tengo una consulta.",
             f'<section class="section"><div class="wrap">{related(0, "")}</div></section>'.replace('section class="section soft"', 'div'),
             [("Inicio", ""), ("404", "404.html")])
    # en GitHub Pages el 404 se sirve en cualquier ruta: usar rutas absolutas desde la raíz del sitio
    import re
    t = re.sub(r'(href|src)="(?!https?:|#|mailto:)([^"]*)"', lambda m: f'{m.group(1)}="{BASE}/{m.group(2)}"', t)
    return t.replace('<meta name="robots" content="index,follow"/>', '<meta name="robots" content="noindex"/>')


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    shutil.copytree("assets", f"{DIST}/assets")
    out = {"index.html": build_index(), "profesionales.html": build_profesionales(), "404.html": build_404()}
    out.update(build_domicilio())
    for p, content in out.items():
        os.makedirs(os.path.dirname(f"{DIST}/{p}") or DIST, exist_ok=True)
        open(f"{DIST}/{p}", "w", encoding="utf-8").write(content)
    urls = ["", "domicilio/", "domicilio/enfermeria/", "domicilio/cuidadores/",
            "domicilio/acompanamiento-terapeutico/", "profesionales.html", "privacidad/"]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"  <url><loc>{BASE}/{u}</loc><lastmod>{HOY}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    open(f"{DIST}/sitemap.xml", "w").write("\n".join(sm) + "\n")
    robots = (f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n" if PROD
              else "User-agent: *\nDisallow: /\n")
    open(f"{DIST}/robots.txt", "w").write(robots)
    if PROD and DATOS["dominio_final"]:
        open(f"{DIST}/CNAME", "w").write(DATOS["dominio_final"].split("//")[1] + "\n")
    open(f"{DIST}/.nojekyll", "w").write("")
    print(("PRODUCCIÓN" if PROD else "PRUEBA (noindex)"), "->", BASE, "|", len(out), "páginas")


if __name__ == "__main__":
    main()
