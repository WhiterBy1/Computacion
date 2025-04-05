"""
Sistema de Ranking para Juego de Tic Tac Toe Avanzado con Timelines
-------------------------------------------------------------------
Este sistema permite gestionar jugadores, partidas, rankings y timelines
para un juego avanzado de Tic Tac Toe con mecánicas de viaje en el tiempo.
"""

# =============================================================================
# 1. CONFIGURACIÓN E IMPORTACIONES
# =============================================================================

import os
import re
import json
import random
import hashlib
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from tkinter.font import Font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, desc, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from typing import List, Dict, Optional, Union, Tuple

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tictactoe_advanced")

# Crear la cadena de conexión
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Inicializar el motor de base de datos y la base declarativa
engine = create_engine(DATABASE_URI, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Colores para la interfaz
COLORS = {
    "bg_dark": "#2c3e50",
    "bg_light": "#ecf0f1",
    "accent": "#3498db",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "text_dark": "#34495e",
    "text_light": "#bdc3c7"
}

# Rangos del sistema
RANKS = {
    0: "Sin Clasificar",
    500: "Bronce",
    1000: "Plata",
    1500: "Oro",
    2000: "Platino",
    2500: "Diamante",
    3000: "Maestro"
}

# =============================================================================
# 2. MODELOS SQLALCHEMY (BASE DE DATOS)
# =============================================================================

class Server(Base):
    """Modelo para servidores de juego"""
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    region = Column(String(30), nullable=False)
    
    # Relaciones
    players = relationship("Player", back_populates="server")
    
    def __repr__(self):
        return f"<Server(name='{self.name}', region='{self.region}')>"


class Player(Base):
    """Modelo para jugadores"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    
    # Relaciones
    server = relationship("Server", back_populates="players")
    stats = relationship("PlayerStats", uselist=False, back_populates="player", cascade="all, delete-orphan")
    rankings = relationship("PlayerRanking", uselist=False, back_populates="player", cascade="all, delete-orphan")
    mmr_history = relationship("MMRHistory", back_populates="player", cascade="all, delete-orphan")
    match_players = relationship("MatchPlayer", back_populates="player", cascade="all, delete-orphan")
    moves = relationship("Move", back_populates="player")
    timelines_created = relationship("Timeline", foreign_keys="Timeline.created_by_player_id", back_populates="created_by_player")
    
    def __repr__(self):
        return f"<Player(username='{self.username}', level={self.level})>"


class PlayerStats(Base):
    """Modelo para estadísticas de jugadores"""
    __tablename__ = "player_stats"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    games_drawn = Column(Integer, default=0)
    total_timelines_created = Column(Integer, default=0)
    average_move_time = Column(Float, default=0.0)
    max_win_streak = Column(Integer, default=0)
    
    # Relaciones
    player = relationship("Player", back_populates="stats")
    
    def __repr__(self):
        return f"<PlayerStats(player_id={self.player_id}, games_won={self.games_won})>"
        
    @property
    def games_lost(self):
        return self.games_played - self.games_won - self.games_drawn
        
    @property
    def win_ratio(self):
        if self.games_played == 0:
            return 0.0
        return round(self.games_won / self.games_played, 2)


class PlayerRanking(Base):
    """Modelo para rankings de jugadores"""
    __tablename__ = "player_rankings"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    current_mmr = Column(Integer, default=1000)
    rank_label = Column(String(20), default="Sin Clasificar")
    win_ratio = Column(Float, default=0.0)
    max_win_streak = Column(Integer, default=0)
    average_victory_speed = Column(Float, default=0.0)  # En segundos
    timeline_usage_score = Column(Float, default=0.0)
    
    # Relaciones
    player = relationship("Player", back_populates="rankings")
    
    def __repr__(self):
        return f"<PlayerRanking(player_id={self.player_id}, mmr={self.current_mmr}, rank='{self.rank_label}')>"


class Match(Base):
    """Modelo para partidas"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    duration_seconds = Column(Integer, default=0)
    total_moves = Column(Integer, default=0)
    total_timelines_created = Column(Integer, default=0)
    final_state_description = Column(Text, nullable=True)
    
    # Relaciones
    winner = relationship("Player", foreign_keys=[winner_id])
    match_players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")
    moves = relationship("Move", back_populates="match", cascade="all, delete-orphan")
    timelines = relationship("Timeline", back_populates="match", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Match(id={self.id}, created_at='{self.created_at}')>"
    
    @property
    def status(self):
        return "Finalizada" if self.finished_at else "En progreso"


class MatchPlayer(Base):
    """Modelo para jugadores en partidas (relación M:M con datos)"""
    __tablename__ = "match_players"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    player_order = Column(Integer)  # 1 o 2 (X o O)
    is_winner = Column(Boolean, default=False)
    average_move_time = Column(Float, default=0.0)
    timelines_created = Column(Integer, default=0)
    
    # Relaciones
    match = relationship("Match", back_populates="match_players")
    player = relationship("Player", back_populates="match_players")
    
    def __repr__(self):
        return f"<MatchPlayer(match_id={self.match_id}, player_id={self.player_id}, order={self.player_order})>"


class Move(Base):
    """Modelo para movimientos en partidas"""
    __tablename__ = "moves"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    timeline_id = Column(Integer, ForeignKey("timelines.id"))
    sub_board_index = Column(Integer)  # 0-8 (índice del sub-tablero)
    cell_index = Column(Integer)  # 0-8 (índice de la celda dentro del sub-tablero)
    move_number = Column(Integer)  # Número global en la partida
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    time_taken_seconds = Column(Float, default=0.0)
    
    # Relaciones
    match = relationship("Match", back_populates="moves")
    player = relationship("Player", back_populates="moves")
    timeline = relationship(
        "Timeline", 
        back_populates="moves",
        foreign_keys=[timeline_id]
        )
    
    def __repr__(self):
        return f"<Move(match_id={self.match_id}, player_id={self.player_id}, sub_board={self.sub_board_index}, cell={self.cell_index})>"


class Timeline(Base):
    """Modelo para líneas temporales (timelines)"""
    __tablename__ = "timelines"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    parent_timeline_id = Column(Integer, ForeignKey("timelines.id"), nullable=True)
    created_by_player_id = Column(Integer, ForeignKey("players.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    starting_move_id = Column(Integer, ForeignKey("moves.id"), nullable=True)
    description = Column(String(200), nullable=True)
    
    # Relaciones
    match = relationship("Match", back_populates="timelines")
    parent_timeline = relationship("Timeline", backref="child_timelines", remote_side=[id])
    created_by_player = relationship("Player", foreign_keys=[created_by_player_id], back_populates="timelines_created")
    starting_move = relationship("Move", foreign_keys=[starting_move_id])
    moves = relationship("Move", back_populates="timeline", foreign_keys=[Move.timeline_id])
    
    def __repr__(self):
        parent_id = self.parent_timeline_id if self.parent_timeline_id else "None"
        return f"<Timeline(id={self.id}, match_id={self.match_id}, parent_id={parent_id})>"


class MMRHistory(Base):
    """Modelo para historial de MMR"""
    __tablename__ = "mmr_history"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    mmr_before = Column(Integer)
    mmr_after = Column(Integer)
    change_reason = Column(String(200))
    
    # Relaciones
    player = relationship("Player", back_populates="mmr_history")
    match = relationship("Match")
    
    def __repr__(self):
        change = self.mmr_after - self.mmr_before
        sign = "+" if change >= 0 else ""
        return f"<MMRHistory(player_id={self.player_id}, change={sign}{change}, reason='{self.change_reason}')>"


# =============================================================================
# 3. CLASES GESTORAS (LÓGICA DEL NEGOCIO)
# =============================================================================

class GestorJugadores:
    """Clase para gestionar jugadores"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def crear_jugador(self, username: str, password: str, server_id: int) -> Optional[Player]:
        """Crea un nuevo jugador en la base de datos"""
        # Verificar que el nombre de usuario sea único
        if self.session.query(Player).filter(Player.username == username).first():
            return None
        
        # Crear el jugador
        hashed_password = hash_password(password)
        nuevo_jugador = Player(
            username=username,
            hashed_password=hashed_password,
            server_id=server_id
        )
        self.session.add(nuevo_jugador)
        self.session.flush()  # Para obtener el ID
        
        # Crear estadísticas y ranking iniciales
        stats = PlayerStats(player_id=nuevo_jugador.id)
        ranking = PlayerRanking(player_id=nuevo_jugador.id)
        
        self.session.add(stats)
        self.session.add(ranking)
        self.session.commit()
        
        return nuevo_jugador
    
    def editar_jugador(self, player_id: int, data: Dict) -> bool:
        """Edita los datos de un jugador existente"""
        jugador = self.session.query(Player).get(player_id)
        if not jugador:
            return False
        
        # Actualizar campos
        if "username" in data and data["username"] != jugador.username:
            # Verificar que el nuevo nombre de usuario sea único
            if self.session.query(Player).filter(Player.username == data["username"]).first():
                return False
            jugador.username = data["username"]
        
        if "password" in data and data["password"]:
            jugador.hashed_password = hash_password(data["password"])
        
        if "server_id" in data:
            jugador.server_id = data["server_id"]
        
        if "level" in data:
            jugador.level = data["level"]
        
        self.session.commit()
        return True
    
    def eliminar_jugador(self, player_id: int) -> bool:
        """Elimina un jugador y todos sus datos relacionados"""
        jugador = self.session.query(Player).get(player_id)
        if not jugador:
            return False
        
        self.session.delete(jugador)
        self.session.commit()
        return True
    
    def autenticar_jugador(self, username: str, password: str) -> Optional[Player]:
        """Autentica a un jugador por su nombre de usuario y contraseña"""
        jugador = self.session.query(Player).filter(Player.username == username).first()
        if not jugador:
            return None
        
        if verificar_password(password, jugador.hashed_password):
            # Actualizar último login
            jugador.last_login = datetime.datetime.utcnow()
            self.session.commit()
            return jugador
        
        return None
    
    def listar_jugadores(self, server_id: Optional[int] = None) -> List[Player]:
        """Lista jugadores, opcionalmente filtrados por servidor"""
        query = self.session.query(Player)
        if server_id:
            query = query.filter(Player.server_id == server_id)
        
        return query.all()
    
    def buscar_por_username(self, username: str) -> List[Player]:
        """Busca jugadores por username (búsqueda parcial)"""
        return self.session.query(Player).filter(Player.username.like(f"%{username}%")).all()
    
    def obtener_jugador_por_id(self, player_id: int) -> Optional[Player]:
        """Obtiene un jugador por su ID"""
        return self.session.query(Player).get(player_id)


class GestorServidores:
    """Clase para gestionar servidores"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def crear_servidor(self, name: str, region: str) -> Server:
        """Crea un nuevo servidor"""
        servidor = Server(name=name, region=region)
        self.session.add(servidor)
        self.session.commit()
        return servidor
    
    def listar_servidores(self) -> List[Server]:
        """Lista todos los servidores disponibles"""
        return self.session.query(Server).all()
    
    def obtener_servidor(self, server_id: int) -> Optional[Server]:
        """Obtiene un servidor por su ID"""
        return self.session.query(Server).get(server_id)


class GestorPartidas:
    """Clase para gestionar partidas"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def crear_partida(self, player1_id: int, player2_id: int) -> Match:
        """Crea una nueva partida entre dos jugadores"""
        partida = Match()
        self.session.add(partida)
        self.session.flush()  # Para obtener el ID
        
        # Crear la línea temporal principal
        timeline_principal = Timeline(
            match_id=partida.id,
            created_by_player_id=player1_id,
            description="Línea principal"
        )
        self.session.add(timeline_principal)
        
        # Asignar jugadores a la partida
        mp1 = MatchPlayer(match_id=partida.id, player_id=player1_id, player_order=1)
        mp2 = MatchPlayer(match_id=partida.id, player_id=player2_id, player_order=2)
        
        self.session.add(mp1)
        self.session.add(mp2)
        self.session.commit()
        
        return partida
    
    def registrar_movimiento(self, match_id: int, player_id: int, timeline_id: int, 
                           sub_board_index: int, cell_index: int, time_taken: float) -> Move:
        """Registra un nuevo movimiento en una partida"""
        partida = self.session.query(Match).get(match_id)
        if not partida:
            raise ValueError("Partida no encontrada")
        
        # Verificar que el jugador pertenece a la partida
        match_player = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.player_id == player_id
        ).first()
        
        if not match_player:
            raise ValueError("El jugador no pertenece a esta partida")
        
        # Verificar que la timeline pertenece a la partida
        timeline = self.session.query(Timeline).filter(
            Timeline.id == timeline_id,
            Timeline.match_id == match_id
        ).first()
        
        if not timeline:
            raise ValueError("La línea temporal no pertenece a esta partida")
        
        # Obtener el próximo número de movimiento
        next_move_number = self.session.query(func.max(Move.move_number)).filter(
            Move.match_id == match_id
        ).scalar() or 0
        next_move_number += 1
        
        # Crear el movimiento
        movimiento = Move(
            match_id=match_id,
            player_id=player_id,
            timeline_id=timeline_id,
            sub_board_index=sub_board_index,
            cell_index=cell_index,
            move_number=next_move_number,
            time_taken_seconds=time_taken
        )
        
        self.session.add(movimiento)
        
        # Actualizar estadísticas de la partida
        partida.total_moves += 1
        
        # Actualizar el tiempo promedio de movimiento del jugador en la partida
        current_avg = match_player.average_move_time
        current_moves = self.session.query(Move).filter(
            Move.match_id == match_id,
            Move.player_id == player_id
        ).count()
        
        if current_moves == 0:
            match_player.average_move_time = time_taken
        else:
            total_time = current_avg * current_moves
            match_player.average_move_time = (total_time + time_taken) / (current_moves + 1)
        
        self.session.commit()
        return movimiento
    
    def crear_timeline(self, match_id: int, player_id: int, parent_timeline_id: int, 
                     starting_move_id: int, description: str) -> Timeline:
        """Crea una nueva línea temporal (timeline) en una partida"""
        # Verificar que la partida existe
        partida = self.session.query(Match).get(match_id)
        if not partida:
            raise ValueError("Partida no encontrada")
        
        # Verificar que el jugador pertenece a la partida
        match_player = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.player_id == player_id
        ).first()
        
        if not match_player:
            raise ValueError("El jugador no pertenece a esta partida")
        
        # Verificar que la timeline padre pertenece a la partida
        parent_timeline = self.session.query(Timeline).filter(
            Timeline.id == parent_timeline_id,
            Timeline.match_id == match_id
        ).first()
        
        if not parent_timeline:
            raise ValueError("La línea temporal padre no pertenece a esta partida")
        
        # Verificar que el movimiento de inicio pertenece a la timeline padre
        starting_move = self.session.query(Move).filter(
            Move.id == starting_move_id,
            Move.match_id == match_id,
            Move.timeline_id == parent_timeline_id
        ).first()
        
        if not starting_move:
            raise ValueError("El movimiento de inicio no pertenece a la línea temporal padre")
        
        # Crear la nueva timeline
        timeline = Timeline(
            match_id=match_id,
            parent_timeline_id=parent_timeline_id,
            created_by_player_id=player_id,
            starting_move_id=starting_move_id,
            description=description
        )
        
        self.session.add(timeline)
        
        # Actualizar estadísticas
        partida.total_timelines_created += 1
        match_player.timelines_created += 1
        
        # Actualizar estadísticas del jugador
        player_stats = self.session.query(PlayerStats).filter(
            PlayerStats.player_id == player_id
        ).first()
        
        if player_stats:
            player_stats.total_timelines_created += 1
        
        self.session.commit()
        return timeline
    
    def finalizar_partida(self, match_id: int, winner_id: Optional[int] = None) -> Match:
        """Finaliza una partida y actualiza estadísticas"""
        partida = self.session.query(Match).get(match_id)
        if not partida:
            raise ValueError("Partida no encontrada")
        
        # Si ya está finalizada, no hacer nada
        if partida.finished_at:
            return partida
        
        now = datetime.datetime.utcnow()
        partida.finished_at = now
        partida.winner_id = winner_id
        
        # Calcular duración en segundos
        delta = now - partida.created_at
        partida.duration_seconds = int(delta.total_seconds())
        
        # Actualizar match_players
        for mp in partida.match_players:
            # Marcar ganador
            if winner_id and mp.player_id == winner_id:
                mp.is_winner = True
            
            # Actualizar estadísticas del jugador
            stats = self.session.query(PlayerStats).filter(
                PlayerStats.player_id == mp.player_id
            ).first()
            
            if stats:
                stats.games_played += 1
                
                if winner_id is None:
                    # Empate
                    stats.games_drawn += 1
                elif mp.player_id == winner_id:
                    # Victoria
                    stats.games_won += 1
        
        self.session.commit()
        
        # Actualizar MMR
        if winner_id is not None or len(partida.match_players) == 2:
            gestor_mmr = GestorMMR(self.session)
            gestor_mmr.actualizar_mmr_partida(match_id)
        
        return partida
    
    def obtener_partida(self, match_id: int) -> Optional[Match]:
        """Obtiene una partida por su ID"""
        return self.session.query(Match).get(match_id)
    
    def listar_partidas(self, limit: int = 20) -> List[Match]:
        """Lista las últimas partidas"""
        return self.session.query(Match).order_by(desc(Match.created_at)).limit(limit).all()
    
    def listar_partidas_jugador(self, player_id: int, limit: int = 20) -> List[Match]:
        """Lista las últimas partidas de un jugador"""
        return self.session.query(Match).join(MatchPlayer).filter(
            MatchPlayer.player_id == player_id
        ).order_by(desc(Match.created_at)).limit(limit).all()
    
    def generar_partida_simulada(self, player1_id: int, player2_id: int, movimientos: int = 20, 
                               timelines: int = 2, winner_id: Optional[int] = None) -> Match:
        """Genera una partida simulada con movimientos y timelines aleatorios"""
        gestor_timeline = GestorTimeline(self.session)
        
        # Crear la partida
        partida = self.crear_partida(player1_id, player2_id)
        main_timeline_id = self.session.query(Timeline).filter(
            Timeline.match_id == partida.id,
            Timeline.parent_timeline_id.is_(None)
        ).first().id
        
        # Generar movimientos en la línea principal
        current_player_id = player1_id
        last_move_id = None
        
        for i in range(movimientos // 2):  # La mitad en la línea principal
            for _ in range(2):  # Alternar jugadores
                # Generar movimiento aleatorio
                sub_board = random.randint(0, 8)
                cell = random.randint(0, 8)
                time_taken = random.uniform(1.0, 10.0)
                
                move = self.registrar_movimiento(
                    partida.id, current_player_id, main_timeline_id,
                    sub_board, cell, time_taken
                )
                
                last_move_id = move.id
                
                # Alternar jugador
                current_player_id = player2_id if current_player_id == player1_id else player1_id
        
        # Crear timelines alternativas
        created_timelines = [main_timeline_id]
        
        for _ in range(timelines):
            # Seleccionar una timeline padre aleatoria
            parent_timeline_id = random.choice(created_timelines)
            
            # Obtener un movimiento aleatorio de la timeline padre
            parent_moves = self.session.query(Move).filter(
                Move.match_id == partida.id,
                Move.timeline_id == parent_timeline_id
            ).all()
            
            if not parent_moves:
                continue
                
            starting_move_id = random.choice(parent_moves).id
            creator_id = random.choice([player1_id, player2_id])
            
            timeline = gestor_timeline.crear_timeline(
                partida.id, creator_id, parent_timeline_id,
                starting_move_id, f"Timeline alternativa {_ + 1}"
            )
            
            created_timelines.append(timeline.id)
            
            # Generar algunos movimientos en esta timeline
            current_player_id = creator_id
            for _ in range(random.randint(3, 6)):
                # Generar movimiento aleatorio
                sub_board = random.randint(0, 8)
                cell = random.randint(0, 8)
                time_taken = random.uniform(1.0, 10.0)
                
                self.registrar_movimiento(
                    partida.id, current_player_id, timeline.id,
                    sub_board, cell, time_taken
                )
                
                # Alternar jugador
                current_player_id = player2_id if current_player_id == player1_id else player1_id
        
        # Finalizar la partida
        self.finalizar_partida(partida.id, winner_id)
        
        return partida


class GestorTimeline:
    """Clase para gestionar líneas temporales (timelines)"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def crear_timeline(self, match_id: int, player_id: int, parent_timeline_id: int, 
                     starting_move_id: int, description: str) -> Timeline:
        """Crea una nueva línea temporal"""
        # Verificar que la partida existe
        match = self.session.query(Match).get(match_id)
        if not match:
            raise ValueError("Partida no encontrada")
        
        # Verificar que el jugador pertenece a la partida
        match_player = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.player_id == player_id
        ).first()
        
        if not match_player:
            raise ValueError("El jugador no pertenece a esta partida")
        
        # Crear la timeline
        timeline = Timeline(
            match_id=match_id,
            parent_timeline_id=parent_timeline_id,
            created_by_player_id=player_id,
            starting_move_id=starting_move_id,
            description=description
        )
        
        self.session.add(timeline)
        
        # Actualizar estadísticas
        match.total_timelines_created += 1
        
        # Actualizar estadísticas del jugador
        player_stats = self.session.query(PlayerStats).filter(
            PlayerStats.player_id == player_id
        ).first()
        
        if player_stats:
            player_stats.total_timelines_created += 1
        
        self.session.commit()
        return timeline
    
    def obtener_timeline(self, timeline_id: int) -> Optional[Timeline]:
        """Obtiene una línea temporal por su ID"""
        return self.session.query(Timeline).get(timeline_id)
    
    def listar_timelines_partida(self, match_id: int) -> List[Timeline]:
        """Lista todas las líneas temporales de una partida"""
        return self.session.query(Timeline).filter(Timeline.match_id == match_id).all()
    
    def obtener_arbol_timelines(self, match_id: int) -> Dict:
        """Obtiene la estructura de árbol de las líneas temporales de una partida"""
        timelines = self.listar_timelines_partida(match_id)
        
        # Construir el árbol
        arbol = {}
        
        # Primero encontrar la raíz (línea principal)
        for tl in timelines:
            if tl.parent_timeline_id is None:
                arbol[tl.id] = {
                    "id": tl.id,
                    "description": tl.description,
                    "created_by": tl.created_by_player_id,
                    "created_at": tl.created_at,
                    "children": {}
                }
                break
        
        # Función recursiva para agregar hijos
        def agregar_hijos(parent_id, arbol_nodo):
            for tl in timelines:
                if tl.parent_timeline_id == parent_id:
                    arbol_nodo["children"][tl.id] = {
                        "id": tl.id,
                        "description": tl.description,
                        "created_by": tl.created_by_player_id,
                        "created_at": tl.created_at,
                        "children": {}
                    }
                    agregar_hijos(tl.id, arbol_nodo["children"][tl.id])
        
        # Agregar todas las ramas al árbol
        for timeline_id in arbol:
            agregar_hijos(timeline_id, arbol[timeline_id])
        
        return arbol
    
    def obtener_movimientos_timeline(self, timeline_id: int) -> List[Move]:
        """Obtiene todos los movimientos de una línea temporal"""
        return self.session.query(Move).filter(
            Move.timeline_id == timeline_id
        ).order_by(Move.move_number).all()


class GestorRanking:
    """Clase para gestionar rankings de jugadores"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def calcular_rank_label(self, mmr: int) -> str:
        """Calcula la etiqueta de rango basada en el MMR"""
        rank_label = RANKS[0]  # Valor por defecto: Sin Clasificar
        
        for threshold, label in sorted(RANKS.items()):
            if mmr >= threshold:
                rank_label = label
        
        return rank_label
    
    def actualizar_rank_label(self, player_id: int) -> str:
        """Actualiza la etiqueta de rango de un jugador basada en su MMR actual"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        if not ranking:
            return RANKS[0]
        
        rank_label = self.calcular_rank_label(ranking.current_mmr)
        ranking.rank_label = rank_label
        self.session.commit()
        
        return rank_label
    
    def actualizar_stats_ranking(self, player_id: int) -> None:
        """Actualiza las estadísticas en el ranking basadas en las stats del jugador"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        stats = self.session.query(PlayerStats).filter(
            PlayerStats.player_id == player_id
        ).first()
        
        if not ranking or not stats:
            return
        
        # Actualizar ratio de victorias
        if stats.games_played > 0:
            ranking.win_ratio = stats.games_won / stats.games_played
        
        # Actualizar racha máxima
        ranking.max_win_streak = stats.max_win_streak
        
        # Calcular velocidad promedio de victoria
        victorias = self.session.query(Match).filter(
            Match.winner_id == player_id
        ).all()
        
        if victorias:
            total_tiempo = sum(v.duration_seconds for v in victorias)
            ranking.average_victory_speed = total_tiempo / len(victorias)
        
        # Actualizar puntuación de uso de timelines
        timelines_creadas = self.session.query(func.count(Timeline.id)).filter(
            Timeline.created_by_player_id == player_id
        ).scalar() or 0
        
        partidas_jugadas = stats.games_played
        
        if partidas_jugadas > 0:
            ranking.timeline_usage_score = timelines_creadas / partidas_jugadas
        
        self.session.commit()
    
    def obtener_ranking_global(self, limit: int = 20) -> List[Dict]:
        """Obtiene el ranking global de jugadores ordenado por MMR"""
        results = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        ).order_by(
            desc(PlayerRanking.current_mmr)
        ).limit(limit).all()
        
        ranking = []
        for i, (player, pr) in enumerate(results, 1):
            ranking.append({
                "position": i,
                "player_id": player.id,
                "username": player.username,
                "mmr": pr.current_mmr,
                "rank_label": pr.rank_label,
                "win_ratio": pr.win_ratio
            })
        
        return ranking
    
    def obtener_ranking_por_servidor(self, server_id: int, limit: int = 20) -> List[Dict]:
        """Obtiene el ranking de jugadores de un servidor ordenado por MMR"""
        results = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        ).filter(
            Player.server_id == server_id
        ).order_by(
            desc(PlayerRanking.current_mmr)
        ).limit(limit).all()
        
        ranking = []
        for i, (player, pr) in enumerate(results, 1):
            ranking.append({
                "position": i,
                "player_id": player.id,
                "username": player.username,
                "mmr": pr.current_mmr,
                "rank_label": pr.rank_label,
                "win_ratio": pr.win_ratio
            })
        
        return ranking


class GestorMMR:
    """Clase para gestionar el MMR (Matchmaking Rating) de los jugadores"""
    
    def __init__(self, session: Session):
        self.session = session
        self.gestor_ranking = GestorRanking(session)
    
    def actualizar_mmr_partida(self, match_id: int) -> None:
        """Actualiza el MMR de los jugadores después de una partida"""
        match = self.session.query(Match).get(match_id)
        if not match or not match.finished_at:
            raise ValueError("La partida no existe o no ha finalizado")
        
        match_players = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id
        ).all()
        
        if len(match_players) != 2:
            raise ValueError("Esta función solo funciona con partidas de 2 jugadores")
        
        # Obtener los rankings de ambos jugadores
        p1_id = match_players[0].player_id
        p2_id = match_players[1].player_id
        
        p1_ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == p1_id
        ).first()
        
        p2_ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == p2_id
        ).first()
        
        if not p1_ranking or not p2_ranking:
            raise ValueError("Uno o ambos jugadores no tienen ranking")
        
        # Calcular el cambio de MMR basado en el algoritmo ELO simplificado
        # K es el factor de ajuste (cuánto puede cambiar el MMR)
        K = 32
        
        # Calcular probabilidades esperadas
        elo_diff = p2_ranking.current_mmr - p1_ranking.current_mmr
        expected_p1 = 1 / (1 + 10 ** (elo_diff / 400))
        expected_p2 = 1 - expected_p1
        
        # Determinar resultado real (1 = victoria, 0.5 = empate, 0 = derrota)
        if match.winner_id is None:
            # Empate
            actual_p1 = 0.5
            actual_p2 = 0.5
            reason = "Empate"
        elif match.winner_id == p1_id:
            # P1 gana
            actual_p1 = 1
            actual_p2 = 0
            reason = "Victoria"
        else:
            # P2 gana
            actual_p1 = 0
            actual_p2 = 1
            reason = "Victoria"
        
        # Calcular cambio de MMR
        mmr_change_p1 = round(K * (actual_p1 - expected_p1))
        mmr_change_p2 = round(K * (actual_p2 - expected_p2))
        
        # Guardar valores anteriores
        p1_mmr_before = p1_ranking.current_mmr
        p2_mmr_before = p2_ranking.current_mmr
        
        # Actualizar MMR
        p1_ranking.current_mmr += mmr_change_p1
        p2_ranking.current_mmr += mmr_change_p2
        
        # Asegurar que el MMR no sea negativo
        p1_ranking.current_mmr = max(0, p1_ranking.current_mmr)
        p2_ranking.current_mmr = max(0, p2_ranking.current_mmr)
        
        # Actualizar etiquetas de rango
        p1_ranking.rank_label = self.gestor_ranking.calcular_rank_label(p1_ranking.current_mmr)
        p2_ranking.rank_label = self.gestor_ranking.calcular_rank_label(p2_ranking.current_mmr)
        
        # Registrar historial de cambios de MMR
        mmr_history_p1 = MMRHistory(
            player_id=p1_id,
            match_id=match_id,
            mmr_before=p1_mmr_before,
            mmr_after=p1_ranking.current_mmr,
            change_reason=f"{reason} contra {self.session.query(Player).get(p2_id).username}"
        )
        
        mmr_history_p2 = MMRHistory(
            player_id=p2_id,
            match_id=match_id,
            mmr_before=p2_mmr_before,
            mmr_after=p2_ranking.current_mmr,
            change_reason=f"{reason} contra {self.session.query(Player).get(p1_id).username}"
        )
        
        self.session.add(mmr_history_p1)
        self.session.add(mmr_history_p2)
        self.session.commit()
    
    def modificar_mmr_manual(self, player_id: int, cambio: int, razon: str) -> int:
        """Modifica manualmente el MMR de un jugador"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        if not ranking:
            raise ValueError("El jugador no tiene ranking")
        
        # Guardar valor anterior
        mmr_before = ranking.current_mmr
        
        # Actualizar MMR
        ranking.current_mmr += cambio
        
        # Asegurar que el MMR no sea negativo
        ranking.current_mmr = max(0, ranking.current_mmr)
        
        # Actualizar etiqueta de rango
        ranking.rank_label = self.gestor_ranking.calcular_rank_label(ranking.current_mmr)
        
        # Registrar historial
        mmr_history = MMRHistory(
            player_id=player_id,
            mmr_before=mmr_before,
            mmr_after=ranking.current_mmr,
            change_reason=f"Ajuste manual: {razon}"
        )
        
        self.session.add(mmr_history)
        self.session.commit()
        
        return ranking.current_mmr
    
    def restablecer_mmr(self, player_id: int) -> int:
        """Restablece el MMR de un jugador al valor por defecto (1000)"""
        return self.modificar_mmr_manual(
            player_id, 
            1000 - self.session.query(PlayerRanking).filter(
                PlayerRanking.player_id == player_id
            ).first().current_mmr,
            "Restablecimiento del MMR"
        )
    
    def obtener_historial_mmr(self, player_id: int, limit: int = 20) -> List[MMRHistory]:
        """Obtiene el historial de cambios de MMR de un jugador"""
        return self.session.query(MMRHistory).filter(
            MMRHistory.player_id == player_id
        ).order_by(desc(MMRHistory.timestamp)).limit(limit).all()
    
    def obtener_grafico_mmr(self, player_id: int, limit: int = 20) -> Tuple[List[datetime.datetime], List[int]]:
        """Obtiene los datos para graficar la evolución del MMR de un jugador"""
        historial = self.obtener_historial_mmr(player_id, limit)
        historial.reverse()  # Ordenar cronológicamente
        
        fechas = [h.timestamp for h in historial]
        mmr = [h.mmr_after for h in historial]
        
        return fechas, mmr


# =============================================================================
# 4. INTERFAZ GRÁFICA (TKINTER)
# =============================================================================

class App(tk.Tk):
    """Aplicación principal"""
    
    def __init__(self):
        super().__init__()
        
        # Configuración inicial
        self.title("Sistema de Ranking - Tic Tac Toe Avanzado")
        self.geometry("1200x800")
        self.configure(bg=COLORS["bg_light"])
        
        # Variables de estado
        self.logged_in = False
        self.current_user = None
        self.is_admin = False
        
        # Crear la base de datos si no existe
        Base.metadata.create_all(engine)
        
        # Crear la sesión
        self.session = SessionLocal()
        
        # Inicializar gestores
        self.gestor_jugadores = GestorJugadores(self.session)
        self.gestor_servidores = GestorServidores(self.session)
        self.gestor_partidas = GestorPartidas(self.session)
        self.gestor_timeline = GestorTimeline(self.session)
        self.gestor_ranking = GestorRanking(self.session)
        self.gestor_mmr = GestorMMR(self.session)
        
        # Inicializar datos mínimos si la base está vacía
        self.inicializar_datos_base()
        
        # Mostrar pantalla de inicio de sesión
        self.mostrar_login()
    
    def inicializar_datos_base(self):
        """Inicializa datos base si no existen en la base de datos"""
        # Verificar si hay servidores
        if self.session.query(Server).count() == 0:
            # Crear servidores por defecto
            regiones = ["America", "Europa", "Asia", "Oceania"]
            for region in regiones:
                server = Server(name=f"Servidor {region}", region=region)
                self.session.add(server)
            
            self.session.commit()
        
        # Verificar si existe el admin
        if not self.session.query(Player).filter(Player.username == "admin").first():
            # Crear usuario admin
            admin = Player(
                username="admin",
                hashed_password=hash_password("admin"),
                level=99,
                server_id=1
            )
            self.session.add(admin)
            self.session.flush()
            
            # Crear stats y ranking para admin
            stats = PlayerStats(player_id=admin.id)
            ranking = PlayerRanking(player_id=admin.id)
            
            self.session.add(stats)
            self.session.add(ranking)
            self.session.commit()
    
    def mostrar_login(self):
        """Muestra la pantalla de inicio de sesión"""
        # Limpiar ventana
        for widget in self.winfo_children():
            widget.destroy()
        
        # Crear frame principal
        frame = ttk.Frame(self)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Título
        ttk.Label(frame, text="Tic Tac Toe Avanzado", font=("Helvetica", 24, "bold")).pack(pady=(0, 20))
        ttk.Label(frame, text="Sistema de Ranking y Gestión", font=("Helvetica", 16)).pack(pady=(0, 40))
        
        # Frame de login
        login_frame = ttk.Frame(frame)
        login_frame.pack(pady=20)
        
        # Campos de login
        ttk.Label(login_frame, text="Usuario:").grid(row=0, column=0, sticky="w", pady=5)
        username_entry = ttk.Entry(login_frame, width=30)
        username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(login_frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=5)
        password_entry = ttk.Entry(login_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Botón de login
        login_button = ttk.Button(
            login_frame, 
            text="Iniciar Sesión", 
            command=lambda: self.login(username_entry.get(), password_entry.get())
        )
        login_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Botón para crear servidor (solo para inicialización)
        ttk.Button(
            frame,
            text="Crear Servidor",
            command=self.crear_servidor_dialog
        ).pack(pady=10)
        
        # Botón para crear usuario (solo para inicialización)
        ttk.Button(
            frame,
            text="Crear Usuario",
            command=self.crear_usuario_dialog
        ).pack(pady=10)
    
    def login(self, username: str, password: str):
        """Procesa el inicio de sesión"""
        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña son obligatorios")
            return
        
        usuario = self.gestor_jugadores.autenticar_jugador(username, password)
        
        if not usuario:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
            return
        
        self.current_user = usuario
        self.logged_in = True
        self.is_admin = usuario.level >= 90
        
        # Mostrar la interfaz correspondiente
        if self.is_admin:
            self.mostrar_interfaz_admin()
        else:
            self.mostrar_interfaz_jugador()
    
    def logout(self):
        """Cierra la sesión actual"""
        self.current_user = None
        self.logged_in = False
        self.is_admin = False
        self.mostrar_login()
    
    def crear_servidor_dialog(self):
        """Muestra un diálogo para crear un nuevo servidor"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Crear Servidor")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Campos
        ttk.Label(dialog, text="Nombre:").pack(pady=(20, 5))
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Región:").pack(pady=5)
        region_entry = ttk.Entry(dialog, width=30)
        region_entry.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Guardar",
            command=lambda: self.guardar_servidor(
                name_entry.get(),
                region_entry.get(),
                dialog
            )
        ).pack(pady=20)
    
    def guardar_servidor(self, name: str, region: str, dialog: tk.Toplevel):
        """Guarda un nuevo servidor en la base de datos"""
        if not name or not region:
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=dialog)
            return
        
        try:
            self.gestor_servidores.crear_servidor(name, region)
            messagebox.showinfo("Éxito", "Servidor creado correctamente", parent=dialog)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el servidor: {str(e)}", parent=dialog)
    
    def crear_usuario_dialog(self):
        """Muestra un diálogo para crear un nuevo usuario"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Crear Usuario")
        dialog.geometry("300x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Campos
        ttk.Label(dialog, text="Nombre de Usuario:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Contraseña:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        # Selector de servidor
        ttk.Label(dialog, text="Servidor:").pack(pady=5)
        
        servers = self.gestor_servidores.listar_servidores()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        if server_names:
            server_var.set(server_names[0])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Guardar",
            command=lambda: self.guardar_usuario(
                username_entry.get(),
                password_entry.get(),
                server_ids[server_names.index(server_var.get())],
                dialog
            )
        ).pack(pady=20)
    
    def guardar_usuario(self, username: str, password: str, server_id: int, dialog: tk.Toplevel):
        """Guarda un nuevo usuario en la base de datos"""
        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña son obligatorios", parent=dialog)
            return
        
        try:
            jugador = self.gestor_jugadores.crear_jugador(username, password, server_id)
            if jugador:
                messagebox.showinfo("Éxito", "Usuario creado correctamente", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "El nombre de usuario ya existe", parent=dialog)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el usuario: {str(e)}", parent=dialog)
    
    def mostrar_interfaz_admin(self):
        """Muestra la interfaz de administración"""
        # Limpiar ventana
        for widget in self.winfo_children():
            widget.destroy()
        
        # Crear frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")
        
        # Crear notebook (pestañas)
        notebook = ttk.Notebook(main_frame)
        
        # Pestañas
        tab_jugadores = ttk.Frame(notebook)
        tab_partidas = ttk.Frame(notebook)
        tab_ranking = ttk.Frame(notebook)
        tab_mmr = ttk.Frame(notebook)
        
        notebook.add(tab_jugadores, text="Jugadores")
        notebook.add(tab_partidas, text="Partidas")
        notebook.add(tab_ranking, text="Rankings")
        notebook.add(tab_mmr, text="MMR")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Barra superior
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(
            top_frame, 
            text=f"Conectado como: {self.current_user.username} (Admin)",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")
        
        ttk.Button(
            top_frame,
            text="Cerrar Sesión",
            command=self.logout
        ).pack(side="right")
        
        # Llenar pestañas
        self.llenar_tab_jugadores(tab_jugadores)
        self.llenar_tab_partidas(tab_partidas)
        self.llenar_tab_ranking(tab_ranking)
        self.llenar_tab_mmr(tab_mmr)
    
    def llenar_tab_jugadores(self, tab):
        """Llena la pestaña de jugadores"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Búsqueda
        ttk.Label(control_frame, text="Buscar:").pack(side="left", padx=(0, 5))
        busqueda_var = tk.StringVar()
        busqueda_entry = ttk.Entry(control_frame, textvariable=busqueda_var, width=30)
        busqueda_entry.pack(side="left", padx=5)
        
        # Filtro por servidor
        ttk.Label(control_frame, text="Servidor:").pack(side="left", padx=(20, 5))
        
        servers = self.gestor_servidores.listar_servidores()
        server_names = ["Todos"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]
        
        server_var = tk.StringVar(value=server_names[0])
        server_menu = ttk.OptionMenu(control_frame, server_var, *server_names)
        server_menu.pack(side="left", padx=5)
        
        # Botones
        ttk.Button(
            control_frame,
            text="Buscar",
            command=lambda: self.buscar_jugadores(
                busqueda_var.get(),
                None if server_var.get() == "Todos" else server_ids[server_names.index(server_var.get())],
                jugadores_tree
            )
        ).pack(side="left", padx=20)
        
        ttk.Button(
            control_frame,
            text="Crear Jugador",
            command=self.crear_jugador_dialog
        ).pack(side="right", padx=5)
        
        # Tabla de jugadores
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Crear treeview (tabla)
        jugadores_tree = ttk.Treeview(
            table_frame,
            columns=("id", "username", "level", "server", "games", "mmr", "rank"),
            show="headings"
        )
        
        # Configurar columnas
        jugadores_tree.heading("id", text="ID")
        jugadores_tree.heading("username", text="Usuario")
        jugadores_tree.heading("level", text="Nivel")
        jugadores_tree.heading("server", text="Servidor")
        jugadores_tree.heading("games", text="Partidas")
        jugadores_tree.heading("mmr", text="MMR")
        jugadores_tree.heading("rank", text="Rango")
        
        jugadores_tree.column("id", width=50, anchor="center")
        jugadores_tree.column("username", width=150)
        jugadores_tree.column("level", width=50, anchor="center")
        jugadores_tree.column("server", width=150)
        jugadores_tree.column("games", width=70, anchor="center")
        jugadores_tree.column("mmr", width=70, anchor="center")
        jugadores_tree.column("rank", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=jugadores_tree.yview)
        jugadores_tree.configure(yscrollcommand=scrollbar.set)
        
        jugadores_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Menú contextual
        def mostrar_menu_contextual(event):
            item = jugadores_tree.identify_row(event.y)
            if item:
                jugadores_tree.selection_set(item)
                menu_contextual.post(event.x_root, event.y_root)
        
        menu_contextual = tk.Menu(jugadores_tree, tearoff=0)
        menu_contextual.add_command(label="Ver Detalles", command=lambda: self.ver_detalles_jugador(jugadores_tree))
        menu_contextual.add_command(label="Editar", command=lambda: self.editar_jugador_dialog(jugadores_tree))
        menu_contextual.add_separator()
        menu_contextual.add_command(label="Eliminar", command=lambda: self.eliminar_jugador(jugadores_tree))
        
        jugadores_tree.bind("<Button-3>", mostrar_menu_contextual)
        
        # Cargar datos iniciales
        self.cargar_jugadores(jugadores_tree)
    
    def cargar_jugadores(self, tree):
        """Carga la lista de jugadores en el treeview"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Obtener jugadores
        jugadores = self.gestor_jugadores.listar_jugadores()
        
        for jugador in jugadores:
            # Obtener datos relacionados
            stats = jugador.stats
            ranking = jugador.rankings
            servidor = jugador.server
            
            tree.insert(
                "",
                "end",
                values=(
                    jugador.id,
                    jugador.username,
                    jugador.level,
                    servidor.name if servidor else "N/A",
                    stats.games_played if stats else 0,
                    ranking.current_mmr if ranking else 0,
                    ranking.rank_label if ranking else "Sin Clasificar"
                )
            )
    
    def buscar_jugadores(self, busqueda: str, server_id: Optional[int], tree):
        """Busca jugadores según los criterios y actualiza el treeview"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Obtener jugadores según filtros
        if server_id:
            jugadores = self.gestor_jugadores.listar_jugadores(server_id)
        else:
            jugadores = self.gestor_jugadores.listar_jugadores()
        
        # Filtrar por búsqueda
        if busqueda:
            jugadores = [j for j in jugadores if busqueda.lower() in j.username.lower()]
        
        # Insertar en la tabla
        for jugador in jugadores:
            # Obtener datos relacionados
            stats = jugador.stats
            ranking = jugador.rankings
            servidor = jugador.server
            
            tree.insert(
                "",
                "end",
                values=(
                    jugador.id,
                    jugador.username,
                    jugador.level,
                    servidor.name if servidor else "N/A",
                    stats.games_played if stats else 0,
                    ranking.current_mmr if ranking else 0,
                    ranking.rank_label if ranking else "Sin Clasificar"
                )
            )
    
    def crear_jugador_dialog(self):
        """Muestra un diálogo para crear un nuevo jugador"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Crear Jugador")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()
        
        # Campos
        ttk.Label(dialog, text="Nombre de Usuario:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Contraseña:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Nivel:").pack(pady=5)
        level_var = tk.IntVar(value=1)
        level_entry = ttk.Spinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
        level_entry.pack(pady=5)
        
        # Selector de servidor
        ttk.Label(dialog, text="Servidor:").pack(pady=5)
        
        servers = self.gestor_servidores.listar_servidores()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        if server_names:
            server_var.set(server_names[0])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Guardar",
            command=lambda: self.guardar_nuevo_jugador(
                username_entry.get(),
                password_entry.get(),
                level_var.get(),
                server_ids[server_names.index(server_var.get())] if server_names else 1,
                dialog
            )
        ).pack(pady=20)
    
    def guardar_nuevo_jugador(self, username: str, password: str, level: int, server_id: int, dialog: tk.Toplevel):
        """Guarda un nuevo jugador en la base de datos"""
        if not username or not password:
            messagebox.showerror("Error", "Usuario y contraseña son obligatorios", parent=dialog)
            return
        
        try:
            # Crear jugador
            jugador = self.gestor_jugadores.crear_jugador(username, password, server_id)
            
            if not jugador:
                messagebox.showerror("Error", "El nombre de usuario ya existe", parent=dialog)
                return
            
            # Actualizar nivel
            jugador.level = level
            self.session.commit()
            
            messagebox.showinfo("Éxito", "Jugador creado correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de jugadores
            self.cargar_jugadores(self.winfo_children()[0].winfo_children()[0].winfo_children()[1].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear el jugador: {str(e)}", parent=dialog)
    
    def editar_jugador_dialog(self, tree):
        """Muestra un diálogo para editar un jugador existente"""
        # Obtener jugador seleccionado
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un jugador para editar")
            return
        
        # Obtener ID del jugador
        jugador_id = tree.item(selected[0], "values")[0]
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Editar Jugador: {jugador.username}")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Campos
        ttk.Label(dialog, text="Nombre de Usuario:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.insert(0, jugador.username)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Nueva Contraseña (dejar en blanco para mantener):").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Nivel:").pack(pady=5)
        level_var = tk.IntVar(value=jugador.level)
        level_entry = ttk.Spinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
        level_entry.pack(pady=5)
        
        # Selector de servidor
        ttk.Label(dialog, text="Servidor:").pack(pady=5)
        
        servers = self.gestor_servidores.listar_servidores()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        current_server_index = 0
        
        for i, s_id in enumerate(server_ids):
            if s_id == jugador.server_id:
                current_server_index = i
                break
        
        if server_names:
            server_var.set(server_names[current_server_index])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Guardar Cambios",
            command=lambda: self.guardar_edicion_jugador(
                jugador.id,
                {
                    "username": username_entry.get(),
                    "password": password_entry.get(),
                    "level": level_var.get(),
                    "server_id": server_ids[server_names.index(server_var.get())] if server_names else 1
                },
                dialog,
                tree
            )
        ).pack(pady=20)
    
    def guardar_edicion_jugador(self, jugador_id: int, data: Dict, dialog: tk.Toplevel, tree):
        """Guarda los cambios de un jugador en la base de datos"""
        try:
            # Actualizar jugador
            resultado = self.gestor_jugadores.editar_jugador(jugador_id, data)
            
            if not resultado:
                messagebox.showerror("Error", "No se pudo editar el jugador", parent=dialog)
                return
            
            messagebox.showinfo("Éxito", "Jugador actualizado correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de jugadores
            self.cargar_jugadores(tree)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo editar el jugador: {str(e)}", parent=dialog)
    
    def eliminar_jugador(self, tree):
        """Elimina un jugador de la base de datos"""
        # Obtener jugador seleccionado
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un jugador para eliminar")
            return
        
        # Obtener ID del jugador
        jugador_id = tree.item(selected[0], "values")[0]
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Confirmar eliminación
        confirmacion = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar al jugador {jugador.username}?\nEsta acción no se puede deshacer."
        )
        
        if not confirmacion:
            return
        
        try:
            # Eliminar jugador
            resultado = self.gestor_jugadores.eliminar_jugador(jugador_id)
            
            if not resultado:
                messagebox.showerror("Error", "No se pudo eliminar el jugador")
                return
            
            messagebox.showinfo("Éxito", "Jugador eliminado correctamente")
            
            # Actualizar lista de jugadores
            self.cargar_jugadores(tree)
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el jugador: {str(e)}")
    
    def ver_detalles_jugador(self, tree):
        """Muestra los detalles de un jugador"""
        # Obtener jugador seleccionado
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un jugador para ver detalles")
            return
        
        # Obtener ID del jugador
        jugador_id = tree.item(selected[0], "values")[0]
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Crear ventana de detalles
        dialog = tk.Toplevel(self)
        dialog.title(f"Detalles de {jugador.username}")
        dialog.geometry("600x500")
        dialog.transient(self)
        
        # Notebook para pestañas de detalles
        notebook = ttk.Notebook(dialog)
        
        # Pestañas
        tab_info = ttk.Frame(notebook)
        tab_stats = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_mmr = ttk.Frame(notebook)
        
        notebook.add(tab_info, text="Información")
        notebook.add(tab_stats, text="Estadísticas")
        notebook.add(tab_matches, text="Partidas")
        notebook.add(tab_mmr, text="MMR")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Pestaña de información
        info_frame = ttk.Frame(tab_info, padding=20)
        info_frame.pack(fill="both", expand=True)
        
        ttk.Label(info_frame, text="ID:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(jugador.id)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Usuario:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=jugador.username).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Nivel:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(jugador.level)).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Fecha de creación:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=jugador.created_at.strftime("%Y-%m-%d %H:%M")).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Último acceso:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=jugador.last_login.strftime("%Y-%m-%d %H:%M") if jugador.last_login else "Nunca").grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Servidor:", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=f"{jugador.server.name} ({jugador.server.region})" if jugador.server else "N/A").grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        # Pestaña de estadísticas
        if jugador.stats:
            stats = jugador.stats
            stats_frame = ttk.Frame(tab_stats, padding=20)
            stats_frame.pack(fill="both", expand=True)
            
            ttk.Label(stats_frame, text="Partidas jugadas:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_played)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Victorias:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_won)).grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Empates:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_drawn)).grid(row=2, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Derrotas:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_lost)).grid(row=3, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Ratio de victorias:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=f"{stats.win_ratio:.2f}").grid(row=4, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Timelines creadas:", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.total_timelines_created)).grid(row=5, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Tiempo medio por movimiento:", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=f"{stats.average_move_time:.2f}s").grid(row=6, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Racha máxima de victorias:", anchor="e").grid(row=7, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.max_win_streak)).grid(row=7, column=1, padx=5, pady=5, sticky="w")
        
        # Pestaña de partidas
        matches_frame = ttk.Frame(tab_matches)
        matches_frame.pack(fill="both", expand=True)
        
        # Lista de partidas
        matches_tree = ttk.Treeview(
            matches_frame,
            columns=("id", "fecha", "oponente", "resultado", "duracion"),
            show="headings"
        )
        
        matches_tree.heading("id", text="ID")
        matches_tree.heading("fecha", text="Fecha")
        matches_tree.heading("oponente", text="Oponente")
        matches_tree.heading("resultado", text="Resultado")
        matches_tree.heading("duracion", text="Duración")
        
        matches_tree.column("id", width=50, anchor="center")
        matches_tree.column("fecha", width=120)
        matches_tree.column("oponente", width=150)
        matches_tree.column("resultado", width=100, anchor="center")
        matches_tree.column("duracion", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(matches_frame, orient="vertical", command=matches_tree.yview)
        matches_tree.configure(yscrollcommand=scrollbar.set)
        
        matches_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Cargar partidas del jugador
        partidas = self.gestor_partidas.listar_partidas_jugador(jugador.id)
        
        for partida in partidas:
            # Determinar oponente y resultado
            oponente = ""
            resultado = ""
            
            for mp in partida.match_players:
                if mp.player_id != jugador.id:
                    oponente = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id).username
                
                if mp.player_id == jugador.id:
                    if partida.winner_id is None:
                        resultado = "Empate"
                    elif partida.winner_id == jugador.id:
                        resultado = "Victoria"
                    else:
                        resultado = "Derrota"
            
            # Calcular duración
            duracion = formatear_duracion(partida.duration_seconds) if partida.finished_at else "En progreso"
            
            matches_tree.insert(
                "",
                "end",
                values=(
                    partida.id,
                    partida.created_at.strftime("%Y-%m-%d %H:%M"),
                    oponente,
                    resultado,
                    duracion
                )
            )
        
        # Pestaña de MMR
        mmr_frame = ttk.Frame(tab_mmr)
        mmr_frame.pack(fill="both", expand=True)
        
        if jugador.rankings:
            ranking = jugador.rankings
            
            # Información de MMR
            info_mmr_frame = ttk.Frame(mmr_frame)
            info_mmr_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Label(info_mmr_frame, text="MMR Actual:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_mmr_frame, text=str(ranking.current_mmr)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(info_mmr_frame, text="Rango:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_mmr_frame, text=ranking.rank_label).grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            # Historial de MMR
            ttk.Label(mmr_frame, text="Historial de MMR", font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
            
            historial_frame = ttk.Frame(mmr_frame)
            historial_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            historial_tree = ttk.Treeview(
                historial_frame,
                columns=("fecha", "antes", "despues", "cambio", "razon"),
                show="headings"
            )
            
            historial_tree.heading("fecha", text="Fecha")
            historial_tree.heading("antes", text="MMR Anterior")
            historial_tree.heading("despues", text="MMR Nuevo")
            historial_tree.heading("cambio", text="Cambio")
            historial_tree.heading("razon", text="Razón")
            
            historial_tree.column("fecha", width=120)
            historial_tree.column("antes", width=80, anchor="center")
            historial_tree.column("despues", width=80, anchor="center")
            historial_tree.column("cambio", width=80, anchor="center")
            historial_tree.column("razon", width=200)
            
            scrollbar = ttk.Scrollbar(historial_frame, orient="vertical", command=historial_tree.yview)
            historial_tree.configure(yscrollcommand=scrollbar.set)
            
            historial_tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Cargar historial de MMR
            historial = self.gestor_mmr.obtener_historial_mmr(jugador.id)
            
            for h in historial:
                cambio = h.mmr_after - h.mmr_before
                cambio_str = f"+{cambio}" if cambio > 0 else str(cambio)
                
                historial_tree.insert(
                    "",
                    "end",
                    values=(
                        h.timestamp.strftime("%Y-%m-%d %H:%M"),
                        h.mmr_before,
                        h.mmr_after,
                        cambio_str,
                        h.change_reason
                    )
                )
            
            # Gráfico de evolución de MMR
            try:
                fechas, mmr = self.gestor_mmr.obtener_grafico_mmr(jugador.id)
                
                if fechas and mmr:
                    ttk.Label(mmr_frame, text="Evolución de MMR", font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
                    
                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(fechas, mmr, marker='o', linestyle='-', color='blue')
                    ax.set_ylabel('MMR')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Rotar etiquetas del eje x
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Integrar gráfico en Tkinter
                    canvas = FigureCanvasTkAgg(fig, master=mmr_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            except:
                # Si hay algún error con matplotlib, ignorar
                pass
        
        # Botón de cerrar
        ttk.Button(
            dialog,
            text="Cerrar",
            command=dialog.destroy
        ).pack(pady=10)
    
    def llenar_tab_partidas(self, tab):
        """Llena la pestaña de partidas"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Botones
        ttk.Button(
            control_frame,
            text="Crear Partida",
            command=self.crear_partida_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Generar Partida Simulada",
            command=self.generar_partida_simulada_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Actualizar",
            command=lambda: self.cargar_partidas(partidas_tree)
        ).pack(side="right", padx=5)
        
        # Tabla de partidas
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Crear treeview (tabla)
        partidas_tree = ttk.Treeview(
            table_frame,
            columns=("id", "fecha", "jugador1", "jugador2", "ganador", "estado", "duracion", "movimientos", "timelines"),
            show="headings"
        )
        
        # Configurar columnas
        partidas_tree.heading("id", text="ID")
        partidas_tree.heading("fecha", text="Fecha")
        partidas_tree.heading("jugador1", text="Jugador 1")
        partidas_tree.heading("jugador2", text="Jugador 2")
        partidas_tree.heading("ganador", text="Ganador")
        partidas_tree.heading("estado", text="Estado")
        partidas_tree.heading("duracion", text="Duración")
        partidas_tree.heading("movimientos", text="Movimientos")
        partidas_tree.heading("timelines", text="Timelines")
        
        partidas_tree.column("id", width=50, anchor="center")
        partidas_tree.column("fecha", width=120)
        partidas_tree.column("jugador1", width=100)
        partidas_tree.column("jugador2", width=100)
        partidas_tree.column("ganador", width=100)
        partidas_tree.column("estado", width=80, anchor="center")
        partidas_tree.column("duracion", width=80, anchor="center")
        partidas_tree.column("movimientos", width=80, anchor="center")
        partidas_tree.column("timelines", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=partidas_tree.yview)
        partidas_tree.configure(yscrollcommand=scrollbar.set)
        
        partidas_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Menú contextual
        def mostrar_menu_contextual(event):
            item = partidas_tree.identify_row(event.y)
            if item:
                partidas_tree.selection_set(item)
                menu_contextual.post(event.x_root, event.y_root)
        
        menu_contextual = tk.Menu(partidas_tree, tearoff=0)
        menu_contextual.add_command(label="Ver Detalles", command=lambda: self.ver_detalles_partida(partidas_tree))
        menu_contextual.add_command(label="Añadir Movimiento", command=lambda: self.añadir_movimiento_dialog(partidas_tree))
        menu_contextual.add_command(label="Crear Timeline", command=lambda: self.crear_timeline_dialog(partidas_tree))
        menu_contextual.add_separator()
        menu_contextual.add_command(label="Finalizar Partida", command=lambda: self.finalizar_partida_dialog(partidas_tree))
        
        partidas_tree.bind("<Button-3>", mostrar_menu_contextual)
        
        # Cargar datos iniciales
        self.cargar_partidas(partidas_tree)
    
    def cargar_partidas(self, tree):
        """Carga la lista de partidas en el treeview"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Obtener partidas
        partidas = self.gestor_partidas.listar_partidas()
        
        for partida in partidas:
            # Obtener jugadores
            jugadores = []
            for mp in partida.match_players:
                jugador = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id)
                if jugador:
                    jugadores.append((mp.player_order, jugador.username))
            
            # Ordenar jugadores por orden
            jugadores.sort(key=lambda x: x[0])
            
            # Determinar nombres
            jugador1 = jugadores[0][1] if len(jugadores) > 0 else "N/A"
            jugador2 = jugadores[1][1] if len(jugadores) > 1 else "N/A"
            
            # Determinar ganador
            ganador = "Empate"
            if partida.winner_id:
                for player_order, username in jugadores:
                    if self.gestor_jugadores.obtener_jugador_por_id(partida.winner_id).username == username:
                        ganador = username
                        break
            elif not partida.finished_at:
                ganador = "Pendiente"
            
            # Duración
            duracion = formatear_duracion(partida.duration_seconds) if partida.finished_at else "En curso"
            
            tree.insert(
                "",
                "end",
                values=(
                    partida.id,
                    partida.created_at.strftime("%Y-%m-%d %H:%M"),
                    jugador1,
                    jugador2,
                    ganador,
                    partida.status,
                    duracion,
                    partida.total_moves,
                    partida.total_timelines_created
                )
            )
    
    def crear_partida_dialog(self):
        """Muestra un diálogo para crear una nueva partida"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Crear Partida")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Selector de jugador 1
        ttk.Label(dialog, text="Jugador 1 (X):").pack(pady=(20, 5))
        
        jugadores = self.gestor_jugadores.listar_jugadores()
        jugador_names = [j.username for j in jugadores]
        jugador_ids = [j.id for j in jugadores]
        
        jugador1_var = tk.StringVar()
        if jugador_names:
            jugador1_var.set(jugador_names[0])
        
        jugador1_menu = ttk.OptionMenu(dialog, jugador1_var, *jugador_names)
        jugador1_menu.pack(pady=5)
        
        # Selector de jugador 2
        ttk.Label(dialog, text="Jugador 2 (O):").pack(pady=5)
        
        jugador2_var = tk.StringVar()
        if len(jugador_names) > 1:
            jugador2_var.set(jugador_names[1])
        elif jugador_names:
            jugador2_var.set(jugador_names[0])
        
        jugador2_menu = ttk.OptionMenu(dialog, jugador2_var, *jugador_names)
        jugador2_menu.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Crear Partida",
            command=lambda: self.guardar_partida(
                jugador_ids[jugador_names.index(jugador1_var.get())] if jugador_names else 0,
                jugador_ids[jugador_names.index(jugador2_var.get())] if jugador_names else 0,
                dialog
            )
        ).pack(pady=20)
    
    def guardar_partida(self, jugador1_id: int, jugador2_id: int, dialog: tk.Toplevel):
        """Guarda una nueva partida en la base de datos"""
        if jugador1_id == jugador2_id:
            messagebox.showerror("Error", "Debes seleccionar dos jugadores diferentes", parent=dialog)
            return
        
        try:
            # Crear partida
            partida = self.gestor_partidas.crear_partida(jugador1_id, jugador2_id)
            
            messagebox.showinfo("Éxito", f"Partida #{partida.id} creada correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de partidas
            self.cargar_partidas(self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la partida: {str(e)}", parent=dialog)
    
    def generar_partida_simulada_dialog(self):
        """Muestra un diálogo para generar una partida simulada"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Generar Partida Simulada")
        dialog.geometry("400x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Selector de jugador 1
        ttk.Label(dialog, text="Jugador 1 (X):").pack(pady=(20, 5))
        
        jugadores = self.gestor_jugadores.listar_jugadores()
        jugador_names = [j.username for j in jugadores]
        jugador_ids = [j.id for j in jugadores]
        
        jugador1_var = tk.StringVar()
        if jugador_names:
            jugador1_var.set(jugador_names[0])
        
        jugador1_menu = ttk.OptionMenu(dialog, jugador1_var, *jugador_names)
        jugador1_menu.pack(pady=5)
        
        # Selector de jugador 2
        ttk.Label(dialog, text="Jugador 2 (O):").pack(pady=5)
        
        jugador2_var = tk.StringVar()
        if len(jugador_names) > 1:
            jugador2_var.set(jugador_names[1])
        elif jugador_names:
            jugador2_var.set(jugador_names[0])
        
        jugador2_menu = ttk.OptionMenu(dialog, jugador2_var, *jugador_names)
        jugador2_menu.pack(pady=5)
        
        # Número de movimientos
        ttk.Label(dialog, text="Número de movimientos:").pack(pady=5)
        movimientos_var = tk.IntVar(value=20)
        movimientos_spin = ttk.Spinbox(dialog, from_=4, to=100, textvariable=movimientos_var, width=10)
        movimientos_spin.pack(pady=5)
        
        # Número de timelines
        ttk.Label(dialog, text="Número de timelines:").pack(pady=5)
        timelines_var = tk.IntVar(value=2)
        timelines_spin = ttk.Spinbox(dialog, from_=0, to=10, textvariable=timelines_var, width=10)
        timelines_spin.pack(pady=5)
        
        # Ganador
        ttk.Label(dialog, text="Ganador:").pack(pady=5)
        ganador_var = tk.StringVar(value="Aleatorio")
        ganador_opciones = ["Aleatorio", "Jugador 1", "Jugador 2", "Empate"]
        ganador_menu = ttk.OptionMenu(dialog, ganador_var, *ganador_opciones)
        ganador_menu.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Generar Partida",
            command=lambda: self.generar_partida_simulada(
                jugador_ids[jugador_names.index(jugador1_var.get())] if jugador_names else 0,
                jugador_ids[jugador_names.index(jugador2_var.get())] if jugador_names else 0,
                movimientos_var.get(),
                timelines_var.get(),
                ganador_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def generar_partida_simulada(self, jugador1_id: int, jugador2_id: int, movimientos: int, 
                               timelines: int, ganador: str, dialog: tk.Toplevel):
        """Genera una partida simulada"""
        if jugador1_id == jugador2_id:
            messagebox.showerror("Error", "Debes seleccionar dos jugadores diferentes", parent=dialog)
            return
        
        try:
            # Determinar ganador
            winner_id = None
            if ganador == "Jugador 1":
                winner_id = jugador1_id
            elif ganador == "Jugador 2":
                winner_id = jugador2_id
            elif ganador == "Aleatorio" and random.random() > 0.3:  # 70% de probabilidad de tener ganador
                winner_id = jugador1_id if random.random() > 0.5 else jugador2_id
            
            # Generar partida simulada
            partida = self.gestor_partidas.generar_partida_simulada(
                jugador1_id, jugador2_id, movimientos, timelines, winner_id
            )
            
            messagebox.showinfo("Éxito", f"Partida #{partida.id} generada correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de partidas
            self.cargar_partidas(self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar la partida: {str(e)}", parent=dialog)
    
    def ver_detalles_partida(self, tree):
        """Muestra los detalles de una partida"""
        # Obtener partida seleccionada
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una partida para ver detalles")
            return
        
        # Obtener ID de la partida
        partida_id = tree.item(selected[0], "values")[0]
        partida = self.gestor_partidas.obtener_partida(partida_id)
        
        if not partida:
            messagebox.showerror("Error", "Partida no encontrada")
            return
        
        # Crear ventana de detalles
        dialog = tk.Toplevel(self)
        dialog.title(f"Detalles de Partida #{partida.id}")
        dialog.geometry("800x600")
        dialog.transient(self)
        
        # Notebook para pestañas de detalles
        notebook = ttk.Notebook(dialog)
        
        # Pestañas
        tab_info = ttk.Frame(notebook)
        tab_movimientos = ttk.Frame(notebook)
        tab_timelines = ttk.Frame(notebook)
        
        notebook.add(tab_info, text="Información")
        notebook.add(tab_movimientos, text="Movimientos")
        notebook.add(tab_timelines, text="Timelines")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Pestaña de información
        info_frame = ttk.Frame(tab_info, padding=20)
        info_frame.pack(fill="both", expand=True)
        
        # Información general
        ttk.Label(info_frame, text="ID:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(partida.id)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Fecha de creación:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=partida.created_at.strftime("%Y-%m-%d %H:%M")).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Estado:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=partida.status).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        if partida.finished_at:
            ttk.Label(info_frame, text="Fecha de finalización:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_frame, text=partida.finished_at.strftime("%Y-%m-%d %H:%M")).grid(row=3, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(info_frame, text="Duración:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_frame, text=formatear_duracion(partida.duration_seconds)).grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Información de jugadores
        ttk.Label(info_frame, text="Jugadores:", anchor="e", font=("Helvetica", 11, "bold")).grid(row=5, column=0, padx=5, pady=(20, 5), sticky="e")
        
        row = 6
        for mp in partida.match_players:
            jugador = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id)
            if jugador:
                simbolo = "X" if mp.player_order == 1 else "O"
                resultado = ""
                
                if partida.finished_at:
                    if partida.winner_id is None:
                        resultado = "Empate"
                    elif partida.winner_id == mp.player_id:
                        resultado = "Victoria"
                    else:
                        resultado = "Derrota"
                
                ttk.Label(info_frame, text=f"Jugador {mp.player_order} ({simbolo}):", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                ttk.Label(info_frame, text=f"{jugador.username} - {resultado}").grid(row=row, column=1, padx=5, pady=5, sticky="w")
                
                row += 1
                
                if mp.average_move_time > 0:
                    ttk.Label(info_frame, text="Tiempo promedio por movimiento:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                    ttk.Label(info_frame, text=f"{mp.average_move_time:.2f}s").grid(row=row, column=1, padx=5, pady=5, sticky="w")
                    row += 1
                
                if mp.timelines_created > 0:
                    ttk.Label(info_frame, text="Timelines creadas:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                    ttk.Label(info_frame, text=str(mp.timelines_created)).grid(row=row, column=1, padx=5, pady=5, sticky="w")
                    row += 1
        
        # Estadísticas
        ttk.Label(info_frame, text="Estadísticas:", anchor="e", font=("Helvetica", 11, "bold")).grid(row=row, column=0, padx=5, pady=(20, 5), sticky="e")
        row += 1
        
        ttk.Label(info_frame, text="Total de movimientos:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(partida.total_moves)).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        row += 1
        
        ttk.Label(info_frame, text="Total de timelines:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(partida.total_timelines_created)).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        
        # Pestaña de movimientos
        movimientos_frame = ttk.Frame(tab_movimientos)
        movimientos_frame.pack(fill="both", expand=True)
        
        # Selector de timeline
        timeline_frame = ttk.Frame(movimientos_frame)
        timeline_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(timeline_frame, text="Timeline:").pack(side="left", padx=5)
        
        timelines = self.gestor_timeline.listar_timelines_partida(partida.id)
        timeline_names = [f"#{t.id} - {t.description}" for t in timelines]
        timeline_ids = [t.id for t in timelines]
        
        timeline_var = tk.StringVar()
        if timeline_names:
            timeline_var.set(timeline_names[0])
        
        timeline_menu = ttk.OptionMenu(
            timeline_frame, 
            timeline_var, 
            *timeline_names,
            command=lambda _: self.cargar_movimientos(
                movimientos_tree,
                timeline_ids[timeline_names.index(timeline_var.get())] if timeline_names else 0
            )
        )
        timeline_menu.pack(side="left", padx=5)
        
        # Tabla de movimientos
        movimientos_tree = ttk.Treeview(
            movimientos_frame,
            columns=("id", "orden", "jugador", "subtablero", "celda", "tiempo", "timestamp"),
            show="headings"
        )
        
        movimientos_tree.heading("id", text="ID")
        movimientos_tree.heading("orden", text="Orden")
        movimientos_tree.heading("jugador", text="Jugador")
        movimientos_tree.heading("subtablero", text="Sub-Tablero")
        movimientos_tree.heading("celda", text="Celda")
        movimientos_tree.heading("tiempo", text="Tiempo")
        movimientos_tree.heading("timestamp", text="Timestamp")
        
        movimientos_tree.column("id", width=50, anchor="center")
        movimientos_tree.column("orden", width=50, anchor="center")
        movimientos_tree.column("jugador", width=100)
        movimientos_tree.column("subtablero", width=80, anchor="center")
        movimientos_tree.column("celda", width=80, anchor="center")
        movimientos_tree.column("tiempo", width=80, anchor="center")
        movimientos_tree.column("timestamp", width=150)
        
        scrollbar = ttk.Scrollbar(movimientos_frame, orient="vertical", command=movimientos_tree.yview)
        movimientos_tree.configure(yscrollcommand=scrollbar.set)
        
        movimientos_tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Cargar movimientos de la primera timeline si existe
        if timeline_ids:
            self.cargar_movimientos(movimientos_tree, timeline_ids[0])
        
        # Pestaña de timelines
        timelines_frame = ttk.Frame(tab_timelines)
        timelines_frame.pack(fill="both", expand=True)
        
        # Visualización de timelines (árbol)
        ttk.Label(timelines_frame, text="Estructura de Timelines", font=("Helvetica", 12, "bold")).pack(pady=(10, 20))
        
        # Crear un widget de texto para mostrar el árbol
        arbol_text = scrolledtext.ScrolledText(timelines_frame, width=80, height=20)
        arbol_text.pack(padx=10, pady=10, expand=True, fill="both")
        
        # Obtener y mostrar el árbol de timelines
        arbol = self.gestor_timeline.obtener_arbol_timelines(partida.id)
        
        if arbol:
            # Función recursiva para mostrar el árbol
            def mostrar_arbol(nodo, nivel=0):
                indent = "  " * nivel
                raiz_id = list(arbol.keys())[0] if arbol else None
                
                # Si es la raíz, agregar un formato especial
                if nivel == 0:
                    arbol_text.insert(tk.END, f"{indent}● Timeline Principal #{nodo['id']}\n")
                else:
                    arbol_text.insert(tk.END, f"{indent}├─ Timeline #{nodo['id']}\n")
                
                # Agregar detalles
                arbol_text.insert(tk.END, f"{indent}   │ Descripción: {nodo['description']}\n")
                
                jugador = self.gestor_jugadores.obtener_jugador_por_id(nodo['created_by'])
                if jugador:
                    arbol_text.insert(tk.END, f"{indent}   │ Creada por: {jugador.username}\n")
                
                arbol_text.insert(tk.END, f"{indent}   │ Fecha: {nodo['created_at'].strftime('%Y-%m-%d %H:%M')}\n")
                
                # Mostrar hijos
                for hijo_id, hijo in nodo['children'].items():
                    mostrar_arbol(hijo, nivel + 1)
            
            # Mostrar árbol
            for timeline_id, timeline in arbol.items():
                mostrar_arbol(timeline)
        
        # Botón de cerrar
        ttk.Button(
            dialog,
            text="Cerrar",
            command=dialog.destroy
        ).pack(pady=10)
    
    def cargar_movimientos(self, tree, timeline_id: int):
        """Carga los movimientos de una timeline en el treeview"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Obtener movimientos
        movimientos = self.gestor_timeline.obtener_movimientos_timeline(timeline_id)
        
        for movimiento in movimientos:
            # Obtener jugador
            jugador = self.gestor_jugadores.obtener_jugador_por_id(movimiento.player_id)
            
            tree.insert(
                "",
                "end",
                values=(
                    movimiento.id,
                    movimiento.move_number,
                    jugador.username if jugador else "N/A",
                    movimiento.sub_board_index,
                    movimiento.cell_index,
                    f"{movimiento.time_taken_seconds:.2f}s",
                    movimiento.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )
            )
    
    def añadir_movimiento_dialog(self, tree):
        """Muestra un diálogo para añadir un movimiento a una partida"""
        # Obtener partida seleccionada
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una partida para añadir un movimiento")
            return
        
        # Obtener ID de la partida
        partida_id = tree.item(selected[0], "values")[0]
        partida = self.gestor_partidas.obtener_partida(partida_id)
        
        if not partida:
            messagebox.showerror("Error", "Partida no encontrada")
            return
        
        if partida.finished_at:
            messagebox.showwarning("Aviso", "No se pueden añadir movimientos a una partida finalizada")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Añadir Movimiento a Partida #{partida.id}")
        dialog.geometry("400x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Selector de jugador
        ttk.Label(dialog, text="Jugador:").pack(pady=(20, 5))
        
        # Obtener jugadores de la partida
        jugadores = []
        for mp in partida.match_players:
            jugador = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id)
            if jugador:
                jugadores.append((mp.player_id, jugador.username))
        
        jugador_names = [j[1] for j in jugadores]
        jugador_ids = [j[0] for j in jugadores]
        
        jugador_var = tk.StringVar()
        if jugador_names:
            jugador_var.set(jugador_names[0])
        
        jugador_menu = ttk.OptionMenu(dialog, jugador_var, *jugador_names)
        jugador_menu.pack(pady=5)
        
        # Selector de timeline
        ttk.Label(dialog, text="Timeline:").pack(pady=5)
        
        timelines = self.gestor_timeline.listar_timelines_partida(partida.id)
        timeline_names = [f"#{t.id} - {t.description}" for t in timelines]
        timeline_ids = [t.id for t in timelines]
        
        timeline_var = tk.StringVar()
        if timeline_names:
            timeline_var.set(timeline_names[0])
        
        timeline_menu = ttk.OptionMenu(dialog, timeline_var, *timeline_names)
        timeline_menu.pack(pady=5)
        
        # Sub-tablero y celda
        ttk.Label(dialog, text="Sub-tablero (0-8):").pack(pady=5)
        sub_board_var = tk.IntVar(value=0)
        sub_board_spin = ttk.Spinbox(dialog, from_=0, to=8, textvariable=sub_board_var, width=10)
        sub_board_spin.pack(pady=5)
        
        ttk.Label(dialog, text="Celda (0-8):").pack(pady=5)
        cell_var = tk.IntVar(value=0)
        cell_spin = ttk.Spinbox(dialog, from_=0, to=8, textvariable=cell_var, width=10)
        cell_spin.pack(pady=5)
        
        # Tiempo de movimiento
        ttk.Label(dialog, text="Tiempo (segundos):").pack(pady=5)
        time_var = tk.DoubleVar(value=2.0)
        time_spin = ttk.Spinbox(dialog, from_=0.1, to=60.0, increment=0.1, textvariable=time_var, width=10)
        time_spin.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Añadir Movimiento",
            command=lambda: self.guardar_movimiento(
                partida.id,
                jugador_ids[jugador_names.index(jugador_var.get())] if jugador_names else 0,
                timeline_ids[timeline_names.index(timeline_var.get())] if timeline_names else 0,
                sub_board_var.get(),
                cell_var.get(),
                time_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def guardar_movimiento(self, partida_id: int, jugador_id: int, timeline_id: int, 
                         sub_board: int, cell: int, time_taken: float, dialog: tk.Toplevel):
        """Guarda un nuevo movimiento en la base de datos"""
        try:
            # Registrar movimiento
            movimiento = self.gestor_partidas.registrar_movimiento(
                partida_id, jugador_id, timeline_id, sub_board, cell, time_taken
            )
            
            messagebox.showinfo("Éxito", f"Movimiento #{movimiento.move_number} añadido correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de partidas
            self.cargar_partidas(self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo añadir el movimiento: {str(e)}", parent=dialog)
    
    def crear_timeline_dialog(self, tree):
        """Muestra un diálogo para crear una nueva timeline en una partida"""
        # Obtener partida seleccionada
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una partida para crear una timeline")
            return
        
        # Obtener ID de la partida
        partida_id = tree.item(selected[0], "values")[0]
        partida = self.gestor_partidas.obtener_partida(partida_id)
        
        if not partida:
            messagebox.showerror("Error", "Partida no encontrada")
            return
        
        if partida.finished_at:
            messagebox.showwarning("Aviso", "No se pueden crear timelines en una partida finalizada")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Crear Timeline en Partida #{partida.id}")
        dialog.geometry("500x500")
        dialog.transient(self)
        dialog.grab_set()
        
        # Selector de jugador
        ttk.Label(dialog, text="Creada por jugador:").pack(pady=(20, 5))
        
        # Obtener jugadores de la partida
        jugadores = []
        for mp in partida.match_players:
            jugador = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id)
            if jugador:
                jugadores.append((mp.player_id, jugador.username))
        
        jugador_names = [j[1] for j in jugadores]
        jugador_ids = [j[0] for j in jugadores]
        
        jugador_var = tk.StringVar()
        if jugador_names:
            jugador_var.set(jugador_names[0])
        
        jugador_menu = ttk.OptionMenu(dialog, jugador_var, *jugador_names)
        jugador_menu.pack(pady=5)
        
        # Selector de timeline padre
        ttk.Label(dialog, text="Timeline padre:").pack(pady=5)
        
        timelines = self.gestor_timeline.listar_timelines_partida(partida.id)
        timeline_names = [f"#{t.id} - {t.description}" for t in timelines]
        timeline_ids = [t.id for t in timelines]
        
        timeline_var = tk.StringVar()
        if timeline_names:
            timeline_var.set(timeline_names[0])
        
        timeline_menu = ttk.OptionMenu(
            dialog, 
            timeline_var, 
            *timeline_names,
            command=lambda _: self.actualizar_movimientos_timeline(
                movimientos_list,
                timeline_ids[timeline_names.index(timeline_var.get())] if timeline_names else 0
            )
        )
        timeline_menu.pack(pady=5)
        
        # Selector de movimiento de inicio
        ttk.Label(dialog, text="Movimiento de inicio:").pack(pady=5)
        
        # Lista de movimientos (se actualizará al seleccionar una timeline)
        movimientos_frame = ttk.Frame(dialog)
        movimientos_frame.pack(pady=5, fill="both", expand=True)
        
        movimientos_list = tk.Listbox(movimientos_frame, height=8)
        scrollbar = ttk.Scrollbar(movimientos_frame, orient="vertical", command=movimientos_list.yview)
        movimientos_list.configure(yscrollcommand=scrollbar.set)
        
        movimientos_list.pack(side="left", fill="both", expand=True, padx=5)
        scrollbar.pack(side="right", fill="y")
        
        # Actualizar la lista de movimientos con la primera timeline
        if timeline_ids:
            self.actualizar_movimientos_timeline(movimientos_list, timeline_ids[0])
        
        # Descripción
        ttk.Label(dialog, text="Descripción:").pack(pady=5)
        descripcion_entry = ttk.Entry(dialog, width=50)
        descripcion_entry.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Crear Timeline",
            command=lambda: self.guardar_timeline(
                partida.id,
                jugador_ids[jugador_names.index(jugador_var.get())] if jugador_names and jugador_var.get() in jugador_names else 0,
                timeline_ids[timeline_names.index(timeline_var.get())] if timeline_names and timeline_var.get() in timeline_names else 0,
                self.obtener_id_movimiento_seleccionado(movimientos_list),
                descripcion_entry.get(),
                dialog
            )
        ).pack(pady=20)
    
    def actualizar_movimientos_timeline(self, listbox, timeline_id: int):
        """Actualiza la lista de movimientos de una timeline"""
        # Limpiar listbox
        listbox.delete(0, tk.END)
        
        # Obtener movimientos
        movimientos = self.gestor_timeline.obtener_movimientos_timeline(timeline_id)
        
        # Lista para almacenar IDs de movimientos
        self.movimientos_ids = []
        
        for movimiento in movimientos:
            # Obtener jugador
            jugador = self.gestor_jugadores.obtener_jugador_por_id(movimiento.player_id)
            jugador_nombre = jugador.username if jugador else "N/A"
            
            # Añadir movimiento a la lista
            listbox.insert(
                tk.END,
                f"#{movimiento.move_number} - {jugador_nombre} ({movimiento.sub_board_index}, {movimiento.cell_index})"
            )
            
            # Guardar ID del movimiento
            self.movimientos_ids.append(movimiento.id)
    
    def obtener_id_movimiento_seleccionado(self, listbox):
        """Obtiene el ID del movimiento seleccionado en el listbox"""
        selected = listbox.curselection()
        if not selected:
            return None
        
        index = selected[0]
        if 0 <= index < len(self.movimientos_ids):
            return self.movimientos_ids[index]
        
        return None
    
    def guardar_timeline(self, partida_id: int, jugador_id: int, parent_timeline_id: int, 
                       starting_move_id: int, description: str, dialog: tk.Toplevel):
        """Guarda una nueva timeline en la base de datos"""
        if not starting_move_id:
            messagebox.showerror("Error", "Debes seleccionar un movimiento de inicio", parent=dialog)
            return
        
        if not description:
            messagebox.showerror("Error", "La descripción es obligatoria", parent=dialog)
            return
        
        try:
            # Crear timeline
            timeline = self.gestor_partidas.crear_timeline(
                partida_id, jugador_id, parent_timeline_id, starting_move_id, description
            )
            
            messagebox.showinfo("Éxito", f"Timeline #{timeline.id} creada correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de partidas
            self.cargar_partidas(self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la timeline: {str(e)}", parent=dialog)
    
    def finalizar_partida_dialog(self, tree):
        """Muestra un diálogo para finalizar una partida"""
        # Obtener partida seleccionada
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una partida para finalizar")
            return
        
        # Obtener ID de la partida
        partida_id = tree.item(selected[0], "values")[0]
        partida = self.gestor_partidas.obtener_partida(partida_id)
        
        if not partida:
            messagebox.showerror("Error", "Partida no encontrada")
            return
        
        if partida.finished_at:
            messagebox.showwarning("Aviso", "La partida ya está finalizada")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Finalizar Partida #{partida.id}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Selector de resultado
        ttk.Label(dialog, text="Resultado:").pack(pady=(20, 5))
        
        # Obtener jugadores de la partida
        jugadores = []
        for mp in partida.match_players:
            jugador = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id)
            if jugador:
                jugadores.append((mp.player_id, jugador.username))
        
        # Opciones de resultado
        resultado_opciones = ["Empate"] + [f"Gana {j[1]}" for j in jugadores]
        resultado_var = tk.StringVar(value=resultado_opciones[0])
        
        resultado_menu = ttk.OptionMenu(dialog, resultado_var, *resultado_opciones)
        resultado_menu.pack(pady=5)
        
        # Descripción final
        ttk.Label(dialog, text="Descripción del estado final (opcional):").pack(pady=5)
        descripcion = ttk.Entry(dialog, width=50)
        descripcion.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Finalizar Partida",
            command=lambda: self.guardar_finalizacion_partida(
                partida.id,
                None if resultado_var.get() == "Empate" else jugadores[[i for i, j in enumerate(jugadores) if f"Gana {j[1]}" == resultado_var.get()][0]][0],
                descripcion.get(),
                dialog
            )
        ).pack(pady=20)
    
    def guardar_finalizacion_partida(self, partida_id: int, winner_id: Optional[int], 
                                  descripcion: str, dialog: tk.Toplevel):
        """Guarda la finalización de una partida"""
        try:
            # Actualizar descriópción si existe
            if descripcion:
                partida = self.gestor_partidas.obtener_partida(partida_id)
                if partida:
                    partida.final_state_description = descripcion
                    self.session.commit()
            
            # Finalizar partida
            self.gestor_partidas.finalizar_partida(partida_id, winner_id)
            
            messagebox.showinfo("Éxito", "Partida finalizada correctamente", parent=dialog)
            dialog.destroy()
            
            # Actualizar lista de partidas
            self.cargar_partidas(self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0])
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo finalizar la partida: {str(e)}", parent=dialog)
    
    def llenar_tab_ranking(self, tab):
        """Llena la pestaña de rankings"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Selector de servidor
        ttk.Label(control_frame, text="Servidor:").pack(side="left", padx=5)
        
        servers = self.gestor_servidores.listar_servidores()
        server_names = ["Global"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]
        
        server_var = tk.StringVar(value=server_names[0])
        
        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.actualizar_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        )
        server_menu.pack(side="left", padx=5)
        
        # Botón de actualizar
        ttk.Button(
            control_frame,
            text="Actualizar",
            command=lambda: self.actualizar_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        ).pack(side="right", padx=5)
        
        # Tabla de ranking
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Crear treeview (tabla)
        ranking_tree = ttk.Treeview(
            table_frame,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )
        
        # Configurar columnas
        ranking_tree.heading("pos", text="#")
        ranking_tree.heading("id", text="ID")
        ranking_tree.heading("username", text="Usuario")
        ranking_tree.heading("mmr", text="MMR")
        ranking_tree.heading("rank", text="Rango")
        ranking_tree.heading("win_ratio", text="Win Ratio")
        
        ranking_tree.column("pos", width=50, anchor="center")
        ranking_tree.column("id", width=50, anchor="center")
        ranking_tree.column("username", width=150)
        ranking_tree.column("mmr", width=70, anchor="center")
        ranking_tree.column("rank", width=100)
        ranking_tree.column("win_ratio", width=70, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=ranking_tree.yview)
        ranking_tree.configure(yscrollcommand=scrollbar.set)
        
        ranking_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Cargar datos iniciales (ranking global)
        self.actualizar_ranking(ranking_tree)
    
    def actualizar_ranking(self, tree, server_id: Optional[int] = None):
        """Actualiza la tabla de ranking con los datos más recientes"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)
        
        # Obtener ranking
        if server_id:
            ranking = self.gestor_ranking.obtener_ranking_por_servidor(server_id)
        else:
            ranking = self.gestor_ranking.obtener_ranking_global()
        
        # Insertar datos en la tabla
        for jugador in ranking:
            tree.insert(
                "",
                "end",
                values=(
                    jugador["position"],
                    jugador["player_id"],
                    jugador["username"],
                    jugador["mmr"],
                    jugador["rank_label"],
                    f"{jugador['win_ratio']:.2f}"
                )
            )
    
    def llenar_tab_mmr(self, tab):
        """Llena la pestaña de MMR"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Selector de jugador
        ttk.Label(control_frame, text="Jugador:").pack(side="left", padx=5)
        
        jugadores = self.gestor_jugadores.listar_jugadores()
        jugador_names = [j.username for j in jugadores]
        jugador_ids = [j.id for j in jugadores]
        
        jugador_var = tk.StringVar()
        if jugador_names:
            jugador_var.set(jugador_names[0])
        
        jugador_menu = ttk.OptionMenu(control_frame, jugador_var, *jugador_names)
        jugador_menu.pack(side="left", padx=5)
        
        # Botones
        ttk.Button(
            control_frame,
            text="Modificar MMR",
            command=lambda: self.modificar_mmr_dialog(
                jugador_ids[jugador_names.index(jugador_var.get())] if jugador_names else 0
            )
        ).pack(side="left", padx=20)
        
        ttk.Button(
            control_frame,
            text="Restablecer MMR",
            command=lambda: self.restablecer_mmr(
                jugador_ids[jugador_names.index(jugador_var.get())] if jugador_names else 0
            )
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Ver Historial",
            command=lambda: self.ver_historial_mmr(
                jugador_ids[jugador_names.index(jugador_var.get())] if jugador_names else 0
            )
        ).pack(side="left", padx=5)
    
    def modificar_mmr_dialog(self, jugador_id: int):
        """Muestra un diálogo para modificar el MMR de un jugador"""
        if not jugador_id:
            messagebox.showwarning("Aviso", "Selecciona un jugador")
            return
        
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Obtener MMR actual
        ranking = jugador.rankings
        if not ranking:
            messagebox.showerror("Error", "El jugador no tiene ranking")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Modificar MMR de {jugador.username}")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Información actual
        ttk.Label(dialog, text=f"MMR Actual: {ranking.current_mmr}", font=("Helvetica", 12, "bold")).pack(pady=(20, 5))
        ttk.Label(dialog, text=f"Rango: {ranking.rank_label}").pack(pady=5)
        
        # Cambio de MMR
        ttk.Label(dialog, text="Cambio de MMR:").pack(pady=(20, 5))
        cambio_var = tk.IntVar(value=0)
        cambio_spin = ttk.Spinbox(dialog, from_=-500, to=500, increment=10, textvariable=cambio_var, width=10)
        cambio_spin.pack(pady=5)
        
        # Razón
        ttk.Label(dialog, text="Razón:").pack(pady=5)
        razon_entry = ttk.Entry(dialog, width=50)
        razon_entry.pack(pady=5)
        
        # Botón de guardar
        ttk.Button(
            dialog,
            text="Guardar Cambios",
            command=lambda: self.guardar_modificacion_mmr(
                jugador_id,
                cambio_var.get(),
                razon_entry.get(),
                dialog
            )
        ).pack(pady=20)
    
    def guardar_modificacion_mmr(self, jugador_id: int, cambio: int, razon: str, dialog: tk.Toplevel):
        """Guarda la modificación de MMR"""
        if not razon:
            messagebox.showerror("Error", "Debes indicar una razón para el cambio", parent=dialog)
            return
        
        try:
            # Modificar MMR
            nuevo_mmr = self.gestor_mmr.modificar_mmr_manual(jugador_id, cambio, razon)
            
            messagebox.showinfo("Éxito", f"MMR modificado correctamente. Nuevo MMR: {nuevo_mmr}", parent=dialog)
            dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo modificar el MMR: {str(e)}", parent=dialog)
    
    def restablecer_mmr(self, jugador_id: int):
        """Restablece el MMR de un jugador a 1000"""
        if not jugador_id:
            messagebox.showwarning("Aviso", "Selecciona un jugador")
            return
        
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Confirmar
        confirmacion = messagebox.askyesno(
            "Confirmar Restablecimiento",
            f"¿Estás seguro de restablecer el MMR de {jugador.username} a 1000?"
        )
        
        if not confirmacion:
            return
        
        try:
            # Restablecer MMR
            nuevo_mmr = self.gestor_mmr.restablecer_mmr(jugador_id)
            
            messagebox.showinfo("Éxito", f"MMR restablecido correctamente. Nuevo MMR: {nuevo_mmr}")
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo restablecer el MMR: {str(e)}")
    
    def ver_historial_mmr(self, jugador_id: int):
        """Muestra el historial de MMR de un jugador"""
        if not jugador_id:
            messagebox.showwarning("Aviso", "Selecciona un jugador")
            return
        
        jugador = self.gestor_jugadores.obtener_jugador_por_id(jugador_id)
        if not jugador:
            messagebox.showerror("Error", "Jugador no encontrado")
            return
        
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title(f"Historial de MMR de {jugador.username}")
        dialog.geometry("800x500")
        dialog.transient(self)
        
        # Información actual
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ranking = jugador.rankings
        if ranking:
            ttk.Label(info_frame, text=f"MMR Actual: {ranking.current_mmr}", font=("Helvetica", 12, "bold")).pack(side="left", padx=20)
            ttk.Label(info_frame, text=f"Rango: {ranking.rank_label}", font=("Helvetica", 12)).pack(side="left", padx=20)
        
        # Tabla de historial
        table_frame = ttk.Frame(dialog)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Crear treeview (tabla)
        historial_tree = ttk.Treeview(
            table_frame,
            columns=("fecha", "antes", "despues", "cambio", "razon", "partida"),
            show="headings"
        )
        
        # Configurar columnas
        historial_tree.heading("fecha", text="Fecha")
        historial_tree.heading("antes", text="MMR Anterior")
        historial_tree.heading("despues", text="MMR Nuevo")
        historial_tree.heading("cambio", text="Cambio")
        historial_tree.heading("razon", text="Razón")
        historial_tree.heading("partida", text="Partida")
        
        historial_tree.column("fecha", width=150)
        historial_tree.column("antes", width=80, anchor="center")
        historial_tree.column("despues", width=80, anchor="center")
        historial_tree.column("cambio", width=80, anchor="center")
        historial_tree.column("razon", width=300)
        historial_tree.column("partida", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=historial_tree.yview)
        historial_tree.configure(yscrollcommand=scrollbar.set)
        
        historial_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Cargar datos
        historial = self.gestor_mmr.obtener_historial_mmr(jugador_id)
        
        for h in historial:
            cambio = h.mmr_after - h.mmr_before
            cambio_str = f"+{cambio}" if cambio > 0 else str(cambio)
            
            historial_tree.insert(
                "",
                "end",
                values=(
                    h.timestamp.strftime("%Y-%m-%d %H:%M"),
                    h.mmr_before,
                    h.mmr_after,
                    cambio_str,
                    h.change_reason,
                    h.match_id if h.match_id else "-"
                )
            )
        
        # Gráfico de evolución
        try:
            fechas, mmr = self.gestor_mmr.obtener_grafico_mmr(jugador_id)
            
            if fechas and mmr:
                grafico_frame = ttk.Frame(dialog)
                grafico_frame.pack(fill="x", padx=10, pady=10)
                
                fig, ax = plt.subplots(figsize=(10, 3))
                ax.plot(fechas, mmr, marker='o', linestyle='-', color='blue')
                ax.set_title(f"Evolución de MMR de {jugador.username}")
                ax.set_ylabel('MMR')
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Rotar etiquetas del eje x
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Integrar gráfico en Tkinter
                canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
        except:
            # Si hay algún error con matplotlib, ignorar
            pass
        
        # Botón de cerrar
        ttk.Button(
            dialog,
            text="Cerrar",
            command=dialog.destroy
        ).pack(pady=10)
    
    def mostrar_interfaz_jugador(self):
        """Muestra la interfaz de usuario (jugador)"""
        # Limpiar ventana
        for widget in self.winfo_children():
            widget.destroy()
        
        # Crear frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")
        
        # Crear notebook (pestañas)
        notebook = ttk.Notebook(main_frame)
        
        # Pestañas
        tab_perfil = ttk.Frame(notebook)
        tab_partidas = ttk.Frame(notebook)
        tab_ranking = ttk.Frame(notebook)
        
        notebook.add(tab_perfil, text="Mi Perfil")
        notebook.add(tab_partidas, text="Mis Partidas")
        notebook.add(tab_ranking, text="Ranking")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Barra superior
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(
            top_frame, 
            text=f"Conectado como: {self.current_user.username}",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")
        
        ttk.Button(
            top_frame,
            text="Cerrar Sesión",
            command=self.logout
        ).pack(side="right")
        
        # Llenar pestañas
        self.llenar_tab_perfil_jugador(tab_perfil)
        self.llenar_tab_partidas_jugador(tab_partidas)
        self.llenar_tab_ranking_jugador(tab_ranking)
    
    def llenar_tab_perfil_jugador(self, tab):
        """Llena la pestaña de perfil de jugador"""
        # Obtener datos del jugador
        jugador = self.current_user
        stats = jugador.stats
        ranking = jugador.rankings
        
        # Frame principal
        main_frame = ttk.Frame(tab, padding=20)
        main_frame.pack(expand=True, fill="both")
        
        # Información básica
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        ttk.Label(info_frame, text="Información de Perfil", font=("Helvetica", 16, "bold")).pack(anchor="w")
        
        # Datos básicos
        datos_frame = ttk.Frame(main_frame)
        datos_frame.pack(fill="x", pady=10)
        
        ttk.Label(datos_frame, text="Nombre de usuario:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(datos_frame, text=jugador.username, font=("Helvetica", 11, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(datos_frame, text="Nivel:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(datos_frame, text=str(jugador.level)).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(datos_frame, text="Miembro desde:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(datos_frame, text=jugador.created_at.strftime("%Y-%m-%d")).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(datos_frame, text="Servidor:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(datos_frame, text=f"{jugador.server.name} ({jugador.server.region})" if jugador.server else "N/A").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Estadísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(20, 10))
        
        ttk.Label(stats_frame, text="Estadísticas", font=("Helvetica", 14, "bold")).pack(anchor="w")
        
        if stats:
            stats_data = ttk.Frame(stats_frame)
            stats_data.pack(fill="x", pady=5)
            
            # Primera fila (resumen)
            ttk.Label(stats_data, text="Partidas jugadas:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_played)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
          
            ttk.Label(stats_data, text="Victorias:", anchor="e").grid(row=0, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_won)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_data, text="Derrotas:", anchor="e").grid(row=0, column=4, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_lost)).grid(row=0, column=5, padx=5, pady=5, sticky="w")
            
            # Segunda fila
            ttk.Label(stats_data, text="Ratio de victorias:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_data, text=f"{stats.win_ratio:.2f}").grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_data, text="Racha máxima:", anchor="e").grid(row=1, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.max_win_streak)).grid(row=1, column=3, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_data, text="Timelines creadas:", anchor="e").grid(row=1, column=4, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.total_timelines_created)).grid(row=1, column=5, padx=5, pady=5, sticky="w")
      
        # Ranking
        ranking_frame = ttk.Frame(main_frame)
        ranking_frame.pack(fill="x", pady=(20, 10))

        ttk.Label(ranking_frame, text="Ranking", font=("Helvetica", 14, "bold")).pack(anchor="w")

        if ranking:
            ranking_data = ttk.Frame(ranking_frame)
            ranking_data.pack(fill="x", pady=5)

            ttk.Label(ranking_data, text="MMR:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(ranking_data, text=str(ranking.current_mmr), font=("Helvetica", 12, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")

            ttk.Label(ranking_data, text="Rango:", anchor="e").grid(row=0, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(ranking_data, text=ranking.rank_label, font=("Helvetica", 12, "bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")

            # Intentar mostrar gráfico de evolución de MMR
            try:
                fechas, mmr = self.gestor_mmr.obtener_grafico_mmr(jugador.id)

                if fechas and mmr:
                    grafico_frame = ttk.Frame(ranking_frame)
                    grafico_frame.pack(fill="x", pady=10)

                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(fechas, mmr, marker='o', linestyle='-', color='blue')
                    ax.set_title("Evolución de tu MMR")
                    ax.set_ylabel('MMR')
                    ax.grid(True, linestyle='--', alpha=0.7)

                    # Rotar etiquetas del eje x
                    plt.xticks(rotation=45)
                    plt.tight_layout()

                    # Integrar gráfico en Tkinter
                    canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True)
            except:
                # Si hay algún error con matplotlib, ignorar
                pass
              
        # Botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(30, 10))

        ttk.Button(
            buttons_frame,
            text="Cambiar Contraseña",
            command=self.cambiar_password_dialog
        ).pack(side="left", padx=10)

        ttk.Button(
            buttons_frame,
            text="Ver Historial de MMR",
            command=lambda: self.ver_historial_mmr(jugador.id)
        ).pack(side="left", padx=10)
    
    def cambiar_password_dialog(self):
        """Muestra un diálogo para cambiar la contraseña del usuario actual"""
        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Cambiar Contraseña")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Campos
        ttk.Label(dialog, text="Contraseña Actual:").pack(pady=(20, 5))
        current_pw = ttk.Entry(dialog, width=30, show="*")
        current_pw.pack(pady=5)

        ttk.Label(dialog, text="Nueva Contraseña:").pack(pady=5)
        new_pw = ttk.Entry(dialog, width=30, show="*")
        new_pw.pack(pady=5)

        ttk.Label(dialog, text="Confirmar Nueva Contraseña:").pack(pady=5)
        confirm_pw = ttk.Entry(dialog, width=30, show="*")
        confirm_pw.pack(pady=5)

        # Botón de guardar
        ttk.Button(
            dialog,
            text="Cambiar Contraseña",
            command=lambda: self.cambiar_password(
                current_pw.get(),
                new_pw.get(),
                confirm_pw.get(),
                dialog
            )
        ).pack(pady=20)
    
    def cambiar_password(self, current_pw: str, new_pw: str, confirm_pw: str, dialog: tk.Toplevel):
        """Cambia la contraseña del usuario actual"""
        if not current_pw or not new_pw or not confirm_pw:
            messagebox.showerror("Error", "Todos los campos son obligatorios", parent=dialog)
            return

        if new_pw != confirm_pw:
            messagebox.showerror("Error", "Las nuevas contraseñas no coinciden", parent=dialog)
            return

        # Verificar contraseña actual
        if not verificar_password(current_pw, self.current_user.hashed_password):
            messagebox.showerror("Error", "La contraseña actual es incorrecta", parent=dialog)
            return

        try:
            # Actualizar contraseña
            self.current_user.hashed_password = hash_password(new_pw)
            self.session.commit()

            messagebox.showinfo("Éxito", "Contraseña actualizada correctamente", parent=dialog)
            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo actualizar la contraseña: {str(e)}", parent=dialog)
    
    def llenar_tab_partidas_jugador(self, tab):
        """Llena la pestaña de partidas del jugador"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Botón de actualizar
        ttk.Button(
            control_frame,
            text="Actualizar",
            command=lambda: self.cargar_partidas_jugador(partidas_tree)
        ).pack(side="right", padx=5)

        # Tabla de partidas
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Crear treeview (tabla)
        partidas_tree = ttk.Treeview(
            table_frame,
            columns=("id", "fecha", "oponente", "resultado", "duracion", "movimientos", "timelines"),
            show="headings"
        )

        # Configurar columnas
        partidas_tree.heading("id", text="ID")
        partidas_tree.heading("fecha", text="Fecha")
        partidas_tree.heading("oponente", text="Oponente")
        partidas_tree.heading("resultado", text="Resultado")
        partidas_tree.heading("duracion", text="Duración")
        partidas_tree.heading("movimientos", text="Movimientos")
        partidas_tree.heading("timelines", text="Timelines")

        partidas_tree.column("id", width=50, anchor="center")
        partidas_tree.column("fecha", width=120)
        partidas_tree.column("oponente", width=120)
        partidas_tree.column("resultado", width=80, anchor="center")
        partidas_tree.column("duracion", width=80, anchor="center")
        partidas_tree.column("movimientos", width=80, anchor="center")
        partidas_tree.column("timelines", width=80, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=partidas_tree.yview)
        partidas_tree.configure(yscrollcommand=scrollbar.set)

        partidas_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

        # Menú contextual
        def mostrar_menu_contextual(event):
            item = partidas_tree.identify_row(event.y)
            if item:
                partidas_tree.selection_set(item)
                menu_contextual.post(event.x_root, event.y_root)

        menu_contextual = tk.Menu(partidas_tree, tearoff=0)
        menu_contextual.add_command(label="Ver Detalles", command=lambda: self.ver_detalles_partida(partidas_tree))

        partidas_tree.bind("<Button-3>", mostrar_menu_contextual)

        # Cargar datos iniciales
        self.cargar_partidas_jugador(partidas_tree)
    
    def cargar_partidas_jugador(self, tree):
        """Carga las partidas del jugador actual en el treeview"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)

        # Obtener partidas
        partidas = self.gestor_partidas.listar_partidas_jugador(self.current_user.id)

        for partida in partidas:
            # Determinar oponente y resultado
            oponente = ""
            resultado = ""

            for mp in partida.match_players:
                if mp.player_id != self.current_user.id:
                    oponente = self.gestor_jugadores.obtener_jugador_por_id(mp.player_id).username

                if mp.player_id == self.current_user.id:
                    if partida.winner_id is None:
                        resultado = "Empate"
                    elif partida.winner_id == self.current_user.id:
                        resultado = "Victoria"
                    else:
                        resultado = "Derrota"

            # Calcular duración
            duracion = formatear_duracion(partida.duration_seconds) if partida.finished_at else "En progreso"

            tree.insert(
                "",
                "end",
                values=(
                    partida.id,
                    partida.created_at.strftime("%Y-%m-%d %H:%M"),
                    oponente,
                    resultado,
                    duracion,
                    partida.total_moves,
                    partida.total_timelines_created
                )
            )
    
    def llenar_tab_ranking_jugador(self, tab):
        """Llena la pestaña de ranking del jugador"""
        # Frame superior con controles
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Selector de servidor
        ttk.Label(control_frame, text="Servidor:").pack(side="left", padx=5)

        servers = self.gestor_servidores.listar_servidores()
        server_names = ["Global"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]

        server_var = tk.StringVar(value=server_names[0])

        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.actualizar_ranking_jugador(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        )
        server_menu.pack(side="left", padx=5)

        # Botón de actualizar
        ttk.Button(
            control_frame,
            text="Actualizar",
            command=lambda: self.actualizar_ranking_jugador(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        ).pack(side="right", padx=5)

        # Tabla de ranking
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Crear treeview (tabla)
        ranking_tree = ttk.Treeview(
            table_frame,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )

        # Configurar columnas
        ranking_tree.heading("pos", text="#")
        ranking_tree.heading("id", text="ID")
        ranking_tree.heading("username", text="Usuario")
        ranking_tree.heading("mmr", text="MMR")
        ranking_tree.heading("rank", text="Rango")
        ranking_tree.heading("win_ratio", text="Win Ratio")

        ranking_tree.column("pos", width=50, anchor="center")
        ranking_tree.column("id", width=50, anchor="center")
        ranking_tree.column("username", width=150)
        ranking_tree.column("mmr", width=70, anchor="center")
        ranking_tree.column("rank", width=100)
        ranking_tree.column("win_ratio", width=70, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=ranking_tree.yview)
        ranking_tree.configure(yscrollcommand=scrollbar.set)

        ranking_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

        # Cargar datos iniciales (ranking global)
        self.actualizar_ranking_jugador(ranking_tree)
    
    def actualizar_ranking_jugador(self, tree, server_id: Optional[int] = None):
        """Actualiza la tabla de ranking con los datos más recientes"""
        # Limpiar tabla
        for item in tree.get_children():
            tree.delete(item)

        # Obtener ranking
        if server_id:
            ranking = self.gestor_ranking.obtener_ranking_por_servidor(server_id)
        else:
            ranking = self.gestor_ranking.obtener_ranking_global()

        # Resaltar al jugador actual
        current_user_id = self.current_user.id

        # Insertar datos en la tabla
        for jugador in ranking:
            valores = (
                jugador["position"],
                jugador["player_id"],
                jugador["username"],
                jugador["mmr"],
                jugador["rank_label"],
                f"{jugador['win_ratio']:.2f}"
            )

            item_id = tree.insert("", "end", values=valores)

            # Resaltar al jugador actual
            if jugador["player_id"] == current_user_id:
                tree.item(item_id, tags=("current_user",))

        # Configurar estilo para el jugador actual
        tree.tag_configure("current_user", background=COLORS["accent"], foreground="white")


# =============================================================================
# 5. FUNCIONES DE UTILIDAD
# =============================================================================

def hash_password(password: str) -> str:
    """Hashea una contraseña usando SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verificar_password(password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña coincide con su hash"""
    return hash_password(password) == hashed_password


def formatear_duracion(segundos: int) -> str:
    """Formatea una duración en segundos a un formato legible"""
    minutos, segundos = divmod(segundos, 60)
    horas, minutos = divmod(minutos, 60)
    
    if horas > 0:
        return f"{horas}h {minutos}m {segundos}s"
    elif minutos > 0:
        return f"{minutos}m {segundos}s"
    else:
        return f"{segundos}s"


# =============================================================================
# 6. PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()