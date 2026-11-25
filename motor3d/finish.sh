#!/bin/bash
# Uso: finish.sh <id> <arquivo_final.mp4>  -> trilha, junta vídeo+áudio, confere e sobe no GitHub
set -e
cd /home/claude/semana
python3 audio.py "$1" > /dev/null
ffmpeg -loglevel error -y -i "$1.v.mp4" -i "$1.wav" -map 0:v -map 1:a -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 44100 -c:a aac -b:a 192k -shortest -movflags +faststart "final/$1.tmp.mp4"
mv "final/$1.tmp.mp4" "final/$2"
for t in 4 9 12 16; do ffmpeg -loglevel error -y -ss $t -i "final/$2" -frames:v 1 -vf scale=300:-1 "f_$t.jpg"; done
ffmpeg -loglevel error -y -i f_4.jpg -i f_9.jpg -i f_12.jpg -i f_16.jpg -filter_complex hstack=4 chk.jpg
cd /home/claude/oth-videos && cp "/home/claude/semana/final/$2" 3d/ && git add -A && git -c user.name="Claude" -c user.email="noreply@anthropic.com" commit -qm "Vídeo 3D: $2

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01LZne1njZsVrfzpMVy3rJXa" && git -c push.negotiate=true push -q 2>&1 | tail -1
echo "pronto: https://raw.githubusercontent.com/othodontologia-pixel/oth-videos/main/3d/$2"
