import pygame
import os
import threading
import time
import random
from typing import Optional, List, Dict
from enum import Enum

class AudioType(Enum):
    """Tipos de audio en el sistema"""
    SOUNDTRACK = "soundtrack"
    EFFECT = "effect"

class AudioState(Enum):
    """Estados del contexto de la aplicación"""
    LOBBY = "lobby"
    GAME_EARLY = "game_early"
    GAME_LATE = "game_late"
    MENU = "menu"

class AudioManager:
    """Gestor centralizado de audio para la aplicación"""
    
    def __init__(self, audio_folder: str = "sql/Sonidos 2.0/Sonidos 2.0"):
        """
        Inicializar el gestor de audio
        
        Args:
            audio_folder: Carpeta donde están los archivos de audio
        """
        print(f"🎵 Inicializando AudioManager con carpeta: {audio_folder}")
        
        # Inicializar pygame mixer con configuración más compatible
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            print("✅ Pygame mixer inicializado correctamente")
        except pygame.error as e:
            print(f"❌ Error inicializando pygame mixer: {e}")
            return
        
        self.audio_folder = audio_folder
        self.current_state = AudioState.LOBBY
        self.is_muted = False
        self.master_volume = 0.8  # Volumen más alto por defecto
        self.effects_volume = 0.9
        self.music_volume = 0.7
        
        # Canales de audio
        self.music_channel = pygame.mixer.Channel(0)
        self.effects_channel = pygame.mixer.Channel(1)
        
        # Control de threads
        self.music_thread = None
        self.stop_music_flag = threading.Event()
        
        # Cargar todos los audios
        self.sounds = {}
        self.load_sounds()
        
        # Configurar listas de reproducción por contexto
        self.setup_playlists()
        
        # Variables de control
        self.current_playlist = []
        self.current_playlist_index = 0
        self.completed_subboards = 0
        
        # Auto-start en lobby después de inicializar
        self.auto_start_lobby_music()
        
    def load_sounds(self):
        """Cargar todos los archivos de audio"""
        audio_files = {
            # Efectos de sonido
            "win": "ganar.mp3",
            "lose": "Perder.mp3", 
            "subboard_complete": "Cuadro completo.mp3",
            "punto": "punto.mp3",
            
            # Soundtracks de lobby
            "lobby_1": "Lobby 1.wav",
            "lobby_2": "Lobby 2.wav", 
            "lobby_3": "Lobby 3.wav",
            
            # Soundtracks de juego temprano
            "bajo_perron": "Bajo perron.wav",  # CORREGIDA LA RUTA
            "gaming_1": "Gaming 1.wav",
            "gaming_2": "Gaming 2.wav",
            "beat_chevere": "Beat Chevere.wav",
            "divertido": "divertido.wav",
            
            # Soundtracks de juego tardío
            "late_game_1": "Late Game.wav",
            "late_game_2": "Late Game 2.wav"
        }
        
        loaded_count = 0
        for key, filename in audio_files.items():
            file_path = os.path.join(self.audio_folder, filename)
            print(f"🔍 Intentando cargar: {file_path}")
            
            if os.path.exists(file_path):
                try:
                    sound = pygame.mixer.Sound(file_path)
                    self.sounds[key] = sound
                    loaded_count += 1
                    print(f"✓ Audio cargado: {filename}")
                except pygame.error as e:
                    print(f"✗ Error cargando {filename}: {e}")
            else:
                print(f"✗ Archivo no encontrado: {file_path}")
        
        print(f"📊 Total audios cargados: {loaded_count}/{len(audio_files)}")
        
        # Test de reproducción inmediato
        self.test_audio_playback()
    
    def test_audio_playback(self):
        """Probar reproducción de audio inmediatamente"""
        print("🧪 Probando reproducción de audio...")
        
        # Probar un efecto primero
        if "punto" in self.sounds:
            print("🔊 Reproduciendo 'punto' como prueba...")
            try:
                self.sounds["punto"].set_volume(0.8)
                self.effects_channel.play(self.sounds["punto"])
                print("✅ Efecto 'punto' reproducido")
            except Exception as e:
                print(f"❌ Error reproduciendo 'punto': {e}")
        
        # Esperar un poco y probar música de lobby
        threading.Timer(2.0, self.test_lobby_music).start()
    
    def test_lobby_music(self):
        """Probar música de lobby"""
        print("🎵 Probando música de lobby...")
        if "lobby_1" in self.sounds:
            try:
                self.sounds["lobby_1"].set_volume(0.6)
                self.music_channel.play(self.sounds["lobby_1"])
                print("✅ Música 'lobby_1' reproducida")
            except Exception as e:
                print(f"❌ Error reproduciendo 'lobby_1': {e}")
    
    def setup_playlists(self):
        """Configurar las listas de reproducción por contexto"""
        self.playlists = {
            AudioState.LOBBY: ["lobby_1", "lobby_2", "lobby_3"],
            AudioState.GAME_EARLY: ["bajo_perron", "gaming_1", "gaming_2", "beat_chevere", "divertido"],
            AudioState.GAME_LATE: ["late_game_1", "late_game_2"]
        }
    
    def auto_start_lobby_music(self):
        """Auto-iniciar música de lobby después de la inicialización"""
        def delayed_start():
            time.sleep(1)  # Esperar 1 segundo
            print("🎵 Auto-iniciando música de lobby...")
            self.set_context(AudioState.LOBBY)
        
        threading.Thread(target=delayed_start, daemon=True).start()
    
    def set_volume(self, master: float = None, effects: float = None, music: float = None):
        """
        Configurar volúmenes
        
        Args:
            master: Volumen maestro (0.0 - 1.0)
            effects: Volumen de efectos (0.0 - 1.0) 
            music: Volumen de música (0.0 - 1.0)
        """
        if master is not None:
            self.master_volume = max(0.0, min(1.0, master))
            print(f"🔊 Volumen maestro: {self.master_volume}")
        if effects is not None:
            self.effects_volume = max(0.0, min(1.0, effects))
            print(f"🎧 Volumen efectos: {self.effects_volume}")
        if music is not None:
            self.music_volume = max(0.0, min(1.0, music))
            print(f"🎵 Volumen música: {self.music_volume}")
    
    def toggle_mute(self):
        """Alternar silencio total"""
        self.is_muted = not self.is_muted
        print(f"🔇 Audio {'silenciado' if self.is_muted else 'activado'}")
        
        if self.is_muted:
            self.stop_all_audio()
        else:
            self.start_context_music()
    
    def play_effect(self, effect_name: str, interrupt_music: bool = False):
        """
        Reproducir efecto de sonido
        
        Args:
            effect_name: Nombre del efecto a reproducir
            interrupt_music: Si debe interrumpir la música de fondo
        """
        print(f"🎵 Intentando reproducir efecto: {effect_name}")
        
        if self.is_muted:
            print("🔇 Audio silenciado, no reproduciendo efecto")
            return
            
        if effect_name not in self.sounds:
            print(f"❌ Efecto '{effect_name}' no encontrado")
            return
        
        # Interrumpir música si es necesario
        if interrupt_music:
            print("⏸️ Interrumpiendo música para efecto")
            self.stop_music()
        
        # Configurar volumen del efecto
        effect_volume = self.master_volume * self.effects_volume
        self.sounds[effect_name].set_volume(effect_volume)
        
        try:
            # Reproducir efecto
            self.effects_channel.play(self.sounds[effect_name])
            print(f"✅ Efecto '{effect_name}' reproducido con volumen {effect_volume}")
        except Exception as e:
            print(f"❌ Error reproduciendo efecto '{effect_name}': {e}")
        
        # Si interrumpió la música, reanudarla después del efecto
        if interrupt_music:
            effect_duration = 3.0  # Duración estimada
            threading.Timer(effect_duration, self.start_context_music).start()
    
    def start_context_music(self):
        """Iniciar música de acuerdo al contexto actual"""
        print(f"🎵 Iniciando música para contexto: {self.current_state.value}")
        
        if self.is_muted:
            print("🔇 Audio silenciado, no iniciando música")
            return
        
        self.stop_music()
        
        if self.current_state in self.playlists:
            available_songs = [song for song in self.playlists[self.current_state] if song in self.sounds]
            
            if not available_songs:
                print(f"❌ No hay canciones disponibles para {self.current_state.value}")
                return
            
            self.current_playlist = available_songs.copy()
            random.shuffle(self.current_playlist)
            self.current_playlist_index = 0
            
            print(f"📋 Playlist para {self.current_state.value}: {self.current_playlist}")
            
            self.music_thread = threading.Thread(target=self._music_loop, daemon=True)
            self.stop_music_flag.clear()
            self.music_thread.start()
    
    def _music_loop(self):
        """Loop de reproducción de música en hilo separado"""
        print("🔄 Iniciando loop de música")
        
        while not self.stop_music_flag.is_set():
            if not self.current_playlist:
                print("📋 Playlist vacía, terminando loop")
                break
                
            # Obtener próxima canción
            song_name = self.current_playlist[self.current_playlist_index]
            print(f"🎵 Reproduciendo: {song_name}")
            
            if song_name in self.sounds:
                # Configurar volumen
                music_volume = self.master_volume * self.music_volume
                self.sounds[song_name].set_volume(music_volume)
                
                try:
                    # Reproducir
                    self.music_channel.play(self.sounds[song_name])
                    print(f"▶️ '{song_name}' iniciado con volumen {music_volume}")
                    
                    # Esperar a que termine la canción
                    while self.music_channel.get_busy() and not self.stop_music_flag.is_set():
                        time.sleep(0.5)
                    
                    print(f"⏹️ '{song_name}' terminado")
                except Exception as e:
                    print(f"❌ Error reproduciendo '{song_name}': {e}")
            else:
                print(f"❌ Canción '{song_name}' no encontrada en sounds")
            
            # Avanzar al siguiente track
            self.current_playlist_index = (self.current_playlist_index + 1) % len(self.current_playlist)
            
            # Pausa entre canciones
            if not self.stop_music_flag.wait(1.0):  # Pausa de 1 segundo
                continue
            else:
                print("⏹️ Stop flag activado, terminando loop")
                break
        
        print("🔄 Loop de música terminado")
    
    def stop_music(self):
        """Detener música de fondo"""
        print("⏹️ Deteniendo música")
        self.stop_music_flag.set()
        self.music_channel.stop()
        if self.music_thread and self.music_thread.is_alive():
            self.music_thread.join(timeout=2.0)
    
    def stop_all_audio(self):
        """Detener todo el audio"""
        print("⏹️ Deteniendo todo el audio")
        self.stop_music()
        self.effects_channel.stop()
    
    def set_context(self, new_state: AudioState):
        """
        Cambiar contexto de audio
        
        Args:
            new_state: Nuevo estado del contexto
        """
        if new_state != self.current_state:
            print(f"🔄 Cambiando contexto de audio: {self.current_state.value} -> {new_state.value}")
            self.current_state = new_state
            self.start_context_music()
    
    def update_subboards_completed(self, count: int):
        """
        Actualizar número de subtableros completados
        
        Args:
            count: Número de subtableros completados por el jugador líder
        """
        print(f"📊 Actualizando subtableros completados: {self.completed_subboards} -> {count}")
        self.completed_subboards = count
        
        # Cambiar a música de late game si alguien tiene 4+ subtableros
        if count >= 4 and self.current_state == AudioState.GAME_EARLY:
            print("🎵 Cambiando a música de late game (4+ subtableros)")
            self.set_context(AudioState.GAME_LATE)
    
    def on_game_start(self):
        """Llamar cuando inicia una partida"""
        print("🎮 Juego iniciado")
        self.completed_subboards = 0
        self.set_context(AudioState.GAME_EARLY)
    
    def on_game_end(self):
        """Llamar cuando termina una partida"""
        print("🏁 Juego terminado")
        self.set_context(AudioState.LOBBY)
    
    def on_subboard_won(self):
        """Llamar cuando se gana un subtablero"""
        print("🏆 Subtablero ganado")
        self.play_effect("subboard_complete", interrupt_music=False)
    
    def on_match_won(self):
        """Llamar cuando se gana una partida"""
        print("🎉 Partida ganada")
        self.play_effect("win", interrupt_music=True)
    
    def on_match_lost(self):
        """Llamar cuando se pierde una partida"""
        print("😔 Partida perdida")
        self.play_effect("lose", interrupt_music=True)
    
    def on_point_scored(self):
        """Llamar cuando se anota un punto/movimiento importante"""
        # No hacer print para este evento porque es muy frecuente
        self.play_effect("punto", interrupt_music=False)
    
    def cleanup(self):
        """Limpiar recursos al cerrar la aplicación"""
        print("🧹 Limpiando recursos de audio")
        self.stop_all_audio()
        pygame.mixer.quit()


class AudioControlWidget:
    """Widget de control de audio para integrar en la UI"""
    
    def __init__(self, parent, audio_manager: AudioManager):
        """
        Inicializar widget de control
        
        Args:
            parent: Widget padre de tkinter
            audio_manager: Instancia del gestor de audio
        """
        self.parent = parent
        self.audio_manager = audio_manager
        
        # Importar tkinter aquí para evitar problemas de importación circular
        import tkinter as tk
        from tkinter import ttk
        
        # Frame principal del control
        self.control_frame = ttk.Frame(parent)
        
        # Botón de silencio/activar
        self.mute_button = ttk.Button(
            self.control_frame,
            text="🔊" if not audio_manager.is_muted else "🔇",
            command=self.toggle_mute,
            width=3
        )
        self.mute_button.pack(side="left", padx=2)
        
        # Control de volumen maestro
        ttk.Label(self.control_frame, text="Vol:").pack(side="left", padx=2)
        self.volume_scale = ttk.Scale(
            self.control_frame,
            from_=0,
            to=100,
            orient="horizontal",
            length=100,
            command=self.on_volume_change
        )
        self.volume_scale.set(audio_manager.master_volume * 100)
        self.volume_scale.pack(side="left", padx=2)
        
        # Botón de parar música
        self.stop_button = ttk.Button(
            self.control_frame,
            text="⏹",
            command=self.stop_music,
            width=3
        )
        self.stop_button.pack(side="left", padx=2)
        
        # Botón de reanudar música
        self.play_button = ttk.Button(
            self.control_frame,
            text="▶",
            command=self.start_music,
            width=3
        )
        self.play_button.pack(side="left", padx=2)
        
        # NUEVO: Botón de prueba de efectos
        self.test_button = ttk.Button(
            self.control_frame,
            text="🧪",
            command=self.test_effects,
            width=3
        )
        self.test_button.pack(side="left", padx=2)
    
    def pack(self, **kwargs):
        """Empaqueter el widget"""
        self.control_frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Colocar el widget en grid"""
        self.control_frame.grid(**kwargs)
    
    def toggle_mute(self):
        """Alternar silencio"""
        self.audio_manager.toggle_mute()
        self.mute_button.config(
            text="🔇" if self.audio_manager.is_muted else "🔊"
        )
    
    def on_volume_change(self, value):
        """Cambiar volumen maestro"""
        volume = float(value) / 100.0
        self.audio_manager.set_volume(master=volume)
    
    def stop_music(self):
        """Parar música de fondo"""
        self.audio_manager.stop_music()
    
    def start_music(self):
        """Reanudar música de fondo"""
        self.audio_manager.start_context_music()
    
    def test_effects(self):
        """Probar efectos de sonido"""
        print("🧪 Probando efectos...")
        self.audio_manager.play_effect("punto")


def add_audio_to_app(app_instance):
    """
    Función para integrar el sistema de audio en la aplicación principal
    
    Args:
        app_instance: Instancia de la aplicación principal
        
    Returns:
        AudioManager: Instancia del gestor de audio
    """
    print("🎵 Integrando audio en la aplicación...")
    
    # Crear gestor de audio
    audio_manager = AudioManager()
    
    # Agregar referencia al gestor en la aplicación
    app_instance.audio_manager = audio_manager
    
    print("✅ Audio integrado exitosamente")
    return audio_manager


def add_audio_to_game(game_instance, audio_manager: AudioManager):
    """
    Función para integrar audio en el juego Ultimate Tic Tac Toe
    
    Args:
        game_instance: Instancia del juego
        audio_manager: Gestor de audio
    """
    # Agregar referencia al gestor
    game_instance.audio_manager = audio_manager
    
    # Notificar inicio de partida
    audio_manager.on_game_start()
    
    return audio_manager