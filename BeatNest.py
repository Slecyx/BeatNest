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
import uuid

# Constants
APP_TITLE = "BeatNest 🎵"
WINDOW_SIZE = "1000x700"
COLORS = {
    "dark": {
        "bg": "#121212",
        "fg": "#ffffff",
        "accent": "#1db954",
        "secondary": "#1e1e1e",
        "hover": "#2d2d2d",
        "button_bg": "#282828",
        "button_fg": "#ffffff",
        "button_active_bg": "#3a3a3a",
    },
    "light": {
        "bg": "#f5f5f5",
        "fg": "#000000",
        "accent": "#1db954",
        "secondary": "#e0e0e0",
        "hover": "#d0d0d0",
        "button_bg": "#ffffff",
        "button_fg": "#000000",
        "button_active_bg": "#c0c0c0",
    }
}
FONTS = {
    "title": ("Helvetica", 28, "bold"),
    "subtitle": ("Helvetica", 20, "bold"),
    "label": ("Helvetica", 12),
    "button": ("Helvetica", 10, "bold"),
    "track_title": ("Helvetica", 14, "bold"),
    "track_info": ("Helvetica", 12),
    "small": ("Helvetica", 8),
}
SIDEBAR_BUTTONS = [
    {"text": "🏠 Home", "command": "show_home", "tooltip": "Go to Home"},
    {"text": "🔍 Search", "command": "show_search", "tooltip": "Search for songs"},
    {"text": "⭐ Favorites", "command": "show_favorites", "tooltip": "View favorite tracks"},
    {"text": "📚 Playlists", "command": "show_playlists", "tooltip": "Manage playlists"},
    {"text": "🎛 Mix", "command": "show_mix", "tooltip": "View your personal mix"},
    {"text": "📥 Downloads", "command": "show_downloads", "tooltip": "View downloaded tracks"},
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

    def _setup_window(self):
        """Configure the main window settings."""
        self.window.title(APP_TITLE)
        self.window.geometry(WINDOW_SIZE)
        self.window.resizable(True, True)

    def _initialize_state(self):
        """Initialize application state variables."""
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

    def _initialize_services(self):
        """Initialize external services like YTMusic and Genius API."""
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
        """Load saved data from JSON files."""
        self._load_json("playlists.json", lambda data: setattr(self, "playlists", data), {})
        self._load_json("downloads.json", lambda data: setattr(self, "downloads", [tuple(track) for track in data]), [])
        self._load_json("recommendations.json", self._load_recommendations, {"tracks": [], "play_counts": {}})
        self._load_json("search_results.json", lambda data: setattr(self, "tracks", [tuple(track) for track in data]), [])
        self._load_json("listening_history.json", lambda data: setattr(self, "listening_history", [tuple(track) for track in data]), [])
        self._load_json("recent_searches.json", lambda data: setattr(self, "recent_searches", data), [])
        self._load_json("listening_durations.json", lambda data: setattr(self, "listening_durations", data), {})
        self._load_json("user_level.json", self._load_user_level, {"level": 0, "level_name": "Listener", "total_time": 0})

    def _load_json(self, filename, setter, default):
        """Load data from a JSON file with error handling."""
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
        """Load recommendations from JSON data."""
        self.recommended_tracks = [tuple(track) for track in data.get("tracks", [])]
        self.recommendation_play_counts = data.get("play_counts", {})

    def _load_user_level(self, data):
        """Load user level data from JSON."""
        self.user_level = data.get("level", 0)
        self.user_level_name = data.get("level_name", "Listener")
        self.total_listening_time = data.get("total_time", 0)

    def show_loading_screen(self):
        """Display the loading screen with animated progress bar."""
        self.style = ttk.Style()
        self._configure_loading_styles()
        self.loading_frame = ttk.Frame(self.window, style="Loading.TFrame")
        self.loading_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.loading_frame, text="BeatNest", style="Loading.TLabel").pack(expand=True)
        self.loading_progress = ttk.Progressbar(
            self.loading_frame,
            style="Loading.Horizontal.TProgressbar",
            mode="determinate",
            length=300
        )
        self.loading_progress.pack(pady=(0, 50))
        self.animate_loading_progress()

    def _configure_loading_styles(self):
        """Configure styles for the loading screen."""
        colors = COLORS["dark"]
        self.style.configure("Loading.TFrame", background=colors["bg"])
        self.style.configure("Loading.TLabel", background=colors["bg"], foreground=colors["accent"], font=FONTS["title"])
        self.style.configure(
            "Loading.Horizontal.TProgressbar",
            background=colors["accent"],
            troughcolor=colors["secondary"],
            bordercolor=colors["bg"],
            lightcolor=colors["accent"],
            darkcolor=colors["accent"]
        )

    def animate_loading_progress(self):
        """Animate the loading progress bar."""
        if not hasattr(self, "loading_progress") or not self.loading_frame.winfo_exists():
            return
        current = self.loading_progress["value"]
        if current < 100:
            self.loading_progress["value"] = current + 2
            self.window.after(40, self.animate_loading_progress)
        else:
            self.loading_progress["value"] = 0

    def _initialize_ui(self):
        """Initialize the main UI after loading."""
        self.loading_frame.destroy()
        delattr(self, "loading_progress")  # Clean up reference
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._setup_styles()
        self._create_ui()
        self._setup_media_controls()

    def _setup_styles(self):
        """Configure UI styles based on theme."""
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
            relief="flat"
        )
        self.style.map(
            "Rounded.TButton",
            background=[("active", colors["button_active_bg"])],
            foreground=[("active", colors["button_fg"])]
        )
        self.style.configure("TLabel", font=FONTS["label"], background=colors["bg"], foreground=colors["fg"])
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
            rowheight=40,
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
        """Create the main UI components."""
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self._create_sidebar()
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        self._create_player_frame()
        self.show_home()

    def _create_sidebar(self):
        """Create the sidebar with navigation buttons."""
        sidebar = ttk.Frame(self.main_frame, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        sidebar.pack_propagate(False)
        for btn_config in SIDEBAR_BUTTONS:
            btn = ttk.Button(
                sidebar,
                text=btn_config["text"],
                command=getattr(self, btn_config["command"]),
                style="TButton"
            )
            btn.pack(fill=tk.X, pady=5, padx=10)
            btn.bind("<Enter>", lambda e, t=btn_config["tooltip"]: self._show_tooltip(e, t))
            btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _create_player_frame(self):
        """Create the player control frame at the bottom."""
        player_frame = ttk.Frame(self.window, style="TFrame")
        player_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10, padx=10)
        self._create_left_player_frame(player_frame)
        self._create_center_player_frame(player_frame)
        self._create_right_player_frame(player_frame)

    def _create_left_player_frame(self, player_frame):
        """Create the left section of the player frame (thumbnail, track info, like button)."""
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
        """Create the center section of the player frame (controls and progress bar)."""
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

    def _create_right_player_frame(self, player_frame):
        """Create the right section of the player frame (additional controls and volume)."""
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
        """Display a tooltip with fade-in effect."""
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
            pady=3
        )
        label.pack()
        self.tooltip_alpha = 0
        self._fade_in_tooltip()

    def _fade_in_tooltip(self):
        """Animate tooltip fade-in effect."""
        if self.tooltip:
            self.tooltip_alpha += 0.1
            if self.tooltip_alpha >= 1:
                self.tooltip_alpha = 1
            self.tooltip.wm_attributes("-alpha", self.tooltip_alpha)
            if self.tooltip_alpha < 1:
                self.window.after(50, self._fade_in_tooltip)

    def _hide_tooltip(self):
        """Hide and destroy the tooltip."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.tooltip_alpha = 0

    def _setup_media_controls(self):
        """Set up media control key bindings."""
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
        """Save data to a JSON file with error handling."""
        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def save_playlists(self):
        """Save playlists to JSON."""
        self._save_json("playlists.json", self.playlists)

    def save_downloads(self):
        """Save downloads to JSON."""
        self._save_json("downloads.json", [list(track) for track in self.downloads])

    def save_recommendations(self):
        """Save recommendations to JSON."""
        data = {
            "tracks": [list(track) for track in self.recommended_tracks],
            "play_counts": self.recommendation_play_counts
        }
        self._save_json("recommendations.json", data)

    def save_search_results(self):
        """Save search results to JSON."""
        self._save_json("search_results.json", [list(track) for track in self.tracks])

    def save_listening_history(self):
        """Save listening history to JSON."""
        self._save_json("listening_history.json", [list(track) for track in self.listening_history])

    def save_recent_searches(self):
        """Save recent searches to JSON."""
        self._save_json("recent_searches.json", self.recent_searches)

    def save_listening_durations(self):
        """Save listening durations to JSON."""
        self._save_json("listening_durations.json", self.listening_durations)

    def save_user_level(self):
        """Save user level data to JSON."""
        data = {
            "level": self.user_level,
            "level_name": self.user_level_name,
            "total_time": self.total_listening_time
        }
        self._save_json("user_level.json", data)

    def update_user_level(self):
        """Update user level based on total listening time."""
        levels = [
            (0, "Listener"),
            (3600, "Music"),
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
        """Return a time-based greeting."""
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
        """Highlight track frame on hover."""
        event.widget.configure(background=COLORS["dark" if self.is_dark_mode else "light"]["hover"])

    def on_track_frame_leave(self, event):
        """Remove highlight on track frame leave."""
        event.widget.configure(background=COLORS["dark" if self.is_dark_mode else "light"]["bg"])

    def show_home(self):
        """Display the home screen with top tracks and recommendations."""
        self.clear_content()
        ttk.Label(self.content_frame, text=self.get_greeting(), font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        self._display_top_tracks(scrollable_frame)
        self._generate_recommendations()
        self._display_recommended_tracks(scrollable_frame)
        self.loading_label = ttk.Label(self.content_frame, text="", font=FONTS["small"])
        self.loading_label.pack(pady=5)

    def _create_scrollable_frame(self):
        """Create a scrollable frame for content."""
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
        """Display top tracks based on listening history."""
        if not self.listening_history:
            return
        ttk.Label(parent, text="Your Top Tracks", font=FONTS["subtitle"]).pack(anchor="w", pady=(20, 10))
        top_tracks_frame = ttk.Frame(parent)
        top_tracks_frame.pack(fill=tk.X, pady=10)
        track_counts = Counter(self.listening_history)
        for track, count in track_counts.most_common(5):
            self._create_track_frame(top_tracks_frame, track, count)

    def _generate_recommendations(self):
        """Generate track recommendations based on listening history."""
        self.recommended_tracks = []
        self.recommendation_play_counts = {}
        if not self.ytmusic or not self.listening_history:
            return
        top_tracks = [track for track, _ in Counter(self.listening_history).most_common(3)]
        for track in top_tracks:
            self._add_related_tracks(track)
            self._add_artist_tracks(track)
        if len(self.recommended_tracks) < 5 and self.recent_searches:
            self._add_recent_search_tracks()
        if len(self.recommended_tracks) < 5:
            self._add_default_tracks()
        self.save_recommendations()

    def _add_related_tracks(self, track):
        """Add related tracks for a given track."""
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
        """Add tracks by the same artist."""
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
        """Add tracks from recent searches."""
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
        """Add default tracks if recommendations are insufficient."""
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
        """Create a track tuple from API result."""
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
        """Display recommended tracks."""
        if not self.recommended_tracks:
            return
        ttk.Label(parent, text="Recommended for You", font=FONTS["subtitle"]).pack(anchor="w", pady=(20, 10))
        recommended_frame = ttk.Frame(parent)
        recommended_frame.pack(fill=tk.X, pady=10)
        for track in self.recommended_tracks:
            self._create_track_frame(recommended_frame, track, self.recommendation_play_counts.get(track[0], 0), is_recommended=True)

    def _create_track_frame(self, parent, track, count, is_recommended=False):
        """Create a track frame with thumbnail, info, and play button."""
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
            text=f"{track[2]} • Played {count} times",
            font=FONTS["track_info"],
            foreground="#b3b3b3"
        ).pack(anchor="w")
        play_btn = ttk.Button(
            track_frame,
            text="▶",
            command=lambda t=track: self.play_recommended_track(t) if is_recommended else self.play_track(t),
            width=4,
            style="Rounded.TButton"
        )
        play_btn.pack(side=tk.RIGHT, padx=10)
        play_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Play this track"))
        play_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def load_thumbnail_for_track(self, url, label):
        """Load and cache a thumbnail image for a track."""
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
        except Exception:
            label.config(image=None)

    def play_track(self, track):
        """Play a selected track."""
        self.playing_playlist_sequentially = False
        self._stop_current_track()
        self.current_track = track
        self.from_playlist = bool(self.current_playlist)
        self.loading = True
        self.listening_history.append(self.current_track)
        self.save_listening_history()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def play_recommended_track(self, track):
        """Play a recommended track."""
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
        """Stop and release the current track if playing."""
        if self.player and self.is_playing:
            self.player.stop()
            self.player.release()
            self.player = None
            self.is_playing = False
            self.play_button.config(text="▶")

    def show_search(self):
        """Display the search screen."""
        self.clear_content()
        search_frame = ttk.Frame(self.content_frame)
        search_frame.pack(fill=tk.X, pady=(0, 15))
        search_entry = ttk.Combobox(search_frame, textvariable=self.search_var, values=self.recent_searches, font=FONTS["label"])
        search_entry.pack(fill=tk.X, padx=(0, 10))
        search_entry.bind("<Return>", lambda e: self.search_music())
        button_frame = ttk.Frame(search_frame)
        button_frame.pack(fill=tk.X, pady=10)
        self._create_search_buttons(button_frame)
        self._create_search_treeview()
        self.loading_label = ttk.Label(self.content_frame, text="", font=FONTS["small"])
        self.loading_label.pack(pady=5)
        self._populate_search_results()

    def _create_search_buttons(self, parent):
        """Create buttons for search actions."""
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
        """Create the treeview for search results."""
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
        """Populate the search treeview with tracks."""
        for track in self.tracks:
            self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))

    def show_favorites(self):
        """Display the favorites screen."""
        self.clear_content()
        self._create_search_treeview()  # Reuse search treeview
        for track in self.favorites:
            self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))
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
        """Display the playlists screen."""
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
        playlist_frame = ttk.Frame(self.content_frame)
        playlist_frame.pack(fill=tk.BOTH, expand=True)
        for name in self.playlists:
            self._create_playlist_entry(playlist_frame, name)

    def _create_playlist_entry(self, parent, name):
        """Create a playlist entry with buttons."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        playlist_btn = ttk.Button(
            frame,
            text=name,
            command=lambda: self.show_playlist(name),
            style="TButton"
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

    def show_mix(self):
        """Display the personalized mix screen."""
        self.clear_content()
        ttk.Label(self.content_frame, text="Your Mix", font=FONTS["title"]).pack(anchor="w", pady=(0, 20))
        canvas, scrollable_frame = self._create_scrollable_frame()
        mix_tracks = self._generate_mix_tracks()
        if not mix_tracks:
            ttk.Label(scrollable_frame, text="Listen to more tracks to create your mix!", font=FONTS["label"]).pack(pady=10)
            return
        for track in mix_tracks[:20]:
            self._create_track_frame(scrollable_frame, track, 0)
        self.loading_label = ttk.Label(self.content_frame, text="", font=FONTS["small"])
        self.loading_label.pack(pady=5)

    def _generate_mix_tracks(self):
        """Generate tracks for the personalized mix."""
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
        """Display the downloaded tracks screen."""
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
        """Create a frame for a downloaded track."""
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
        """Download a selected track."""
        selection = self.tree.selection()
        if not selection:
            self._show_temp_message("No track selected")
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        if track in self.downloads:
            self._show_temp_message("Track already downloaded")
            return
        self._show_temp_message("Downloading...")
        self.window.config(cursor="wait")
        threading.Thread(target=self._download_and_save_track, args=(track,), daemon=True).start()

    def _download_and_save_track(self, track):
        """Download and save a track to the downloads directory."""
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
        """Delete a downloaded track."""
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
        """Open a dialog to create a new playlist."""
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
        """Add a new playlist with validation."""
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
        """Play a playlist sequentially."""
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
        """Display a specific playlist."""
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
        """Create a track frame for a playlist."""
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
        remove_btn = ttk.Button(
            track_frame,
            text="🗑",
            command=lambda t=track: self.remove_from_playlist(t),
            width=4,
            style="Rounded.TButton"
        )
        remove_btn.pack(side=tk.RIGHT, padx=5)
        remove_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Remove from playlist"))
        remove_btn.bind("<Leave>", lambda e: self._hide_tooltip())

    def _create_playlist_buttons(self, parent, name):
        """Create buttons for playlist actions."""
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
        """Display the settings screen."""
        self.clear_content()
        ttk.Label(self.content_frame, text="Settings", font=FONTS["title"]).pack(pady=20)
        settings_frame = ttk.Frame(self.content_frame)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        self._create_theme_setting(settings_frame)
        self._create_stats_setting(settings_frame)

    def _create_theme_setting(self, parent):
        """Create theme toggle setting."""
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
        """Create stats viewing setting."""
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
        """Display listening statistics."""
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
        """Create a track frame for stats."""
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
        """Delete a playlist."""
        del self.playlists[name]
        if self.current_playlist == name:
            self.current_playlist = None
        self.save_playlists()
        self.show_playlists()

    def download_playlist(self, playlist_name):
        """Download all tracks in a playlist."""
        if not self.playlists[playlist_name]:
            self._show_temp_message("Playlist is empty")
            return
        dialog = self._create_download_dialog(playlist_name)
        self.download_cancelled = False
        total_tracks = len(self.playlists[playlist_name])
        self._start_playlist_download(playlist_name, dialog, total_tracks)

    def _create_download_dialog(self, playlist_name):
        """Create a dialog for playlist download progress."""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Downloading Playlist: {playlist_name}")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        progress_label = ttk.Label(dialog, text="Preparing to download...", font=FONTS["small"])
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
        """Start downloading all tracks in a playlist."""
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
        """Cancel an ongoing playlist download."""
        self.download_cancelled = True
        dialog.destroy()

    def add_to_playlist_from_menu(self):
        """Add a track to a playlist from the context menu."""
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        self._show_add_to_playlist_dialog(track)

    def add_to_playlist_from_player(self):
        """Add the current track to a playlist."""
        if not self.current_track:
            self._show_temp_message("No track playing")
            return
        self._show_add_to_playlist_dialog(self.current_track)

    def _show_add_to_playlist_dialog(self, track):
        """Open a dialog to add a track to a playlist."""
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

    def _add_to_selected_playlist(self, track, playlist_name, new_playlist_name, dialog):
        """Add a track to a selected or new playlist."""
        if new_playlist_name:
            new_playlist_name = new_playlist_name.strip()
            if not new_playlist_name or len(new_playlist_name) > 50 or not re.match(r'^[a-zA-Z0-9\s_-]+$', new_playlist_name):
                self._show_temp_message("Invalid playlist name")
                dialog.destroy()
                return
            if new_playlist_name in self.playlists:
                self._show_temp_message("Playlist already exists")
                dialog.destroy()
                return
            self.playlists[new_playlist_name] = []
            playlist_name = new_playlist_name
        if playlist_name:
            if track not in self.playlists[playlist_name]:
                self.playlists[playlist_name].append(track)
                self.save_playlists()
                self._show_temp_message(f"Added to {playlist_name}")
        dialog.destroy()

    def remove_from_playlist(self, track=None):
        """Remove a track from the current playlist."""
        if not self.current_playlist:
            return
        selection = self.tree.selection()
        if not selection and not track:
            return
        selected_track = track or self.tracks[self.tree.index(selection[0])]
        if selected_track in self.playlists[self.current_playlist]:
            self.playlists[self.current_playlist].remove(selected_track)
            self.save_playlists()
            self.show_playlist(self.current_playlist)
            self._show_temp_message(f"Removed from {self.current_playlist}")

    def sort_by_duration(self):
        """Sort tracks by duration."""
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
                self.tree.insert("end", values=(track[0], track[2], track[3], self.format_time(track[4])))
        self.save_search_results()
        self._show_temp_message("Sorted by duration")

    def clear_search(self):
        """Clear the search query and results."""
        self.search_var.set("")
        self.recent_searches = [s for s in self.recent_searches if s != self.search_var.get()]
        self.save_recent_searches()
        self.tracks = []
        self.save_search_results()
        self.show_search()

    def clear_content(self):
        """Clear all widgets in the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def search_music(self):
        """Search for music using the YTMusic API."""
        query = self.search_var.get()
        if not query:
            self._show_temp_message("Please enter a search query")
            return
        self._show_temp_message("Searching...")
        self.window.config(cursor="wait")
        if query not in self.recent_searches:
            self.recent_searches.insert(0, query)
            if len(self.recent_searches) > 5:
                self.recent_searches.pop()
            self.save_recent_searches()
        if not self.ytmusic:
            self._show_temp_message("YTMusic API not initialized", duration=3000)
            messagebox.showerror("Error", "YTMusic API not initialized. Please check your setup.")
            self.window.config(cursor="")
            return
        self.tracks = []
        self.tree.delete(*self.tree.get_children())
        self._perform_search(query)

    def _perform_search(self, query):
        """Perform the music search with retry logic."""
        for attempt in range(2):
            try:
                results = self.ytmusic.search(query, filter="songs", limit=10)
                if not results:
                    self._show_temp_message("No results found")
                    self.window.config(cursor="")
                    return
                for result in results:
                    if not isinstance(result, dict):
                        continue
                    track = self._create_track_tuple(result)
                    if track and track not in self.tracks:
                        self.tracks.append(track)
                        self.tree.insert("", "end", values=(track[0], track[2], track[3], self.format_time(track[4])))
                self.save_search_results()
                self._show_temp_message(f"Found {len(self.tracks)} tracks")
                self.window.config(cursor="")
                return
            except Exception as e:
                self.window.config(cursor="")
                if attempt == 1:
                    self._show_temp_message("Search failed. Try again.", duration=3000)
                    messagebox.showerror("Error", f"Search failed: {str(e)}")
            finally:
                self.window.config(cursor="")

    def load_thumbnail(self, url):
        """Load and cache a thumbnail for the player."""
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
        except Exception:
            self.thumbnail_label.config(image=None)

    def play_selected(self):
        """Play a selected track from the treeview."""
        if self.loading:
            return
        selection = self.tree.selection()
        if not selection:
            return
        self._stop_current_track()
        index = self.tree.index(selection[0])
        self.current_track = self.tracks[index]
        self.from_playlist = bool(self.current_playlist)
        self.loading = True
        self.listening_history.append(self.current_track)
        self.save_listening_history()
        self.update_now_playing()
        threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def update_now_playing(self):
        """Update the now playing section with current track info."""
        if self.current_track:
            self.track_label.config(text=self.current_track[0])
            self.artist_label.config(text=self.current_track[2])
            self.load_thumbnail(self.current_track[5])
            self.like_button.config(text="❤️" if self.current_track in self.favorites else "♡")

    def update_progress(self):
        """Update the progress bar and time labels."""
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
                    self.progress["value"] = (current_time / total_time) * 100
                    self.current_time_label.config(text=self.format_time(current_time))
                    self.total_time_label.config(text=self.format_time(total_time))
                else:
                    self.progress["value"] = 0
                    self.current_time_label.config(text="0:00")
                    self.total_time_label.config(text="0:00")
            self.window.after(500, self.update_progress)
        else:
            self.progress["value"] = 0
            self.current_time_label.config(text="0:00")
            self.total_time_label.config(text="0:00")
            self.last_update_time = None

    def stream_music(self, video_id):
        """Stream music from a YouTube video ID."""
        try:
            self.window.config(cursor="wait")
            audio_url = self._get_audio_url(video_id)
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
        except Exception:
            self._show_temp_message("Failed to play track", duration=3000)
            self.is_playing = False
            self.play_button.config(text="▶")
        finally:
            self.window.config(cursor="")

    def _get_audio_url(self, video_id):
        """Get the audio URL for a track, preferring downloaded files."""
        downloaded_track = next((track for track in self.downloads if track[1] == video_id), None)
        if downloaded_track and os.path.exists(downloaded_track[6]):
            return downloaded_track[6]
        if downloaded_track:
            self.downloads.remove(downloaded_track)
            self.save_downloads()
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "force_generic_extractor": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info["url"]

    def toggle_play_pause(self):
        """Toggle play/pause state."""
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
        """Play the next track."""
        if self.loading:
            return
        if self.is_repeat and self.current_track:
            self.loading = True
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()
            return
        next_track = self._get_next_track()
        if next_track:
            self.current_track = next_track
            self.from_playlist = bool(self.current_playlist)
            self.loading = True
            self.listening_history.append(self.current_track)
            self.save_listening_history()
            self.update_now_playing()
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()
        else:
            self._stop_current_track()
            self.current_track = None
            self.from_playlist = False
            self.update_now_playing()

    def _get_next_track(self):
        """Determine the next track to play."""
        if self.queue:
            return self.queue.pop(0)
        if self.is_shuffle and self.current_playlist and self.playlists[self.current_playlist]:
            if not self.shuffle_order:
                self.shuffle_order = list(range(len(self.playlists[self.current_playlist])))
                random.shuffle(self.shuffle_order)
            if self.shuffle_order:
                index = self.shuffle_order.pop(0)
                return self.playlists[self.current_playlist][index]
        if self.playing_playlist_sequentially and self.current_playlist and self.playlists[self.current_playlist]:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                return self.playlists[self.current_playlist][current_index + 1]
        if self.from_playlist and self.current_playlist and self.playlists[self.current_playlist]:
            current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
            if current_index + 1 < len(self.playlists[self.current_playlist]):
                return self.playlists[self.current_playlist][current_index + 1]
        return None

    def play_previous(self):
        """Play the previous track."""
        if self.loading:
            return
        if not self.current_playlist or not self.playlists[self.current_playlist]:
            return
        current_index = self.playlists[self.current_playlist].index(self.current_track) if self.current_track in self.playlists[self.current_playlist] else -1
        if current_index > 0:
            self.current_track = self.playlists[self.current_playlist][current_index - 1]
            self.from_playlist = True
            self.loading = True
            self.listening_history.append(self.current_track)
            self.save_listening_history()
            self.update_now_playing()
            threading.Thread(target=self.stream_music, args=(self.current_track[1],), daemon=True).start()

    def add_to_queue(self):
        """Add a selected track to the queue."""
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        track = self.tracks[index]
        self.queue.append(track)
        self._show_temp_message(f"Added to queue: {track[0]}")

    def add_to_favorites(self):
        """Add the current or selected track to favorites."""
        if self.current_track:
            if self.current_track not in self.favorites:
                self.favorites.append(self.current_track)
                self._show_temp_message(f"Added to favorites: {self.current_track[0]}")
                self.like_button.config(text="❤️")
            else:
                self.favorites.remove(self.current_track)
                self._show_temp_message(f"Removed from favorites: {self.current_track[0]}")
                self.like_button.config(text="♡")
        else:
            selection = self.tree.selection()
            if not selection:
                return
            index = self.tree.index(selection[0])
            track = self.tracks[index]
            if track not in self.favorites:
                self.favorites.append(track)
                self._show_temp_message(f"Added to favorites: {track[0]}")
            else:
                self.favorites.remove(track)
                self._show_temp_message(f"Removed from favorites: {track[0]}")
        self.show_favorites()

    def toggle_shuffle(self):
        """Toggle shuffle mode."""
        self.is_shuffle = not self.is_shuffle
        self._show_temp_message("Shuffle " + ("On" if self.is_shuffle else "Off"))
        self.shuffle_order = []

    def toggle_repeat(self):
        """Toggle repeat mode."""
        self.is_repeat = not self.is_repeat
        self._show_temp_message("Repeat " + ("On" if self.is_repeat else "Off"))

    def toggle_mute(self):
        """Toggle mute state."""
        self.is_muted = not self.is_muted
        if self.player:
            self.player.audio_set_mute(self.is_muted)
        self.mute_button.config(text="🔇" if self.is_muted else "🔊")
        self._show_temp_message("Mute " + ("On" if self.is_muted else "Off"))

    def set_volume(self, value):
        """Set the player volume."""
        volume = int(float(value))
        if self.player:
            self.player.audio_set_volume(volume)
        if self.is_muted and volume > 0:
            self.toggle_mute()

    def seek_track(self, event):
        """Seek to a position in the track based on progress bar click."""
        if self.player and self.is_playing and self.player.get_length() > 0:
            x = event.x
            width = self.progress.winfo_width()
            fraction = x / width
            total_time = self.player.get_length() / 1000
            seek_time = fraction * total_time
            self.player.set_time(int(seek_time * 1000))
            self.progress["value"] = fraction * 100
            self.current_time_label.config(text=self.format_time(seek_time))

    def show_context_menu(self, event):
        """Show the context menu for a treeview item."""
        self.tree.selection_set(self.tree.identify_row(event.y))
        self.context_menu.post(event.x_root, event.y_root)

    def format_time(self, seconds):
        """Format seconds into mm:ss format."""
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            return "0:00"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.is_dark_mode = not self.is_dark_mode
        self._setup_styles()
        self._initialize_ui()
        self._show_temp_message("Theme switched to " + ("Dark" if self.is_dark_mode else "Light"))

    def show_device_info(self):
        """Show device selection dialog (placeholder)."""
        dialog = tk.Toplevel(self.window)
        dialog.title("Select Device")
        dialog.geometry("300x150")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        ttk.Label(dialog, text="Available Devices:").pack(pady=10)
        ttk.Label(dialog, text="Local Playback (Default)").pack()
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy,
            style="Rounded.TButton"
        ).pack(pady=10)

    def show_lyrics(self):
        """Show lyrics for the current track."""
        if not self.current_track:
            self._show_temp_message("No track playing")
            return
        dialog = tk.Toplevel(self.window)
        dialog.title("Lyrics")
        dialog.geometry("400x500")
        dialog.transient(self.window)
        dialog.grab_set()
        dialog.configure(bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"])
        canvas = tk.Canvas(dialog, bg=COLORS["dark" if self.is_dark_mode else "light"]["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        lyrics_label = ttk.Label(
            scrollable_frame,
            text="Fetching lyrics...",
            font=FONTS["label"],
            wraplength=350,
            justify="center"
        )
        lyrics_label.pack(pady=10)
        copy_btn = ttk.Button(
            scrollable_frame,
            text="📋 Copy Lyrics",
            command=lambda: self.copy_lyrics(lyrics_label),
            style="Rounded.TButton"
        )
        copy_btn.pack(pady=10)
        copy_btn.bind("<Enter>", lambda e: self._show_tooltip(e, "Copy lyrics to clipboard"))
        copy_btn.bind("<Leave>", lambda e: self._hide_tooltip())
        threading.Thread(target=self._fetch_lyrics, args=(self.current_track, lyrics_label), daemon=True).start()

    def _fetch_lyrics(self, track, lyrics_label):
        """Fetch lyrics for a track using Genius API."""
        try:
            song = self.genius.search_song(track[0], track[2])
            if song and song.lyrics:
                lyrics_label.config(text=song.lyrics)
            else:
                lyrics_label.config(text="Lyrics not found.")
        except Exception:
            lyrics_label.config(text="Failed to fetch lyrics.")

    def copy_lyrics(self, lyrics_label):
        """Copy lyrics to the clipboard."""
        lyrics = lyrics_label.cget("text")
        if lyrics and lyrics != "Fetching lyrics..." and lyrics != "Lyrics not found." and lyrics != "Failed to fetch lyrics.":
            pyperclip.copy(lyrics)
            self._show_temp_message("Lyrics copied to clipboard")
        else:
            self._show_temp_message("No lyrics to copy")

    def _show_temp_message(self, message, duration=2000):
        """Show a temporary message in the loading label."""
        if hasattr(self, "loading_label") and self.loading_label.winfo_exists():
            self.loading_label.config(text=message)
            self.window.after(duration, lambda: self.loading_label.config(text="") if self.loading_label.winfo_exists() else None)

    def run(self):
        """Run the application."""
        self.window.mainloop()

if __name__ == "__main__":
    app = BeatNest()
    app.run()
