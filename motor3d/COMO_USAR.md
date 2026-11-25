# Motor de vídeos 3D (padrão atual dos Reels da OTH)

Vídeos verticais 1080x1920, 30 fps, ~23 s, animação 3D com os dentes do modelo
"Permanent Dentition" (University of Dundee, School of Dentistry, CC BY 4.0 — dar crédito na legenda e no rodapé).

## Arquivos
- `dental3d.js`: renderizador WebGL2 próprio (carrega GLB, gengiva procedural, tártaro, inflamação, cárie/restauração, raio-X, metal, transparência).
- `*3d.html`: um vídeo por página (legendas, câmera, animação). Use como modelo.
- `build3d.py`: gera carie/siso/gengivite/alinhador a partir de um molde comum (bom ponto de partida para novos temas).
- `render3d.mjs <pagina.html> <id> [preview t1,t2]`: gera `<id>.v.mp4` (ou quadros de prévia). Precisa de `m3d/dentition.glb` em /home/claude/m3d/ e da pasta de trabalho /home/claude/semana (ajuste os caminhos se mudar).
- `audio.py <id>`: trilha original + efeitos sincronizados (eventos vêm de `<id>.json`).
- `finish.sh <id> <arquivo.mp4>`: junta vídeo+áudio (-14 LUFS), sobe em `3d/` neste repositório.

## Regras importantes
- Rode UM navegador 3D por vez (dois ao mesmo tempo estouram a memória).
- Canvas 720x1280 ampliado: ~2 s por quadro, ~25 min por vídeo.
- Sempre conferir quadros de prévia antes do render completo.
- Rodapé: "Animação 3D ilustrativa · Modelo: University of Dundee (CC BY 4.0)".
