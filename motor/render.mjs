import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { renameSync, writeFileSync } from 'node:fs';

const FPS = 30, D = '/home/claude/semana';
const [mode, ...ids] = process.argv.slice(2);
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });

for (const id of ids) {
  await page.goto(`file://${D}/reel.html?v=${id}`); await page.evaluate(() => document.fonts.ready);
  const info = await page.evaluate(() => EVENTS());
  writeFileSync(`${D}/${id}.json`, JSON.stringify(info));
  if (mode === 'events') continue;
  if (mode === 'preview') {
    const ts = process.env.TS ? process.env.TS.split(',').map(Number) : [2.5, 6, info.dur - .5];
    for (const t of ts) { await page.evaluate(x => setT(x), t); await page.screenshot({ path: `${D}/p_${id}_${t}.jpg`, type: 'jpeg', quality: 92 }); }
    continue;
  }
  const tmp = `${D}/${id}.v.tmp.mp4`;
  const ff = spawn('ffmpeg', ['-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', tmp], { stdio: ['pipe', 'ignore', 'inherit'] });
  for (let f = 0; f < Math.round(FPS * info.dur); f++) {
    await page.evaluate(x => setT(x), f / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  if (await new Promise(r => ff.on('close', r)) !== 0) throw new Error('ffmpeg falhou ' + id);
  renameSync(tmp, `${D}/${id}.v.mp4`);
}
await browser.close();
