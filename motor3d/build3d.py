"""Gera as páginas 3D (cárie, siso, gengivite, alinhador) a partir de um molde comum."""
src = open('/home/claude/semana/aparelho3d.html').read()
HEAD = src.replace('<canvas id="c" width="1080" height="1920"></canvas>','<canvas id="c" width="720" height="1280"></canvas>').split('<script src="dental3d.js"></script>')[0]
HEAD = HEAD.replace('<div id="mes"><div class="n" id="mesn">MÊS 1</div><div class="track"><b id="mesb"></b></div></div>',
  '<div id="mes"><div class="n" id="mesn"></div><div class="track"><b id="mesb"></b></div></div><div id="glow" style="position:absolute;width:420px;height:420px;margin:-210px 0 0 -210px;border-radius:50%;opacity:0;mix-blend-mode:screen"></div>')

COMMON = r'''<script src="dental3d.js"></script>
<script>
document.getElementById('caps').innerHTML = CAPS.map(c => `<div class="cap ${c[3]||''}"><div>${c[2]}</div></div>`).join('');
const caps = [...document.querySelectorAll('.cap')], segs = [...CAPS.map(c => [c[0], c[1]]), [FIM, DUR]];
document.getElementById('bar').innerHTML = '<i><b></b></i>'.repeat(segs.length);
const fills = [...document.querySelectorAll('.bar b')];
const clamp = x => Math.max(0, Math.min(1, x)), ease = x => 1 - Math.pow(1 - x, 3), eio = x => x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x + 2, 3)/2;
const back = x => { const c = 2.2; return 1 + (c+1)*Math.pow(x-1,3) + c*Math.pow(x-1,2); };
const starSVG = '<svg viewBox="-50 -50 100 100"><path d="M0-48L8-8 48 0 8 8 0 48-8 8-48 0-8-8Z" fill="#fff"/><circle r="10" fill="#fff" opacity=".8"/></svg>';
const stars = Array.from({ length: 6 }, () => { const s = document.createElement('div'); s.className = 'star'; s.innerHTML = starSVG; document.getElementById('fx').appendChild(s); return s; });
const dots = Array.from({ length: 26 }, () => { const d = document.createElement('div'); d.style.cssText = 'position:absolute;border-radius:50%;opacity:0'; document.getElementById('fx').appendChild(d); return d; });
const norm = a => { const l = Math.hypot(...a); return a.map(v => v / l); }, cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
const add = (a, b, k = 1) => a.map((v, i) => v + b[i]*k);
const T = v => [1,0,0,0, 0,1,0,0, 0,0,1,0, v[0],v[1],v[2],1];
const Sc = s => [s,0,0,0, 0,s,0,0, 0,0,s,0, 0,0,0,1];
const HIDE = [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,1];
function rotAxis(a, g) { const [x, y, z] = norm(a), c = Math.cos(g), s = Math.sin(g), C = 1 - c;
  return [c + x*x*C, y*x*C + z*s, z*x*C - y*s, 0, x*y*C - z*s, c + y*y*C, z*y*C + x*s, 0, x*z*C + y*s, y*z*C - x*s, c + z*z*C, 0, 0,0,0,1]; }
function about(P, M) { return M4.mul(T(P), M4.mul(M, T(P.map(v => -v)))); }
function tube(pts, r) {
  const cr = (p0, p1, p2, p3, u) => p1.map((v, i) => .5 * (2*v + (-p0[i] + p2[i])*u + (2*p0[i] - 5*v + 4*p2[i] - p3[i])*u*u + (-p0[i] + 3*v - 3*p2[i] + p3[i])*u*u*u));
  const C = []; for (let i = 0; i < pts.length - 1; i++) { const p0 = pts[Math.max(0, i-1)], p3 = pts[Math.min(pts.length-1, i+2)]; for (let k = 0; k < 14; k++) C.push(cr(p0, pts[i], pts[i+1], p3, k/14)); } C.push(pts[pts.length-1]);
  const SIDES = 8, pos = [], nor = [], idx = [];
  for (let i = 0; i < C.length; i++) { const a = C[Math.max(0, i-1)], b = C[Math.min(C.length-1, i+1)]; const tg = norm(b.map((v, k) => v - a[k])); let u1 = cross(tg, [0,1,0]); if (Math.hypot(...u1) < .01) u1 = cross(tg, [1,0,0]); u1 = norm(u1); const u2 = cross(u1, tg);
    for (let s = 0; s < SIDES; s++) { const g = s / SIDES * Math.PI * 2; const d = add(u1.map(v => v * Math.cos(g)), u2, Math.sin(g)); pos.push(...add(C[i], d, r)); nor.push(...d); } }
  for (let i = 0; i < C.length - 1; i++) for (let s = 0; s < SIDES; s++) { const a = i*SIDES + s, b = i*SIDES + (s+1) % SIDES; idx.push(a, a + SIDES, b, b, a + SIDES, b + SIDES); }
  return { pos: new Float32Array(pos), nor: new Float32Array(nor), idx: new Uint32Array(idx) };
}
const outward = (p, d) => { const r = Math.hypot(p.center[0], p.center[2] - .9); return [p.center[0] * (r + d) / r, 0, .9 + (p.center[2] - .9) * (r + d) / r]; };
function ui(t, cam, STARP, ST0) {
  stars.forEach((s, i) => { if (!STARP[i]) return; const lt = t - (ST0 + i * .4); const kk = lt < 0 ? 0 : Math.sin(clamp(lt / 1) * Math.PI); const q = S.project(cam, STARP[i]);
    s.style.left = q[0] + 'px'; s.style.top = q[1] + 'px'; s.style.opacity = t > FIM ? 0 : kk; s.style.transform = `rotate(${lt * 80}deg) scale(${.4 + .8 * kk})`; });
  CAPS.forEach((c, i) => { const lt = t - c[0], d = c[1] - c[0]; caps[i].style.opacity = (lt < 0 || lt > d) ? 0 : clamp(lt / .3) * clamp((d - lt) / .25); caps[i].style.transform = `translateY(${(1 - ease(clamp(lt / .4))) * 40}px)`; });
  segs.forEach((s, i) => fills[i].style.width = clamp((t - s[0]) / (s[1] - s[0])) * 100 + '%');
  const f = clamp((t - FIM) / .5), fim = document.getElementById('fim'); fim.style.opacity = f; fim.querySelector('.q').style.transform = `translateY(${(1 - ease(f)) * 50}px)`;
  const fo = fim.querySelector('.follow'); fo.style.transform = `scale(${t < FIM + 1.2 ? .4 + .6 * back(clamp((t - FIM - .6) / .5)) : 1 + .05 * Math.sin((t - FIM - 1.2) * 5)})`; fo.style.opacity = clamp((t - FIM - .6) * 4);
  document.body.style.opacity = clamp(t / .3);
}
const LOAD = () => initScene(document.getElementById('c'), 'http://local.test/m3d/dentition.glb', { gumU: { crown: .37, depth: 1.3 }, gumL: { crown: .42, depth: 1.3 } });
'''

PAGES = {}

# ------------------------------------------------------------------ CÁRIE
PAGES['carie3d.html'] = ('Você já teve <span class="k">cárie</span>?', r'''
const CAPS = [
  [0.2, 3.4, 'Uma <span class="k">mancha escura</span> no dente?'],
  [3.4, 6.6, 'Pode ser o começo de uma <span class="k">cárie</span>.', 'small'],
  [6.6, 9.8, 'As bactérias usam o <span class="k">açúcar</span> e produzem ácido.', 'small'],
  [9.8, 13.0, 'O ácido vai <span class="k">destruindo</span> o dente aos poucos.', 'small'],
  [13.0, 16.2, 'Tratada no início, a cárie é mais <span class="k">simples</span> de resolver.', 'small'],
  [16.2, 19.4, 'Por isso, visite o dentista <span class="k">regularmente</span>.', 'small'],
];
const FIM = 19.4; window.DUR = 23.4;
''', r'''
let MOL = null, CC = null, STARP = [];
window.EVENTS = () => { const ev = [{ t: .1, k: 'hook' }]; CAPS.slice(1).forEach(c => ev.push({ t: c[0], k: 'whoosh' }));
  ev.push({ t: 6.8, k: 'move', d: 6 }); ev.push({ t: 13.3, k: 'sweep', d: 1.8 }); [15.3, 15.7, 16.1].forEach(t => ev.push({ t, k: 'sparkle' })); ev.push({ t: FIM, k: 'fim' });
  return { dur: DUR, estilo: 'tech', events: ev.sort((a, b) => a.t - b.t) }; };
window.ready = (async () => { window.S = await LOAD();
  const teeth = S.prims.filter(p => !p.gum && p.cejY !== undefined);
  MOL = teeth.filter(p => p.lower && p.center[0] > 0 && p.center[2] > 1.75 && p.center[2] < 2.1)[0];
  let top = -1e9, best = null; for (let i = 0; i < MOL.pos.length; i += 9) { const w = M4.apply(MOL.model, [MOL.pos[i], MOL.pos[i+1], MOL.pos[i+2]]); const d = Math.hypot(w[0] - MOL.center[0], w[2] - MOL.center[2]); if (d < .06 && w[1] > top) { top = w[1]; best = w; } }
  CC = [MOL.center[0] + .01, top - .015, MOL.center[2] + .01];
  STARP = [[CC[0], CC[1] + .03, CC[2]], [CC[0] + .05, CC[1] + .02, CC[2] - .04], [CC[0] - .05, CC[1] + .02, CC[2] + .04]];
  return true; })();
const C_WIDE = { eye: [.72, 3.7, 1.55], target: [.8, 1.05, 2.0] }, C_CLOSE = { eye: [.82, 2.55, 1.62], target: [.86, 1.12, 1.98] };
const lerp = (a, b, k) => a.map((v, i) => v + (b[i] - v) * k);
function camAt(t) { let k = eio(clamp((t - 3.2) / 2.6)) - eio(clamp((t - 15.8) / 3.2)); const sw = .05 * Math.sin(t * .35);
  const e = lerp(C_WIDE.eye, C_CLOSE.eye, k), g = lerp(C_WIDE.target, C_CLOSE.target, k); return { eye: [e[0] + sw, e[1], e[2]], target: g, fov: .6, up: [0, 0, 1] }; }
window.setT = t => {
  const cam = camAt(t);
  const kk = .3 + .7 * eio(clamp((t - 3.4) / 9.6)), rest = eio(clamp((t - 13.3) / 1.8));
  S.draw(cam, { filter: p => p.lower, L1: cam.eye.map((v, i) => v - cam.target[i]).map((v, i) => i === 0 ? v + .6 : v), expo: .6, caries: p => p === MOL ? { c: [...CC, .13], k: t < 3.4 ? .3 : kk, r: rest } : null });
  const q = S.project(cam, CC);
  dots.forEach((d, i) => { const on = t > 6.6 && t < 13.0; const a = i * 2.39 + t * (1.2 + (i % 5) * .3), rr = 30 + (i * 37) % 90 + 10 * Math.sin(t * 3 + i);
    d.style.width = d.style.height = (8 + i % 4 * 3) + 'px'; d.style.background = i % 3 ? 'rgba(150,230,90,.85)' : 'rgba(210,250,120,.9)'; d.style.boxShadow = '0 0 10px rgba(160,240,90,.8)';
    d.style.left = (q[0] + Math.cos(a) * rr) + 'px'; d.style.top = (q[1] + Math.sin(a) * rr * .7) + 'px'; d.style.opacity = on ? clamp((t - 6.6) / .5) * clamp((13 - t) / .5) * .9 : 0; });
  ui(t, cam, STARP, 15.3);
};''')

# ------------------------------------------------------------------ SISO
PAGES['siso3d.html'] = ('Você já tirou o <span class="k">siso</span>?', r'''
const CAPS = [
  [0.2, 3.4, 'O <span class="k">siso</span> é o último dente a nascer.'],
  [3.4, 6.6, 'Muitas vezes, falta <span class="k">espaço</span> na arcada.', 'small'],
  [6.6, 9.8, 'Ele fica <span class="k">preso</span> no osso ou nasce torto.', 'small'],
  [9.8, 13.0, 'Isso pode causar dor e <span class="k">inflamação</span>.', 'small'],
  [13.0, 16.2, 'Quando indicado, a <span class="k">extração</span> resolve.', 'small'],
  [16.2, 19.4, 'Só o dentista avalia, com <span class="k">radiografia</span>.', 'small'],
];
const FIM = 19.4; window.DUR = 23.4;
''', r'''
let SISO = null, PIV = null, STARP = [], M2 = null;
window.EVENTS = () => { const ev = [{ t: .1, k: 'hook' }]; CAPS.slice(1).forEach(c => ev.push({ t: c[0], k: 'whoosh' }));
  ev.push({ t: 3.6, k: 'sweep', d: 1.2 }); ev.push({ t: 7.0, k: 'move', d: 5.5 }); ev.push({ t: 13.4, k: 'wire', d: 1.6 }); ev.push({ t: 15.0, k: 'pop' });
  [16.4, 16.9].forEach(t => ev.push({ t, k: 'sparkle' })); ev.push({ t: FIM, k: 'fim' }); return { dur: DUR, estilo: 'cinema', events: ev.sort((a, b) => a.t - b.t) }; };
window.ready = (async () => { window.S = await LOAD();
  const teeth = S.prims.filter(p => !p.gum && p.cejY !== undefined);
  const right = teeth.filter(p => p.lower && p.center[0] > 0).sort((a, b) => a.center[2] - b.center[2]);
  SISO = right[0]; M2 = right[1]; PIV = [SISO.center[0], SISO.min[1] + .04, SISO.center[2] - .02];
  STARP = [[M2.center[0] + .1, M2.max[1] - .02, M2.center[2]], [SISO.center[0] + .1, SISO.cejY + .02, SISO.center[2]]];
  return true; })();
const SIS = k => M4.mul(T([0, -.14 * k, .0]), about(PIV, rotAxis([1, 0, 0], SGN * .7 * k)));
let SGN = 1;
function camAt(t) { const yaw = 1.25 + .06 * Math.sin(t * .3) - .15 * eio(clamp((t - 15.5) / 3.5)); const dist = 3.1 - .4 * eio(clamp((t - 3.2) / 3)) + .5 * eio(clamp((t - 15) / 3));
  const tg = [.98, .9, 1.42]; return { eye: [tg[0] + Math.sin(yaw) * dist, tg[1] + .45, tg[2] + Math.cos(yaw) * dist], target: tg, fov: .55 }; }
window.setT = t => {
  const cam = camAt(t);
  const xr = clamp((t - 3.6) / 1.2) * (1 - clamp((t - 15.4) / 1.0));       // gengiva translúcida (raio-X)
  const ex = eio(clamp((t - 13.4) / 1.6));                                   // extração
  S.draw(cam, { filter: p => p.lower && p.gum !== 2 && p.gum !== 3, L1: [.5, .6, .5], expo: .74,
    xform: p => p === SISO ? (ex >= .999 ? HIDE : M4.mul(T([.02 * ex, .75 * ex, 0]), M4.mul(about(PIV, rotAxis([0, 0, 1], -.4 * ex)), SIS(1)))) : M4.id(),
    alpha: p => p.gum ? 1 - .72 * xr : (p === SISO ? 1 - ex : 1),
    xray: p => (!p.gum && xr > 0) ? [1, .55 * xr, 0] : null });
  const g = document.getElementById('glow'); const q = S.project(cam, [M2.center[0], M2.cejY - .05, M2.center[2] - .2]);
  g.style.left = q[0] + 'px'; g.style.top = q[1] + 'px'; g.style.background = 'radial-gradient(circle,rgba(255,70,60,.7),rgba(255,40,40,0) 65%)';
  g.style.opacity = t > 6.8 && t < 13.2 ? (.6 + .4 * Math.sin((t - 6.8) * 5)) * clamp((t - 6.8) / .4) * clamp((13.2 - t) / .4) : 0;
  ui(t, cam, STARP, 16.4);
};''')

# ------------------------------------------------------------------ GENGIVITE + FIO DENTAL
PAGES['gengivite3d.html'] = ('Você usa <span class="k">fio dental</span> todo dia?', r'''
const CAPS = [
  [0.2, 3.4, 'Gengiva <span class="k">sangrando</span> ao escovar?'],
  [3.4, 6.6, 'Pode ser <span class="k">gengivite</span>: inflamação da gengiva.', 'small'],
  [6.6, 9.8, 'A placa entre os dentes é a <span class="k">principal causa</span>.', 'small'],
  [9.8, 13.6, 'O <span class="k">fio dental</span> limpa onde a escova não chega.', 'small'],
  [13.6, 16.6, 'Com a limpeza certa, a gengiva <span class="k">desinflama</span>.', 'small'],
  [16.6, 19.6, 'Se o sangramento continuar, <span class="k">procure seu dentista</span>.', 'small'],
];
const FIM = 19.6; window.DUR = 23.6; const FLOSS = [9.9, 13.5];
''', r'''
let GAPS = [], FL = null, STARP = [];
window.EVENTS = () => { const ev = [{ t: .1, k: 'hook' }]; CAPS.slice(1).forEach(c => ev.push({ t: c[0], k: 'whoosh' }));
  for (let i = 0; i < 5; i++) ev.push({ t: FLOSS[0] + i * (FLOSS[1] - FLOSS[0]) / 5 + .15, k: 'wire', d: .45 });
  [14.0, 14.5, 15.0].forEach(t => ev.push({ t, k: 'sparkle' })); ev.push({ t: FIM, k: 'fim' }); return { dur: DUR, estilo: 'lofi', events: ev.sort((a, b) => a.t - b.t) }; };
window.ready = (async () => { window.S = await LOAD();
  const teeth = S.prims.filter(p => !p.gum && p.cejY !== undefined);
  const up = teeth.filter(p => !p.lower && p.center[2] > 2.15).sort((a, b) => a.center[0] - b.center[0]);
  for (let i = 0; i < up.length - 1; i++) { const a = up[i], b = up[i+1]; const mx = (a.center[0] + b.center[0]) / 2; if (Math.abs(mx) > .5) continue;
    const o = outward({ center: [mx, 0, (a.center[2] + b.center[2]) / 2] }, .06); GAPS.push({ x: mx, z: o[2], xo: o[0], ytop: (a.cejY + b.cejY) / 2 - .02, ybot: (a.cejY + b.cejY) / 2 - Math.min(a.crownH, b.crownH) * .85 }); }
  STARP = up.filter(p => Math.abs(p.center[0]) < .5).map(p => { const o = outward(p, .12); return [o[0], p.cejY - p.crownH * .5, o[2]]; });
  FL = S.add({ name: 'FLOSS', gum: 5, color: [1.05, 1.05, 1.08], pos: new Float32Array(3), nor: new Float32Array(3), idx: new Uint32Array(0) });
  return true; })();
function camAt(t) { const yaw = .18 * Math.sin(t * .22) - .05; const dist = 5.9 - .6 * eio(clamp((t - 6.4) / 3)) + .6 * eio(clamp((t - 13.6) / 3)); const tg = [0, 1.18, 2.45];
  return { eye: [tg[0] + Math.sin(yaw) * dist, tg[1] + .02, tg[2] + Math.cos(yaw) * dist], target: tg, fov: .42 }; }
window.setT = t => {
  const cam = camAt(t);
  // fio dental: passa de espaço em espaço, da esquerda para a direita
  const fp = clamp((t - FLOSS[0]) / (FLOSS[1] - FLOSS[0])); const gi = Math.min(GAPS.length - 1, Math.floor(fp * GAPS.length)); const lp = fp * GAPS.length - gi;
  const on = t > FLOSS[0] - .3 && t < FLOSS[1] + .3; let sweep = t < FLOSS[0] ? -1e3 : (t > FLOSS[1] ? 1e3 : GAPS[gi].x - .12 + lp * .2);
  if (on && GAPS.length) { const G = GAPS[gi]; const dip = Math.sin(clamp(lp) * Math.PI); const y = G.ybot + (G.ytop - G.ybot) * dip; const tz = G.z - .02;
    const g = tube([[G.x - .42, y - .05, tz + .55], [G.x - .05, y, tz + .03], [G.x, y + .004, tz - .02], [G.x + .05, y, tz + .03], [G.x + .42, y - .05, tz + .55]], .0085);
    FL.pos = g.pos; FL.nor = g.nor; FL.idx = g.idx; FL.hidden = false; S.update(FL); } else FL.hidden = true;
  S.draw(cam, { L1: [.25, .45, .9], expo: .72, infl: 1, dirt: .85, sweep, band: p => .07 });
  // gotinhas de sangue na gengiva inflamada (início)
  dots.forEach((d, i) => { const G = GAPS[i % Math.max(1, GAPS.length)]; if (!G) return; const q = S.project(cam, [G.x + ((i * 13) % 7 - 3) * .006, G.ytop + .015, G.z + .02]); const ph = (t * .6 + i * .37) % 1;
    d.style.width = d.style.height = (6 + i % 3 * 3) + 'px'; d.style.background = 'rgba(200,20,30,.9)'; d.style.boxShadow = 'none';
    d.style.left = (q[0] + (i % 5 - 2) * 4) + 'px'; d.style.top = (q[1] + ph * 26) + 'px'; d.style.opacity = t < 6.4 && i < 10 ? (1 - ph) * clamp((t - .6) / .5) * clamp((6.4 - t) / .5) : 0; });
  ui(t, cam, STARP, 14.0);
};''')

# ------------------------------------------------------------------ ALINHADOR
PAGES['alinhador3d.html'] = ('Você usaria <span class="k">alinhador</span>?', r'''
const CAPS = [
  [0.2, 3.4, 'Aparelho <span class="k">invisível</span>?'],
  [3.4, 6.6, 'São placas <span class="k">transparentes</span>, feitas sob medida.', 'small'],
  [6.6, 10.2, 'Cada placa move os dentes <span class="k">um pouquinho</span>.', 'small'],
  [10.2, 13.8, 'De tempos em tempos, você troca para a <span class="k">próxima</span>.', 'small'],
  [13.8, 17.0, 'Dá para tirar para <span class="k">comer</span> e escovar.', 'small'],
  [17.0, 20.2, 'O dentista avalia se o seu caso <span class="k">permite</span>.', 'small'],
];
const FIM = 20.2; window.DUR = 24.2; const MOVE = [6.6, 13.8];
''', r'''
const MIS = { U: [[.35, .1, .16, 0], [-.5, -.2, -.2, -.03], [.3, .3, .22, .05], [.2, 0, .1, 0], [-.12, .03, 0, 0]],
              U2: [[-.2, .16, -.14, .02], [.45, -.18, .2, -.02], [-.35, .26, -.24, .05], [-.22, 0, -.1, 0], [.14, -.02, 0, 0]],
              L: [[.6, .1, .2, .02], [-.4, -.2, -.18, -.02], [.35, .18, .16, .03], [.16, 0, .06, 0], [0, 0, 0, 0]],
              L2: [[-.5, -.16, -.22, -.02], [.45, .14, .2, .02], [-.28, .16, -.18, .03], [-.18, 0, -.06, 0], [0, 0, 0, 0]] };
const ZC = .9; let SHELLS = [], STARP = [];
const X = (p, k) => { if (!p.mis || k <= 0) return M4.id(); const [rv, tip, md, dy] = p.mis.map(v => v * k); const Pv = [p.center[0], p.cejY, p.center[2]];
  const rad = norm([p.center[0], 0, p.center[2] - ZC]), tg = cross([0,1,0], rad);
  return M4.mul(T([0, (p.lower ? 1 : -1) * dy, 0]), about(Pv, M4.mul(rotAxis([0,1,0], rv), M4.mul(rotAxis(tg, tip), rotAxis(rad, md))))); };
window.EVENTS = () => { const ev = [{ t: .1, k: 'hook' }]; CAPS.slice(1).forEach(c => ev.push({ t: c[0], k: 'whoosh' }));
  ev.push({ t: 3.7, k: 'sweep', d: 1.4 }); ev.push({ t: MOVE[0], k: 'move', d: MOVE[1] - MOVE[0] }); for (let i = 1; i < 6; i++) ev.push({ t: MOVE[0] + i * 1.2, k: 'click' });
  ev.push({ t: 14.0, k: 'wire', d: 1.0 }); [17.2, 17.6, 18.0].forEach(t => ev.push({ t, k: 'sparkle' })); ev.push({ t: FIM, k: 'fim' }); return { dur: DUR, estilo: 'pop', events: ev.sort((a, b) => a.t - b.t) }; };
window.ready = (async () => { window.S = await LOAD();
  const teeth = S.prims.filter(p => !p.gum && p.cejY !== undefined);
  for (const lower of [false, true]) for (const side of [1, -1]) {
    teeth.filter(p => p.lower === lower && Math.sign(p.center[0]) === side && p.center[2] > 2.0).sort((a, b) => Math.abs(a.center[0]) - Math.abs(b.center[0]))
      .forEach((p, i) => { p.mis = (lower ? (side > 0 ? MIS.L : MIS.L2) : (side > 0 ? MIS.U : MIS.U2))[i] || [0,0,0,0]; }); }
  teeth.filter(p => p.center[2] > 1.7).forEach(p => { const sh = Object.assign({}, p, { shell: true, parent: p, name: 'SHELL' }); S.prims.push(sh); SHELLS.push(sh); });
  STARP = teeth.filter(p => p.center[2] > 2.35).sort((a, b) => Math.abs(a.center[0]) - Math.abs(b.center[0])).slice(0, 5).map(p => { const o = outward(p, .12); return [o[0], p.cejY + (p.lower ? 1 : -1) * p.crownH * .5, o[2]]; });
  return true; })();
function camAt(t) { const yaw = -.25 + .1 * Math.sin(t * .25) + (t > 16.6 ? .5 * eio(clamp((t - 16.6) / 4)) : 0);
  const dist = 6.6 - .7 * eio(clamp((t - 6.2) / 2)) + .9 * eio(clamp((t - 13.6) / 2.5)); const tg = [0, 1.13, 2.4];
  return { eye: [tg[0] + Math.sin(yaw) * dist, tg[1] + .15, tg[2] + Math.cos(yaw) * dist], target: tg, fov: .42 }; }
window.setT = t => {
  const cam = camAt(t);
  const k = 1 - eio(clamp((t - MOVE[0]) / (MOVE[1] - MOVE[0])));
  const sin_ = eio(clamp((t - 3.7) / 1.3)), sout = eio(clamp((t - 14.0) / 1.0));   // placa entra / sai
  const placa = Math.max(1, Math.min(20, Math.round(1 + 19 * clamp((t - MOVE[0]) / (MOVE[1] - MOVE[0])))));
  const blink = t > MOVE[0] && t < MOVE[1] ? 1 - .5 * Math.pow(Math.max(0, Math.sin(((t - MOVE[0]) / (MOVE[1] - MOVE[0])) * Math.PI * 19)), 30) : 1;
  S.draw(cam, { L1: [.25, .45, .9], expo: .72,
    xform: p => { if (p.shell) { const par = p.parent; const off = (par.lower ? -1 : 1) * (.3 * (1 - sin_) + .4 * sout); const c = par.center;
        return M4.mul(T([0, off, 0]), M4.mul(X(par, k), about(c, [1.04,0,0,0, 0,1.03,0,0, 0,0,1.05,0, 0,0,0,1]))); }
      return p.gum ? M4.id() : X(p, k); },
    alpha: p => p.shell ? .3 * sin_ * (1 - sout) * blink : 1,
    clip: p => p.shell ? [1, p.parent.cejY + (p.parent.lower ? 1 : -1) * .005, p.parent.lower ? 1 : -1] : null,
    xray: p => p.shell ? [1, .7, 0] : null });
  const mes = document.getElementById('mes'); mes.style.opacity = t > MOVE[0] - .2 && t < MOVE[1] + .8 ? clamp((t - MOVE[0] + .2) / .3) * clamp((MOVE[1] + .8 - t) / .4) : 0;
  document.getElementById('mesn').textContent = 'PLACA ' + placa; document.getElementById('mesb').style.width = clamp((t - MOVE[0]) / (MOVE[1] - MOVE[0])) * 100 + '%';
  ui(t, cam, STARP, 17.2);
};''')

for name, (endq, pre, post) in PAGES.items():
    h = HEAD.replace('Você <span class="k">usaria aparelho</span>?', endq)
    open('/home/claude/semana/' + name, 'w').write(h + '<script>' + pre + '</script>\n' + COMMON.replace('<script src="dental3d.js"></script>\n<script>', '<script src="dental3d.js"></script>\n<script>') + post + '\n</script>\n</body></html>')
print('ok', list(PAGES))
