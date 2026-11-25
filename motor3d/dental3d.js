// Renderizador WebGL2 mínimo para GLB (sem bibliotecas externas)
const M4 = {
  id: () => [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1],
  mul(a, b) { const o = new Array(16); for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) { let s = 0; for (let k = 0; k < 4; k++) s += a[k*4 + r] * b[c*4 + k]; o[c*4 + r] = s; } return o; },
  trs(t, q, s) { t = t || [0,0,0]; q = q || [0,0,0,1]; s = s || [1,1,1]; const [x,y,z,w] = q;
    return [(1-2*(y*y+z*z))*s[0], 2*(x*y+z*w)*s[0], 2*(x*z-y*w)*s[0], 0,
            2*(x*y-z*w)*s[1], (1-2*(x*x+z*z))*s[1], 2*(y*z+x*w)*s[1], 0,
            2*(x*z+y*w)*s[2], 2*(y*z-x*w)*s[2], (1-2*(x*x+y*y))*s[2], 0, t[0], t[1], t[2], 1]; },
  persp(fov, asp, n, f) { const t = 1 / Math.tan(fov/2); return [t/asp,0,0,0, 0,t,0,0, 0,0,(f+n)/(n-f),-1, 0,0,2*f*n/(n-f),0]; },
  look(e, c, u) { const sub = (a,b) => a.map((v,i) => v - b[i]), nrm = a => { const l = Math.hypot(...a); return a.map(v => v/l); }, crs = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]], dot = (a,b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
    const z = nrm(sub(e, c)), x = nrm(crs(u, z)), y = crs(z, x);
    return [x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0, -dot(x,e),-dot(y,e),-dot(z,e),1]; },
  apply(m, p) { return [0,1,2].map(i => m[i]*p[0] + m[4+i]*p[1] + m[8+i]*p[2] + m[12+i]); },
};

async function loadGLB(url) {
  const buf = await (await fetch(url)).arrayBuffer(); const dv = new DataView(buf); console.log('glb bytes', buf.byteLength);
  const jlen = dv.getUint32(12, true); const json = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, jlen)));
  const binOff = 20 + jlen + 8;
  const view = i => { const bv = json.bufferViews[i]; return { off: binOff + (bv.byteOffset || 0), len: bv.byteLength, stride: bv.byteStride || 0 }; };
  const SZ = { SCALAR:1, VEC2:2, VEC3:3, VEC4:4 }, CT = { 5126: Float32Array, 5125: Uint32Array, 5123: Uint16Array, 5121: Uint8Array };
  const acc = i => { const a = json.accessors[i], v = view(a.bufferView), T = CT[a.componentType], n = SZ[a.type];
    const off = v.off + (a.byteOffset || 0);
    if (!v.stride || v.stride === n * T.BYTES_PER_ELEMENT) return new T(buf.slice(off, off + a.count * n * T.BYTES_PER_ELEMENT));
    const out = new T(a.count * n), src = new DataView(buf); const get = T === Float32Array ? 'getFloat32' : T === Uint32Array ? 'getUint32' : T === Uint16Array ? 'getUint16' : 'getUint8';
    for (let k = 0; k < a.count; k++) for (let c = 0; c < n; c++) out[k*n + c] = src[get](off + k*v.stride + c*T.BYTES_PER_ELEMENT, true); return out; };
  const images = await Promise.all((json.images || []).map(async im => { const v = view(im.bufferView); if (v.off + v.len > buf.byteLength) return null; try { return await createImageBitmap(new Blob([new Uint8Array(buf, v.off, v.len)], { type: im.mimeType }), { imageOrientation: 'none' }); } catch (e) { return null; } }));
  for (let i = 0; i < images.length; i++) if (!images[i]) images[i] = images[i-1] || images[i+1];
  const prims = [];
  const walk = (ni, parent) => { const n = json.nodes[ni]; const local = n.matrix || M4.trs(n.translation, n.rotation, n.scale); const w = M4.mul(parent, local);
    if (n.mesh !== undefined) json.meshes[n.mesh].primitives.forEach(p => { const mat = json.materials[p.material] || {}; const bct = mat.pbrMetallicRoughness && mat.pbrMetallicRoughness.baseColorTexture;
      prims.push({ name: n.name || '', model: w, pos: acc(p.attributes.POSITION), nor: acc(p.attributes.NORMAL), uv: p.attributes.TEXCOORD_0 !== undefined ? acc(p.attributes.TEXCOORD_0) : null,
        idx: p.indices !== undefined ? acc(p.indices) : null, img: bct ? images[json.textures[bct.index].source] : null }); });
    (n.children || []).forEach(c => walk(c, w)); };
  (json.scenes[json.scene || 0].nodes).forEach(n => walk(n, M4.id()));
  return prims;
}

const VS = `#version 300 es
in vec3 aP; in vec3 aN; in vec2 aU; uniform mat4 uM, uVP, uMb; out vec3 vW; out vec3 vN; out vec2 vU; out vec3 vL; out vec3 vW0;
void main(){ vec4 w = uM * vec4(aP,1.); vW = w.xyz; vN = normalize(mat3(uM) * aN); vU = aU; vL = aP; vW0 = (uMb * vec4(aP,1.)).xyz; gl_Position = uVP * w; }`;
const FS = `#version 300 es
precision highp float; in vec3 vW; in vec3 vN; in vec2 vU; in vec3 vL; in vec3 vW0; out vec4 o; uniform vec3 uClip;
uniform sampler2D uT; uniform int uHasT; uniform vec3 uEye; uniform float uDirt; uniform float uSweep; uniform float uGlow; uniform vec4 uCEJ; uniform vec3 uTint; uniform int uGum; uniform float uInfl; uniform float uExpo; uniform float uCrown; uniform float uBand; uniform vec3 uL1; uniform float uAlpha; uniform vec4 uCar; uniform float uCarK; uniform float uRest; uniform vec3 uXray;
float h(vec3 p){ return fract(sin(dot(p, vec3(127.1,311.7,74.7))) * 43758.5453); }
float n3(vec3 p){ vec3 i = floor(p), f = fract(p); f = f*f*(3.-2.*f);
  return mix(mix(mix(h(i),h(i+vec3(1,0,0)),f.x), mix(h(i+vec3(0,1,0)),h(i+vec3(1,1,0)),f.x), f.y), mix(mix(h(i+vec3(0,0,1)),h(i+vec3(1,0,1)),f.x), mix(h(i+vec3(0,1,1)),h(i+vec3(1,1,1)),f.x), f.y), f.z); }
float fbm(vec3 p){ float s = 0., a = .5; for(int i=0;i<5;i++){ s += a*n3(p); p *= 2.03; a *= .5; } return s; }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14), 0., 1.); }
float ggx(vec3 N, vec3 V, vec3 L, float r){ vec3 H = normalize(V+L); float a = r*r, a2 = a*a; float nh = max(dot(N,H),0.); float d = nh*nh*(a2-1.)+1.; float D = a2/(3.14159*d*d);
  float nl = max(dot(N,L),0.), nv = max(dot(N,V),.001); float k = (r+1.)*(r+1.)/8.; float G = nl/(nl*(1.-k)+k) * nv/(nv*(1.-k)+k); float F = .045 + .955*pow(1.-max(dot(H,V),0.),5.); return D*G*F/(4.*nv+.0001)*nl; }
void main(){
  if (uClip.x > .5 && (vW0.y - uClip.y) * uClip.z < -.002) discard;
  vec3 N = normalize(vN); vec3 V = normalize(uEye - vW); if (dot(N,V) < 0.) N = -N;
  vec3 base = uHasT == 1 ? pow(texture(uT, vU).rgb, vec3(2.2)) : vec3(.92,.89,.82);
  base *= uTint;
  float rough0 = .32; float sssAmt = .25; vec3 sssCol = vec3(1.,.75,.55);
  if (uGum >= 1) {
    float infl = uInfl * smoothstep(uSweep - .25, uSweep + .25, vW.x);
    float nz = fbm(vW*14.), vein = fbm(vW*40.);
    if (uGum == 2) { base = pow(vec3(.70,.30,.34), vec3(2.2)); } if (uGum == 3) { base = pow(vec3(.40,.11,.13), vec3(2.2)); }
    vec3 healthy = vec3(.86,.45,.47), inflamed = vec3(.74,.27,.3);
    if (uGum == 1) base = pow(mix(healthy, inflamed, infl), vec3(2.2)) * (.85 + .3*nz) * (1. - .12*smoothstep(.55,.75,vein));
    else base *= (.8 + .35*nz);
    // pontilhado (casca de laranja) na gengiva saudável
    if (uGum == 1) { vec3 g = vec3(fbm(vW*55.+1.), fbm(vW*55.+7.), fbm(vW*55.+3.)) - .5; N = normalize(N + g * .12 * (1. - infl)); }
    rough0 = uGum == 1 ? mix(.4, .3, infl) : .55; sssAmt = .6; sssCol = vec3(1.,.35,.3);
  }
  // sujeira: faixa perto da junção coroa-raiz (uCEJ: altura y, largura, direção +1/-1, ativa)
  float rough = rough0, wet = uGum >= 2 ? .25 : 1.;
  if (uCEJ.w > .5) {
    float d = (vW.y - uCEJ.x) * uCEJ.z;            // >0 = em direção à coroa
    float inc = smoothstep(uCrown*.72, uCrown*1.02, d);
    base = mix(base, base * vec3(.86,.88,.92), inc * .35);   // borda incisal translúcida
    sssCol = mix(sssCol, vec3(.6,.75,1.), inc);
    float band = uBand > 0. ? smoothstep(uBand, 0., d) * smoothstep(-.05, .05, d) : 0.;
    float nz = fbm(vW * 9.);
    float tart = smoothstep(.32, .52, nz * .8 + band * .6) * smoothstep(.0, .35, band);
    float clean = smoothstep(uSweep - .25, uSweep + .25, vW.x);  // 1 = ainda sujo
    float amt = uDirt * clean;
    vec3 stain = base * pow(vec3(1.0,.88,.62), vec3(2.2));
    base = mix(base, stain, amt * .8);
    vec3 tc = pow(mix(vec3(.80,.62,.30), vec3(.58,.40,.17), n3(vW*30.)), vec3(2.2));
    base = mix(base, tc, tart * amt);
    rough = mix(rough, .75, tart * amt); wet = 1. - tart * amt * .9;
    vec3 gr = vec3(fbm(vW*60.+2.), fbm(vW*60.+5.), fbm(vW*60.+9.)) - .5; N = normalize(N + gr * 1.3 * tart * amt);
    float ao = mix(.55, 1., smoothstep(-.01, .06, d)); base *= ao;   // sombra de contato junto da gengiva
  }
  if (uGum == 4) {
    vec3 R = reflect(-V, N); float env = mix(.04, 1.1, smoothstep(-.3, .7, R.y)) + .9*pow(max(dot(R, normalize(vec3(-.5,.4,.8))),0.), 24.);
    vec3 m = vec3(.78,.8,.84); vec3 Lm = normalize(uL1);
    vec3 cm = m * env * .9 + m * 3.5 * ggx(N,V,Lm,.22) + vec3(1.) * 1.5 * ggx(N,V,Lm,.08) + m * .12 * max(dot(N,Lm),0.);
    o = vec4(pow(aces(cm * uExpo), vec3(1./2.2)), uAlpha); return;
  }
  if (uCar.w > 0.) {
    float dc = length(vW0 - uCar.xyz) / uCar.w; float edge = fbm(vW0 * 26.) * .55;
    float les = smoothstep(uCarK + .05, uCarK - .15, dc + edge * .6) * step(.01, uCarK);
    float rest = les * uRest;
    vec3 brown = pow(mix(vec3(.55,.36,.16), vec3(.24,.14,.06), smoothstep(.55, 1., les)), vec3(2.2));
    base = mix(base, brown, les * (1. - uRest));
    base = mix(base, pow(vec3(.93,.91,.86), vec3(2.2)), rest);
    vec3 gc = vec3(fbm(vW0*80.+3.), fbm(vW0*80.+8.), fbm(vW0*80.+1.)) - .5; N = normalize(N + gc * 1.4 * les * (1. - uRest));
    rough = mix(rough, .7, les * (1. - uRest));
  }
  vec3 L1 = normalize(uL1), L2 = normalize(vec3(-.8,.15,.4)), L3 = normalize(vec3(.1,.6,-.9));
  vec3 C1 = vec3(1.,.97,.92)*2.2, C2 = vec3(.75,.85,1.)*.55, C3 = vec3(.6,.9,1.)*1.4;
  float w = .18;
  vec3 dif = base * (C1*max((dot(N,L1)+w)/(1.+w),0.) + C2*max((dot(N,L2)+w)/(1.+w),0.) + C3*max(dot(N,L3),0.)*.4);
  dif += base * mix(vec3(.05,.055,.065), vec3(.13,.12,.115), N.y*.5+.5);           // ambiente
  float sss = pow(1. - max(dot(N,V),0.), 2.) * sssAmt; dif += base * sssCol * sss;   // translucidez
  vec3 spec = (C1*ggx(N,V,L1,rough) + C2*ggx(N,V,L2,rough) + C3*ggx(N,V,L3,rough)) * wet;
  spec += C1 * ggx(N,V,L1,.09) * .35 * wet;                                       // brilho molhado
  float rim = pow(1. - max(dot(N,V),0.), 4.) * .5;
  vec3 col = dif + spec + C3 * rim * .25 + uGlow * vec3(.6,1.,.95) * .4;
  vec3 outc = pow(aces(col * uExpo), vec3(1./2.2));
  if (uXray.x > .5) { float fr = pow(1. - max(dot(N,V),0.), 1.5); outc = mix(outc, vec3(.55,.85,1.) * (.35 + fr), uXray.y); }
  o = vec4(outc, uAlpha);
}`;


function buildGum(teeth, lower, P) {
  P = Object.assign({ crown: .43, depth: .8, pap: .075, thick: .03, bulge: .06, zc: .9 }, P || {});
  const info = teeth.map(p => {
    const h = p.max[1] - p.min[1]; const cej = lower ? p.max[1] - P.crown*h : p.min[1] + P.crown*h;
    let rmin = 1e9, rmax = -1e9;
    for (let i = 0; i < p.pos.length; i += 9) { const w = M4.apply(p.model, [p.pos[i], p.pos[i+1], p.pos[i+2]]); if (Math.abs(w[1] - cej) < .05) { const r = Math.hypot(w[0], w[2] - P.zc); rmin = Math.min(rmin, r); rmax = Math.max(rmax, r); } }
    p.cejY = cej; p.crownH = P.crown * h;
    return { th: Math.atan2(p.center[0], p.center[2] - P.zc), cej, rmin, rmax };
  }).filter(t => t.rmax > 0).sort((a, b) => a.th - b.th);
  const at = th => { let i = 0; while (i < info.length - 2 && info[i+1].th < th) i++; const a = info[i], b = info[i+1]; let u = (th - a.th) / (b.th - a.th); const uc = Math.max(0, Math.min(1, u)); const k = .5 - .5*Math.cos(Math.PI*uc);
    const lerp = f => a[f] + (b[f] - a[f]) * k; const pap = (u >= 0 && u <= 1) ? P.pap * Math.pow(Math.sin(Math.PI*u), 4) : 0; return { cej: lerp('cej'), rmin: lerp('rmin'), rmax: lerp('rmax'), pap }; };
  const NS = 420, NV = 36, dir = lower ? -1 : 1; const th0 = info[0].th - .3, th1 = info[info.length-1].th + .3;
  const pos = [], idx = [];
  const ring = (side) => { const base = pos.length / 3;
    for (let i = 0; i <= NS; i++) { const th = th0 + (th1 - th0) * i/NS; const A = at(th); const m = A.cej - dir * A.pap;
      for (let j = 0; j <= NV; j++) { const v = j/NV; const roll = Math.sqrt(Math.min(1, v/.06)); const y = m + dir * P.depth * v;
        const r = side > 0 ? A.rmax + P.thick*roll + P.bulge*Math.min(1, v/.4) : A.rmin - P.thick*roll - P.bulge*1.6*Math.min(1, v/.3);
        pos.push(Math.sin(th)*r, y, P.zc + Math.cos(th)*r); } }
    for (let i = 0; i < NS; i++) for (let j = 0; j < NV; j++) { const a = base + i*(NV+1) + j, b = a + NV + 1; side > 0 ? idx.push(a, b, a+1, b, b+1, a+1) : idx.push(a, a+1, b, b, a+1, b+1); }
    return base; };
  const o = ring(1), n = ring(-1);
  for (let i = 0; i < NS; i++) { const a = o + i*(NV+1), b = o + (i+1)*(NV+1), c = n + i*(NV+1), d = n + (i+1)*(NV+1); idx.push(a, c, b, b, c, d); }
  const nor = new Float32Array(pos.length);
  for (let k = 0; k < idx.length; k += 3) { const [a, b, c] = [idx[k], idx[k+1], idx[k+2]]; const A = pos.slice(a*3, a*3+3), B = pos.slice(b*3, b*3+3), C = pos.slice(c*3, c*3+3);
    const u = [B[0]-A[0], B[1]-A[1], B[2]-A[2]], v = [C[0]-A[0], C[1]-A[1], C[2]-A[2]]; const nn = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]];
    for (const q of [a, b, c]) for (let t = 0; t < 3; t++) nor[q*3+t] += nn[t]; }
  return { name: lower ? 'GUM_L' : 'GUM_U', gum: true, lower, model: M4.id(), pos: new Float32Array(pos), nor, uv: null, idx: new Uint32Array(idx), img: null, info };
}

async function initScene(canvas, url, opt) {
  const gl = canvas.getContext('webgl2', { antialias: true, preserveDrawingBuffer: true });
  const sh = (t, s) => { const x = gl.createShader(t); gl.shaderSource(x, s); gl.compileShader(x); if (!gl.getShaderParameter(x, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(x); return x; };
  const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(pr);
  let prims = (await loadGLB(url)).filter(p => true);
  // descarta superfícies planas (sem altura)
  prims = prims.filter(p => { let a = 1e9, b = -1e9; for (let i = 1; i < p.pos.length; i += 30) { const w = M4.apply(p.model, [p.pos[i-1], p.pos[i], p.pos[i+1]]); a = Math.min(a, w[1]); b = Math.max(b, w[1]); } return b - a > .05; });
  const U = n => gl.getUniformLocation(pr, n);
  const bb = { min: [1e9,1e9,1e9], max: [-1e9,-1e9,-1e9] };
  for (const p of prims) {
    p.vao = gl.createVertexArray(); gl.bindVertexArray(p.vao);
    const vb = (data, loc, n) => { const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, 0, 0); };
    vb(p.pos, gl.getAttribLocation(pr, 'aP'), 3); vb(p.nor, gl.getAttribLocation(pr, 'aN'), 3); if (p.uv) vb(p.uv, gl.getAttribLocation(pr, 'aU'), 2);
    if (p.idx) { const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); let ix = p.idx; if (ix instanceof Uint8Array) ix = new Uint16Array(ix); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, ix, gl.STATIC_DRAW); p.count = ix.length; p.itype = ix instanceof Uint32Array ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT; }
    else p.count = p.pos.length / 3;
    if (p.img) { p.tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, p.tex); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, p.img); gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); }
    // caixa e centro de cada dente em coordenadas do mundo
    const c = [0,0,0]; const pmin = [1e9,1e9,1e9], pmax = [-1e9,-1e9,-1e9];
    for (let i = 0; i < p.pos.length; i += 3 * 7) { const w = M4.apply(p.model, [p.pos[i], p.pos[i+1], p.pos[i+2]]); for (let k = 0; k < 3; k++) { pmin[k] = Math.min(pmin[k], w[k]); pmax[k] = Math.max(pmax[k], w[k]); bb.min[k] = Math.min(bb.min[k], w[k]); bb.max[k] = Math.max(bb.max[k], w[k]); } }
    p.min = pmin; p.max = pmax; p.center = pmin.map((v, k) => (v + pmax[k]) / 2);
    p.lower = p.center[1] < 1.2;
  }
  const setup = p => { p.vao = gl.createVertexArray(); gl.bindVertexArray(p.vao);
    const vb = (data, loc, n) => { const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, n, gl.FLOAT, false, 0, 0); };
    vb(p.pos, gl.getAttribLocation(pr, 'aP'), 3); vb(p.nor, gl.getAttribLocation(pr, 'aN'), 3);
    const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, p.idx, gl.STATIC_DRAW); p.count = p.idx.length; p.itype = gl.UNSIGNED_INT; };
  const ell = (c, r) => { const pos = [], nor = [], idx = []; const A = 64, B = 32;
    for (let i = 0; i <= B; i++) { const v = i / B * Math.PI; for (let j = 0; j <= A; j++) { const u = j / A * 2 * Math.PI; const n = [Math.sin(v)*Math.cos(u), Math.cos(v), Math.sin(v)*Math.sin(u)];
      pos.push(c[0] + r[0]*n[0], c[1] + r[1]*n[1], c[2] + r[2]*n[2]); nor.push(n[0]/r[0], n[1]/r[1], n[2]/r[2]); } }
    for (let i = 0; i < B; i++) for (let j = 0; j < A; j++) { const a = i*(A+1) + j, b = a + A + 1; idx.push(a, b, a+1, b, b+1, a+1); }
    return { name: 'TONGUE', gum: 2, lower: true, model: M4.id(), pos: new Float32Array(pos), nor: new Float32Array(nor), idx: new Uint32Array(idx) }; };
  const gums = [buildGum(prims.filter(p => p.lower), true, opt && opt.gumL), buildGum(prims.filter(p => !p.lower), false, opt && opt.gumU)];
  gums.push(ell([0, .5, 1.55], [.6, .09, .8]));
  { const pos = new Float32Array([-6,.5,-4, 6,.5,-4, 6,.5,8, -6,.5,8]); gums.push({ name: 'FLOOR', gum: 3, lower: true, model: M4.id(), pos, nor: new Float32Array([0,1,0, 0,1,0, 0,1,0, 0,1,0]), idx: new Uint32Array([0,2,1, 0,3,2]) }); }
  gums.forEach(g => { setup(g); prims.push(g); });
  const upload = p => { if (!p.vao) { p.vao = gl.createVertexArray(); p.bufs = [gl.createBuffer(), gl.createBuffer(), gl.createBuffer()]; }
    gl.bindVertexArray(p.vao);
    [[p.pos, 'aP'], [p.nor, 'aN']].forEach(([d, n], k) => { gl.bindBuffer(gl.ARRAY_BUFFER, p.bufs[k]); gl.bufferData(gl.ARRAY_BUFFER, d, gl.DYNAMIC_DRAW); const l = gl.getAttribLocation(pr, n); gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, 3, gl.FLOAT, false, 0, 0); });
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, p.bufs[2]); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, p.idx, gl.DYNAMIC_DRAW); p.count = p.idx.length; p.itype = gl.UNSIGNED_INT; };
  return {
    gl, prims, bb,
    add(p) { p.model = p.model || M4.id(); upload(p); prims.push(p); return p; },
    update(p) { upload(p); },
    project(cam, pt) { const VP = M4.mul(M4.persp(cam.fov || .6, canvas.width / canvas.height, .05, 200), M4.look(cam.eye, cam.target, cam.up || [0,1,0])); const v = [0,1,2,3].map(i => VP[i]*pt[0] + VP[4+i]*pt[1] + VP[8+i]*pt[2] + VP[12+i]); const sc = (canvas.clientWidth || canvas.width) / canvas.width; return [(v[0]/v[3]*.5 + .5) * canvas.width * sc, (1 - (v[1]/v[3]*.5 + .5)) * canvas.height * sc]; },
    draw(cam, opts = {}) {
      gl.viewport(0, 0, canvas.width, canvas.height); gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); gl.enable(gl.DEPTH_TEST);
      gl.useProgram(pr);
      const VP = M4.mul(M4.persp(cam.fov || .6, canvas.width / canvas.height, .05, 200), M4.look(cam.eye, cam.target, cam.up || [0,1,0]));
      gl.uniformMatrix4fv(U('uVP'), false, VP); gl.uniform3fv(U('uEye'), cam.eye);
      gl.uniform1f(U('uDirt'), opts.dirt || 0); gl.uniform1f(U('uInfl'), opts.infl || 0); gl.uniform1f(U('uExpo'), opts.expo || .62); gl.uniform3fv(U('uL1'), opts.L1 || [.35,.55,.9]); gl.uniform1f(U('uSweep'), opts.sweep === undefined ? -1e3 : opts.sweep); gl.uniform1f(U('uGlow'), opts.glow || 0);
      const alphaOf = p => (opts.alpha ? opts.alpha(p) : 1);
      const pass = (list, blend) => { if (blend) { gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false); } else { gl.disable(gl.BLEND); gl.depthMask(true); }
      for (const p of list) {
        if (opts.filter && !opts.filter(p)) continue; if (p.hidden || p.count === 0) continue;
        const a = alphaOf(p); if (a <= .003) continue; gl.uniform1f(U('uAlpha'), a);
        const car = opts.caries && opts.caries(p); gl.uniform4fv(U('uCar'), car ? car.c : [0,0,0,0]); gl.uniform1f(U('uCarK'), car ? car.k : 0); gl.uniform1f(U('uRest'), car ? car.r : 0);
        gl.uniform3fv(U('uXray'), (opts.xray && opts.xray(p)) || [0,0,0]);
        const cej = opts.cej ? opts.cej(p) : null;
        gl.uniform4fv(U('uCEJ'), (p.gum || p.cejY === undefined) ? [0,0,0,0] : [p.cejY, 0, p.lower ? 1 : -1, 1]); gl.uniform1f(U('uCrown'), p.crownH || 0); gl.uniform1f(U('uBand'), (!p.gum && opts.band) ? opts.band(p) : 0);
        gl.uniform3fv(U('uTint'), p.color || (opts.tint ? opts.tint(p) : [1,.965,.9]));
        gl.uniformMatrix4fv(U('uM'), false, opts.xform ? M4.mul(opts.xform(p), p.model) : p.model); gl.uniformMatrix4fv(U('uMb'), false, p.model); gl.uniform3fv(U('uClip'), (opts.clip && opts.clip(p)) || [0,0,0]);
        gl.uniform1i(U('uGum'), p.gum === 5 ? 0 : (p.gum >= 2 ? p.gum : (p.gum ? 1 : 0))); gl.uniform1i(U('uHasT'), p.tex ? 1 : 0); if (p.tex) { gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, p.tex); gl.uniform1i(U('uT'), 0); }
        gl.bindVertexArray(p.vao); if (p.idx) gl.drawElements(gl.TRIANGLES, p.count, p.itype, 0); else gl.drawArrays(gl.TRIANGLES, 0, p.count);
      }
      };
      pass(prims.filter(p => alphaOf(p) >= .999), false); pass(prims.filter(p => alphaOf(p) < .999), true); gl.depthMask(true); gl.disable(gl.BLEND);
      gl.finish();
    },
  };
}
window.M4 = M4; window.initScene = initScene;
