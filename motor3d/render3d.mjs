// Renderiza uma página 3D (com window.ready) em vídeo. Uso: node render3d.mjs <pagina.html> <saida-sem-ext> [preview t1,t2,...]
import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { readFileSync, renameSync, writeFileSync } from 'node:fs';
const ROOT = '/home/claude', FPS = 30;
const [page_, out, mode, ts] = process.argv.slice(2);
const b = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
p.on('pageerror', e => console.log('[erro]', e.message));
await p.route('http://local.test/**', r => { const f = new URL(r.request().url()).pathname; const path = f.startsWith('/m3d/') ? ROOT + f : ROOT + '/semana' + f;
  const ct = path.endsWith('.html') ? 'text/html' : path.endsWith('.js') ? 'text/javascript' : 'application/octet-stream'; r.fulfill({ body: readFileSync(path), contentType: ct }); });
await p.goto('http://local.test/' + page_); await p.evaluate(() => window.ready); await p.evaluate(() => document.fonts.ready);
const info = await p.evaluate(() => EVENTS()); writeFileSync(`${ROOT}/semana/${out}.json`, JSON.stringify(info));
if (mode === 'preview') {
  for (const t of ts.split(',').map(Number)) { await p.evaluate(x => setT(x), t); await p.screenshot({ path: `${ROOT}/semana/p_${out}_${t}.jpg`, type: 'jpeg', quality: 90 }); }
} else {
  const tmp = `${ROOT}/semana/${out}.v.tmp.mp4`;
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', tmp], { stdio: ['pipe', 'ignore', 'inherit'] });
  const N = Math.round(FPS * info.dur); const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    await p.evaluate(x => setT(x), f / FPS);
    const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f % 100 === 0) console.log(`quadro ${f}/${N} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); if (await new Promise(r => ff.on('close', r)) !== 0) throw new Error('ffmpeg falhou');
  renameSync(tmp, `${ROOT}/semana/${out}.v.mp4`);
}
await b.close();
