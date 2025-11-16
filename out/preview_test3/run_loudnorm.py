import json
import subprocess
from podcastforge.audio.ffmpeg_pipe import find_ffmpeg
import sys

ff = find_ffmpeg()
if not ff:
    print('ffmpeg not found; install or place under third_party/ffmpeg/bin or on PATH')
    sys.exit(2)

infile = 'out/preview_test3/script_preview.mp4'
out = 'out/preview_test3/script_preview_normalized.mp3'
print('Using ffmpeg:', ff)

# pass 1: measure
cmd1 = [ff, '-hide_banner', '-nostats', '-i', infile,
        '-af', 'loudnorm=I=-16:TP=-1:LRA=7:print_format=json',
        '-f', 'null', '-']
print('Running measurement pass...')
proc = subprocess.run(cmd1, capture_output=True, text=True)
stderr = proc.stderr
j = None
for line in stderr.splitlines():
    line = line.strip()
    if line.startswith('{') and 'measured_' in line:
        try:
            j = json.loads(line)
            break
        except Exception:
            pass

if not j:
    print('Measurement failed or loudnorm did not return json; doing single-pass encode')
    cmd_fallback = [ff, '-hide_banner', '-i', infile, '-af', 'loudnorm=I=-16:TP=-1:LRA=7', '-ar', '44100', '-ac', '2', '-b:a', '128k', out, '-y']
    subprocess.run(cmd_fallback)
    print('Wrote (fallback):', out)
    sys.exit(0)

measured_I = j.get('input_i')
measured_TP = j.get('input_tp')
measured_LRA = j.get('input_lra')
measured_thresh = j.get('input_thresh')
print('Measured params:', measured_I, measured_TP, measured_LRA, measured_thresh)

cmd2 = [ff, '-hide_banner', '-nostats', '-i', infile,
        '-af', f"loudnorm=I=-16:TP=-1:LRA=7:measured_I={measured_I}:measured_TP={measured_TP}:measured_LRA={measured_LRA}:measured_thresh={measured_thresh}",
        '-ar', '44100', '-ac', '2', '-b:a', '128k', out, '-y']
print('Running apply pass...')
subprocess.run(cmd2)
print('Wrote:', out)
