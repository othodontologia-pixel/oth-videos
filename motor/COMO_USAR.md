# Como gerar os vídeos
1. Editar `videos.js` (hook, 5 frases curtas, pergunta final; `*palavra*` = destaque) e `legendas.json`.
2. `node render.mjs render <ids>` gera o vídeo (1080x1920, 30 fps) a partir de `reel.html`.
3. `python3 audio.py <ids>` gera trilha original + efeitos sincronizados (estilos: cinema, tech, pop, lofi).
4. Juntar com ffmpeg (`-c:v copy`, `loudnorm=I=-14`), subir em `AAAA-semana-NN/` e agendar no Metricool (blogId 8354544, Instagram Reel) usando o link raw do GitHub.
5. Anotar os temas em `temas_usados.md`.
