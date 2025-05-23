import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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
import uuid
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_CLIENT_ID = "34b9609c1e7040399366b042c7eb8149"
SPOTIFY_CLIENT_SECRET = "39c6ad0251b44ad5811f6d80b34c9fd7"

# Constants
APP_TITLE = "BeatNest 🎵"
WINDOW_SIZE = "1000x700"
COLORS = {
    "dark": {
        "bg": "#191414",
        "fg": "#FFFFFF",
        "accent": "#1DB954",
        "secondary": "#222326",
        "hover": "#282828",
        "button_bg": "#1DB954",
        "button_fg": "#FFFFFF",
        "button_active_bg": "#1ed760",
        "card_bg": "#232323",
        "card_shadow": "#101010",
    },
    "light": {
        "bg": "#f5f5f5",
        "fg": "#191414",
        "accent": "#1DB954",
        "secondary": "#e0e0e0",
        "hover": "#d0d0d0",
        "button_bg": "#1DB954",
        "button_fg": "#FFFFFF",
        "button_active_bg": "#1ed760",
        "card_bg": "#ffffff",
        "card_shadow": "#cccccc",
    }
}
FONTS = {
    "title": ("Segoe UI", 28, "bold"),
    "subtitle": ("Segoe UI", 20, "bold"),
    "label": ("Segoe UI", 12),
    "button": ("Segoe UI", 11, "bold"),
    "track_title": ("Segoe UI", 14, "bold"),
    "track_info": ("Segoe UI", 12),
    "small": ("Segoe UI", 9),
}
SIDEBAR_BUTTONS = [
    {"text": "🏠 Home", "command": "show_home", "tooltip": "Go to Home"},
    {"text": "🔍 Search", "command": "show_search", "tooltip": "Search for songs"},
    {"text": "⭐ Favorites", "command": "show_favorites", "tooltip": "View favorite tracks"},
    {"text": "📚 Playlists", "command": "show_playlists", "tooltip": "Manage playlists"},
    {"text": "🎛 Mix", "command": "show_mix", "tooltip": "View your personal mix"},
    {"text": "📥 downloads", "command": "show_downloads", "tooltip": "View downloaded tracks"},
    {"text": "⚙️ Settings", "command": "show_settings", "tooltip": "Open settings"},
]
CONTROL_BUTTONS = [
    {"text": "🔀", "command": "toggle_shuffle", "tooltip": "Toggle shuffle"},
    {"text": "⏮", "command": "play_previous", "tooltip": "Previous track"},
    {"text": "▶", "command": "toggle_play_pause", "tooltip": "Play/Pause"},
    {"text": "⏭", "command": "play_next", "tooltip": "Next track"},
    {"text": "🔁", "command": "toggle_repeat", "tooltip": "Toggle repeat"},
]
ADDITIONAL_CONTROLS = [
    {"text": "➕", "command": "add_to_playlist_from_player", "tooltip": "Add to playlist"},
    {"text": "💻", "command": "show_device_info", "tooltip": "Select device"},
    {"text": "🎤", "command": "show_lyrics", "tooltip": "Show lyrics"},
]

class BeatNest:
    """Main application class for BeatNest music player."""
    
    def __init__(self):
        self.window = tk.Tk()
        self._setup_window()
        self._initialize_state()
        self._initialize_services()
        self._load_data()
        self.show_loading_screen()
        self.window.after(2000, self._initialize_ui)
        self.home_search_var = tk.StringVar()
        self.search_var = tk.StringVar()

    def _setup_window(self):
        self.window.title(APP_TITLE)
        self.window.geometry(WINDOW_SIZE)
        self.window.resizable(True, True)

    def _initialize_state(self):
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
        self.tooltip = None
        self.tooltip_alpha = 0
        self.search_filter = tk.StringVar(value="songs")  # For search type filtering

    def _initialize_services(self):
        self.genius = lyricsgenius.Genius(
            "9M_xBhLea6HK5dKV7nxHQaNo_ZtmdecjyIXqXiQbswMKmtYwSxezfM0W0Qajjmvh",
            timeout=5
        )
        try:
            self.ytmusic = YTMusic()
        except Exception as e:
            self.ytmusic = None
            messagebox.showerror("Error", "Failed to initialize YTMusic API. Search may not work.")

    def _load_data(self):
        self._load_json("playlists.json", lambda data: setattr(self, "playlists", data), {})
        self._load_json("downloads.json", lambda data: setattr(self, "downloads", [tuple(track) for track in data]), [])
        self._load_json("recommendations.json", self._load_recommendations, {"tracks": [], "play_counts": {}})
        self._load_json("search_results.json", lambda data: setattr(self, "tracks", [tuple(track) for track in data]), [])
        self._load_json("listening_history.json", lambda data: setattr(self, "listening_history", [tuple(track) for track in data]), [])
        self._load_json("recent_searches.json", lambda data: setattr(self, "recent_searches", data), [])
        self._load_json("listening_durations.json", lambda data: setattr(self, "listening_durations", data), {})
        self._load_json("user_level.json", self._load_user_level, {"level": 0, "level_name": "Listener", "total_time": 0})

    def _load_json(self, filename, setter, default):
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    data = json.load(f)
                    setter(data)
            else:
                setter(default)
        except Exception:
            setter(default)

    def _load_recommendations(self, data):
        self.recommended_tracks = [tuple(track) for track in data.get("tracks", [])]
        self.recommendation_play_counts = data.get("play_counts", {})

    def _load_user_level(self, data):
        self.user_level = data.get("level", 0)
        self.user_level_name = data.get("level_name", "Listener")
        self.total_listening_time = data.get("total_time", 0)

    def show_loading_screen(self):
        self.style = ttk.Style()
        self._configure_loading_styles()
        
        self.loading_frame = ttk.Frame(self.window, style="Loading.TFrame")
        self.loading_frame.pack(fill=tk.BOTH, expand=True)
        
        self.logo_canvas = tk.Canvas(
            self.loading_frame, 
            width=200,
            height=200,
            bg=COLORS["dark"]["bg"],
            highlightthickness=0
        )
        self.logo_canvas.place(relx=0.5, rely=0.4, anchor="center")
        
        self.logo_items = []
        colors = ["#1DB954", "#1ED760", "#23E268"]
        for i in range(3):
            size = 200 - (i * 40)
            item = self.logo_canvas.create_arc(
                20+(i*20), 20+(i*20),
                size-(i*20), size-(i*20),
                start=0, extent=300,
                fill=colors[i]
            )
            self.logo_items.append(item)
        
        title_frame = ttk.Frame(self.loading_frame, style="Loading.TFrame")
        title_frame.place(relx=0.5, rely=0.65, anchor="center")
        
        title = tk.Label(
            title_frame,
            text="BeatNest",
            font=("Helvetica", 48, "bold"),
            fg="#FFFFFF",
            bg=COLORS["dark"]["bg"]
        )
        title.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="Your Personal Music Companion",
            font=("Helvetica", 16),
            fg="#B3B3B3",
            bg=COLORS["dark"]["bg"]
        )
        subtitle.pack(pady=10)
        
        progress_frame = ttk.Frame(self.loading_frame, style="Loading.TFrame")
        progress_frame.place(relx=0.5, rely=0.8, anchor="center")
        
        self.loading_progress = ttk.Progressbar(
            progress_frame,
            style="LoadingBar.Horizontal.TProgressbar",
            length=300,
            mode="determinate"
        )
        self.loading_progress.pack(pady=10)
        
        self.loading_status = tk.Label(
            progress_frame,
            text="Starting up...",
            font=("Helvetica", 12),
            fg="#B3B3B3",
            bg=COLORS["dark"]["bg"]
        )
        self.loading_status.pack()
        
        self._animate_logo()
        self.animate_loading_progress()
        self.animate_loading_text()

    def _configure_loading_styles(self):
        colors = COLORS["dark"]
        self.style.configure("Loading.TFrame", background=colors["bg"])
        self.style.configure(
            "LoadingBar.Horizontal.TProgressbar",
            troughcolor=colors["secondary"],
            background=colors["accent"],
            borderwidth=0,
            thickness=6
        )

    def _animate_logo(self):
        if not hasattr(self, "logo_canvas") or not self.loading_frame.winfo_exists():
            return
        angles = [0, 120, 240]
        for item, angle in zip(self.logo_items, angles):
            current_angle = float(self.logo_canvas.itemcget(item, "start"))
            new_angle = (current_angle + 2) % 360
            self.logo_canvas.itemconfig(item, start=new_angle)
        self.window.after(20, self._animate_logo)

    def animate_loading_progress(self):
        if not hasattr(self, "loading_progress") or not self.loading_frame.winfo_exists():
            return
        current = self.loading_progress["value"]
        if current < 100:
            increment = 0.5 if current < 20 else 1.2 if current < 60 else 0.5
            self.loading_progress["value"] = current + increment
            self.window.after(20, self.animate_loading_progress)
        else:
            self.loading_progress["value"] = 0

    def animate_loading_text(self):
        if not hasattr(self, "loading_status") or not self.loading_frame.winfo_exists():
            return
        messages = [
            "Starting up...",
            "Loading resources...",
            "Preparing your library...",
            "Almost ready...",
            "Launching BeatNest..."
        ]
        current_idx = getattr(self, "_loading_msg_idx", 0)
        self.loading_status.config(text=messages[current_idx])
        self._loading_msg_idx = (current_idx + 1) % len(messages)
        self.window.after(1000, self.animate_loading_text)

    def _initialize_ui(self):
        self.loading_frame.destroy()
        delattr(self, "loading_progress")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_styles()
        self._create_ui()
        self._setup_media_controls()

    def _setup_styles(self):
        colors = COLORS["dark" if self.is_dark_mode else "light"]
        self.window.configure(bg=colors["bg"])
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure(
            "TButton",
            padding=8,
            font=FONTS["button"],
            borderwidth=0,
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            relief="flat"
        )
        self.style.map(
            "TButton",
            background=[("active", colors["button_active_bg"])],
            foreground=[("active", colors["button_fg"])]
        )
        self.style.configure(
            "Rounded.TButton",
            background=colors["button_bg"],
            foreground=colors["button_fg"],
            borderwidth=0,
            padding=8,
            font=FONTS["button"],
            relief="flat",
            bordercolor=colors["secondary"],
            borderradius=10
        )
        self.style.map(
            "Rounded.TButton",
            background=[("active", colors["button_active_bg"])],
            foreground=[("active", colors["button_fg"])]
        )
        self.style.configure(
            "Search.TEntry",
            padding=12,
            font=("Helvetica", 14),
            fieldbackground=colors["secondary"],
            foreground=colors["fg"],
            relief="flat",
            bordercolor=colors["accent"],
            borderradius=20
        )
        self.style.configure(
            "TLabel",
            font=FONTS["label"],
            background=colors["bg"],
            foreground=colors["fg"]
        )
        self.style.configure(
            "TEntry",
            padding=10,
            font=FONTS["label"],
            fieldbackground=colors["secondary"],
            foreground=colors["fg"],
            relief="flat"
        )
        self.style.configure(
            "TCombobox",
            padding=10,
            font=FONTS["label"],
            fieldbackground=colors["secondary"],
            foreground=colors["fg"],
            relief="flat"
        )
        self.style.configure(
            "TProgressbar",
            thickness=5,
            background=colors["accent"],
            troughcolor=colors["secondary"],
            borderwidth=0
        )
        self.style.configure(
            "Treeview",
            rowheight=60,
            font=FONTS["label"],
            background=colors["secondary"],
            foreground=colors["fg"],
            fieldbackground=colors["secondary"]
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["accent"])],
            foreground=[("selected", "#ffffff")]
        )
        self.style.configure(
            "Horizontal.TScale",
            background=colors["bg"],
            troughcolor=colors["secondary"],
            sliderrelief="flat"
        )
        self.style.map("Horizontal.TScale", background=[("active", colors["hover"])])

    def _create_ui(self):
        # Ana pencereyi grid ile iki satıra böl
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=0)
        self.window.grid_columnconfigure(0, weight=1)
    
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self._create_sidebar()
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        self._create_player_frame_grid()
        self.show_home()
        self._create_recommendation_bar()
        self._create_player_frame_grid()
        self.show_home()


    
    def _create_player_frame_grid(self):
        player_frame = ttk.Frame(self.window, style="TFrame")
        player_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self._create_left_player_frame(player_frame)
        self._create_center_player_frame(player_frame)
        self._create_right_player_frame(player_frame)
    def _create_sidebar(self):
        sidebar = tk.Frame(self.main_frame, bg=COLORS["dark"]["bg"], width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)
        for btn_config in SIDEBAR_BUTTONS:
            btn = tk.Button(
                sidebar,
                text=btn_config["text"],
                command=getattr(self, btn_config["command"]),
                font=FONTS["button"],
                bg=COLORS["dark"]["secondary"],
                fg=COLORS["dark"]["fg"],
                activebackground=COLORS["dark"]["accent"],
                activeforeground="#fff",
                bd=0,
                relief="flat",
                height=2,
                width=20,
                highlightthickness=0,
                cursor="hand2"
            )
            btn.pack(fill=tk.X, pady=8, padx=16)

    def _create_player_frame(self):
        # player_frame doğrudan self.window'a pack edilmeli
        player_frame = ttk.Frame(self.window, style="TFrame")
        player_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        # ...devamı aynı...
        self._create_left_player_frame(player_frame)
        self._create_center_player_frame(player_frame)
        self._create_right_player_frame(player_frame)

    def _create_left_player_frame(self, player_frame):
        left_frame = ttk.Frame(player_frame, style="TFrame")
        left_frame.pack(side=tk.LEFT, padx=10)
        self.thumbnail_label = ttk.Label(left_frame, image=None, background=COLORS["dark"]["bg"])
        self.thumbnail_label.pack(side=tk.LEFT, padx=5)
        info_frame = ttk.Frame(left_frame, style="TFrame")
        info_frame.pack(side=tk.LEFT, padx=5)
        self.track_label = ttk.Label(
            info_frame,
            text="No track playing",
            font=FONTS["label"],
            wraplength=200,
            foreground="#ffffff"
        )
        self.track_label.pack(anchor="w")
        self.artist_label = ttk.Label(
            info_frame,
            text="",
            font=FONTS["small"],
            wraplength=200,
            foreground="#b3b3b3"
        )
        self.artist_label.pack(anchor="w")
        self.like_button = ttk.Button(
            left_frame,
            text="♡",
            command=self.add_to_favorites,
            width=3,
            style="Rounded.TButton"
        )
        self.like_button.pack(side=tk.LEFT, padx=5)
        self.like_button.bind("<Enter>", lambda e: self._show_tooltip(e, "Add to favorites"))
        self.like_button.bind("<Leave>", lambda e: self._hide_tooltip())

    def _create_center_player_frame(self, player_frame):
        center_frame = ttk.Frame(player_frame, style="TFrame")
        center_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        controls_frame = ttk.Frame(center_frame, style="TFrame")
        controls_frame.pack(anchor="center")
        for btn_config in CONTROL_BUTTONS:
            btn = ttk.Button(
                controls_frame,
                text=btn_config["text"],
                command=getattr(self, btn_config["command"]),
                width=3,
                style="Rounded.TButton"
            )
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, t=btn_config["tooltip"]: self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())
            if btn_config["text"] == "▶":
                self.play_button = btn
        progress_frame = ttk.Frame(center_frame, style="TFrame")
        progress_frame.pack(fill=tk.X, pady=5, padx=50)
        self.current_time_label = ttk.Label(
            progress_frame,
            text="0:00",
            font=FONTS["small"],
            foreground="#b3b3b3"
        )
        self.current_time_label.pack(side=tk.LEFT, padx=5)
        self.progress = ttk.Progressbar(progress_frame, length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.progress.bind("<Button-1>", self.seek_track)
        self.total_time_label = ttk.Label(
            progress_frame,
            text="0:00",
            font=FONTS["small"],
            foreground="#b3b3b3"
        )
        self.total_time_label.pack(side=tk.LEFT, padx=5)

    def _create_recommendation_bar(self):
            # Eğer varsa eski barı yok et
            if hasattr(self, "recommendation_bar"):
                self.recommendation_bar.destroy()
            self.recommendation_bar = tk.Frame(self.window, bg=COLORS["dark"]["secondary"], height=70)
            self.recommendation_bar.grid(row=1, column=0, sticky="ew")
            # Önerilen şarkıları yükle
            self._update_recommendation_bar()
        
    def _update_recommendation_bar(self):
            for widget in self.recommendation_bar.winfo_children():
                widget.destroy()
            if not self.recommended_tracks:
                return
            tk.Label(
                self.recommendation_bar,
                text="Recommended:",
                font=FONTS["track_info"],
                bg=COLORS["dark"]["secondary"],
                fg=COLORS["dark"]["accent"]
            ).pack(side=tk.LEFT, padx=10)
            for track in self.recommended_tracks[:3]:  # İlk 3 öneri
                btn = tk.Button(
                    self.recommendation_bar,
                    text=track[0][:18] + ("..." if len(track[0]) > 18 else ""),
                    font=FONTS["small"],
                    bg=COLORS["dark"]["accent"],
                    fg="#fff",
                    bd=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda t=track: self.play_recommended_track(t)
                )
                btn.pack(side=tk.LEFT, padx=5, pady=10)











    def _create_right_player_frame(self, player_frame):
        right_frame = ttk.Frame(player_frame, style="TFrame")
        right_frame.pack(side=tk.RIGHT, padx=10)
        for btn_config in ADDITIONAL_CONTROLS:
            btn = ttk.Button(
                right_frame,
                text=btn_config["text"],
                command=getattr(self, btn_config["command"]),
                width=3,
                style="Rounded.TButton"
            )
            btn.pack(side=tk.LEFT, padx=3)
            btn.bind("<Enter>", lambda e, t=btn_config["tooltip"]: self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())
        volume_frame = ttk.Frame(right_frame, style="TFrame")
        volume_frame.pack(side=tk.LEFT, padx=(5, 0))
        self.mute_button = ttk.Button(
            volume_frame,
            text="🔊",
            command=self.toggle_mute,
            width=3,
            style="Rounded.TButton"
        )
        self.mute_button.pack(side=tk.LEFT, padx=(0, 2))
        self.mute_button.bind("<Enter>", lambda e: self._show_tooltip(e, "Toggle mute"))
        self.mute_button.bind("<Leave>", lambda e: self._hide_tooltip())
        self.volume_slider = ttk.Scale(
            volume_frame,
            from_=0,
            to=100,
            orient="horizontal",
            command=self.set_volume,
            length=100,
            style="Horizontal.TScale"
        )
        self.volume_slider.set(50)
        self.volume_slider.pack(side=tk.LEFT)

    def _show_tooltip(self, event, text):
        if self.tooltip:
            self.tooltip.destroy()
        x, y = event.x_root + 20, event.y_root + 10
        self.tooltip = tk.Toplevel(self.window)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tooltip,
            text=text,
            background=COLORS["dark"]["button_bg"],
            foreground=COLORS["dark"]["button_fg"],
            font=FONTS["small"],
            padx=5,
            pady=3,
            borderwidth=1,
            relief="solid"
        )
        label.pack()
        self.tooltip_alpha = 0
        self._fade_in_tooltip()

    def _fade_in_tooltip(self):
        if self.tooltip:
            self.tooltip_alpha += 0.1
            if self.tooltip_alpha >= 1:
                self.tooltip_alpha = 1
            self.tooltip.wm_attributes("-alpha", self.tooltip_alpha)
            if self.tooltip_alpha < 1:
                self.window.after(50, self._fade_in_tooltip)

    def _hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.tooltip_alpha = 0

    def _setup_media_controls(self):
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

    def _save_json(self, filename, data):
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def save_playlists(self):
        self._save_json("playlists.json", self.playlists)

    def save_downloads(self):
        self._save_json("downloads.json", [list(track) for track in self.downloads])

    def save_recommendations(self):
        data = {
            "tracks": [list(track) for track in self.recommended_tracks],
            "play_counts": self.recommendation_play_counts
        }
        self._save_json("recommendations.json", data)

    def save_search_results(self):
        self._save_json("search_results.json", [list(track) for track in self.tracks])

    def save_listening_history(self):
        self._save_json("listening_history.json", [list(track) for track in self.listening_history])

    def save_recent_searches(self):
        self._save_json("recent_searches.json", self.recent_searches)

    def save_listening_durations(self):
        self._save_json("listening_durations.json", self.listening_durations)

    def save_user_level(self):
        data = {
            "level": self.user_level,
            "level_name": self.user_level_name,
            "total_time": self.total_listening_time
        }
        self._save_json("user_level.json", data)

    def update_user_level(self):
        levels = [
            (0, "Listener"),
            (3600, "Music Enthusiast"),
            (10800, "Melody Master"),
            (36000, "Harmony Hero"),
            (108000, "Symphony Star"),
            (360000, "Legendary Listener")
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
        greetings = {
            range(0, 12): f"Good Morning, {self.user_level_name}!",
            range(12, 17): f"Good Afternoon, {self.user_level_name}!",
            range(17, 22): f"Good Evening, {self.user_level_name}!",
            range(22, 24): f"Good Night, {self.user_level_name}!"
        }
        for time_range, greeting in greetings.items():
            if hour in time_range:
                return greeting
        return f"Hello, {self.user_level_name}!"

    def on_track_frame_enter(self, event):
        event.widget.configure(background=COLORS["dark" if self.is_dark_mode else "light"]["hover"])

    def on_track_frame_leave(self, event):
        event.widget.configure(background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])

    def show_home(self):
        self.clear_content()
        # Arama barı
        search_container = tk.Frame(self.content_frame, bg=COLORS["dark"]["bg"])
        search_container.pack(fill=tk.X, pady=(10, 20))
        search_entry = tk.Entry(
            search_container,
            textvariable=self.home_search_var,  # <-- Burada değişti!
            font=("Segoe UI", 16),
            bg=COLORS["dark"]["secondary"],
            fg=COLORS["dark"]["fg"],
            bd=0,
            relief="flat",
            highlightthickness=0,
            insertbackground=COLORS["dark"]["fg"]
        )
        search_entry.pack(fill=tk.X, padx=30, pady=10, ipady=10)
        search_entry.bind("<KeyRelease>", self._home_search_suggestions)
        search_entry.bind("<Return>", lambda e: self._home_search_action())
        # ...devamı aynı...
        search_btn = tk.Button(
            search_container,
            text="🔍",
            command=self.search_music,
            font=FONTS["button"],
            bg=COLORS["dark"]["accent"],
            fg="#fff",
            bd=0,
            relief="flat",
            width=4,
            height=1,
            cursor="hand2"
        )
        search_btn.place(relx=0.97, rely=0.5, anchor="e")
    
        # Anlık arama sonuçları için frame
        self.home_search_results_frame = tk.Frame(self.content_frame, bg=COLORS["dark"]["bg"])
        self.home_search_results_frame.pack(fill=tk.X, padx=30)
    
        # Eğer arama kutusu boşsa önerilenler ve playlistler
        if not self.search_var.get().strip():
            greeting = tk.Label(
                self.content_frame,
                text=self.get_greeting(),
                font=FONTS["title"],
                anchor="w",
                bg=COLORS["dark"]["bg"],
                fg=COLORS["dark"]["accent"]
            )
            greeting.pack(pady=(0, 20), padx=30, anchor="w")
            self._generate_recommendations()
            self._display_recommended_tracks(self.content_frame)
            self._update_recommendation_bar()
            ttk.Label(self.content_frame, text="Your Playlists", font=FONTS["subtitle"]).pack(anchor="w", pady=(30, 10), padx=30)
            playlist_frame = tk.Frame(self.content_frame, bg=COLORS["dark"]["bg"])
            playlist_frame.pack(fill=tk.X, padx=30)
            for name in self.playlists:
                self._create_playlist_entry(playlist_frame, name)
        
    def _home_search_action(self):
            query = self.home_search_var.get().strip()
            if query:
                self._home_search_suggestions(None)



    def _home_search_suggestions(self, event):
        query = self.home_search_var.get().strip()  # <-- Burada değişti!
        # ...devamı aynı...
        # Sonuçlar frame'ini temizle
        for widget in self.home_search_results_frame.winfo_children():
            widget.destroy()
        if not query:
            # Arama kutusu boşsa ana ekranı tekrar göster
            self.show_home()
            return
        # Arama işlemini thread ile yap
        def search_and_display():
            try:
                results = self.ytmusic.search(query, filter=self.search_filter.get(), limit=10)
                tracks = []
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    track = self._create_track_tuple(result)
                    if track and track not in tracks:
                        tracks.append(track)
                self.window.after(0, lambda: self._show_home_search_results(tracks))
            except Exception:
                pass
        threading.Thread(target=search_and_display, daemon=True).start()
        
    def _show_home_search_results(self, tracks):
            for widget in self.home_search_results_frame.winfo_children():
                widget.destroy()
            if not tracks:
                return
            for track in tracks:
                self._create_search_track_frame(self.home_search_results_frame, track)






    def _create_scrollable_frame(self):
        canvas = tk.Canvas(self.content_frame, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return canvas, scrollable_frame

    def _display_top_tracks(self, parent):
        if not self.listening_history:
            return
        ttk.Label(parent, text="Your Top Tracks", font=FONTS["subtitle"]).pack(anchor="w", pady=(20, 10))
        top_tracks_frame = ttk.Frame(parent)
        top_tracks_frame.pack(fill=tk.X, pady=10)
        track_counts = Counter(self.listening_history)
        for track, count in track_counts.most_common(5):
            self._create_track_card(top_tracks_frame, track, count)

    def _generate_recommendations(self):
        self.recommended_tracks = []
        self.recommendation_play_counts = {}
    
        # 1. Dinleme geçmişinden en çok dinlenen sanatçılardan öner
        if self.ytmusic and self.listening_history:
            artist_counter = Counter([track[2] for track in self.listening_history])
            top_artists = [artist for artist, _ in artist_counter.most_common(2)]
            for artist in top_artists:
                try:
                    results = self.ytmusic.search(artist, filter="songs", limit=3)
                    for result in results:
                        rec_track = self._create_track_tuple(result)
                        if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                            self.recommended_tracks.append(rec_track)
                            self.recommendation_play_counts[rec_track[0]] = 0
                except Exception:
                    continue
    
        # 2. Favorilerden benzer şarkılar öner
        if self.ytmusic and self.favorites:
            for fav in self.favorites[:2]:
                try:
                    related = self.ytmusic.get_song(fav[1]).get("related", {}).get("items", [])
                    for item in related[:2]:
                        rec_track = self._create_track_tuple(item)
                        if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                            self.recommended_tracks.append(rec_track)
                            self.recommendation_play_counts[rec_track[0]] = 0
                except Exception:
                    continue
    
        # 3. Son aramalardan öner
        if self.ytmusic and self.recent_searches:
            for search in self.recent_searches[:2]:
                try:
                    results = self.ytmusic.search(search, filter="songs", limit=2)
                    for result in results:
                        rec_track = self._create_track_tuple(result)
                        if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                            self.recommended_tracks.append(rec_track)
                            self.recommendation_play_counts[rec_track[0]] = 0
                except Exception:
                    continue
    
        # 4. Eğer hala az öneri varsa popüler/örnek şarkılar ekle
        if self.ytmusic and len(self.recommended_tracks) < 5:
            try:
                results = self.ytmusic.search("The Beatles", filter="songs", limit=5 - len(self.recommended_tracks))
                for result in results:
                    rec_track = self._create_track_tuple(result)
                    if rec_track and rec_track not in self.recommended_tracks:
                        self.recommended_tracks.append(rec_track)
                        self.recommendation_play_counts[rec_track[0]] = 0
            except Exception:
                pass
        

    def _add_related_tracks(self, track):
        try:
            related = self.ytmusic.get_song(track[1]).get("related", {}).get("items", [])
            for item in related[:2]:
                rec_track = self._create_track_tuple(item)
                if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                    self.recommended_tracks.append(rec_track)
                    self.recommendation_play_counts[rec_track[0]] = 0
        except Exception:
            pass

    def _add_artist_tracks(self, track):
        try:
            results = self.ytmusic.search(track[2], filter="songs", limit=2)
            for result in results:
                if not isinstance(result, dict):
                    continue
                rec_track = self._create_track_tuple(result)
                if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                    self.recommended_tracks.append(rec_track)
                    self.recommendation_play_counts[rec_track[0]] = 0
        except Exception:
            pass

    def _add_recent_search_tracks(self):
        try:
            results = self.ytmusic.search(self.recent_searches[0], filter="songs", limit=3)
            for result in results:
                if not isinstance(result, dict):
                    continue
                rec_track = self._create_track_tuple(result)
                if rec_track and rec_track not in self.recommended_tracks and rec_track not in self.listening_history:
                    self.recommended_tracks.append(rec_track)
                    self.recommendation_play_counts[rec_track[0]] = 0
        except Exception:
            pass

    def _add_default_tracks(self):
        try:
            results = self.ytmusic.search("The Beatles", filter="songs", limit=5 - len(self.recommended_tracks))
            for result in results:
                if not isinstance(result, dict):
                    continue
                rec_track = self._create_track_tuple(result)
                if rec_track and rec_track not in self.recommended_tracks:
                    self.recommended_tracks.append(rec_track)
                    self.recommendation_play_counts[rec_track[0]] = 0
        except Exception:
            pass

    def _create_track_tuple(self, item):
        title = item.get("title", "Unknown")
        video_id = item.get("videoId", "")
        if not video_id:
            return None
        artist_name = item.get("artists", [{}])[0].get("name", "Unknown") if item.get("artists") else "Unknown"
        album = item.get("album", {}).get("name", "Unknown") if item.get("album") else "Unknown"
        duration = item.get("duration_seconds", 0) or 0
        thumbnail = item.get("thumbnails", [{}])[0].get("url", "")
        return (title, video_id, artist_name, album, duration, thumbnail)

    def _display_recommended_tracks(self, parent):
        if not self.recommended_tracks:
            return
        ttk.Label(parent, text="Recommended for You", font=FONTS["subtitle"]).pack(anchor="w", pady=(20, 10))
        recommended_frame = ttk.Frame(parent)
        recommended_frame.pack(fill=tk.X, pady=10)
        for i, track in enumerate(self.recommended_tracks):
            self._create_search_track_frame(recommended_frame, track)

    def _create_track_card(self, parent, track, count, is_recommended=False):
        card_frame = tk.Frame(parent, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"], bd=2, relief="flat")
        card_frame.pack(side=tk.LEFT, padx=5, pady=5, fill="y")
        card_frame.bind("<Enter>", lambda e: card_frame.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["hover"]))
        card_frame.bind("<Leave>", lambda e: card_frame.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"]))
        card_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_recommended_track(t) if is_recommended else self.play_track(t))
        
        thumbnail_label = ttk.Label(card_frame, image=None, background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        thumbnail_label.pack(pady=5)
        self.load_thumbnail_for_track(track[5], thumbnail_label)
        
        info_frame = ttk.Frame(card_frame)
        info_frame.pack(fill=tk.X, padx=5)
        ttk.Label(info_frame, text=track[0][:20] + ("..." if len(track[0]) > 20 else ""), font=FONTS["track_title"], foreground="#ffffff").pack(anchor="w")
        ttk.Label(
            info_frame,
            text=f"{track[2][:15] + ('...' if len(track[2]) > 15 else '')} • {count} plays",
            font=FONTS["small"],
            foreground="#b3b3b3"
        ).pack(anchor="w")
        
        play_btn = ttk.Button(
            card_frame,
            text="▶",
            command=lambda t=track: self.play_recommended_track(t) if is_recommended else self.play_track(t),
            width=3,
            style="Rounded.TButton"
        )
        play_btn.pack(pady=5)
        play_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Play this track"))
        play_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def load_thumbnail_for_track(self, url, label):
        if not url:
            self.window.after(0, lambda: label.config(image=None) if label.winfo_exists() else None)
            return
        try:
            if url not in self.image_cache:
                response = requests.get(url, timeout=5)
                img_data = BytesIO(response.content)
                img = Image.open(img_data).resize((60, 60), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_cache[url] = photo
                self.image_references.append(photo)
            # Ana thread'de ve label hâlâ varsa güncelle
            self.window.after(0, lambda: label.config(image=self.image_cache[url]) if label.winfo_exists() else None)
        except Exception:
            self.window.after(0, lambda: label.config(image=None) if label.winfo_exists() else None)

    def play_track(self, track):
        self.playing_playlist_sequentially = False
        self._stop_current_track()
        self.current_track = track
        self.from_playlist = bool(self.current_playlist)
        self.loading = True
        # Aynı şarkı art arda 
        if not self.listening_history or self.listening_history[-1] != self.current_track:
            self.listening_history.append(self.current_track)
            self.save_listening_history()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def play_recommended_track(self, track):
        self.playing_playlist_sequentially = False
        self._stop_current_track()
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

    def _stop_current_track(self):
        if self.player and self.is_playing:
            self.player.stop()
            self.player.release()
            self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")

    def show_search(self):
        self.clear_content()
        search_container = ttk.Frame(self.content_frame, style="TFrame")
        search_container.pack(fill=tk.X, pady=10)
        
        # Large search bar
        search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            font=("Segoe UI", 14),
            bg=COLORS["dark"]["secondary"],
            fg=COLORS["dark"]["fg"],
            bd=0,
            relief="flat",
            highlightthickness=0,
            insertbackground=COLORS["dark"]["fg"]
        )
        search_entry.pack(fill=tk.X, padx=20, pady=16, ipady=8)
        search_entry.pack(fill=tk.X, padx=(0, 10), pady=10)
        search_entry.bind("<KeyRelease>", self._search_suggestions)
        search_entry.bind("<Return>", lambda e: self.search_music())
        
        # Filter buttons
        filter_frame = ttk.Frame(search_container, style="TFrame")
        filter_frame.pack(fill=tk.X, pady=5)
        filters = [
            ("Songs", "songs"),
            ("Artists", "artists"),
            ("Albums", "albums")
        ]
        for text, value in filters:
            btn = ttk.Radiobutton(
                filter_frame,
                text=text,
                value=value,
                variable=self.search_filter,
                style="Rounded.TButton",
                command=self.search_music
            )
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, t=f"Search for {text.lower()}": self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())
        
        # Suggestions and results
        self.suggestions_frame = ttk.Frame(self.content_frame, style="TFrame")
        self.suggestions_frame.pack(fill=tk.X, pady=5)
        canvas, self.search_results_frame = self._create_scrollable_frame()
        
        self.loading_label = ttk.Label(self.content_frame, text="", font=FONTS["small"])
        self.loading_label.pack(pady=5)
        self._populate_search_results()

    def _search_suggestions(self, event):
        query = self.search_var.get().strip()
        if not query or not self.ytmusic:
            self.suggestions_frame.destroy()
            self.suggestions_frame = ttk.Frame(self.content_frame, style="TFrame")
            self.suggestions_frame.pack(fill=tk.X, pady=5)
            self.tracks = []
            self._populate_search_results()
            return
        threading.Thread(target=self._fetch_suggestions, args=(query,), daemon=True).start()
        self.search_music()

    def _fetch_suggestions(self, query):
        try:
            suggestions = self.ytmusic.get_search_suggestions(query, filter=self.search_filter.get())
            self.window.after(0, lambda: self._display_suggestions(suggestions))
        except Exception:
            self.window.after(0, lambda: self._display_suggestions([]))

    def _display_suggestions(self, suggestions):
        for widget in self.suggestions_frame.winfo_children():
            widget.destroy()
        if suggestions:
            ttk.Label(self.suggestions_frame, text="Suggestions", font=FONTS["subtitle"]).pack(anchor="w", pady=5)
            for suggestion in suggestions[:5]:
                btn = ttk.Button(
                    self.suggestions_frame,
                    text=suggestion,
                    command=lambda s=suggestion: self._select_suggestion(s),
                    style="Rounded.TButton"
                )
                btn.pack(fill=tk.X, padx=10, pady=2)
                btn.bind("<Enter>", lambda e, s=suggestion: self._show_tooltip(e, f"Search for {s}"))
                btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _select_suggestion(self, suggestion):
        self.search_var.set(suggestion)
        self.search_music()

    def _create_search_buttons(self, parent):
        buttons = [
            {"text": "🔍 Search", "command": self.search_music, "tooltip": "Search for songs"},
            {"text": "🗑 Clear Search", "command": self.clear_search, "tooltip": "Clear search query"},
            {"text": "Sort by Duration", "command": self.sort_by_duration, "tooltip": "Sort tracks by duration"},
        ]
        for btn_config in buttons:
            btn = ttk.Button(parent, text=btn_config["text"], command=btn_config["command"], style="Rounded.TButton")
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, t=btn_config["tooltip"]: self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _create_search_treeview(self):
        self.tree = ttk.Treeview(
            self.content_frame,
            columns=("Title", "Artist", "Album", "Duration"),
            show="headings"
        )
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
        self.context_menu = tk.Menu(self.window, tearoff=0, bg=COLORS["dark"]["button_bg"], fg=COLORS["dark"]["button_fg"], font=FONTS["small"])
        self.context_menu.add_command(label="Play Now", command=self.play_selected)
        self.context_menu.add_command(label="Add to Queue", command=self.add_to_queue)
        self.context_menu.add_command(label="Add to Favorites", command=self.add_to_favorites)
        self.context_menu.add_command(label="Add to Playlist", command=self.add_to_playlist_from_menu)
        self.context_menu.add_command(label="Remove from Playlist", command=self.remove_from_playlist)
        self.context_menu.add_command(label="Download", command=self.download_track)

    def _populate_search_results(self):
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()
        if not self.tracks:
            ttk.Label(self.search_results_frame, text="Sonuç bulunamadı.", font=FONTS["label"]).pack(anchor="w", pady=10)
            return
    
        for track in self.tracks:
            self._create_search_track_frame(self.search_results_frame, track)
    
    def _create_search_track_frame(self, parent, track):
        frame = tk.Frame(parent, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"], bd=1, relief="solid")
        frame.pack(fill=tk.X, pady=2, padx=5)  # Daha küçük padding
        # ...devamı aynı...
        frame.bind("<Enter>", self.on_track_frame_enter)
        frame.bind("<Leave>", self.on_track_frame_leave)
        frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))
    
        # Kapak fotoğrafı
        thumbnail_label = ttk.Label(frame, image=None, background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        thumbnail_label.pack(side=tk.LEFT, padx=10)
        threading.Thread(target=self.load_thumbnail_for_track, args=(track[5], thumbnail_label), daemon=True).start()
    
        # Bilgi ve butonlar aynı satırda
        info_frame = ttk.Frame(frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
        # Şarkı ismini kısalt (ör: 35 karakter)
        title = track[0]
        max_len = 35
        if len(title) > max_len:
            title = title[:max_len-3] + "..."
    
        ttk.Label(info_frame, text=title, font=FONTS["track_title"], foreground="#ffffff", anchor="w").pack(anchor="w")
        ttk.Label(info_frame, text=f"{track[2]} • {track[3]}", font=FONTS["track_info"], foreground="#b3b3b3", anchor="w").pack(anchor="w")
        ttk.Label(info_frame, text=self.format_time(track[4]), font=FONTS["small"], foreground="#b3b3b3", anchor="w").pack(anchor="w")
    
        # Butonlar (her zaman sağda)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=tk.RIGHT, padx=5)
    
        play_btn = ttk.Button(
            btn_frame,
            text="▶",
            command=lambda t=track: self.play_track(t),
            width=4,
            style="Rounded.TButton"
        )
        play_btn.pack(side=tk.LEFT, padx=2)
        play_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Çal"))
        play_btn.bind("<Leave>", lambda e: self._hide_tooltip())
    
        fav_btn = ttk.Button(
            btn_frame,
            text="♥" if track in self.favorites else "♡",
            command=lambda t=track: self._toggle_favorite_from_search(t, fav_btn),
            width=4,
            style="Rounded.TButton"
        )
        fav_btn.pack(side=tk.LEFT, padx=2)
        fav_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Favorilere ekle/çıkar"))
        fav_btn.bind("<Leave>", lambda e: self._hide_tooltip())
    
        add_playlist_btn = ttk.Button(
            btn_frame,
            text="➕",
            command=lambda t=track: self._show_add_to_playlist_dialog(t),
            width=4,
            style="Rounded.TButton"
        )
        add_playlist_btn.pack(side=tk.LEFT, padx=2)
        add_playlist_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Playlist'e ekle"))
        add_playlist_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def show_favorites(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Favorites", font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        for track in self.favorites:
            self._create_track_card(scrollable_frame, track, 0)
        fav_btn = ttk.Button(
            self.content_frame,
            text="❤️ Add Current to Favorites",
            command=self.add_to_favorites,
            style="Rounded.TButton"
        )
        fav_btn.pack(pady=10)
        fav_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Add current track to favorites"))
        fav_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        self.loading_label = ttk.Label(
            self.content_frame,
            text="No favorites yet!" if not self.favorites else "",
            font=FONTS["small"]
        )
        self.loading_label.pack(pady=5)

    def show_playlists(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Playlists", font=FONTS["title"]).pack(pady=20)
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        create_btn = ttk.Button(
            button_frame,
            text="➕ Create Playlist",
            command=self.create_playlist,
            style="Rounded.TButton"
        )
        create_btn.pack(side=tk.LEFT, padx=5)
        create_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Create a new playlist"))
        create_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        import_btn = ttk.Button(
            button_frame,
            text="📤 Import Playlist",
            command=self.import_playlist,
            style="Rounded.TButton"
        )
        import_btn.pack(side=tk.LEFT, padx=5)
        import_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Import a playlist"))
        import_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        playlist_frame = ttk.Frame(self.content_frame)
        playlist_frame.pack(fill=tk.BOTH, expand=True)
        for name in self.playlists:
            self._create_playlist_entry(playlist_frame, name)

    def _create_playlist_entry(self, parent, name):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        playlist_btn = ttk.Button(
            frame,
            text=name,
            command=lambda: self.show_playlist(name),
            style="Rounded.TButton"
        )
        playlist_btn.pack(side=tk.LEFT)
        playlist_btn.bind("<Enter>", lambda e: self._show_tooltip(e, f"View {name} playlist"))
        playlist_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        play_btn = ttk.Button(
            frame,
            text="▶",
            command=lambda: self.play_playlist_sequentially(name),
            width=4,
            style="Rounded.TButton"
        )
        play_btn.pack(side=tk.LEFT, padx=5)
        play_btn.bind("<Enter>", lambda e: self._show_tooltip(e, f"Play {name} playlist sequentially"))
        play_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        delete_btn = ttk.Button(
            frame,
            text="🗑",
            command=lambda: self.delete_playlist(name),
            style="Rounded.TButton"
        )
        delete_btn.pack(side=tk.RIGHT)
        delete_btn.bind("<Enter>", lambda e: self._show_tooltip(e, f"Delete {name} playlist"))
        delete_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def import_playlist(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Import Playlist")
        dialog.geometry("500x320")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        
        ttk.Label(dialog, text="Import Playlist", font=FONTS["subtitle"]).pack(pady=10)
        ttk.Label(dialog, text="Playlist Name:").pack()
        playlist_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=playlist_name_var, width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Import from:").pack(pady=5)
        import_type = tk.StringVar(value="file")
        ttk.Radiobutton(dialog, text="JSON File", value="file", variable=import_type).pack()
        ttk.Radiobutton(dialog, text="Spotify URL", value="url", variable=import_type).pack()
        
        file_frame = ttk.Frame(dialog)
        file_frame.pack(pady=5)
        file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=file_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Browse", command=lambda: file_var.set(filedialog.askopenfilename(filetypes=[("JSON files", "*.json")]))).pack(side=tk.LEFT)
        
        url_frame = ttk.Frame(dialog)
        url_frame.pack(pady=5)
        url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=url_var, width=30).pack()
        
        import_btn = ttk.Button(
            dialog,
            text="Import",
            command=lambda: self._do_import_playlist(playlist_name_var.get(), import_type.get(), file_var.get(), url_var.get(), dialog),
            style="Rounded.TButton"
        )
        import_btn.pack(pady=10)
        import_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Import the playlist"))
        import_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _do_import_playlist(self, playlist_name, import_type, file_path, spotify_url, dialog):
        if not playlist_name.strip():
            messagebox.showerror("Error", "Playlist name cannot be empty")
            return
        if playlist_name in self.playlists:
            messagebox.showerror("Error", "Playlist already exists")
            return
        self.playlists[playlist_name] = []
        if import_type == "file" and file_path:
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    for track_data in data.get("tracks", []):
                        track = self._create_track_tuple(track_data)
                        if track and track not in self.playlists[playlist_name]:
                            self.playlists[playlist_name].append(track)
                self.save_playlists()
                self._show_temp_message(f"Imported playlist: {playlist_name}")
                self.show_playlists()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import playlist: {str(e)}")
        elif import_type == "url" and spotify_url:
            threading.Thread(target=self._import_spotify_playlist, args=(playlist_name, spotify_url, dialog), daemon=True).start()
        else:
            messagebox.showerror("Error", "Please provide a file or URL")

    def _import_spotify_playlist(self, playlist_name, spotify_url, dialog):
        try:
            if "spotify.com/playlist/" not in spotify_url:
                self.window.after(0, lambda: messagebox.showerror("Error", "Invalid Spotify URL"))
                return
    
            # Spotipy ile playlisti çek
            sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            ))
            playlist_id = spotify_url.split("/")[-1].split("?")[0]
            results = sp.playlist_tracks(playlist_id)
            tracks = results["items"]
    
            added_count = 0
            for item in tracks:
                track_info = item["track"]
                title = track_info["name"]
                artist = track_info["artists"][0]["name"]
                # YouTube Music'te arama yap
                ytm_results = self.ytmusic.search(f"{title} {artist}", filter="songs", limit=1)
                if ytm_results:
                    ytm_track = self._create_track_tuple(ytm_results[0])
                    if ytm_track and ytm_track not in self.playlists[playlist_name]:
                        self.playlists[playlist_name].append(ytm_track)
                        added_count += 1
    
            self.save_playlists()
            self.window.after(0, lambda: self._show_temp_message(f"Imported {added_count} tracks from Spotify"))
            self.window.after(0, self.show_playlists)
            self.window.after(0, dialog.destroy)
        except Exception as e:
            self.window.after(0, lambda: messagebox.showerror("Error", f"Failed to import Spotify playlist: {str(e)}"))

    def show_mix(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Your Mix", font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        mix_tracks = self._generate_mix_tracks()
        if not mix_tracks:
            ttk.Label(scrollable_frame, text="Listen to more tracks to create your mix!", font=FONTS["label"]).pack(pady=10)
            return
        for track in mix_tracks[:20]:
            self._create_track_card(scrollable_frame, track, 0)
        self.loading_label = ttk.Label(self.content_frame, text="", font=FONTS["small"])
        self.loading_label.pack(pady=5)

    def _generate_mix_tracks(self):
        mix_tracks = []
        if not self.listening_history or not self.ytmusic:
            return mix_tracks
        track_counts = Counter(self.listening_history)
        mix_tracks.extend([track for track, _ in track_counts.most_common(10)])
        for track, _ in track_counts.most_common(3):
            try:
                related = self.ytmusic.get_song(track[1]).get("related", {}).get("items", [])
                for item in related[:2]:
                    rec_track = self._create_track_tuple(item)
                    if rec_track and rec_track not in mix_tracks:
                        mix_tracks.append(rec_track)
            except Exception:
                pass
        return mix_tracks

    def show_downloads(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Downloads", font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        for track in self.downloads:
            self._create_download_track_frame(scrollable_frame, track)
        self.loading_label = ttk.Label(
            self.content_frame,
            text="No downloaded tracks yet!" if not self.downloads else "",
            font=FONTS["small"]
        )
        self.loading_label.pack(pady=5)

    def _create_download_track_frame(self, parent, track):
        track_frame = tk.Frame(parent, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        track_frame.pack(fill=tk.X, pady=5)
        track_frame.bind("<Enter>", self.on_track_frame_enter)
        track_frame.bind("<Leave>", self.on_track_frame_leave)
        track_frame.bind("<Double-Button-1>", lambda e, t=track: self.play_track(t))
        thumbnail_label = ttk.Label(track_frame, image=None, background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        thumbnail_label.pack(side=tk.LEFT, padx=10)
        self.load_thumbnail_for_track(track[5], thumbnail_label)
        info_frame = ttk.Frame(track_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(info_frame, text=track[0], font=FONTS["track_title"], foreground="#ffffff").pack(anchor="w")
        ttk.Label(
            info_frame,
            text=f"{track[2]} • {track[3]} • {self.format_time(track[4])}",
            font=FONTS["track_info"],
            foreground="#b3b3b3"
        ).pack(anchor="w")
        play_btn = ttk.Button(
            track_frame,
            text="▶",
            command=lambda t=track: self.play_track(t),
            width=4,
            style="Rounded.TButton"
        )
        play_btn.pack(side=tk.RIGHT, padx=10)
        play_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Play this track"))
        play_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        delete_btn = ttk.Button(
            track_frame,
            text="🗑",
            command=lambda t=track: self.delete_download(t),
            width=4,
            style="Rounded.TButton"
        )
        delete_btn.pack(side=tk.RIGHT, padx=5)
        delete_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Delete downloaded track"))
        delete_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def download_track(self):
        selection = self.tree.selection() if hasattr(self, 'tree') else []
        if not selection:
            self._show_temp_message("No track selected")
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        if track in self.downloads:
            self._show_temp_message("Track already downloaded")
            return
        self._show_temp_message("Downloading...")
        self.window.config(cursor="watch")
        threading.Thread(target=self._download_and_save_track, args=(track,), daemon=True).start()

    def _download_and_save_track(self, track):
        try:
            video_id = track[1]
            url = f"https://www.youtube.com/watch?v={video_id}"
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"downloads/{track[0]} - {track[2]}.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
                "quiet": True,
                "no_warnings": True,
            }
            os.makedirs("downloads", exist_ok=True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            file_path = f"downloads/{track[0]} - {track[2]}.mp3"
            downloaded_track = (*track, file_path)
            self.downloads.append(downloaded_track)
            self.save_downloads()
            self._show_temp_message(f"Downloaded: {track[0]}")
        except Exception as e:
            self._show_temp_message("Download failed", duration=3000)
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
            self._show_temp_message(f"Deleted: {track[0]}")
        except Exception:
            self._show_temp_message("Failed to delete track")

    def create_playlist(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Create Playlist")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        ttk.Label(dialog, text="Enter playlist name:").pack(pady=10)
        playlist_name_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=playlist_name_var, width=30).pack(pady=5)
        create_btn = ttk.Button(
            dialog,
            text="Create",
            command=lambda: self._add_new_playlist(playlist_name_var.get(), dialog),
            style="Rounded.TButton"
        )
        create_btn.pack(pady=10)
        create_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Create the playlist"))
        create_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _add_new_playlist(self, playlist_name, dialog):
        playlist_name = playlist_name.strip()
        if not playlist_name:
            messagebox.showerror("Error", "Playlist name cannot be empty")
            return
        if len(playlist_name) > 50 or not re.match(r'^[a-zA-Z0-9\s_-]+$', playlist_name):
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
        ttk.Label(self.content_frame, text=name, font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        self.tracks = self.playlists[name]
        for track in self.tracks:
            self._create_playlist_track_frame(scrollable_frame, track)
        button_frame = ttk.Frame(self.content_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self._create_playlist_buttons(button_frame, name)
        self.loading_label = ttk.Label(
            self.content_frame,
            text="No tracks in this playlist!" if not self.tracks else "",
            font=FONTS["small"]
        )
        self.loading_label.pack(pady=5)

    def _create_playlist_track_frame(self, parent, track):
        card = tk.Frame(
            parent,
            bg=COLORS["dark"]["card_bg"],
            bd=0,
            highlightthickness=0
        )
        card.pack(fill=tk.X, pady=10, padx=10)
        card.configure(relief="flat")
        card.bind("<Enter>", lambda e: card.config(bg=COLORS["dark"]["hover"]))
        card.bind("<Leave>", lambda e: card.config(bg=COLORS["dark"]["card_bg"]))
    
        thumbnail_label = tk.Label(card, image=None, bg=COLORS["dark"]["card_bg"])
        thumbnail_label.pack(side=tk.LEFT, padx=16, pady=8)
        self.load_thumbnail_for_track(track[5], thumbnail_label)
    
        info_frame = tk.Frame(card, bg=COLORS["dark"]["card_bg"])
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(info_frame, text=track[0], font=FONTS["track_title"], bg=COLORS["dark"]["card_bg"], fg="#fff").pack(anchor="w")
        tk.Label(info_frame, text=f"{track[2]} • {track[3]} • {self.format_time(track[4])}", font=FONTS["track_info"], bg=COLORS["dark"]["card_bg"], fg="#b3b3b3").pack(anchor="w")
    
        btn_frame = tk.Frame(card, bg=COLORS["dark"]["card_bg"])
        btn_frame.pack(side=tk.RIGHT, padx=10)
        play_btn = tk.Button(
            btn_frame,
            text="▶",
            command=lambda t=track: self.play_track(t),
            font=FONTS["button"],
            bg=COLORS["dark"]["accent"],
            fg="#fff",
            bd=0,
            relief="flat",
            width=3,
            height=1,
            cursor="hand2"
        )
        play_btn.pack(side=tk.LEFT, padx=4)
        remove_btn = tk.Button(
            btn_frame,
            text="🗑",
            command=lambda t=track: self.remove_from_playlist(t),
            font=FONTS["button"],
            bg=COLORS["dark"]["secondary"],
            fg="#fff",
            bd=0,
            relief="flat",
            width=3,
            height=1,
            cursor="hand2"
        )
        remove_btn.pack(side=tk.LEFT, padx=4)

    def _create_playlist_buttons(self, parent, name):
        buttons = [
            {"text": "➕ Add Current to Playlist", "command": self.add_to_playlist, "tooltip": "Add current track to playlist"},
            {"text": "📥 Download All", "command": lambda: self.download_playlist(name), "tooltip": "Download all tracks in playlist"},
            {"text": "Sort by Duration", "command": self.sort_by_duration, "tooltip": "Sort tracks by duration"},
        ]
        for btn_config in buttons:
            btn = ttk.Button(parent, text=btn_config["text"], command=btn_config["command"], style="Rounded.TButton")
            btn.pack(side=tk.LEFT, padx=5)
            btn.bind("<Enter>", lambda e, t=btn_config["tooltip"]: self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def show_settings(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Settings", font=FONTS["title"]).pack(pady=20)
        settings_frame = ttk.Frame(self.content_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        self._create_theme_setting(settings_frame)
        self._create_stats_setting(settings_frame)

    def _create_theme_setting(self, parent):
        theme_frame = ttk.Frame(parent)
        theme_frame.pack(fill=tk.X, pady=10)
        ttk.Label(theme_frame, text="Theme:", font=FONTS["label"]).pack(side=tk.LEFT, padx=10)
        theme_btn = ttk.Button(
            theme_frame,
            text="Toggle Dark/Light Mode",
            command=self.toggle_theme,
            style="Rounded.TButton"
        )
        theme_btn.pack(side=tk.LEFT, padx=10)
        theme_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Toggle between dark and light mode"))
        theme_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _create_stats_setting(self, parent):
        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=10)
        ttk.Label(stats_frame, text="Stats:", font=FONTS["label"]).pack(side=tk.LEFT, padx=10)
        stats_btn = ttk.Button(
            stats_frame,
            text="View Listening Stats",
            command=self.show_stats,
            style="Rounded.TButton"
        )
        stats_btn.pack(side=tk.LEFT, padx=10)
        stats_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "View your listening statistics"))
        stats_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def show_stats(self):
        self.clear_content()
        ttk.Label(self.content_frame, text="Listening Statistics", font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        stats_frame = ttk.Frame(self.content_frame)
        stats_frame.pack(fill=tk.X, pady=10)
        ttk.Label(stats_frame, text=f"Level: {self.user_level_name}", font=FONTS["track_title"]).pack(anchor="w", padx=10)
        hours = int(self.total_listening_time // 3600)
        minutes = int((self.total_listening_time % 3600) // 60)
        ttk.Label(
            stats_frame,
            text=f"Total Listening Time: {hours}h {minutes}m",
            font=FONTS["label"]
        ).pack(anchor="w", padx=10)
        if not self.listening_history:
            ttk.Label(self.content_frame, text="No listening history yet!", font=FONTS["label"]).pack(pady=10)
            return
        canvas, scrollable_frame = self._create_scrollable_frame()
        track_counts = Counter(self.listening_history)
        for track, count in track_counts.most_common():
            self._create_stats_track_frame(scrollable_frame, track, count)

    def _create_stats_track_frame(self, parent, track, count):
        track_frame = tk.Frame(parent, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        track_frame.pack(fill=tk.X, pady=5)
        thumbnail_label = ttk.Label(track_frame, image=None, background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        thumbnail_label.pack(side=tk.LEFT, padx=10)
        self.load_thumbnail_for_track(track[5], thumbnail_label)
        info_frame = ttk.Frame(track_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(info_frame, text=track[0], font=FONTS["track_title"], foreground="#ffffff").pack(anchor="w")
        duration_key = f"{track[0]} - {track[2]}"
        duration = self.listening_durations.get(duration_key, 0)
        duration_mins = int(duration // 60)
        duration_secs = int(duration % 60)
        ttk.Label(
            info_frame,
            text=f"{track[2]} • Played {count} times • Listened for {duration_mins}:{duration_secs:02d}",
            font=FONTS["track_info"],
            foreground="#b3b3b3"
        ).pack(anchor="w")

    def delete_playlist(self, name):
        del self.playlists[name]
        if self.current_playlist == name:
            self.current_playlist = None
        self.save_playlists()
        self.show_playlists()

    def download_playlist(self, playlist_name):
        if not self.playlists[playlist_name]:
            self._show_temp_message("Playlist is empty")
            return
        dialog, progress_label, progress_bar, status_label, cancel_btn = self._create_download_dialog(playlist_name)
        self.download_cancelled = False
        total_tracks = len(self.playlists[playlist_name])
        self._start_playlist_download(playlist_name, (dialog, progress_label, progress_bar, status_label, cancel_btn), total_tracks)

    def _create_download_dialog(self, playlist_name):
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Downloading Playlist: {playlist_name}")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        progress_label = ttk.Label(dialog, text="downloading (If the loading bar is not full, please don't worry, just wait)", font=FONTS["small"])
        progress_label.pack(pady=10)
        progress_bar = ttk.Progressbar(dialog, mode="determinate", length=300)
        progress_bar.pack(pady=10)
        status_label = ttk.Label(dialog, text="", font=FONTS["small"])
        status_label.pack(pady=5)
        cancel_btn = ttk.Button(
            dialog,
            text="Cancel",
            command=lambda: self.cancel_download(dialog)
        )
        cancel_btn.pack(pady=10)
        return dialog, progress_label, progress_bar, status_label, cancel_btn

    def _start_playlist_download(self, playlist_name, dialog_info, total_tracks):
        dialog, progress_label, progress_bar, status_label, cancel_btn = dialog_info
        completed_downloads = 0

        def update_progress(track_name, current, total):
            if not dialog.winfo_exists():
                return
            progress_bar["value"] = (current / total) * 100
            progress_label.config(text=f"Downloading: {track_name}")
            status_label.config(text=f"Progress: {current}/{total} tracks")
            dialog.update()

        def download_track_threaded(track):
            nonlocal completed_downloads
            try:
                if self.download_cancelled:
                    return
                if track in self.downloads:
                    completed_downloads += 1
                    update_progress(track[0], completed_downloads, total_tracks)
                    return
                video_id = track[1]
                url = f"https://www.youtube.com/watch?v={video_id}"
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": f"downloads/{track[0]} - {track[2]}.%(ext)s",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }],
                    "quiet": True,
                    "no_warnings": True,
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
                for thread in threads:
                    thread.join()
                if not self.download_cancelled and dialog.winfo_exists():
                    progress_label.config(text="Download completed!")
                    status_label.config(text=f"Successfully downloaded {completed_downloads}/{total_tracks} tracks")
                    cancel_btn.config(text="Close")
                    self._show_temp_message(f"Playlist '{playlist_name}' downloaded")
            except Exception as e:
                if dialog.winfo_exists():
                    progress_label.config(text="Download failed!")
                    status_label.config(text=str(e))

        threading.Thread(target=download_all_tracks, daemon=True).start()

    def cancel_download(self, dialog):
        self.download_cancelled = True
        dialog.destroy()

    def add_to_playlist_from_menu(self):
        selection = self.tree.selection() if hasattr(self, 'tree') else []
        if not selection:
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        self._show_add_to_playlist_dialog(track)

    def add_to_playlist_from_player(self):
        if not self.current_track:
            self._show_temp_message("No track playing")
            return
        self._show_add_to_playlist_dialog(self.current_track)

    def _show_add_to_playlist_dialog(self, track):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add to Playlist")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        ttk.Label(dialog, text="Select or create a playlist:").pack(pady=10)
        playlist_var = tk.StringVar()
        playlist_dropdown = ttk.Combobox(dialog, textvariable=playlist_var, values=list(self.playlists.keys()))
        playlist_dropdown.pack(pady=5, padx=10)
        new_playlist_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=new_playlist_var, width=30).pack(pady=5)
        add_btn = ttk.Button(
            dialog,
            text="Add",
            command=lambda: self._add_to_selected_playlist(track, playlist_var.get(), new_playlist_var.get(), dialog),
            style="Rounded.TButton"
        )
        add_btn.pack(pady=10)
        add_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Add to selected playlist"))
        add_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _add_to_selected_playlist(self, track, selected_playlist, new_playlist_name, dialog):
        if not selected_playlist and not new_playlist_name:
            messagebox.showerror("Error", "Please select or create a playlist")
            return
        if new_playlist_name and new_playlist_name in self.playlists:
            messagebox.showerror("Error", "Playlist already exists")
            return
        if new_playlist_name:
            self.playlists[new_playlist_name] = []
            self.save_playlists()
            selected_playlist = new_playlist_name
        if track not in self.playlists[selected_playlist]:
            self.playlists[selected_playlist].append(track)
            self.save_playlists()
            self._show_temp_message(f"Added to {selected_playlist}")
            dialog.destroy()
        else:
            messagebox.showerror("Error", "Track already in playlist")
        dialog.destroy()

    def add_to_playlist(self):
        if not self.current_track:
            self._show_temp_message("No track playing")
            return
        if not self.current_playlist:
            self._show_temp_message("No playlist selected")
            return
        if self.current_track not in self.playlists[self.current_playlist]:
            self.playlists[self.current_playlist].append(self.current_track)
            self.save_playlists()
            self._show_temp_message(f"Added to {self.current_playlist}")
            self.show_playlist(self.current_playlist)
        else:
            self._show_temp_message("Track already in playlist")

    def remove_from_playlist(self, track=None):
        if not self.current_playlist:
            return
        if track:
            if track in self.playlists[self.current_playlist]:
                self.playlists[self.current_playlist].remove(track)
                self.save_playlists()
                self.show_playlist(self.current_playlist)
                self._show_temp_message(f"Removed from {self.current_playlist}")
            return
        if hasattr(self, 'tree'):
            selection = self.tree.selection()
            if not selection:
                return
            selected_track = self.tracks[self.tree.index(selection[0])]
            if selected_track in self.playlists[self.current_playlist]:
                self.playlists[self.current_playlist].remove(selected_track)
                self.save_playlists()
                self.show_playlist(self.current_playlist)
                self._show_temp_message(f"Removed from {self.current_playlist}")

    def sort_by_duration(self):
        if not self.tracks:
            return
        self.tracks.sort(key=lambda x: x[4])
        if self.current_playlist:
            self.playlists[self.current_playlist] = self.tracks
            self.save_playlists()
        self._populate_search_results()

    def show_context_menu(self, event):
        selection = self.tree.selection() if hasattr(self, 'tree') else []
        if selection:
            self.context_menu.post(event.x_root, event.y_root)

    def play_selected(self):
        selection = self.tree.selection() if hasattr(self, 'tree') else []
        if not selection:
            return
        index = self.tree.index(selection[0])
        self.play_track(self.tracks[index])

    def add_to_queue(self):
        selection = self.tree.selection() if hasattr(self, 'tree') else []
        if not selection:
            self._show_temp_message("No track selected")
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        if track not in self.queue:
            self.queue.append(track)
            self._show_temp_message(f"Added to queue: {track[0]}")
        else:
            self._show_temp_message("Track already in queue")

    def add_to_favorites(self):
        track = None
        if hasattr(self, 'tree'):
            selection = self.tree.selection()
            if selection:
                index = self.tree.index(selection[0])
                track = self.tracks[index]
        if not track and self.current_track:
            track = self.current_track
        if not track:
            self._show_temp_message("No track selected")
            return
        if track not in self.favorites:
            self.favorites.append(track)
            self._show_temp_message(f"Added to favorites: {track[0]}")
            if track == self.current_track:
                self.like_button.config(text="♥")
        else:
            self.favorites.remove(track)
            self._show_temp_message(f"Removed from favorites: {track[0]}")
            if track == self.current_track:
                self.like_button.config(text="♡")
        self.save_favorites()

    def save_favorites(self):
        self._save_json("favorites.json", [list(track) for track in self.favorites])

    def search_music(self):
        query = self.search_var.get().strip()
        if not query or not self.ytmusic:
            self.tracks = []
            self._populate_search_results()
            return
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            if len(self.recent_searches) > 10:
                self.recent_searches.pop()
            self.save_recent_searches()
        self.loading_label.config(text="Searching...")
        self.window.config(cursor="watch")
        threading.Thread(target=self._perform_search, args=(query,), daemon=True).start()

    def _perform_search(self, query):
        try:
            results = self.ytmusic.search(query, filter=self.search_filter.get(), limit=20)
            tracks = []
            for result in results:
                if not isinstance(result, dict):
                    continue
                track = self._create_track_tuple(result)
                if track and track not in tracks:
                    tracks.append(track)
            self.tracks = tracks
            self.save_search_results()
            self.window.after(0, self._update_search_results)
        except Exception as e:
            self.window.after(0, lambda: self._show_temp_message(f"Search failed: {str(e)}"))
        finally:
            self.window.after(0, lambda: self.window.config(cursor=""))

    def _update_search_results(self):
        self.loading_label.config(text="")
        self._populate_search_results()

    def clear_search(self):
        self.search_var.set("")
        self.tracks = []
        self._populate_search_results()

    def stream_music(self, video_id):
        try:
            url = self._get_stream_url(video_id)
            if not url:
                self._show_temp_message("Failed to stream track")
                self.loading = False
                return
            self.player = vlc.MediaPlayer(url)
            self.player.audio_set_volume(int(self.volume_slider.get()))
            self.player.play()
            self.is_playing = True
            self.play_button.config(text="⏸")
            self.loading = False
            self.window.after(100, self._check_playback)
            self._update_progress()
            self.last_update_time = time.time()
            self._track_listening_duration()
        except Exception as e:
            self._show_temp_message(f"Streaming error: {str(e)}")
            self.loading = False

    def _get_stream_url(self, video_id):
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info["url"]
        except Exception:
            return None

    def _check_playback(self):
        if not self.player:
            return
        if self.player.get_state() == vlc.State.Ended:
            self._handle_track_ended()
        else:
            self.window.after(1000, self._check_playback)

    def _handle_track_ended(self):
        self.is_playing = False
        self.play_button.config(text="▶")
        if self.is_repeat:
            self.play_track(self.current_track)
        elif self.playing_playlist_sequentially and self.current_playlist:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                self.current_track = self.playlists[self.current_playlist][current_index + 1]
                self.play_track(self.current_track)
            else:
                self.playing_playlist_sequentially = False
        elif self.queue:
            self.current_track = self.queue.pop(0)
            self.play_track(self.current_track)
        elif self.is_shuffle and self.shuffle_order:
            next_index = self.shuffle_order.pop(0)
            if self.from_playlist and self.current_playlist:
                self.current_track = self.playlists[self.current_playlist][next_index]
                self.play_track(self.current_track)
        elif self.from_playlist and self.current_playlist:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                self.current_track = self.playlists[self.current_playlist][current_index + 1]
                self.play_track(self.current_track)
            else:
                self.current_track = None
                self.update_now_playing()

    def _track_listening_duration(self):
        if not self.is_playing or not self.current_track:
            return
        current_time = time.time()
        if self.last_update_time:
            duration = current_time - self.last_update_time
            self.total_listening_time += duration
            duration_key = f"{self.current_track[0]} - {self.current_track[2]}"
            self.listening_durations[duration_key] = self.listening_durations.get(duration_key, 0) + duration
            self.save_listening_durations()
            self.save_user_level()
            self.update_user_level()
        self.last_update_time = current_time
        self.window.after(1000, self._track_listening_duration)

    def update_now_playing(self):
        if not self.current_track:
            self.track_label.config(text="No track playing")
            self.artist_label.config(text="")
            self.thumbnail_label.config(image=None)
            self.like_button.config(text="♡")
            self.current_time_label.config(text="0:00")
            self.total_time_label.config(text="0:00")
            self.progress["value"] = 0
            return
        self.track_label.config(text=self.current_track[0])
        self.artist_label.config(text=f"{self.current_track[2]} • {self.current_track[3]}")
        self.load_thumbnail_for_track(self.current_track[5], self.thumbnail_label)
        self.like_button.config(text="♥" if self.current_track in self.favorites else "♡")
        self.total_time_label.config(text=self.format_time(self.current_track[4]))

    def _update_progress(self):
        if not self.player or not self.is_playing:
            return
        try:
            current_time = self.player.get_time() / 1000
            total_time = self.current_track[4]
            self.current_time_label.config(text=self.format_time(current_time))
            self.progress["value"] = (current_time / total_time) * 100
            self.window.after(1000, self._update_progress)
        except Exception:
            self.window.after(1000, self._update_progress)

    def seek_track(self, event):
        if not self.player or not self.current_track:
            return
        x = event.x
        width = self.progress.winfo_width()
        fraction = x / width
        new_time = fraction * self.current_track[4] * 1000
        self.player.set_time(int(new_time))

    def toggle_play_pause(self):
        if not self.current_track:
            return
        if self.loading:
            return
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_button.config(text="▶")
        else:
            self.player.play()
            self.is_playing = True
            self.play_button.config(text="⏸")
            self._update_progress()
            self.last_update_time = time.time()
            self._track_listening_duration()

    def play_next(self):
        if self.queue:
            self.current_track = self.queue.pop(0)
            self.play_track(self.current_track)
        elif self.is_shuffle and self.shuffle_order:
            next_index = self.shuffle_order.pop(0)
            if self.from_playlist and self.current_playlist:
                self.current_track = self.playlists[self.current_playlist][next_index]
                self.play_track(self.current_track)
        elif self.from_playlist and self.current_playlist:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                self.current_track = self.playlists[self.current_playlist][current_index + 1]
                self.play_track(self.current_track)
        elif self.current_track:
            self._play_next_recommended()

    def _play_next_recommended(self):
        if not self.recommended_tracks:
            return
        self.current_track = self.recommended_tracks[0]
        self.play_recommended_track(self.current_track)

    def play_previous(self):
        if not self.current_track:
            return
        if self.from_playlist and self.current_playlist:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index > 0:
                self.current_track = self.playlists[self.current_playlist][current_index - 1]
                self.play_track(self.current_track)

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        if self.is_shuffle and self.current_playlist:
            self.shuffle_order = list(range(len(self.playlists[self.current_playlist])))
            if self.current_track:
                current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
                if current_index in self.shuffle_order:
                    self.shuffle_order.remove(current_index)
            random.shuffle(self.shuffle_order)
        else:
            self.shuffle_order = []
        self._show_temp_message("Shuffle " + ("ON" if self.is_shuffle else "OFF"))

    def toggle_repeat(self):
        self.is_repeat = not self.is_repeat
        self._show_temp_message("Repeat " + ("ON" if self.is_repeat else "OFF"))

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.player.audio_set_volume(0)
            self.mute_button.config(text="🔇")
        else:
            volume = int(self.volume_slider.get())
            self.player.audio_set_volume(volume)
            self.mute_button.config(text="🔊")
        self._show_temp_message("Mute " + ("ON" if self.is_muted else "OFF"))

    def set_volume(self, value):
        volume = int(float(value))
        if self.player and not self.is_muted:
            self.player.audio_set_volume(volume)

    def format_time(self, seconds):
        if seconds is None or seconds <= 0:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_temp_message(self, message, duration=2000):
        if hasattr(self, 'loading_label'):
            self.loading_label.config(text=message)
            self.window.after(duration, lambda: self.loading_label.config(text=""))

    def show_lyrics(self):
        if not self.current_track:
            self._show_temp_message("No track playing")
            return
        dialog = tk.Toplevel(self.window)
        dialog.title("Lyrics")
        dialog.geometry("400x500")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        ttk.Label(dialog, text=f"{self.current_track[0]} - {self.current_track[2]}", font=FONTS["track_title"]).pack(pady=10)
        lyrics_text = tk.Text(dialog, height=20, width=50, bg=COLORS["dark" if self.is_dark_mode else "light"]["secondary"], fg=COLORS["dark" if self.is_dark_mode else "light"]["fg"], font=FONTS["label"])
        lyrics_text.pack(pady=10, padx=10)
        lyrics_text.config(state="normal")
        lyrics_text.delete(1.0, tk.END)
        threading.Thread(target=self._fetch_lyrics, args=(self.current_track[0], self.current_track[2], lyrics_text, dialog), daemon=True).start()

    def _fetch_lyrics(self, title, artist, text_widget, dialog):
        try:
            song = self.genius.search_song(title, artist, get_full_info=False)
            if song and song.lyrics:
                lyrics = song.lyrics
                if dialog.winfo_exists():
                    self.window.after(0, lambda: text_widget.insert(tk.END, lyrics))
            else:
                if dialog.winfo_exists():
                    self.window.after(0, lambda: text_widget.insert(tk.END, "Lyrics not found"))
            if dialog.winfo_exists():
                self.window.after(0, lambda: text_widget.config(state="disabled"))
        except Exception:
            if dialog.winfo_exists():
                self.window.after(0, lambda: text_widget.insert(tk.END, "Failed to fetch lyrics"))
                self.window.after(0, lambda: text_widget.config(state="disabled"))

    def show_device_info(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Device Info")
        dialog.geometry("300x200")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        ttk.Label(dialog, text="Connected Devices", font=FONTS["track_title"]).pack(pady=10)
        device_var = tk.StringVar(value="This Device")
        devices = ["This Device", "Speaker", "Headphones"]
        ttk.Combobox(dialog, textvariable=device_var, values=devices, state="readonly").pack(pady=10)
        ttk.Button(dialog, text="Connect", command=dialog.destroy, style="Rounded.TButton").pack(pady=10)

    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self._setup_styles()
        self._create_ui()
        self.show_settings()

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = BeatNest()
    app.run()
