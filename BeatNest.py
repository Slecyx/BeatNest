import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
from ytmusicapi import YTMusic
import yt_dlp
import vlc
import threading
import time
from PIL import Image, ImageTk
import requests
from io import BytesIO
import random
import json
import os
import re
from pynput import keyboard
from collections import Counter
from datetime import datetime
import lyricsgenius
import pyperclip

class BeatNest:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("BeatNest 🎵")
        self.window.geometry("1000x700")
        self.window.resizable(True, True)

        self.is_dark_mode = True
        self.search_var = tk.StringVar()
        self.recent_searches = []
        self.tracks = []
        self.favorites = []
        self.playlists = {}
        self.downloads = []
        self.current_playlist = None
        self.player = None
        self.current_track = None
        self.is_playing = False
        self.loading = False
        self.image_cache = {}
        self.is_dark_mode = True
        self.bg_color = "#121212"
        self.fg_color = "#ffffff"
        self.accent_color = "#1db954"
        self.secondary_color = "#1e1e1e"
        self.hover_color = "#2d2d2d"
        self.button_bg = "#282828"
        self.button_fg = "#ffffff"
        self.button_active_bg = "#3a3a3a"
        self.image_references = []
        self.queue = []
        self.is_shuffle = False
        self.is_repeat = False
        self.is_muted = False
        self.shuffle_order = []
        self.from_playlist = False
        self.listening_history = []
        self.recommended_tracks = []
        self.recommendation_play_counts = {}
        self.playing_playlist_sequentially = False
        self.listening_durations = {}
        self.last_update_time = None
        self.user_level = 0
        self.user_level_name = "Listener"
        self.total_listening_time = 0

        # Initialize Genius API for lyrics (replace with your Genius API token)
        self.genius = lyricsgenius.Genius("9M_xBhLea6HK5dKV7nxHQaNo_ZtmdecjyIXqXiQbswMKmtYwSxezfM0W0Qajjmvh", timeout=5)

        self.load_playlists()
        self.load_downloads()
        self.load_recommendations()
        self.load_search_results()
        self.load_listening_history()
        self.load_recent_searches()
        self.load_listening_durations()
        self.load_user_level()

        try:
            self.ytmusic = YTMusic()
        except Exception as e:
            self.ytmusic = None
            messagebox.showerror("Error", "Failed to initialize YTMusic API. Search may not work.")

        self.show_loading_screen()
        self.window.after(2000, self.initialize_ui)

    def show_loading_screen(self):
        self.style = ttk.Style()
        self.style.configure("Loading.TFrame", background=self.bg_color)
        self.style.configure("Loading.TLabel", background=self.bg_color, foreground="#1db954", font=("Helvetica", 36, "bold"))
        self.style.configure("Loading.Horizontal.TProgressbar",
                            background=self.accent_color,
                            troughcolor=self.secondary_color,
                            bordercolor=self.bg_color,
                            lightcolor=self.accent_color,
                            darkcolor=self.accent_color
                            )

        # Create loading frame with style
        self.loading_frame = ttk.Frame(self.window, style="Loading.TFrame")
        self.loading_frame.pack(fill=tk.BOTH, expand=True)

        # Add label with style
        ttk.Label(
            self.loading_frame,
            text="BeatNest",
            style="Loading.TLabel"
        ).pack(expand=True)

        # Progress bar
        self.loading_progress = ttk.Progressbar(
            self.loading_frame,
            style="Loading.Horizontal.TProgressbar",
            mode='determinate',
            length=300
        )
        self.loading_progress.pack(pady=(0, 50))

        # Start progress animation
        self.animate_loading_progress()

    def animate_loading_progress(self):
        if not hasattr(self, 'loading_progress'):
            return

        current = self.loading_progress['value']
        if current < 100:
            self.loading_progress['value'] = current + 2
            self.window.after(40, self.animate_loading_progress)
        else:
            self.loading_progress['value'] = 0

    def initialize_ui(self):
        self.loading_frame.destroy()
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.setup_styles()
        self.create_ui()
        self.setup_media_controls()

    def setup_styles(self):
        self.bg_color = "#121212" if self.is_dark_mode else "#f5f5f5"
        self.fg_color = "#ffffff" if self.is_dark_mode else "#000000"
        self.accent_color = "#1db954"
        self.secondary_color = "#1e1e1e" if self.is_dark_mode else "#e0e0e0"
        self.hover_color = "#2d2d2d" if self.is_dark_mode else "#d0d0d0"
        self.button_bg = "#282828" if self.is_dark_mode else "#ffffff"
        self.button_fg = "#ffffff" if self.is_dark_mode else "#000000"
        self.button_active_bg = "#3a3a3a" if self.is_dark_mode else "#c0c0c0"

        self.window.configure(bg=self.bg_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TButton", padding=8, font=("Helvetica", 10, "bold"), borderwidth=0, background=self.button_bg, foreground=self.button_fg, relief="flat")
        self.style.map("TButton", background=[("active", self.button_active_bg)], foreground=[("active", self.button_fg)])
        self.style.configure("Rounded.TButton", background=self.button_bg, foreground=self.button_fg, borderwidth=0, padding=8, font=("Helvetica", 10, "bold"), relief="flat")
        self.style.map("Rounded.TButton", background=[("active", self.button_active_bg)], foreground=[("active", self.button_fg)])
        self.style.configure("TLabel", font=("Helvetica", 12), background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TEntry", padding=10, font=("Helvetica", 12), fieldbackground=self.secondary_color, foreground=self.fg_color, relief="flat")
        self.style.configure("TCombobox", padding=10, font=("Helvetica", 12), fieldbackground=self.secondary_color, foreground=self.fg_color, relief="flat")
        self.style.configure("TProgressbar", thickness=5, background=self.accent_color, troughcolor=self.secondary_color, borderwidth=0)
        self.style.configure("Treeview", rowheight=40, font=("Helvetica", 11), background=self.secondary_color, foreground=self.fg_color, fieldbackground=self.secondary_color)
        self.style.map("Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#ffffff")])
        self.style.configure("Horizontal.TScale", background=self.bg_color, troughcolor=self.secondary_color, sliderrelief="flat")
        self.style.map("Horizontal.TScale", background=[("active", self.hover_color)])

    def create_ui(self):
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        sidebar = ttk.Frame(self.main_frame, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)

        buttons = [
            ("🏠 Home", lambda: self.show_home(), "Go to Home"),
            ("🔍 Search", lambda: self.show_search(), "Search for songs"),
            ("⭐ Favorites", lambda: self.show_favorites(), "View favorite tracks"),
            ("📚 Playlists", lambda: self.show_playlists(), "Manage playlists"),
            ("🎛 Mix", lambda: self.show_mix(), "View your personal mix"),
            ("📥 Downloads", lambda: self.show_downloads(), "View downloaded tracks"),
            ("⚙️ Settings", lambda: self.show_settings(), "Open settings")
        ]
        for text, command, tooltip in buttons:
            btn = ttk.Button(sidebar, text=text, command=command, style="TButton")
            btn.pack(fill=tk.X, pady=5, padx=10)
            btn.bind("<Enter>", lambda e, t=tooltip: self.show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        player_frame = ttk.Frame(self.window, style="TFrame")
        player_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)

        left_frame = ttk.Frame(player_frame, style="TFrame")
        left_frame.pack(side=tk.LEFT, padx=10)

        self.thumbnail_label = ttk.Label(left_frame, image=None, background=self.bg_color)
        self.thumbnail_label.pack(side=tk.LEFT, padx=5)

        info_frame = ttk.Frame(left_frame, style="TFrame")
        info_frame.pack(side=tk.LEFT, padx=5)
        self.track_label = ttk.Label(info_frame, text="No track playing", font=("Helvetica", 12, "bold"), wraplength=200, foreground="#ffffff")
        self.track_label.pack(anchor="w")
        self.artist_label = ttk.Label(info_frame, text="", font=("Helvetica", 10), wraplength=200, foreground="#b3b3b3")
        self.artist_label.pack(anchor="w")

        self.like_button = ttk.Button(left_frame, text="♡", command=self.add_to_favorites, width=3, style="Rounded.TButton")
        self.like_button.pack(side=tk.LEFT, padx=5)
        self.like_button.bind("<Enter>", lambda e: self.show_tooltip(e, "Add to favorites"))
        self.like_button.bind("<Leave>", lambda e: self.hide_tooltip())

        center_frame = ttk.Frame(player_frame, style="TFrame")
        center_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        controls_frame = ttk.Frame(center_frame, style="TFrame")
        controls_frame.pack(anchor="center")

        button_style = "Rounded.TButton"
        buttons_controls = [
            ("🔀", self.toggle_shuffle, "Toggle shuffle"),
            ("⏮", self.play_previous, "Previous track"),
            ("▶", self.toggle_play_pause, "Play/Pause"),
            ("⏭", self.play_next, "Next track"),
            ("🔁", self.toggle_repeat, "Toggle repeat")
        ]
        self.play_button = None
        for text, command, tooltip in buttons_controls:
            btn = ttk.Button(controls_frame, text=text, command=command, width=3, style=button_style)
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, t=tooltip: self.show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self.hide_tooltip())
            if text == "▶":
                self.play_button = btn

        progress_frame = ttk.Frame(center_frame, style="TFrame")
        progress_frame.pack(fill=tk.X, pady=5, padx=50)
        self.current_time_label = ttk.Label(progress_frame, text="0:00", font=("Helvetica", 8), foreground="#b3b3b3")
        self.current_time_label.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(progress_frame, length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress.bind("<Button-1>", self.seek_track)
        self.total_time_label = ttk.Label(progress_frame, text="0:00", font=("Helvetica", 8), foreground="#b3b3b3")
        self.total_time_label.pack(side=tk.LEFT, padx=5)

        right_frame = ttk.Frame(player_frame, style="TFrame")
        right_frame.pack(side=tk.RIGHT, padx=10)

        additional_controls = [
            ("➕", self.add_to_playlist_from_player, "Add to playlist"),
            ("💻", lambda: messagebox.showinfo("Info", "Device selection not implemented yet"), "Select device"),
            ("🎤", self.show_lyrics, "Show lyrics"),
        ]
        for text, command, tooltip in additional_controls:
            btn = ttk.Button(right_frame, text=text, command=command, width=3, style=button_style)
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, t=tooltip: self.show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self.hide_tooltip())

        volume_frame = ttk.Frame(right_frame, style="TFrame")
        volume_frame.pack(side=tk.LEFT, padx=(5, 0))
        self.mute_button = ttk.Button(volume_frame, text="🔊", command=self.toggle_mute, width=3, style=button_style)
        self.mute_button.pack(side=tk.LEFT, padx=(0, 2))
        self.mute_button.bind("<Enter>", lambda e: self.show_tooltip(e, "Toggle mute"))
        self.mute_button.bind("<Leave>", lambda e: self.hide_tooltip())
        self.volume_slider = ttk.Scale(volume_frame, from_=0, to=100, orient="horizontal", command=self.set_volume, length=100, style="Horizontal.TScale")
        self.volume_slider.set(50)
        self.volume_slider.pack(side=tk.LEFT)

        self.tooltip = None
        self.tooltip_alpha = 0
        self.show_home()

    def show_tooltip(self, event, text):
        if self.tooltip:
            self.tooltip.destroy()
        x = event.x_root + 20
        y = event.y_root + 10
        self.tooltip = tk.Toplevel(self.window)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=text, background="#282828", foreground="#ffffff", font=("Helvetica", 10), padx=5, pady=3)
        label.pack()
        self.tooltip_alpha = 0
        self.fade_in_tooltip()

    def fade_in_tooltip(self):
        if self.tooltip:
            self.tooltip_alpha += 0.1
            if self.tooltip_alpha >= 1:
                self.tooltip_alpha = 1
            self.tooltip.wm_attributes("-alpha", self.tooltip_alpha)
            if self.tooltip_alpha < 1:
                self.window.after(50, self.fade_in_tooltip)

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.tooltip_alpha = 0

    def setup_media_controls(self):
        def on_press(key):
            try:
                if key == keyboard.Key.media_play_pause:
                    self.toggle_play_pause()
                elif key == keyboard.Key.media_next:
                    self.play_next()
                elif key == keyboard.Key.media_previous:
                    self.play_previous()
            except:
                pass

        self.listener = keyboard.Listener(on_press=on_press)
        self.listener.start()

    def load_playlists(self):
        try:
            if os.path.exists("playlists.json"):
                with open("playlists.json", "r") as f:
                    self.playlists = json.load(f)
        except Exception as e:
            self.playlists = {}

    def save_playlists(self):
        try:
            with open("playlists.json", "w") as f:
                json.dump(self.playlists, f, indent=4)
        except Exception as e:
            pass

    def load_downloads(self):
        try:
            if os.path.exists("downloads.json"):
                with open("downloads.json", "r") as f:
                    self.downloads = [tuple(track) for track in json.load(f)]
            else:
                self.downloads = []
        except Exception as e:
            self.downloads = []

    def save_downloads(self):
        try:
            with open("downloads.json", "w") as f:
                json.dump([list(track) for track in self.downloads], f, indent=4)
        except Exception as e:
            pass

    def load_recommendations(self):
        try:
            if os.path.exists("recommendations.json"):
                with open("recommendations.json", "r") as f:
                    data = json.load(f)
                    self.recommended_tracks = [tuple(track) for track in data.get("tracks", [])]
                    self.recommendation_play_counts = data.get("play_counts", {})
            else:
                self.recommended_tracks = []
                self.recommendation_play_counts = {}
        except Exception as e:
            self.recommended_tracks = []
            self.recommendation_play_counts = {}

    def save_recommendations(self):
        try:
            data = {
                "tracks": [list(track) for track in self.recommended_tracks],
                "play_counts": self.recommendation_play_counts
            }
            with open("recommendations.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            pass

    def load_search_results(self):
        try:
            if os.path.exists("search_results.json"):
                with open("search_results.json", "r") as f:
                    self.tracks = [tuple(track) for track in json.load(f)]
            else:
                self.tracks = []
        except Exception as e:
            self.tracks = []

    def save_search_results(self):
        try:
            with open("search_results.json", "w") as f:
                json.dump([list(track) for track in self.tracks], f, indent=4)
        except Exception as e:
            pass

    def load_listening_history(self):
        try:
            if os.path.exists("listening_history.json"):
                with open("listening_history.json", "r") as f:
                    self.listening_history = [tuple(track) for track in json.load(f)]
            else:
                self.listening_history = []
        except Exception as e:
            self.listening_history = []

    def save_listening_history(self):
        try:
            with open("listening_history.json", "w") as f:
                json.dump([list(track) for track in self.listening_history], f, indent=4)
        except Exception as e:
            pass

    def load_recent_searches(self):
        try:
            if os.path.exists("recent_searches.json"):
                with open("recent_searches.json", "r") as f:
                    self.recent_searches = json.load(f)
            else:
                self.recent_searches = []
        except Exception as e:
            self.recent_searches = []

    def save_recent_searches(self):
        try:
            with open("recent_searches.json", "w") as f:
                json.dump(self.recent_searches, f, indent=4)
        except Exception as e:
            pass

    def load_listening_durations(self):
        try:
            if os.path.exists("listening_durations.json"):
                with open("listening_durations.json", "r") as f:
                    self.listening_durations = json.load(f)
            else:
                self.listening_durations = {}
        except Exception as e:
            self.listening_durations = {}

    def save_listening_durations(self):
        try:
            with open("listening_durations.json", "w") as f:
                json.dump(self.listening_durations, f, indent=4)
        except Exception as e:
            pass

    def load_user_level(self):
        try:
            if os.path.exists("user_level.json"):
                with open("user_level.json", "r") as f:
                    data = json.load(f)
                    self.user_level = data.get("level", 0)
                    self.user_level_name = data.get("level_name", "Listener")
                    self.total_listening_time = data.get("total_time", 0)
            else:
                self.user_level = 0
                self.user_level_name = "Listener"
                self.total_listening_time = 0
        except Exception as e:
            self.user_level = 0
            self.user_level_name = "Listener"
            self.total_listening_time = 0

    def save_user_level(self):
        try:
            data = {
                "level": self.user_level,
                "level_name": self.user_level_name,
                "total_time": self.total_listening_time
            }
            with open("user_level.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            pass

    def update_user_level(self):
        levels = [
            (0, "Listener"),
            (3600, "Music Fan"),  # 1 hour
            (10800, "Melody Master"),  # 3 hours
            (36000, "Harmony Hero"),  # 10 hours
            (108000, "Symphony Star"),  # 30 hours
            (360000, "Legendary Listener")  # 100 hours
        ]
        for time_threshold, name in reversed(levels):
            if self.total_listening_time >= time_threshold:
                if self.user_level_name != name:
                    self.user_level = levels.index((time_threshold, name))
                    self.user_level_name = name
                    self.save_user_level()
                    messagebox.showinfo("Level Up!", f"Congratulations! You've reached {name} level!")
                break

    def get_greeting(self):
        hour = datetime.now().hour
        if 0 <= hour < 12:
            return f"Good Morning, {self.user_level_name}!"
        elif 12 <= hour < 17:
            return f"Good Afternoon, {self.user_level_name}!"
        elif 17 <= hour < 22:
            return f"Good Evening, {self.user_level_name}!"
        else:
            return f"Good Night, {self.user_level_name}!"

    def on_track_frame_enter(self, event):
        event.widget.configure(background=self.hover_color)

    def on_track_frame_leave(self, event):
        event.widget.configure(background=self.bg_color)

    def show_home(self):
        self.clear_content()

        ttk.Label(self.content_frame, text=self.get_greeting(), font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(0, 20))

        canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if self.listening_history:
            ttk.Label(scrollable_frame, text="Your Top Tracks", font=("Helvetica", 20, "bold")).pack(anchor="w", pady=(20, 10))
            top_tracks_frame = ttk.Frame(scrollable_frame)
            top_tracks_frame.pack(fill=tk.X, pady=10)

            track_counts = Counter(self.listening_history)
            top_tracks = track_counts.most_common(5)

            for track, count in top_tracks:
                track_frame = tk.Frame(top_tracks_frame, bg=self.bg_color)
                track_frame.pack(fill=tk.X, pady=5)
                track_frame.bind("<Enter>", self.on_track_frame_enter)
                track_frame.bind("<Leave>", self.on_track_frame_leave)
                track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))

                thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
                thumbnail_label.pack(side=tk.LEFT, padx=10)
                self.load_thumbnail_for_track(track[5], thumbnail_label)

                info_frame = ttk.Frame(track_frame)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
                ttk.Label(info_frame, text=f"{track[2]} • Played {count} times", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

                play_btn = ttk.Button(track_frame, text="▶", command=lambda t=track: self.play_track(t), width=4, style="Rounded.TButton")
                play_btn.pack(side=tk.RIGHT, padx=10)
                play_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Play this track"))
                play_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.recommended_tracks = []
        self.recommendation_play_counts = {}
        if self.ytmusic:
            if self.listening_history:
                top_tracks = [track for track, _ in Counter(self.listening_history).most_common(3)]
                for track in top_tracks:
                    try:
                        video_id = track[1]
                        related = self.ytmusic.get_song(video_id).get("related", {}).get("items", [])
                        for item in related[:2]:
                            title = item.get("title", "Unknown")
                            video_id = item.get("videoId", "")
                            artist_name = item.get("artist", "Unknown")
                            album = item.get("album", "Unknown")
                            duration = item.get("duration_seconds", 0) or 0
                            thumbnail = item.get("thumbnails", [{}])[0].get("url", "")
                            rec_track = (title, video_id, artist_name, album, duration, thumbnail)
                            if rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                                self.recommended_tracks.append(rec_track)
                                self.recommendation_play_counts[title] = 0
                    except Exception as e:
                        try:
                            artist = track[2]
                            results = self.ytmusic.search(artist, filter="songs", limit=2)
                            if not results:
                                continue
                            for result in results:
                                if not isinstance(result, dict):
                                    continue
                                title = result.get("title", "Unknown")
                                video_id = result.get("videoId", "")
                                if not video_id:
                                    continue
                                artist_name = result.get("artists", [{}])[0].get("name", "Unknown") if result.get("artists") else "Unknown"
                                album = result.get("album", {}).get("name", "Unknown") if result.get("album") else "Unknown"
                                duration = result.get("duration_seconds", 0) or 0
                                thumbnail = result.get("thumbnails", [{}])[0].get("url", "")
                                rec_track = (title, video_id, artist_name, album, duration, thumbnail)
                                if rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                                    self.recommended_tracks.append(rec_track)
                                    self.recommendation_play_counts[title] = 0
                        except Exception as e:
                            pass

            if len(self.recommended_tracks) < 5 and self.recent_searches:
                recent_query = self.recent_searches[0]
                try:
                    results = self.ytmusic.search(recent_query, filter="songs", limit=3)
                    if not results:
                        pass
                    for result in results:
                        if not isinstance(result, dict):
                            continue
                        title = result.get("title", "Unknown")
                        video_id = result.get("videoId", "")
                        if not video_id:
                            continue
                        artist_name = result.get("artists", [{}])[0].get("name", "Unknown") if result.get("artists") else "Unknown"
                        album = result.get("album", {}).get("name", "Unknown") if result.get("album") else "Unknown"
                        duration = result.get("duration_seconds", 0) or 0
                        thumbnail = result.get("thumbnails", [{}])[0].get("url", "")
                        rec_track = (title, video_id, artist_name, album, duration, thumbnail)
                        if rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                            self.recommended_tracks.append(rec_track)
                            self.recommendation_play_counts[title] = 0
                except Exception as e:
                    pass

            if len(self.recommended_tracks) < 5:
                try:
                    default_artist = "The Beatles"
                    results = self.ytmusic.search(default_artist, filter="songs", limit=5 - len(self.recommended_tracks))
                    if not results:
                        pass
                    for result in results:
                        if not isinstance(result, dict):
                            continue
                        title = result.get("title", "Unknown")
                        video_id = result.get("videoId", "")
                        if not video_id:
                            continue
                        artist_name = result.get("artists", [{}])[0].get("name", "Unknown") if result.get("artists") else "Unknown"
                        album = result.get("album", {}).get("name", "Unknown") if result.get("album") else "Unknown"
                        duration = result.get("duration_seconds", 0) or 0
                        thumbnail = result.get("thumbnails", [{}])[0].get("url", "")
                        rec_track = (title, video_id, artist_name, album, duration, thumbnail)
                        if rec_track not in self.recommended_tracks:
                            self.recommended_tracks.append(rec_track)
                            self.recommendation_play_counts[title] = 0
                except Exception as e:
                    pass

            self.save_recommendations()

        if self.recommended_tracks:
            ttk.Label(scrollable_frame, text="Recommended for You", font=("Helvetica", 20, "bold")).pack(anchor="w", pady=(20, 10))
            recommended_frame = ttk.Frame(scrollable_frame)
            recommended_frame.pack(fill=tk.X, pady=10)

            for track in self.recommended_tracks:
                track_frame = tk.Frame(recommended_frame, bg=self.bg_color)
                track_frame.pack(fill=tk.X, pady=5)
                track_frame.bind("<Enter>", self.on_track_frame_enter)
                track_frame.bind("<Leave>", self.on_track_frame_leave)
                track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))

                thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
                thumbnail_label.pack(side=tk.LEFT, padx=10)
                self.load_thumbnail_for_track(track[5], thumbnail_label)

                info_frame = ttk.Frame(track_frame)
                info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
                ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
                play_count = self.recommendation_play_counts.get(track[0], 0)
                ttk.Label(info_frame, text=f"{track[2]} • Played {play_count} times", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

                play_btn = ttk.Button(track_frame, text="▶", command=lambda t=track: self.play_recommended_track(t), width=4, style="Rounded.TButton")
                play_btn.pack(side=tk.RIGHT, padx=10)
                play_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Play this track"))
                play_btn.bind("<Leave>", lambda e: self.hide_tooltip())

    def load_thumbnail_for_track(self, url, label):
        if not url:
            label.config(image=None)
            return
        try:
            if url not in self.image_cache:
                response = requests.get(url, timeout=5)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_cache[url] = photo
                self.image_references.append(photo)
            label.config(image=self.image_cache[url])
        except Exception as e:
            label.config(image=None)

    def play_track(self, track):
        self.playing_playlist_sequentially = False
        if self.player and self.is_playing:
            self.player.stop()
            self.player.release()
            self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")

        self.current_track = track
        self.from_playlist = bool(self.current_playlist)
        self.loading = True
        self.listening_history.append(self.current_track)
        self.save_listening_history()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def play_recommended_track(self, track):
        self.playing_playlist_sequentially = False
        if self.player and self.is_playing:
            self.player.stop()
            self.player.release()
            self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")

        self.current_track = track
        self.from_playlist = False
        self.loading = True
        self.listening_history.append(self.current_track)
        self.save_listening_history()
        self.recommendation_play_counts[track[0]] = self.recommendation_play_counts.get(track[0], 0) + 1
        self.save_recommendations()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()
        self.show_home()

    def show_search(self):
        self.clear_content()
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill=tk.X, pady=(0, 15))

        search_entry = ttk.Combobox(search_frame, textvariable=self.search_var, values=self.recent_searches, font=("Helvetica", 12))
        search_entry.pack(fill=tk.X, padx=(0, 10))
        search_entry.bind("<Return>", lambda e: self.search_music())

        button_frame = ttk.Frame(search_frame)
        button_frame.pack(fill=tk.X, pady=10)
        search_btn = ttk.Button(button_frame, text="🔍 Search", command=self.search_music, style="Rounded.TButton")
        search_btn.pack(side=tk.LEFT, padx=5)
        search_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Search for songs"))
        search_btn.bind("<Leave>", lambda e: self.hide_tooltip())
        clear_btn = ttk.Button(button_frame, text="🗑 Clear Search", command=self.clear_search, style="Rounded.TButton")
        clear_btn.pack(side=tk.LEFT, padx=5)
        clear_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Clear search query"))
        clear_btn.bind("<Leave>", lambda e: self.hide_tooltip())
        sort_btn = ttk.Button(button_frame, text="Sort by Duration", command=self.sort_by_duration, style="Rounded.TButton")
        sort_btn.pack(side=tk.LEFT, padx=5)
        sort_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Sort tracks by duration"))
        sort_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.tree = ttk.Treeview(self.content_frame, columns=("Title", "Artist", "Album", "Duration"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Artist", text="Artist")
        self.tree.heading("Album", text="Album")
        self.tree.heading("Duration", text="Duration")
        self.tree.column("Title", width=300)
        self.tree.column("Artist", width=200)
        self.tree.column("Album", width=200)
        self.tree.column("Duration", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda e: self.play_selected())
        self.tree.bind("<Button-3>", self.show_context_menu)

        for track in self.tracks:
            self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))

        self.loading_label = ttk.Label(self.content_frame, text="", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)

        self.context_menu = tk.Menu(self.window, tearoff=0, bg="#282828", fg="#ffffff", font=("Helvetica", 10))
        self.context_menu.add_command(label="Play Now", command=self.play_selected)
        self.context_menu.add_command(label="Add to Queue", command=self.add_to_queue)
        self.context_menu.add_command(label="Add to Favorites", command=self.add_to_favorites)
        self.context_menu.add_command(label="Add to Playlist", command=self.add_to_playlist_from_menu)
        self.context_menu.add_command(label="Remove from Playlist", command=self.remove_from_playlist)
        self.context_menu.add_command(label="Download", command=self.download_track)

    def show_favorites(self):
        self.clear_content()
        self.tree = ttk.Treeview(self.content_frame, columns=("Title", "Artist", "Album", "Duration"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Artist", text="Artist")
        self.tree.heading("Album", text="Album")
        self.tree.heading("Duration", text="Duration")
        self.tree.column("Title", width=300)
        self.tree.column("Artist", width=200)
        self.tree.column("Album", width=200)
        self.tree.column("Duration", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<Double-1>", lambda e: self.play_selected())
        self.tree.bind("<Button-3>", self.show_context_menu)

        for track in self.favorites:
            self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))

        fav_btn = ttk.Button(self.content_frame, text="❤️ Add Current to Favorites", command=self.add_to_favorites, style="Rounded.TButton")
        fav_btn.pack(pady=10)
        fav_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Add current track to favorites"))
        fav_btn.bind("<Leave>", lambda e: self.hide_tooltip())
        self.loading_label = ttk.Label(self.content_frame, text="No favorites yet!" if not self.favorites else "", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)

    def show_playlists(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Playlists", font=("Helvetica", 28, "bold")).pack(pady=20)

        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        create_btn = ttk.Button(button_frame, text="➕ Create Playlist", command=self.create_playlist, style="Rounded.TButton")
        create_btn.pack(side=tk.LEFT, padx=5)
        create_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Create a new playlist"))
        create_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        playlist_frame = ttk.Frame(self.content_frame)
        playlist_frame.pack(fill=tk.BOTH, expand=True)

        for widget in playlist_frame.winfo_children():
            widget.destroy()

        for name in self.playlists:
            frame = ttk.Frame(playlist_frame)
            frame.pack(fill=tk.X, pady=5)
            playlist_btn = ttk.Button(frame, text=name, command=lambda n=name: self.show_playlist(n), style="TButton")
            playlist_btn.pack(side=tk.LEFT)
            playlist_btn.bind("<Enter>", lambda e, n=name: self.show_tooltip(e, f"View {n} playlist"))
            playlist_btn.bind("<Leave>", lambda e: self.hide_tooltip())
            play_playlist_btn = ttk.Button(frame, text="▶", command=lambda n=name: self.play_playlist_sequentially(n), width=4, style="Rounded.TButton")
            play_playlist_btn.pack(side=tk.LEFT, padx=5)
            play_playlist_btn.bind("<Enter>", lambda e, n=name: self.show_tooltip(e, f"Play {n} playlist sequentially"))
            play_playlist_btn.bind("<Leave>", lambda e: self.hide_tooltip())
            delete_btn = ttk.Button(frame, text="🗑", command=lambda n=name: self.delete_playlist(n), style="Rounded.TButton")
            delete_btn.pack(side=tk.RIGHT)
            delete_btn.bind("<Enter>", lambda e, n=name: self.show_tooltip(e, f"Delete {n} playlist"))
            delete_btn.bind("<Leave>", lambda e: self.hide_tooltip())

    def show_mix(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Your Mix", font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(0, 20))

        canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        mix_tracks = []
        if self.listening_history:
            track_counts = Counter(self.listening_history)
            top_tracks = track_counts.most_common(10)
            mix_tracks.extend([track for track, _ in top_tracks])

            for track, _ in top_tracks[:3]:
                try:
                    video_id = track[1]
                    related = self.ytmusic.get_song(video_id).get("related", {}).get("items", [])
                    for item in related[:2]:
                        title = item.get("title", "Unknown")
                        video_id = item.get("videoId", "")
                        artist_name = item.get("artist", "Unknown")
                        album = item.get("album", "Unknown")
                        duration = item.get("duration_seconds", 0) or 0
                        thumbnail = item.get("thumbnails", [{}])[0].get("url", "")
                        rec_track = (title, video_id, artist_name, album, duration, thumbnail)
                        if rec_track not in mix_tracks:
                            mix_tracks.append(rec_track)
                except Exception:
                    pass

        if not mix_tracks:
            ttk.Label(scrollable_frame, text="Listen to more tracks to create your mix!", font=("Helvetica", 14)).pack(pady=10)
            return

        for track in mix_tracks[:20]:
            track_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
            track_frame.pack(fill=tk.X, pady=5)
            track_frame.bind("<Enter>", self.on_track_frame_enter)
            track_frame.bind("<Leave>", self.on_track_frame_leave)
            track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))

            thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
            thumbnail_label.pack(side=tk.LEFT, padx=10)
            self.load_thumbnail_for_track(track[5], thumbnail_label)

            info_frame = ttk.Frame(track_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
            ttk.Label(info_frame, text=f"{track[2]} • {track[3]}", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

            play_btn = ttk.Button(track_frame, text="▶", command=lambda t=track: self.play_track(t), width=4, style="Rounded.TButton")
            play_btn.pack(side=tk.RIGHT, padx=10)
            play_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Play this track"))
            play_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.loading_label = ttk.Label(self.content_frame, text="", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)

    def show_downloads(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Downloads", font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(0, 20))

        canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for track in self.downloads:
            track_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
            track_frame.pack(fill=tk.X, pady=5)
            track_frame.bind("<Enter>", self.on_track_frame_enter)
            track_frame.bind("<Leave>", self.on_track_frame_leave)
            track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))

            thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
            thumbnail_label.pack(side=tk.LEFT, padx=10)
            self.load_thumbnail_for_track(track[5], thumbnail_label)

            info_frame = ttk.Frame(track_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
            ttk.Label(info_frame, text=f"{track[2]} • {track[3]} • {self.format_time(track[4])}", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

            play_btn = ttk.Button(track_frame, text="▶", command=lambda t=track: self.play_track(t), width=4, style="Rounded.TButton")
            play_btn.pack(side=tk.RIGHT, padx=10)
            play_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Play this track"))
            play_btn.bind("<Leave>", lambda e: self.hide_tooltip())

            delete_btn = ttk.Button(track_frame, text="🗑", command=lambda t=track: self.delete_download(t), width=4, style="Rounded.TButton")
            delete_btn.pack(side=tk.RIGHT, padx=5)
            delete_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Delete downloaded track"))
            delete_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.loading_label = ttk.Label(self.content_frame, text="No downloaded tracks yet!" if not self.downloads else "", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)

    def download_track(self):
        selection = self.tree.selection()
        if not selection:
            self.loading_label.config(text="No track selected")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return

        index = self.tree.index(selection[0])
        track = self.tracks[index]
        if track in self.downloads:
            self.loading_label.config(text="Track already downloaded")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return

        self.loading_label.config(text="Downloading...")
        self.window.config(cursor="wait")
        threading.Thread(target=self.download_and_save_track, args=(track,), daemon=True).start()

    def download_and_save_track(self, track):
        try:
            video_id = track[1]
            url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f"downloads/{track[0]} - {track[2]}.%(ext)s",
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }

            os.makedirs("downloads", exist_ok=True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            file_path = f"downloads/{track[0]} - {track[2]}.mp3"
            downloaded_track = (*track, file_path)
            self.downloads.append(downloaded_track)
            self.save_downloads()

            self.loading_label.config(text=f"Downloaded: {track[0]}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
        except Exception as e:
            self.loading_label.config(text="Download failed")
            self.window.after(3000, lambda: self.loading_label.config(text=""))
        finally:
            self.window.config(cursor="")

    def delete_download(self, track):
        try:
            file_path = track[6]
            if os.path.exists(file_path):
                os.remove(file_path)
            self.downloads.remove(track)
            self.save_downloads()
            self.show_downloads()
            self.loading_label.config(text=f"Deleted: {track[0]}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
        except Exception as e:
            self.loading_label.config(text="Failed to delete track")
            self.window.after(2000, lambda: self.loading_label.config(text=""))

    def create_playlist(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Playlist")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=self.bg_color)

        ttk.Label(dialog, text="Enter playlist name:").pack(pady=10)
        playlist_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=playlist_name_var, width=30).pack(pady=5)
        create_btn = ttk.Button(dialog, text="Create", command=lambda: self.add_new_playlist(playlist_name_var.get(), dialog), style="Rounded.TButton")
        create_btn.pack(pady=10)
        create_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Create the playlist"))
        create_btn.bind("<Leave>", lambda e: self.hide_tooltip())

    def add_new_playlist(self, playlist_name, dialog):
        if not playlist_name:
            messagebox.showerror("Error", "Playlist name cannot be empty")
            return
        playlist_name = playlist_name.strip()
        if not playlist_name or len(playlist_name) > 50 or not re.match(r'^[a-zA-Z0-9\s_-]+$', playlist_name):
            messagebox.showerror("Error", "Invalid playlist name")
            dialog.destroy()
            return
        if playlist_name in self.playlists:
            messagebox.showerror("Error", "Playlist already exists")
            dialog.destroy()
            return
        self.playlists[playlist_name] = []
        self.save_playlists()
        self.show_playlists()
        dialog.destroy()

    def play_playlist_sequentially(self, name):
        self.current_playlist = name
        self.playing_playlist_sequentially = True
        if self.playlists[name]:
            self.current_track = self.playlists[name][0]
            self.from_playlist = True
            self.loading = True
            self.listening_history.append(self.current_track)
            self.save_listening_history()
            self.update_now_playing()
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def show_playlist(self, name):
        self.clear_content()
        self.current_playlist = name

        ttk.Label(self.content_frame, text=name, font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(0, 20))

        canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tracks = self.playlists[name]
        for track in self.playlists[name]:
            track_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
            track_frame.pack(fill=tk.X, pady=5)
            track_frame.bind("<Enter>", self.on_track_frame_enter)
            track_frame.bind("<Leave>", self.on_track_frame_leave)
            track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))

            thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
            thumbnail_label.pack(side=tk.LEFT, padx=10)
            self.load_thumbnail_for_track(track[5], thumbnail_label)

            info_frame = ttk.Frame(track_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
            ttk.Label(info_frame, text=f"{track[2]} • {track[3]} • {self.format_time(track[4])}", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

            play_btn = ttk.Button(track_frame, text="▶", command=lambda t=track: self.play_track(t), width=4, style="Rounded.TButton")
            play_btn.pack(side=tk.RIGHT, padx=10)
            play_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Play this track"))
            play_btn.bind("<Leave>", lambda e: self.hide_tooltip())

            remove_btn = ttk.Button(track_frame, text="🗑", command=lambda t=track: self.remove_from_playlist(t), width=4, style="Rounded.TButton")
            remove_btn.pack(side=tk.RIGHT, padx=5)
            remove_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Remove from playlist"))
            remove_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Add current track button
        add_btn = ttk.Button(button_frame, text="➕ Add Current to Playlist",
                             command=self.add_to_playlist,
                             style="Rounded.TButton")
        add_btn.pack(side=tk.LEFT, padx=5)
        add_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Add current track to playlist"))
        add_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        # Download all button
        download_all_btn = ttk.Button(button_frame, text="📥 Download All",
                                     command=lambda: self.download_playlist(name),
                                     style="Rounded.TButton")
        download_all_btn.pack(side=tk.LEFT, padx=5)
        download_all_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Download all tracks in playlist"))
        download_all_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        # Sort button
        sort_btn = ttk.Button(button_frame, text="Sort by Duration",
                             command=self.sort_by_duration,
                             style="Rounded.TButton")
        sort_btn.pack(side=tk.LEFT, padx=5)
        sort_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Sort tracks by duration"))
        sort_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        self.loading_label = ttk.Label(self.content_frame, text="No tracks in this playlist!" if not self.playlists[name] else "", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)

    def show_settings(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Settings", font=("Helvetica", 28, "bold")).pack(pady=20)

        settings_frame = ttk.Frame(self.content_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)

        theme_frame = ttk.Frame(settings_frame)
        theme_frame.pack(fill=tk.X, pady=10)
        ttk.Label(theme_frame, text="Theme:", font=("Helvetica", 14)).pack(side=tk.LEFT, padx=10)
        theme_btn = ttk.Button(theme_frame, text="Toggle Dark/Light Mode", command=self.toggle_theme, style="Rounded.TButton")
        theme_btn.pack(side=tk.LEFT, padx=10)
        theme_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Toggle between dark and light mode"))
        theme_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        stats_frame = ttk.Frame(settings_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        ttk.Label(stats_frame, text="Stats:", font=("Helvetica", 14)).pack(side=tk.LEFT, padx=10)
        stats_btn = ttk.Button(stats_frame, text="View Listening Stats", command=self.show_stats, style="Rounded.TButton")
        stats_btn.pack(side=tk.LEFT, padx=10)
        stats_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "View your listening statistics"))
        stats_btn.bind("<Leave>", lambda e: self.hide_tooltip())

    def show_stats(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Listening Statistics", font=("Helvetica", 28, "bold")).pack(anchor="w", pady=(0, 20))

        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        ttk.Label(stats_frame, text=f"Level: {self.user_level_name}", font=("Helvetica", 16, "bold")).pack(anchor="w", padx=10)
        hours = int(self.total_listening_time // 3600)
        minutes = int((self.total_listening_time % 3600) // 60)
        ttk.Label(stats_frame, text=f"Total Listening Time: {hours}h {minutes}m", font=("Helvetica", 14)).pack(anchor="w", padx=10)

        if not self.listening_history:
            ttk.Label(self.content_frame, text="No listening history yet!", font=("Helvetica", 14)).pack(pady=10)
            return

        track_counts = Counter(self.listening_history)
        sorted_tracks = track_counts.most_common()

        canvas = tk.Canvas(self.content_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for track, count in sorted_tracks:
            track_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
            track_frame.pack(fill=tk.X, pady=5)

            thumbnail_label = ttk.Label(track_frame, image=None, background=self.bg_color)
            thumbnail_label.pack(side=tk.LEFT, padx=10)
            self.load_thumbnail_for_track(track[5], thumbnail_label)

            info_frame = ttk.Frame(track_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(info_frame, text=track[0], font=("Helvetica", 14, "bold"), foreground="#ffffff").pack(anchor="w")
            duration_key = f"{track[0]} - {track[2]}"
            duration = self.listening_durations.get(duration_key, 0)
            duration_mins = int(duration // 60)
            duration_secs = int(duration % 60)
            ttk.Label(info_frame, text=f"{track[2]} • Played {count} times • Listened for {duration_mins}:{duration_secs:02d}", font=("Helvetica", 12), foreground="#b3b3b3").pack(anchor="w")

    def delete_playlist(self, name):
        del self.playlists[name]
        if self.current_playlist == name:
            self.current_playlist = None
        self.save_playlists()
        self.show_playlists()

    def download_playlist(self, playlist_name):
        if not self.playlists[playlist_name]:
            self.loading_label.config(text="Playlist is empty")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return

        # Create progress dialog
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Downloading Playlist: {playlist_name}")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=self.bg_color)

        # Progress information
        progress_label = ttk.Label(dialog, text="Preparing to download...", font=("Helvetica", 10))
        progress_label.pack(pady=10)

        progress_bar = ttk.Progressbar(dialog, mode="determinate", length=300)
        progress_bar.pack(pady=10)

        status_label = ttk.Label(dialog, text="", font=("Helvetica", 9))
        status_label.pack(pady=5)

        # Cancel button
        self.download_cancelled = False
        cancel_btn = ttk.Button(dialog, text="Cancel", command=lambda: self.cancel_download(dialog))
        cancel_btn.pack(pady=10)

        total_tracks = len(self.playlists[playlist_name])
        completed_downloads = 0

        def update_progress(track_name, current, total):
            if not dialog.winfo_exists():
                return
            progress_bar['value'] = (current / total) * 100
            progress_label.config(text=f"Downloading: {track_name}")
            status_label.config(text=f"Progress: {current}/{total} tracks")
            dialog.update()

        def download_track_threaded(track):
            nonlocal completed_downloads
            try:
                if self.download_cancelled:
                    return

                # Skip if already downloaded
                if track in self.downloads:
                    completed_downloads += 1
                    update_progress(track[0], completed_downloads, total_tracks)
                    return

                video_id = track[1]
                url = f"https://www.youtube.com/watch?v={video_id}"

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': f"downloads/{track[0]} - {track[2]}.%(ext)s",
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'quiet': True,
                    'no_warnings': True,
                }

                os.makedirs("downloads", exist_ok=True)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                file_path = f"downloads/{track[0]} - {track[2]}.mp3"
                downloaded_track = (*track, file_path)

                if downloaded_track not in self.downloads:
                    self.downloads.append(downloaded_track)
                    self.save_downloads()

                completed_downloads += 1
                update_progress(track[0], completed_downloads, total_tracks)

            except Exception as e:
                status_label.config(text=f"Error downloading {track[0]}: {str(e)}")

        def download_all_tracks():
            try:
                threads = []
                for track in self.playlists[playlist_name]:
                    if self.download_cancelled:
                        break
                    thread = threading.Thread(target=download_track_threaded, args=(track,))
                    threads.append(thread)
                    thread.start()

                # Wait for all threads to complete
                for thread in threads:
                    thread.join()

                if not self.download_cancelled and dialog.winfo_exists():
                    progress_label.config(text="Download completed!")
                    status_label.config(text=f"Successfully downloaded {completed_downloads}/{total_tracks} tracks")
                    cancel_btn.config(text="Close")
                    self.loading_label.config(text=f"Playlist '{playlist_name}' downloaded")
                    self.window.after(2000, lambda: self.loading_label.config(text=""))

            except Exception as e:
                if dialog.winfo_exists():
                    progress_label.config(text="Download failed!")
                    status_label.config(text=str(e))

        # Start download process in a separate thread
        threading.Thread(target=download_all_tracks, daemon=True).start()

    def cancel_download(self, dialog):
        self.download_cancelled = True
        dialog.destroy()

    def add_to_playlist_from_menu(self):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        self.show_add_to_playlist_dialog(track)

    def add_to_playlist_from_player(self):
        if not self.current_track:
            self.loading_label.config(text="No track playing")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return
        self.show_add_to_playlist_dialog(self.current_track)

    def show_add_to_playlist_dialog(self, track):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add to Playlist")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=self.bg_color)

        ttk.Label(dialog, text="Select or create a playlist:").pack(pady=10)
        playlist_var = tk.StringVar()
        playlist_dropdown = ttk.Combobox(dialog, textvariable=playlist_var, values=list(self.playlists.keys()))
        playlist_dropdown.pack(pady=5, padx=10)
        new_playlist_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=new_playlist_var, width=30).pack(pady=5)
        add_btn = ttk.Button(dialog, text="Add", command=lambda: self.add_to_selected_playlist(track, playlist_var.get(), new_playlist_var.get(), dialog), style="Rounded.TButton")
        add_btn.pack(pady=10)
        add_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Add to selected playlist"))
        add_btn.bind("<Leave>", lambda e: self.hide_tooltip())

    def add_to_selected_playlist(self, track, playlist_name, new_playlist_name, dialog):
        if new_playlist_name:
            new_playlist_name = new_playlist_name.strip()
            if not new_playlist_name or len(new_playlist_name) > 50 or not re.match(r'^[a-zA-Z0-9\s_-]+$', new_playlist_name):
                self.loading_label.config(text="Invalid playlist name")
                self.window.after(2000, lambda: self.loading_label.config(text=""))
                dialog.destroy()
                return
            if new_playlist_name in self.playlists:
                self.loading_label.config(text="Playlist already exists")
                self.window.after(2000, lambda: self.loading_label.config(text=""))
                dialog.destroy()
                return
            self.playlists[new_playlist_name] = []
            playlist_name = new_playlist_name
        if playlist_name:
            if track not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(track)
                self.save_playlists()
                self.loading_label.config(text=f"Added to {playlist_name}")
                self.window.after(2000, lambda: self.loading_label.config(text=""))
        dialog.destroy()

    def remove_from_playlist(self, track=None):
        if not self.current_playlist:
            return
        selection = self.tree.selection()
        if not selection and not track:
            return
        if track:
            selected_track = track
        else:
            index = self.tree.index(selection[0])
            selected_track = self.tracks[index]
        if selected_track in self.playlists[self.current_playlist]:
            self.playlists[self.current_playlist].remove(selected_track)
            self.save_playlists()
            self.show_playlist(self.current_playlist)
            self.loading_label.config(text=f"Removed from {self.current_playlist}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))

    def sort_by_duration(self):
        if not self.tracks:
            return
        self.tracks.sort(key=lambda x: x[4])
        if self.current_playlist:
            self.playlists[self.current_playlist] = self.tracks
            self.save_playlists()
            self.show_playlist(self.current_playlist)
        else:
            self.tree.delete(*self.tree.get_children())
            for track in self.tracks:
                self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))
        self.loading_label.config(text="Sorted by duration")
        self.window.after(2000, lambda: self.loading_label.config(text=""))

    def clear_search(self):
        self.search_var.set("")
        self.recent_searches = [s for s in self.recent_searches if s != self.search_var.get()]
        self.save_recent_searches()
        self.tracks = []
        self.save_search_results()
        self.show_search()

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def search_music(self):
        query = self.search_var.get()
        if not query:
            self.loading_label.config(text="Please enter a search query")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return

        self.loading_label.config(text="Searching...")
        self.window.config(cursor="wait")

        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            if len(self.recent_searches) > 5:
                self.recent_searches.pop()
            self.save_recent_searches()

        if not self.ytmusic:
            self.loading_label.config(text="YTMusic API not initialized")
            self.window.config(cursor="")
            messagebox.showerror("Error", "YTMusic API not initialized. Please check your setup.")
            self.window.after(3000, lambda: self.loading_label.config(text=""))
            return

        self.tracks = []
        self.tree.delete(*self.tree.get_children())

        for attempt in range(2):
            try:
                results = self.ytmusic.search(query, filter="songs", limit=10)
                if not results:
                    self.loading_label.config(text="No results found")
                    self.window.after(2000, lambda: self.loading_label.config(text=""))
                    self.window.config(cursor="")
                    return

                for result in results:
                    if not isinstance(result, dict):
                        continue
                    title = result.get("title", "Unknown")
                    video_id = result.get("videoId", "")
                    if not video_id:
                        continue
                    artist_name = result.get("artists", [{}])[0].get("name", "Unknown") if result.get("artists") else "Unknown"
                    album = result.get("album", {}).get("name", "Unknown") if result.get("album") else "Unknown"
                    duration = result.get("duration_seconds", 0) or 0
                    thumbnail = result.get("thumbnails", [{}])[0].get("url", "")
                    track = (title, video_id, artist_name, album, duration, thumbnail)
                    if track not in self.tracks:
                        self.tracks.append(track)
                        self.tree.insert("", "end", values=(title, artist_name, album, self.format_time(duration)))
                self.save_search_results()
                self.loading_label.config(text=f"Found {len(self.tracks)} tracks")
                self.window.after(2000, lambda: self.loading_label.config(text=""))
                self.window.config(cursor="")
                return

            except Exception as e:
                self.window.config(cursor="")
                if attempt == 1:
                    self.loading_label.config(text="Search failed. Try again.")
                    self.window.after(3000, lambda: self.loading_label.config(text=""))
                    messagebox.showerror("Error", f"Search failed: {str(e)}")
            finally:
                self.window.config(cursor="")

    def load_thumbnail(self, url):
        if not url:
            self.thumbnail_label.config(image=None)
            return
        try:
            if url not in self.image_cache:
                response = requests.get(url, timeout=5)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((40, 40), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_cache[url] = photo
                self.image_references.append(photo)
            self.thumbnail_label.config(image=self.image_cache[url])
        except Exception as e:
            self.thumbnail_label.config(image=None)

    def load_artist_thumbnail(self, artist_name):
        pass

    def play_selected(self):
        self.playing_playlist_sequentially = False
        if self.loading:
            return
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])

        if self.player and self.is_playing:
            self.player.stop()
            self.player.release()
            self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")

        self.current_track = self.tracks[index]
        self.from_playlist = bool(self.current_playlist)
        self.loading = True
        self.listening_history.append(self.current_track)
        self.save_listening_history()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def update_now_playing(self):
        if self.current_track:
            title = self.current_track[0]
            artist = self.current_track[2]
            album = self.current_track[3]
            thumbnail = self.current_track[5]
            self.track_label.config(text=title)
            self.artist_label.config(text=artist)
            self.load_thumbnail(thumbnail)
            self.like_button.config(text="❤️" if self.current_track in self.favorites else "♡")

    def update_progress(self):
        if self.player and self.is_playing:
            state = self.player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error):
                self.play_next()
                return
            if state == vlc.State.Playing:
                current_time = self.player.get_time() / 1000
                total_time = self.player.get_length() / 1000

                current_timestamp = time.time()
                if self.current_track and self.last_update_time:
                    duration_key = f"{self.current_track[0]} - {self.current_track[2]}"
                    time_delta = current_timestamp - self.last_update_time
                    self.listening_durations[duration_key] = self.listening_durations.get(duration_key, 0) + time_delta
                    self.total_listening_time += time_delta
                    self.update_user_level()
                    self.save_listening_durations()
                self.last_update_time = current_timestamp

                if total_time > 0:
                    self.progress['value'] = (current_time / total_time) * 100
                    self.current_time_label.config(text=self.format_time(current_time))
                    self.total_time_label.config(text=self.format_time(total_time))
                else:
                    self.progress['value'] = 0
                    self.current_time_label.config(text="0:00")
                    self.total_time_label.config(text="0:00")
            self.window.after(500, self.update_progress)
        else:
            self.progress['value'] = 0
            self.current_time_label.config(text="0:00")
            self.total_time_label.config(text="0:00")
            self.last_update_time = None

    def stream_music(self, video_id):
        try:
            self.window.config(cursor="wait")

            downloaded_track = next((track for track in self.downloads if track[1] == video_id), None)
            if downloaded_track:
                file_path = downloaded_track[6]
                if os.path.exists(file_path):
                    audio_url = file_path
                else:
                    self.downloads.remove(downloaded_track)
                    self.save_downloads()
                    audio_url = None
            else:
                audio_url = None

            if not audio_url:
                url = f"https://www.youtube.com/watch?v={video_id}"
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'force_generic_extractor': True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    audio_url = info['url']

            if self.player:
                self.player.stop()
                self.player.release()
                self.player = None

            self.player = vlc.MediaPlayer(audio_url)
            self.player.audio_set_volume(int(self.volume_slider.get()))
            self.player.play()
            self.is_playing = True
            self.play_button.config(text="⏸")
            self.loading = False
            self.window.after(1000, self.update_progress)
        except Exception as e:
            self.loading_label.config(text="Failed to play track")
            self.window.after(3000, lambda: self.loading_label.config(text=""))
            self.is_playing = False
            self.play_button.config(text="▶")
        finally:
            self.window.config(cursor="")

    def toggle_play_pause(self):
        if self.loading:
            return
        if self.player:
            if self.is_playing:
                self.player.pause()
                self.is_playing = False
                self.play_button.config(text="▶")
            else:
                self.player.play()
                self.is_playing = True
                self.play_button.config(text="⏸")
                self.window.after(1000, self.update_progress)
        elif self.current_track:
            self.loading = True
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def play_next(self):
        if self.loading:
            return
        if self.is_repeat and self.current_track:
            self.loading = True
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()
            return

        next_track = None
        if self.queue:
            next_track = self.queue.pop(0)
        elif self.is_shuffle and self.current_playlist and self.playlists[self.current_playlist]:
            if not self.shuffle_order:
                self.shuffle_order = random.sample(range(len(self.playlists[self.current_playlist])), len(self.playlists[self.current_playlist]))
            next_index = self.shuffle_order.pop(0)
            next_track = self.playlists[self.current_playlist][next_index]
        elif self.current_playlist and self.playlists[self.current_playlist] and self.playing_playlist_sequentially:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                next_track = self.playlists[self.current_playlist][current_index + 1]

        if next_track:
            self.current_track = next_track
            self.from_playlist = bool(self.current_playlist)
            self.loading = True
            self.listening_history.append(self.current_track)
            self.save_listening_history()
            self.update_now_playing()
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()
        else:
            if self.player:
                self.player.stop()
                self.player.release()
                self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")
            self.current_track = None
            self.from_playlist = False
            self.update_now_playing()

    def play_previous(self):
        if self.loading:
            return
        if self.player and self.player.get_time() > 5000:
            self.player.set_time(0)
            return
        if self.listening_history:
            if len(self.listening_history) > 1:
                self.listening_history.pop(-1)
                prev_track = self.listening_history[-1]
                self.current_track = prev_track
                self.from_playlist = bool(self.current_playlist)
                self.loading = True
                self.update_now_playing()
                threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def seek_track(self, event):
        if not self.player or not self.is_playing:
            return
        total_time = self.player.get_length() / 1000
        if total_time <= 0:
            return
        width = self.progress.winfo_width()
        click_x = event.x
        seek_percentage = click_x / width
        seek_time = seek_percentage * total_time * 1000
        self.player.set_time(int(seek_time))

    def set_volume(self, value):
        if self.player:
            volume = int(float(value))
            self.player.audio_set_volume(volume)
            self.is_muted = volume == 0
            self.mute_button.config(text="🔇" if self.is_muted else "🔊")

    def toggle_mute(self):
        if self.is_muted:
            self.volume_slider.set(50)
            self.set_volume(50)
        else:
            self.volume_slider.set(0)
            self.set_volume(0)

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        self.shuffle_order = []
        self.loading_label.config(text="Shuffle " + ("enabled" if self.is_shuffle else "disabled"))
        self.window.after(2000, lambda: self.loading_label.config(text=""))

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self.loading_label.config(text="Repeat " + ("enabled" if self.is_repeat else "disabled"))
        self.window.after(2000, lambda: self.loading_label.config(text=""))

    def add_to_queue(self):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        if track not in self.queue:
            self.queue.append(track)
            self.loading_label.config(text=f"Added to queue: {track[0]}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))

    def add_to_favorites(self):
        if not self.current_track:
            selection = self.tree.selection()
            if not selection:
                return
            index = self.tree.index(selection[0])
            self.current_track = self.tracks[index]
        if self.current_track not in self.favorites:
            self.favorites.append(self.current_track)
            self.like_button.config(text="❤️")
            self.loading_label.config(text=f"Added to favorites: {self.current_track[0]}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
        else:
            self.favorites.remove(self.current_track)
            self.like_button.config(text="♡")
            self.loading_label.config(text=f"Removed from favorites: {self.current_track[0]}")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
        self.show_favorites()

    def show_lyrics(self):
        if not self.current_track:
            self.loading_label.config(text="No track playing")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
            return

        dialog = tk.Toplevel(self.window)
        dialog.title(f"Lyrics: {self.current_track[0]}")
        dialog.geometry("500x600")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=self.bg_color)

        lyrics_frame = ttk.Frame(dialog)
        lyrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(lyrics_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(lyrics_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        lyrics_label = ttk.Label(scrollable_frame, text="Fetching lyrics...", font=("Helvetica", 12), wraplength=450, foreground="#ffffff")
        lyrics_label.pack(pady=10, padx=10)

        copy_btn = ttk.Button(dialog, text="📋 Copy Lyrics", command=lambda: self.copy_lyrics(lyrics_label), style="Rounded.TButton")
        copy_btn.pack(pady=10)
        copy_btn.bind("<Enter>", lambda e: self.show_tooltip(e, "Copy lyrics to clipboard"))
        copy_btn.bind("<Leave>", lambda e: self.hide_tooltip())

        threading.Thread(target=self.fetch_lyrics, args=(self.current_track[0], self.current_track[2], lyrics_label), daemon=True).start()

    def copy_lyrics(self, lyrics_label):
        lyrics = lyrics_label.cget("text")
        if lyrics and lyrics != "Fetching lyrics..." and lyrics != "Lyrics not found.":
            pyperclip.copy(lyrics)
            self.loading_label.config(text="Lyrics copied to clipboard")
            self.window.after(2000, lambda: self.loading_label.config(text=""))
        else:
            self.loading_label.config(text="No lyrics to copy")
            self.window.after(2000, lambda: self.loading_label.config(text=""))

    def fetch_lyrics(self, title, artist, lyrics_label):
        try:
            song = self.genius.search_song(title, artist)
            if song:
                lyrics = song.lyrics
                cleaned_lyrics = re.sub(r'\[.*?\]', '', lyrics)
                cleaned_lyrics = cleaned_lyrics.strip()
                lyrics_label.config(text=cleaned_lyrics)
            else:
                lyrics_label.config(text="Lyrics not found.")
        except Exception as e:
            lyrics_label.config(text="Lyrics not found.")

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.setup_styles()
        self.create_ui()
        self.loading_label.config(text="Theme changed")
        self.window.after(2000, lambda: self.loading_label.config(text=""))

    def format_time(self, seconds):
        if isinstance(seconds, str) and ':' in seconds:
            return seconds
        try:
            seconds = int(seconds)
        except (TypeError, ValueError):
            return "0:00"
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    def show_context_menu(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        self.context_menu.post(event.x_root, event.y_root)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = BeatNest()
    app.run()
