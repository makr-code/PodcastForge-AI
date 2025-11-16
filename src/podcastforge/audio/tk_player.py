"""Minimal Tkinter audio player UI.

Supports WAV/MP3/MP4 playback using multiple backends:
- pygame (preferred, supports pause/unpause)
- simpleaudio + ffmpeg (convert to WAV then play)
- ffplay subprocess (fallback)

The UI is intentionally minimal: Open, Play, Pause, Stop, Volume slider
and a small progress label.
"""
from __future__ import annotations

import os
import sys
import threading
import tempfile
import shutil
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional


class BaseBackend:
    def play(self, path: str, start_pos: float = 0.0):
        raise NotImplementedError()

    def pause(self):
        raise NotImplementedError()

    def resume(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def set_volume(self, v: float):
        pass


class PygameBackend(BaseBackend):
    def __init__(self):
        try:
            import pygame

            pygame.mixer.init()
            self.pygame = pygame
            self._available = True
        except Exception:
            self._available = False

    def available(self):
        return getattr(self, '_available', False)

    def play(self, path: str, start_pos: float = 0.0):
        pg = self.pygame
        pg.mixer.music.load(path)
        pg.mixer.music.play()

    def pause(self):
        self.pygame.mixer.music.pause()

    def resume(self):
        self.pygame.mixer.music.unpause()

    def stop(self):
        self.pygame.mixer.music.stop()

    def set_volume(self, v: float):
        self.pygame.mixer.music.set_volume(v)


class SimpleAudioBackend(BaseBackend):
    def __init__(self, ffmpeg_bin: Optional[str] = None):
        try:
            import simpleaudio as sa

            self.sa = sa
            self._available = True
        except Exception:
            self._available = False
        self._play_obj = None
        self._temp_wav: Optional[Path] = None
        self.ffmpeg = ffmpeg_bin or shutil.which('ffmpeg')

    def available(self):
        return getattr(self, '_available', False)

    def _ensure_wav(self, path: str) -> str:
        p = Path(path)
        if p.suffix.lower() == '.wav':
            return str(p)
        if not self.ffmpeg:
            raise RuntimeError('ffmpeg not found to transcode file to WAV')
        tmp = Path(tempfile.mkdtemp(prefix='pf_player_')) / (p.stem + '.wav')
        cmd = [self.ffmpeg, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(p), str(tmp)]
        subprocess.run(cmd, check=True)
        self._temp_wav = tmp
        return str(tmp)

    def play(self, path: str, start_pos: float = 0.0):
        wav = self._ensure_wav(path)
        wave_obj = self.sa.WaveObject.from_wave_file(wav)
        self._play_obj = wave_obj.play()

    def pause(self):
        # simpleaudio has no pause; emulate by stopping
        if self._play_obj:
            self._play_obj.stop()

    def resume(self):
        # no resume support
        pass

    def stop(self):
        if self._play_obj:
            self._play_obj.stop()
        if self._temp_wav and self._temp_wav.exists():
            try:
                self._temp_wav.unlink()
            except Exception:
                pass


class FFplayBackend(BaseBackend):
    def __init__(self):
        self.proc = None

    def available(self):
        return True

    def play(self, path: str, start_pos: float = 0.0):
        # ffplay is commonly available with ffmpeg. -autoexit exits when done.
        cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error', str(path)]
        self.proc = subprocess.Popen(cmd)

    def pause(self):
        # Not supported
        pass

    def resume(self):
        pass

    def stop(self):
        if self.proc:
            try:
                self.proc.kill()
            except Exception:
                pass


def choose_backend():
    # prefer pygame
    try:
        b = PygameBackend()
        if b.available():
            return b
    except Exception:
        pass
    # next try simpleaudio
    try:
        ff = shutil.which('ffmpeg') or shutil.which('ffmpeg.exe')
        b2 = SimpleAudioBackend(ffmpeg_bin=ff)
        if b2.available():
            return b2
    except Exception:
        pass
    # fallback to ffplay
    return FFplayBackend()


class TkAudioPlayer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack(fill='both', expand=True)
        self.create_widgets()
        self.backend = choose_backend()
        self.current_file: Optional[str] = None
        self.playing = False
        self._play_thread: Optional[threading.Thread] = None

    def create_widgets(self):
        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=8)

        self.file_var = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.file_var)
        ent.pack(side='left', fill='x', expand=True)

        btn_open = ttk.Button(top, text='Open', command=self.open_file)
        btn_open.pack(side='left', padx=4)

        ctrl = ttk.Frame(self)
        ctrl.pack(fill='x', padx=8, pady=(0,8))

        self.btn_play = ttk.Button(ctrl, text='Play', command=self.play)
        self.btn_play.pack(side='left')
        self.btn_pause = ttk.Button(ctrl, text='Pause', command=self.pause)
        self.btn_pause.pack(side='left', padx=4)
        self.btn_stop = ttk.Button(ctrl, text='Stop', command=self.stop)
        self.btn_stop.pack(side='left')

        vol_frame = ttk.Frame(self)
        vol_frame.pack(fill='x', padx=8, pady=(0,8))
        ttk.Label(vol_frame, text='Volume').pack(side='left')
        self.vol = tk.DoubleVar(value=1.0)
        vol_slider = ttk.Scale(vol_frame, from_=0.0, to=1.0, variable=self.vol, command=self._on_volume)
        vol_slider.pack(side='left', fill='x', expand=True, padx=6)

        self.status = ttk.Label(self, text='Ready')
        self.status.pack(fill='x', padx=8, pady=(0,8))

    def open_file(self):
        file = filedialog.askopenfilename(filetypes=[('Audio files', '*.wav *.mp3 *.mp4;*.m4a'), ('All files', '*.*')])
        if file:
            self.file_var.set(file)
            self.current_file = file

    def _play_worker(self, path: str):
        try:
            self.status.config(text=f'Playing: {Path(path).name}')
            self.backend.play(path)
            self.playing = True
            # If backend is FFplay or simpleaudio, we don't have an event loop to wait on.
            # Wait until process/obj completes if possible.
            if hasattr(self.backend, '_play_obj'):
                # simpleaudio
                po = getattr(self.backend, '_play_obj', None)
                if po:
                    po.wait_done()
            elif hasattr(self.backend, 'proc') and getattr(self.backend, 'proc', None) is not None:
                self.backend.proc.wait()
        except Exception as e:
            messagebox.showerror('Playback error', str(e))
        finally:
            self.playing = False
            self.status.config(text='Stopped')

    def play(self):
        path = self.file_var.get()
        if not path:
            messagebox.showinfo('No file', 'Choose a file first')
            return
        self.current_file = path
        # run playback in background thread so UI stays responsive
        t = threading.Thread(target=self._play_worker, args=(path,), daemon=True)
        t.start()
        self._play_thread = t

    def pause(self):
        try:
            self.backend.pause()
            self.status.config(text='Paused')
        except Exception:
            pass

    def stop(self):
        try:
            self.backend.stop()
            self.status.config(text='Stopped')
        except Exception:
            pass

    def _on_volume(self, v):
        try:
            self.backend.set_volume(float(v))
        except Exception:
            pass


def run_app():
    root = tk.Tk()
    root.title('PodcastForge — Audio Player')
    root.geometry('480x140')
    app = TkAudioPlayer(master=root)
    root.mainloop()


if __name__ == '__main__':
    run_app()
