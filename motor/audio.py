"""Trilhas originais + efeitos sonoros, sincronizados com os eventos de cada vídeo."""
import json, sys
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 44100
D = '/home/claude/semana'

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)
def env_adsr(n, a, d, s, r, sr=SR):
    a, d, r = int(a*sr), int(d*sr), int(r*sr)
    sus = max(n - a - d - r, 0)
    e = np.concatenate([np.linspace(0, 1, max(a,1)), np.linspace(1, s, max(d,1)), np.full(sus, s), np.linspace(s, 0, max(r,1))])
    return e[:n] if len(e) >= n else np.pad(e, (0, n-len(e)))
def lp(x, fc, order=2): return sosfilt(butter(order, fc, 'low', fs=SR, output='sos'), x)
def hp(x, fc, order=2): return sosfilt(butter(order, fc, 'high', fs=SR, output='sos'), x)
def bp(x, lo, hi): return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)

def saw(f, n, harm=10):
    t = np.arange(n) / SR; y = np.zeros(n)
    for k in range(1, harm+1):
        if f*k > SR/2.2: break
        y += np.sin(2*np.pi*f*k*t) / k
    return y * .6
def pluck(f, dur, bright=.5, decay=.996):
    n = int(dur*SR); N = max(int(SR / f), 2)
    rng = np.random.default_rng(int(f*100))
    x = np.zeros(n); burst = rng.uniform(-1, 1, N); x[:N] = lp(burst, 1500 + 6000*bright, 1)
    a = np.zeros(N+2); a[0] = 1; a[N] = -decay/2; a[N+1] = -decay/2
    return lfilter([1], a, x) * env_adsr(n, .001, .05, .8, .05)
def rhodes(f, dur):
    n = int(dur*SR); t = np.arange(n)/SR
    y = np.sin(2*np.pi*f*t + .8*np.exp(-t*3)*np.sin(2*np.pi*f*2*t)) + .25*np.sin(2*np.pi*f*3*t)*np.exp(-t*6)
    return y * np.exp(-t*1.6) * env_adsr(n, .005, .1, .9, .15) * (1 + .15*np.sin(2*np.pi*4.5*t))
def bell(f, dur):
    n = int(dur*SR); t = np.arange(n)/SR
    return (np.sin(2*np.pi*f*t)*np.exp(-t*2.2) + .5*np.sin(2*np.pi*f*2.76*t)*np.exp(-t*4) + .25*np.sin(2*np.pi*f*5.4*t)*np.exp(-t*7)) * env_adsr(n, .002, .1, 1, .1)
def pad(freqs, dur, bright=1800, att=.4):
    n = int(dur*SR); y = np.zeros(n)
    for f in freqs:
        for det in (-.12, 0, .12):
            y += saw(f * 2**(det/12), n, 8)
    return lp(y / (len(freqs)*3), bright) * env_adsr(n, att, .3, .85, min(.6, dur*.4))
def bass(f, dur, kind='sub'):
    n = int(dur*SR); t = np.arange(n)/SR
    y = np.sin(2*np.pi*f*t) + (.35*lp(saw(f, n, 6), 600) if kind == 'saw' else .15*np.sin(2*np.pi*f*2*t))
    return y * env_adsr(n, .005, .08, .8, .06)
def kick(soft=1.0):
    n = int(.45*SR); t = np.arange(n)/SR
    f = 45 + 95*np.exp(-t*28); ph = 2*np.pi*np.cumsum(f)/SR
    return np.sin(ph) * np.exp(-t*7) * soft + .15*np.random.default_rng(1).uniform(-1,1,n)*np.exp(-t*120)
def snare(tone=.4):
    n = int(.3*SR); t = np.arange(n)/SR; rng = np.random.default_rng(2)
    return bp(rng.uniform(-1,1,n), 1200, 7000)*np.exp(-t*16) + tone*np.sin(2*np.pi*190*t)*np.exp(-t*25)
def clap():
    n = int(.3*SR); t = np.arange(n)/SR; rng = np.random.default_rng(3); nz = bp(rng.uniform(-1,1,n), 900, 5000)
    e = np.exp(-t*20);
    for o in (0.0, .011, .022): e = e + (t >= o) * np.exp(-np.maximum(t-o,0)*180) * .6
    return nz * e * .8
def hat(open_=False):
    n = int((.25 if open_ else .06)*SR); t = np.arange(n)/SR; rng = np.random.default_rng(4)
    return hp(rng.uniform(-1,1,n), 7000, 4) * np.exp(-t*(12 if open_ else 70)) * .5
def timpani(f=55):
    n = int(1.6*SR); t = np.arange(n)/SR; rng = np.random.default_rng(5)
    return (np.sin(2*np.pi*f*t*(1+.04*np.exp(-t*8)))*np.exp(-t*2.5) + .3*lp(rng.uniform(-1,1,n), 400)*np.exp(-t*10))

def place(buf, sig, t, gain=1.0, pan=0.0):
    i = int(t*SR)
    if i >= len(buf): return
    s = sig[:len(buf)-i] * gain
    buf[i:i+len(s), 0] += s * np.sqrt((1-pan)/2) * 1.41
    buf[i:i+len(s), 1] += s * np.sqrt((1+pan)/2) * 1.41

def reverb(x, secs=1.6, wet=.25, seed=7):
    rng = np.random.default_rng(seed); n = int(secs*SR); t = np.arange(n)/SR
    out = np.zeros_like(x)
    for c in range(2):
        ir = rng.normal(0, 1, n) * np.exp(-t*4.5/secs); ir = lp(ir, 5000); ir /= np.sqrt(np.sum(ir**2))
        out[:, c] = fftconvolve(x[:, c], ir)[:len(x)]
    return x*(1-wet) + out*wet

# ---------------------------------------------------------------- estilos
CHORDS = {  # graus em semitons a partir da tônica
    'pop':    [[0,4,7],[7,11,14],[9,12,16],[5,9,12]],
    'pop2':   [[5,9,12],[7,11,14],[0,4,7],[9,12,16]],
    'tech':   [[9,12,16],[5,9,12],[0,4,7],[7,11,14]],
    'tech2':  [[0,3,7],[8,12,15],[3,7,10],[10,14,17]],
    'lofi':   [[2,5,9,12],[7,11,14,17],[0,4,7,11],[9,12,16,19]],
    'cinema': [[0,3,7],[8,12,15],[3,7,10],[10,14,17]],
    'cinema2':[[0,3,7],[5,8,12],[8,12,15],[7,11,14]],
}

def track(estilo, dur, variant):
    buf = np.zeros((int(dur*SR) + SR, 2))
    rng = np.random.default_rng(variant*31 + 5)
    if estilo == 'pop':
        bpm, key, prog = 118, [60, 62][variant%2], CHORDS['pop' if variant%2==0 else 'pop2']
    elif estilo == 'tech':
        bpm, key, prog = 108, [57, 55][variant%2], CHORDS['tech' if variant%2==0 else 'tech2']
    elif estilo == 'lofi':
        bpm, key, prog = 82, [60, 65][variant%2], CHORDS['lofi']
    else:
        bpm, key, prog = 76, [50, 53][variant%2], CHORDS['cinema' if variant%2==0 else 'cinema2']
    beat = 60 / bpm; bar = beat*4; nbars = int(np.ceil(dur / bar)) + 1
    swing = .16 if estilo == 'lofi' else 0
    melody_pat = rng.permutation([0, 1, 2, 1, 2, 3, 2, 1])

    for b in range(nbars):
        t0 = b*bar; ch = prog[b % len(prog)]; root = key + ch[0] - 12
        intro = b < 2
        if estilo == 'cinema':
            place(buf, pad([mtof(key+n-12) for n in ch] + [mtof(key+ch[0]-24)], bar*1.05, 1200, .9), t0, .55)
            if b % 2 == 0 or not intro: place(buf, timpani(mtof(root-12)), t0, .7 if not intro else .4)
            if not intro: place(buf, timpani(mtof(root-12)), t0 + beat*2.5, .35)
            for i in range(4 if not intro else 2):
                n = key + 12 + ch[melody_pat[(b+i) % 8] % len(ch)]
                place(buf, bell(mtof(n), 1.6), t0 + i*beat*(1 if not intro else 2), .16, pan=rng.uniform(-.5,.5))
            place(buf, bass(mtof(root-12), bar, 'sub'), t0, .45)
        elif estilo == 'lofi':
            for i, n in enumerate(ch):
                place(buf, rhodes(mtof(key+n-12), bar*.95), t0 + i*.018, .22, pan=(i-1.5)*.25)
            place(buf, bass(mtof(root-12), beat*1.8, 'sub'), t0, .5); place(buf, bass(mtof(root-12+7), beat*1.5, 'sub'), t0 + beat*2.5, .4)
            if not intro or b == 1:
                for i in range(4):
                    tt = t0 + i*beat
                    if i in (0,) or (i == 2 and b % 2): place(buf, kick(.8), tt, .65)
                    if i in (1, 3): place(buf, snare(.3), tt, .42)
                    for h in (0, 1): place(buf, hat(), tt + h*beat/2 + (swing*beat if h else 0), .3)
            if b % 2 == 1:
                for i in range(3):
                    n = key + 12 + ch[melody_pat[(b*3+i) % 8] % len(ch)]
                    place(buf, rhodes(mtof(n), beat*1.2), t0 + beat*(1 + i*.75), .13)
        else:  # pop / tech
            place(buf, pad([mtof(key+n) for n in ch], bar, 2500 if estilo=='pop' else 1600, .05), t0, .22)
            step = beat/4 if estilo == 'tech' else beat/2
            for i in range(int(bar/step)):
                n = key + 12 + ch[melody_pat[i % 8] % len(ch)] + (12 if (estilo == 'tech' and i % 8 == 7) else 0)
                place(buf, pluck(mtof(n), step*1.8, .7 if estilo=='pop' else .45), t0 + i*step, .32 if estilo=='tech' else .38, pan=.35*np.sin(i))
            for i in range(8):
                place(buf, bass(mtof(root), beat/2*.9, 'saw' if estilo=='tech' else 'sub'), t0 + i*beat/2, .42 if i % 2 == 0 else .3)
            if not intro:
                for i in range(4):
                    tt = t0 + i*beat
                    place(buf, kick(), tt, .75)
                    if i in (1, 3): place(buf, clap() if estilo=='pop' else snare(.2), tt, .4)
                    place(buf, hat(estilo=='pop'), tt + beat/2, .22)
                    if estilo == 'tech': place(buf, hat(), tt + beat/4, .1); place(buf, hat(), tt + 3*beat/4, .1)
            elif b == 1:
                for i in range(4): place(buf, kick(.6), t0 + i*beat, .4)
    buf = reverb(buf, 2.4 if estilo=='cinema' else 1.4, .32 if estilo=='cinema' else .2, variant)
    if estilo == 'lofi':
        buf = np.stack([lp(buf[:,c], 4200) for c in range(2)], 1)
        n = len(buf); cr = np.zeros(n); idx = rng.integers(0, n, int(dur*14)); cr[idx] = rng.uniform(-.3, .3, len(idx))
        hiss = hp(rng.normal(0, .004, n), 3000)
        buf += np.stack([lp(cr, 6000) + hiss]*2, 1)
    # filtro abrindo na introdução e fade no final
    n = int(dur*SR); buf = buf[:n]
    op = int(min(2*bar, 4)*SR); w = np.linspace(.35, 1, op)
    buf[:op] *= w[:, None]
    fo = int(2.2*SR); buf[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    return buf / (np.max(np.abs(buf)) + 1e-9)

# ---------------------------------------------------------------- efeitos
def whoosh(dur=.55, up=True, seed=9):
    n = int(dur*SR); t = np.linspace(0, 1, n); rng = np.random.default_rng(seed)
    nz = rng.uniform(-1, 1, n); y = np.zeros(n); s = 0.0
    fc = (300 + 5200*t**1.5) if up else (5500 - 5200*t**.7)
    a = 1 - np.exp(-2*np.pi*fc/SR)
    for i in range(n): s += a[i]*(nz[i]-s); y[i] = s
    e = np.sin(np.pi*t)**2 if up else np.exp(-t*4)*(1-np.exp(-t*60))
    return y * e
def pop_sfx(seed=0):
    n = int(.12*SR); t = np.arange(n)/SR; f0 = 380 + 60*seed
    ph = 2*np.pi*np.cumsum(f0 + 900*(1-np.exp(-t*40)))/SR
    return np.sin(ph) * np.exp(-t*38) * (1-np.exp(-t*2000))
def impact():
    n = int(1.2*SR); t = np.arange(n)/SR; rng = np.random.default_rng(11)
    f = 38 + 70*np.exp(-t*12)
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*3.5) + .4*lp(rng.uniform(-1,1,n), 900)*np.exp(-t*9)
def ding():
    return bell(1318.5, 2.0)*.6 + bell(1975.5, 2.0)*.35

def sfx_track(info):
    dur = info['dur']; buf = np.zeros((int(dur*SR)+SR, 2)); k = 0
    for e in info['events']:
        t = e['t']
        if e['k'] == 'hook':
            place(buf, impact(), t + .05, .9); place(buf, whoosh(.5, False, 3), t + .05, .35)
        elif e['k'] == 'whoosh':
            w = whoosh(.5, True, k); place(buf, w, max(0, t - .4), .3, pan=-.4 + .8*(k % 2)); k += 1
        elif e['k'] == 'pop':
            place(buf, pop_sfx(k % 4), t + .04, .3); k += 1
        elif e['k'] == 'fim':
            place(buf, whoosh(.5, True, 77), max(0, t - .4), .55); place(buf, ding(), t + .9, .45)
    buf = reverb(buf, .9, .15, 3)
    return buf[:int(dur*SR)]

if __name__ == '__main__':
    seen = {}
    for vid in sys.argv[1:]:
        info = json.load(open(f'{D}/{vid}.json'))
        st = info['estilo']; var = seen.get(st, 0); seen[st] = var + 1
        mus = track(st, info['dur'], var); sfx = sfx_track(info)
        mix = mus * .55 + sfx * .6
        mix /= max(1.0, np.max(np.abs(mix)) / .95)
        wavfile.write(f'{D}/{vid}.wav', SR, (mix * 32767).astype(np.int16))
        wavfile.write(f'{D}/{vid}_musica.wav', SR, (mus * .9 * 32767).astype(np.int16))
        print(vid, st, var, round(info['dur'], 1))
