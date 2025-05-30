import os
import re
import json
import random
import hashlib
import datetime
import copy
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from tkinter.font import Font
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, desc, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from typing import List, Dict, Optional, Union, Tuple
from accessibility_manager import make_accessible, add_accessibility_to_app, add_game_accessibility
from analytics_module import add_analytics_to_app

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
PASSWORD_ADMIN = os.getenv("PASSWORD_ADMIN")
USER_ADMIN = os.getenv("USER_ADMIN")

# Create connection string
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize database engine and declarative base
engine = create_engine(DATABASE_URI, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

# Colors for the interface
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

# Ranks in the system
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
# DATABASE MODELS
# =============================================================================

class Server(Base):
    """Model for game servers"""
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    region = Column(String(30), nullable=False)
    
    # Relationships
    players = relationship("Player", back_populates="server")
    
    def __repr__(self):
        return f"<Server(name='{self.name}', region='{self.region}')>"


class Player(Base):
    """Model for players"""
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    last_login = Column(DateTime, nullable=True)
    server_id = Column(Integer, ForeignKey("servers.id"))
    
    # Relationships
    server = relationship("Server", back_populates="players")
    stats = relationship("PlayerStats", uselist=False, back_populates="player", cascade="all, delete-orphan")
    rankings = relationship("PlayerRanking", uselist=False, back_populates="player", cascade="all, delete-orphan")
    mmr_history = relationship("MMRHistory", back_populates="player", cascade="all, delete-orphan")
    match_players = relationship("MatchPlayer", back_populates="player", cascade="all, delete-orphan")
    moves = relationship("Move", back_populates="player")
    
    def __repr__(self):
        return f"<Player(username='{self.username}', level={self.level})>"


class PlayerStats(Base):
    """Model for player statistics"""
    __tablename__ = "player_stats"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    games_drawn = Column(Integer, default=0)
    average_move_time = Column(Float, default=0.0)
    max_win_streak = Column(Integer, default=0)
    
    # Relationships
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
    """Model for player rankings"""
    __tablename__ = "player_rankings"
    
    player_id = Column(Integer, ForeignKey("players.id"), primary_key=True)
    current_mmr = Column(Integer, default=1000)
    rank_label = Column(String(20), default="Sin Clasificar")
    win_ratio = Column(Float, default=0.0)
    max_win_streak = Column(Integer, default=0)
    average_victory_speed = Column(Float, default=0.0)  # In seconds
    
    # Relationships
    player = relationship("Player", back_populates="rankings")
    
    def __repr__(self):
        return f"<PlayerRanking(player_id={self.player_id}, mmr={self.current_mmr}, rank='{self.rank_label}')>"


class Match(Base):
    """Model for matches"""
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    finished_at = Column(DateTime, nullable=True)
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    duration_seconds = Column(Integer, default=0)
    total_moves = Column(Integer, default=0)
    final_state_description = Column(Text, nullable=True)
    
    # Relationships
    winner = relationship("Player", foreign_keys=[winner_id])
    match_players = relationship("MatchPlayer", back_populates="match", cascade="all, delete-orphan")
    moves = relationship("Move", back_populates="match", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Match(id={self.id}, created_at='{self.created_at}')>"
    
    @property
    def status(self):
        return "Finalizada" if self.finished_at else "En progreso"


class MatchPlayer(Base):
    """Model for players in matches (M:M relationship with data)"""
    __tablename__ = "match_players"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    player_order = Column(Integer)  # 1 or 2 (X or O)
    is_winner = Column(Boolean, default=False)
    average_move_time = Column(Float, default=0.0)
    
    # Relationships
    match = relationship("Match", back_populates="match_players")
    player = relationship("Player", back_populates="match_players")
    
    def __repr__(self):
        return f"<MatchPlayer(match_id={self.match_id}, player_id={self.player_id}, order={self.player_order})>"


class Move(Base):
    """Model for moves in matches"""
    __tablename__ = "moves"
    
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("matches.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    sub_board_index = Column(Integer)  # 0-8 (sub-board index)
    cell_index = Column(Integer)  # 0-8 (cell index within sub-board)
    move_number = Column(Integer)  # Global number in the match
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    time_taken_seconds = Column(Float, default=0.0)
    
    # Relationships
    match = relationship("Match", back_populates="moves")
    player = relationship("Player", back_populates="moves")
    
    def __repr__(self):
        return f"<Move(match_id={self.match_id}, player_id={self.player_id}, sub_board={self.sub_board_index}, cell={self.cell_index})>"


class MMRHistory(Base):
    """Model for MMR history"""
    __tablename__ = "mmr_history"
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    mmr_before = Column(Integer)
    mmr_after = Column(Integer)
    change_reason = Column(String(200))
    
    # Relationships
    player = relationship("Player", back_populates="mmr_history")
    match = relationship("Match")
    
    def __repr__(self):
        change = self.mmr_after - self.mmr_before
        sign = "+" if change >= 0 else ""
        return f"<MMRHistory(player_id={self.player_id}, change={sign}{change}, reason='{self.change_reason}')>"


# =============================================================================
# BUSINESS LOGIC CLASSES
# =============================================================================

class DataRepository:
    """Base repository class for database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def commit(self):
        """Commit changes to the database"""
        self.session.commit()
    
    def add(self, entity):
        """Add an entity to the database"""
        self.session.add(entity)
        return entity
    
    def delete(self, entity):
        """Delete an entity from the database"""
        self.session.delete(entity)
        return True
    
    def flush(self):
        """Flush changes to the database"""
        self.session.flush()


class PlayerRepository(DataRepository):
    """Repository for player operations"""
    
    def get_by_id(self, player_id: int) -> Optional[Player]:
        """Get a player by ID"""
        return self.session.get(Player, player_id)
    
    def get_by_username(self, username: str) -> Optional[Player]:
        """Get a player by username"""
        return self.session.query(Player).filter(Player.username == username).first()
    
    def search_by_username(self, username: str) -> List[Player]:
        """Search players by username (partial match)"""
        return self.session.query(Player).filter(Player.username.like(f"%{username}%")).all()
    
    def list_all(self, server_id=None, page=1, per_page=20, sort_by="username", sort_dir="asc"):
        query = self.session.query(Player)
        
        if server_id:
            query = query.filter(Player.server_id == server_id)
        
        # Mapeo de columnas a campos de la base de datos
        column_mapping = {
            "username": Player.username,
            "level": Player.level,
            "created_at": Player.created_at,
            "mmr": PlayerRanking.current_mmr,
            "win_ratio": PlayerRanking.win_ratio
        }
        
        # Verificar si necesitamos hacer join con PlayerRanking
        if sort_by in ["mmr", "win_ratio"]:
            query = query.join(PlayerRanking)
        
        sort_column = column_mapping.get(sort_by, Player.username)
        
        # Aplicar dirección de ordenamiento
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        players = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return players, total
    
    def create(self, username: str, password: str, server_id: int) -> Optional[Player]:
        """Create a new player"""
        # Check if username is unique
        if self.get_by_username(username):
            return None
        
        # Create player
        hashed_password = hash_password(password)
        new_player = Player(
            username=username,
            hashed_password=hashed_password,
            server_id=server_id
        )
        self.add(new_player)
        self.flush()  # To get the ID
        
        # Create initial stats and ranking
        stats = PlayerStats(player_id=new_player.id)
        ranking = PlayerRanking(player_id=new_player.id)
        
        self.add(stats)
        self.add(ranking)
        self.commit()
        
        return new_player
    
    def update(self, player_id: int, data: Dict) -> bool:
        """Update player data"""
        player = self.get_by_id(player_id)
        if not player:
            return False
        
        # Update fields
        if "username" in data and data["username"] != player.username:
            # Check if new username is unique
            if self.get_by_username(data["username"]):
                return False
            player.username = data["username"]
        
        if "password" in data and data["password"]:
            player.hashed_password = hash_password(data["password"])
        
        if "server_id" in data:
            player.server_id = data["server_id"]
        
        if "level" in data:
            player.level = data["level"]
        
        self.commit()
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[Player]:
        """Authenticate a player by username and password"""
        player = self.get_by_username(username)
        if not player:
            return None
        
        if verify_password(password, player.hashed_password):
            # Update last login
            player.last_login = datetime.datetime.now(datetime.timezone.utc)
            self.commit()
            return player
        
        return None


class ServerRepository(DataRepository):
    """Repository for server operations"""
    
    def get_by_id(self, server_id: int) -> Optional[Server]:
        """Get a server by ID"""
        return self.session.get(Server, server_id)
    
    def list_all(self) -> List[Server]:
        """List all available servers"""
        return self.session.query(Server).all()
    
    def create(self, name: str, region: str) -> Server:
        """Create a new server"""
        server = Server(name=name, region=region)
        self.add(server)
        self.commit()
        return server


class MatchRepository(DataRepository):
    """Repository for match operations"""
    
    def get_by_id(self, match_id: int) -> Optional[Match]:
        """Get a match by ID"""
        return self.session.get(Match, match_id)
    
    def list_all(self, page: int = 1, per_page: int = 20, sort_by: str = "created_at", sort_dir: str = "desc") -> Tuple[List[Match], int]:
        # Mapeo de columnas a campos de la base de datos
        column_mapping = {
            "created_at": Match.created_at,
            "total_moves": Match.total_moves,
            "duration_seconds": Match.duration_seconds,
            "status": Match.finished_at  # Para ordenar por estado (los nulls van primero)
        }

        # Obtener la columna de ordenamiento
        sort_column = column_mapping.get(sort_by, Match.created_at)

        # Construir la consulta base
        query = self.session.query(Match)

        # Manejar orden especial por estado
        if sort_by == "status":
            # Los partidos no finalizados (finished_at es NULL) van primero
            if sort_dir == "asc":
                query = query.order_by(Match.finished_at.is_(None).desc(), Match.finished_at.asc())
            else:
                query = query.order_by(Match.finished_at.is_(None).desc(), Match.finished_at.desc())
        else:
            # Ordenamiento normal para otras columnas
            if sort_dir.lower() == "asc":
                query = query.order_by(sort_column.asc())
            else:
                query = query.order_by(sort_column.desc())

        # Contar el total para la paginación
        total = query.count()

        # Aplicar paginación
        matches = query.offset((page - 1) * per_page).limit(per_page).all()

        return matches, total
    
    def list_by_player(self, player_id: int, page: int = 1, per_page: int = 20, sort_by: str = "created_at", sort_dir: str = "desc") -> Tuple[List[Match], int]:
        """List matches for a player with pagination and sorting"""
        # Determine sort column
        if sort_by == "created_at":
            sort_col = Match.created_at
        elif sort_by == "total_moves":
            sort_col = Match.total_moves
        elif sort_by == "duration_seconds":
            sort_col = Match.duration_seconds
        else:
            sort_col = Match.created_at  # Default
        
        # Determine sort direction
        if sort_dir.lower() == "asc":
            query = self.session.query(Match).join(MatchPlayer).filter(
                MatchPlayer.player_id == player_id
            ).order_by(sort_col)
        else:
            query = self.session.query(Match).join(MatchPlayer).filter(
                MatchPlayer.player_id == player_id
            ).order_by(desc(sort_col))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        matches = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return matches, total
    
    def create(self, player1_id: int, player2_id: int) -> Match:
        """Create a new match between two players"""
        match = Match()
        self.add(match)
        self.flush()  # To get the ID
        
        # Assign players to the match
        mp1 = MatchPlayer(match_id=match.id, player_id=player1_id, player_order=1)
        mp2 = MatchPlayer(match_id=match.id, player_id=player2_id, player_order=2)
        
        self.add(mp1)
        self.add(mp2)
        self.commit()
        
        return match
    
    def register_move(self, match_id: int, player_id: int, sub_board_index: int, 
                     cell_index: int, time_taken: float) -> Move:
        """Register a new move in a match"""
        match = self.get_by_id(match_id)
        if not match:
            raise ValueError("Match not found")
        
        # Check if player belongs to the match
        match_player = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id,
            MatchPlayer.player_id == player_id
        ).first()
        
        if not match_player:
            raise ValueError("Player does not belong to this match")
        
        # Get next move number
        next_move_number = self.session.query(func.max(Move.move_number)).filter(
            Move.match_id == match_id
        ).scalar() or 0
        next_move_number += 1
        
        # Create the move
        move = Move(
            match_id=match_id,
            player_id=player_id,
            sub_board_index=sub_board_index,
            cell_index=cell_index,
            move_number=next_move_number,
            time_taken_seconds=time_taken
        )
        
        self.add(move)
        
        # Update match statistics
        match.total_moves += 1
        
        # Update player's average move time in the match
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
        
        self.commit()
        return move
    
    def finish_match(self, match_id: int, winner_id: Optional[int] = None) -> Match:
        """Finish a match and update statistics"""
        match = self.get_by_id(match_id)
        if not match:
            raise ValueError("Match not found")
        
        # If already finished, do nothing
        if match.finished_at:
            return match
        
        now = datetime.datetime.now()
        match.finished_at = now
        match.winner_id = winner_id
        
        # Calculate duration in seconds
        delta = now - match.created_at
        match.duration_seconds = int(delta.total_seconds())
        
        # Update match_players
        for mp in match.match_players:
            # Mark winner
            if winner_id and mp.player_id == winner_id:
                mp.is_winner = True
            
            # Update player statistics
            stats = self.session.query(PlayerStats).filter(
                PlayerStats.player_id == mp.player_id
            ).first()
            
            if stats:
                stats.games_played += 1
                
                if winner_id is None:
                    # Draw
                    stats.games_drawn += 1
                elif mp.player_id == winner_id:
                    # Victory
                    stats.games_won += 1
        
        self.commit()
        
        # Update MMR
        if winner_id is not None or len(match.match_players) == 2:
            mmr_service = MMRService(self.session)
            mmr_service.update_match_mmr(match_id)
        
        return match
    
    def generate_simulated_match(self, player1_id: int, player2_id: int, moves: int = 20, 
                               winner_id: Optional[int] = None) -> Match:
        """Generate a simulated match with random moves"""
        # Create the match
        match = self.create(player1_id, player2_id)
        
        # Generate moves
        current_player_id = player1_id
        
        for i in range(moves):
            # Generate random move
            sub_board = random.randint(0, 8)
            cell = random.randint(0, 8)
            time_taken = random.uniform(1.0, 10.0)
            
            self.register_move(
                match.id, current_player_id, sub_board, cell, time_taken
            )
            
            # Alternate player
            current_player_id = player2_id if current_player_id == player1_id else player1_id
        
        # Finish the match
        self.finish_match(match.id, winner_id)
        
        return match


class RankingService:
    """Service for managing player rankings"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def calculate_rank_label(self, mmr: int) -> str:
        """Calculate rank label based on MMR"""
        rank_label = RANKS[0]  # Default value: Unranked
        
        for threshold, label in sorted(RANKS.items()):
            if mmr >= threshold:
                rank_label = label
        
        return rank_label
    
    def update_rank_label(self, player_id: int) -> str:
        """Update a player's rank label based on current MMR"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        if not ranking:
            return RANKS[0]
        
        rank_label = self.calculate_rank_label(ranking.current_mmr)
        ranking.rank_label = rank_label
        self.session.commit()
        
        return rank_label
    
    def update_ranking_stats(self, player_id: int) -> None:
        """Update ranking statistics based on player stats"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        stats = self.session.query(PlayerStats).filter(
            PlayerStats.player_id == player_id
        ).first()
        
        if not ranking or not stats:
            return
        
        # Update win ratio
        if stats.games_played > 0:
            ranking.win_ratio = stats.win_ratio
        
        # Update max win streak
        ranking.max_win_streak = stats.max_win_streak
        
        # Calculate average victory speed
        victories = self.session.query(Match).filter(
            Match.winner_id == player_id
        ).all()
        
        if victories:
            total_time = sum(v.duration_seconds for v in victories)
            ranking.average_victory_speed = total_time / len(victories)
        
        self.session.commit()
    
    def get_global_ranking(self, page: int = 1, per_page: int = 20, sort_by: str = "mmr", sort_dir: str = "desc") -> Tuple[List[Dict], int]:
        """Get global player ranking with pagination and sorting"""
        # Join Player and PlayerRanking
        query = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        )
        
        # Determine sort column
        if sort_by == "mmr":
            sort_col = PlayerRanking.current_mmr
        elif sort_by == "username":
            sort_col = Player.username
        elif sort_by == "win_ratio":
            sort_col = PlayerRanking.win_ratio
        else:
            sort_col = PlayerRanking.current_mmr  # Default
        
        # Determine sort direction
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_col)
        else:
            query = query.order_by(desc(sort_col))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        
        ranking = []
        for i, (player, pr) in enumerate(results, (page - 1) * per_page + 1):
            ranking.append({
                "position": i,
                "player_id": player.id,
                "username": player.username,
                "mmr": pr.current_mmr,
                "rank_label": pr.rank_label,
                "win_ratio": pr.win_ratio
            })
        
        return ranking, total
    
    def get_server_ranking(self, server_id: int, page: int = 1, per_page: int = 20, sort_by: str = "mmr", sort_dir: str = "desc") -> Tuple[List[Dict], int]:
        """Get server player ranking with pagination and sorting"""
        # Join Player and PlayerRanking
        query = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        ).filter(
            Player.server_id == server_id
        )
        
        # Determine sort column
        if sort_by == "mmr":
            sort_col = PlayerRanking.current_mmr
        elif sort_by == "username":
            sort_col = Player.username
        elif sort_by == "win_ratio":
            sort_col = PlayerRanking.win_ratio
        else:
            sort_col = PlayerRanking.current_mmr  # Default
        
        # Determine sort direction
        if sort_dir.lower() == "asc":
            query = query.order_by(sort_col)
        else:
            query = query.order_by(desc(sort_col))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        results = query.offset((page - 1) * per_page).limit(per_page).all()
        
        ranking = []
        for i, (player, pr) in enumerate(results, (page - 1) * per_page + 1):
            ranking.append({
                "position": i,
                "player_id": player.id,
                "username": player.username,
                "mmr": pr.current_mmr,
                "rank_label": pr.rank_label,
                "win_ratio": pr.win_ratio
            })
        
        return ranking, total


class MMRService:
    """Service for managing player MMR (Matchmaking Rating)"""
    
    def __init__(self, session: Session):
        self.session = session
        self.ranking_service = RankingService(session)
    
    def update_match_mmr(self, match_id: int) -> None:
        """Update players' MMR after a match"""
        match = self.session.get(Match, match_id)
        if not match or not match.finished_at:
            raise ValueError("Match does not exist or has not finished")
        
        match_players = self.session.query(MatchPlayer).filter(
            MatchPlayer.match_id == match_id
        ).all()
        
        if len(match_players) != 2:
            raise ValueError("This function only works with 2-player matches")
        
        # Get rankings for both players
        p1_id = match_players[0].player_id
        p2_id = match_players[1].player_id
        
        p1_ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == p1_id
        ).first()
        
        p2_ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == p2_id
        ).first()
        
        if not p1_ranking or not p2_ranking:
            raise ValueError("One or both players do not have a ranking")
        
        # Calculate MMR change based on simplified ELO algorithm
        # K is the adjustment factor (how much MMR can change)
        K = 32
        
        # Calculate expected probabilities
        elo_diff = p2_ranking.current_mmr - p1_ranking.current_mmr
        expected_p1 = 1 / (1 + 10 ** (elo_diff / 400))
        expected_p2 = 1 - expected_p1
        
        # Determine actual result (1 = win, 0.5 = draw, 0 = loss)
        if match.winner_id is None:
            # Draw
            actual_p1 = 0.5
            actual_p2 = 0.5
            reason = "Empate"
        elif match.winner_id == p1_id:
            # P1 wins
            actual_p1 = 1
            actual_p2 = 0
            reason = "Victoria"
        else:
            # P2 wins
            actual_p1 = 0
            actual_p2 = 1
            reason = "Victoria"
        
        # Calculate MMR change
        mmr_change_p1 = round(K * (actual_p1 - expected_p1))
        mmr_change_p2 = round(K * (actual_p2 - expected_p2))
        
        # Save previous values
        p1_mmr_before = p1_ranking.current_mmr
        p2_mmr_before = p2_ranking.current_mmr
        
        # Update MMR
        p1_ranking.current_mmr += mmr_change_p1
        p2_ranking.current_mmr += mmr_change_p2
        
        # Ensure MMR is not negative
        p1_ranking.current_mmr = max(0, p1_ranking.current_mmr)
        p2_ranking.current_mmr = max(0, p2_ranking.current_mmr)
        
        # Update rank labels
        p1_ranking.rank_label = self.ranking_service.calculate_rank_label(p1_ranking.current_mmr)
        p2_ranking.rank_label = self.ranking_service.calculate_rank_label(p2_ranking.current_mmr)
        
        # Record MMR history
        p1_reason = reason
        p2_reason = reason
        
        if reason == "Victoria":
            if actual_p1 == 1:  # P1 ganó
                p2_reason = "Derrota"
            else:  # P2 ganó
                p1_reason = "Derrota"
        
        mmr_history_p1 = MMRHistory(
            player_id=p1_id,
            match_id=match_id,
            mmr_before=p1_mmr_before,
            mmr_after=p1_ranking.current_mmr,
            change_reason=f"{p1_reason} contra {self.session.get(Player, p2_id).username}"
        )
        
        mmr_history_p2 = MMRHistory(
            player_id=p2_id,
            match_id=match_id,
            mmr_before=p2_mmr_before,
            mmr_after=p2_ranking.current_mmr,
            change_reason=f"{p2_reason} contra {self.session.get(Player, p1_id).username}"
        )
        
        self.session.add(mmr_history_p1)
        self.session.add(mmr_history_p2)
        
        # Update win ratio in rankings
        self.ranking_service.update_ranking_stats(p1_id)
        self.ranking_service.update_ranking_stats(p2_id)
        
        self.session.commit()
        
        # Print MMR changes for debugging
        print(f"MMR Changes: Player 1 ({p1_mmr_before} → {p1_ranking.current_mmr}, {mmr_change_p1:+}), " +
          f"Player 2 ({p2_mmr_before} → {p2_ranking.current_mmr}, {mmr_change_p2:+})")
    
    def modify_mmr_manual(self, player_id: int, change: int, reason: str) -> int:
        """Manually modify a player's MMR"""
        ranking = self.session.query(PlayerRanking).filter(
            PlayerRanking.player_id == player_id
        ).first()
        
        if not ranking:
            raise ValueError("Player does not have a ranking")
        
        # Save previous value
        mmr_before = ranking.current_mmr
        
        # Update MMR
        ranking.current_mmr += change
        
        # Ensure MMR is not negative
        ranking.current_mmr = max(0, ranking.current_mmr)
        
        # Update rank label
        ranking.rank_label = self.ranking_service.calculate_rank_label(ranking.current_mmr)
        
        # Record history
        mmr_history = MMRHistory(
            player_id=player_id,
            mmr_before=mmr_before,
            mmr_after=ranking.current_mmr,
            change_reason=f"Manual adjustment: {reason}"
        )
        
        self.session.add(mmr_history)
        self.session.commit()
        
        return ranking.current_mmr
    
    def reset_mmr(self, player_id: int) -> int:
        """Reset a player's MMR to the default value (1000)"""
        return self.modify_mmr_manual(
            player_id, 
            1000 - self.session.query(PlayerRanking).filter(
                PlayerRanking.player_id == player_id
            ).first().current_mmr,
            "MMR Reset"
        )
    
    def get_mmr_history(self, player_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[MMRHistory], int]:
        """Get MMR change history for a player with pagination"""
        query = self.session.query(MMRHistory).filter(
            MMRHistory.player_id == player_id
        ).order_by(desc(MMRHistory.timestamp))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        history = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return history, total
    
    def get_mmr_graph_data(self, player_id: int, limit: int = 20) -> Tuple[List[datetime.datetime], List[int]]:
        """Get data for graphing a player's MMR evolution"""
        history, _ = self.get_mmr_history(player_id, per_page=limit)
        history.reverse()  # Sort chronologically
        
        dates = [h.timestamp for h in history]
        mmr = [h.mmr_after for h in history]
        
        return dates, mmr


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify if a password matches its hash"""
    return hash_password(password) == hashed_password


def format_duration(seconds: int) -> str:
    """Format a duration in seconds to a readable format"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


# Custom validation functions
def validate_integer(value):
    """Validate if a value is a valid integer"""
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_float(value):
    """Validate if a value is a valid float"""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_required(value):
    """Validate if a value is not empty"""
    return value is not None and str(value).strip() != ""


# Custom widgets for validation
class ValidatedSpinbox(ttk.Spinbox):
    """A spinbox that only accepts numeric values"""
    
    def __init__(self, *args, **kwargs):
        self.var = kwargs.get('textvariable') or tk.StringVar()
        kwargs['textvariable'] = self.var
        
        super().__init__(*args, **kwargs)
        
        # Register validation command
        vcmd = (self.register(self._validate), '%P')
        self.configure(validate='key', validatecommand=vcmd)
        
        # Set default value if not provided
        if not self.var.get():
            self.var.set(kwargs.get('from_', 0))
    
    def _validate(self, value):
        """Validate the input value"""
        # Allow empty string or valid number
        if value == "":
            return True
        
        # Check if it's a valid number
        try:
            float(value)
            return True
        except ValueError:
            return False


class ValidatedEntry(ttk.Entry):
    """An entry widget with validation"""
    
    def __init__(self, *args, validate_func=None, error_msg=None, **kwargs):
        self.var = kwargs.get('textvariable') or tk.StringVar()
        kwargs['textvariable'] = self.var
        
        self.validate_func = validate_func
        self.error_msg = error_msg or "Invalid input"
        
        super().__init__(*args, **kwargs)
        
        # Register validation command if provided
        if validate_func:
            vcmd = (self.register(self._validate), '%P')
            self.configure(validate='focusout', validatecommand=vcmd)
            
            # Add invalidcommand to show error message
            self.configure(invalidcommand=(self.register(self._show_error), '%P'))
    
    def _validate(self, value):
        """Validate the input value"""
        if self.validate_func:
            return self.validate_func(value)
        return True
    
    def _show_error(self, value):
        """Show error message for invalid input"""
        messagebox.showerror("Validation Error", self.error_msg)
        self.focus_set()
        return False

class SortManager:
    def __init__(self):
        self.current_sort_column = None
        self.current_sort_direction = "asc"  # or "desc"
    
    def toggle_sort(self, column):
        if column == self.current_sort_column:
            # Si es la misma columna, alternamos la dirección
            self.current_sort_direction = "desc" if self.current_sort_direction == "asc" else "asc"
        else:
            # Nueva columna, empezamos con ascendente
            self.current_sort_column = column
            self.current_sort_direction = "asc"
        return self.current_sort_direction
    
    def get_sort_icon(self, column):
        if column == self.current_sort_column:
            return "↑" if self.current_sort_direction == "asc" else "↓"
        return ""
# =============================================================================
# GAME
# =============================================================================

class UltimateTicTacToe:
    def __init__(self, root, session=None, player1_id=None, player2_id=None):
        self.root = root
        self.root.title("Triqui de Triquis")
        self.root.resizable(False, False)
        
        # Conexión a la base de datos
        self.session = session
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.match_id = None
        self.match_created = False
        
        # Colores
        self.bg_color = "#f0f0f0"
        self.grid_color = "#000000"
        self.player_X_color = "#3498db"  # Azul
        self.player_O_color = "#e74c3c"  # Rojo
        
        # Variables para el tiempo
        self.move_start_time = time.time()
        self.player_X_times = []
        self.player_O_times = []
        
        # Estado del juego
        self.current_player = "X"
        self.next_board = None  # Puede ser None al principio (cualquier tablero)
        self.game_boards = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.board_winners = [[None for _ in range(3)] for _ in range(3)]
        self.game_winner = None
        
        # Crear marcos para los tableros
        self.frames = [[None for _ in range(3)] for _ in range(3)]
        self.buttons = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        
        # Crear el tablero principal
        self.main_frame = tk.Frame(root, bg=self.grid_color, padx=5, pady=5)
        self.main_frame.pack(padx=10, pady=10)
        
        # Información del juego
        self.info_frame = tk.Frame(root)
        self.info_frame.pack(pady=5)
        
        self.player_label = tk.Label(self.info_frame, text=f"Turno del Jugador: {self.current_player}", font=("Arial", 12))
        self.player_label.grid(row=0, column=0, padx=10)
        
        self.next_board_label = tk.Label(self.info_frame, text="Tablero activo: Cualquiera", font=("Arial", 12))
        self.next_board_label.grid(row=0, column=1, padx=10)
        
        self.time_label = tk.Label(self.info_frame, text="Tiempo: 0s", font=("Arial", 12))
        self.time_label.grid(row=0, column=2, padx=10)
        
        self.restart_button = tk.Button(self.info_frame, text="Reiniciar Juego", command=self.restart_game)
        self.restart_button.grid(row=0, column=3, padx=10)
        
        self.tutorial_button = tk.Button(
                self.info_frame,
                text="❓ Tutorial",
                bg="#f39c12",
                fg="white",
                font=("Arial", 10, "bold"),
                command=self.show_tutorial,
                relief="flat",
                padx=15,
                pady=5,
                cursor="hand2"
            )
        self.tutorial_button.grid(row=0, column=4, padx=10)

        
        
        # Actualizar el contador de tiempo
        self.update_time()
        
        # Crear los tableros
        self.create_boards()
        
        self.accessibility_manager = add_game_accessibility(self.root, self)
        
        self.create_position_indicator()
        
        # Crear partida en la base de datos si hay jugadores
        if self.session and self.player1_id and self.player2_id:
            self.create_match_in_db()
    
    
    def show_tutorial(self):
        """Mostrar un tutorial mejorado del juego"""
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("🎮 Tutorial - Ultimate Tic Tac Toe")
        tutorial_window.geometry("700x550")
        tutorial_window.transient(self.root)
        tutorial_window.grab_set()
        tutorial_window.configure(bg="#f8f9fa")
        tutorial_window.resizable(False, False)

        # Header con estilo visual
        header_frame = tk.Frame(tutorial_window, bg="#3498db", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame, 
            text="🎮 Ultimate Tic Tac Toe", 
            font=("Helvetica", 20, "bold"),
            bg="#3498db", 
            fg="white"
        )
        title.pack(pady=15)

        subtitle = tk.Label(
            header_frame,
            text="Guía Rápida de Juego",
            font=("Helvetica", 12),
            bg="#3498db",
            fg="#ecf0f1"
        )
        subtitle.pack()

        # Contenido principal
        content_frame = tk.Frame(tutorial_window, bg="#f8f9fa")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)

        # Texto del tutorial con mejor formato
        tutorial_sections = [
            ("🎯 Objetivo Principal", 
             "Gana 3 tableros pequeños en línea (horizontal, vertical o diagonal) para ganar la partida global. Cada tablero pequeño es un triqui tradicional de 3x3."),

            ("🎮 Mecánicas de Juego", 
             "• Haz clic en una celda del tablero resaltado (azul para X, rojo para O)\n• Tu jugada determina en qué tablero debe jugar tu oponente\n• El tablero destino corresponde a la posición de tu celda (1-9)"),

            ("🏆 Ganar un Tablero", 
             "Para conquistar un tablero pequeño, haz una línea de 3 símbolos iguales:\n• Horizontal: misma fila\n• Vertical: misma columna\n• Diagonal: esquina a esquina"),

            ("🔄 Tableros Bloqueados", 
             "Si envías al oponente a un tablero ya ganado o empatado:\n• Puede elegir jugar en cualquier tablero disponible\n• Aprovecha esta situación estratégicamente"),

            ("💡 Estrategias Avanzadas", 
             "• Controla el centro: da más opciones de movimiento\n• Piensa globalmente: cada jugada afecta dos niveles\n• Fuerza al oponente a tableros desfavorables\n• Bloquea sus líneas ganadoras tanto local como globalmente"),

            ("⚡ Tips de Maestro", 
             "• Observa el tiempo: decisiones rápidas pero inteligentes\n• Usa tableros bloqueados para recuperar control\n• Prioriza tableros centrales y esquinas\n• ¡Practica para desarrollar visión estratégica!")
        ]

        # Crear un frame con scrollbar para el contenido
        canvas = tk.Canvas(content_frame, bg="#f8f9fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f8f9fa")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Añadir secciones al frame scrollable
        for i, (section_title, content) in enumerate(tutorial_sections):
            # Frame para cada sección con sombra
            section_frame = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
            section_frame.pack(fill="x", pady=8, padx=5)

            # Barra de color lateral
            color_bar = tk.Frame(section_frame, bg="#3498db", width=4)
            color_bar.pack(side="left", fill="y")

            # Contenido de la sección
            content_container = tk.Frame(section_frame, bg="white")
            content_container.pack(side="left", fill="both", expand=True)

            # Título de la sección
            title_label = tk.Label(
                content_container,
                text=section_title,
                font=("Helvetica", 14, "bold"),
                bg="white",
                fg="#2c3e50",
                anchor="w"
            )
            title_label.pack(fill="x", padx=15, pady=(15, 8))

            # Contenido de la sección
            content_label = tk.Label(
                content_container,
                text=content,
                font=("Helvetica", 11),
                bg="white",
                fg="#34495e",
                anchor="w",
                justify="left",
                wraplength=580
            )
            content_label.pack(fill="x", padx=15, pady=(0, 15))

        # Pack canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Footer con botones
        footer_frame = tk.Frame(tutorial_window, bg="#ecf0f1", height=70)
        footer_frame.pack(fill="x")
        footer_frame.pack_propagate(False)

        # Frame para centrar botones
        buttons_frame = tk.Frame(footer_frame, bg="#ecf0f1")
        buttons_frame.pack(expand=True)

        # Botón de cerrar
        close_button = tk.Button(
            buttons_frame, 
            text="✅ ¡Entendido, a Jugar!", 
            command=tutorial_window.destroy, 
            bg="#27ae60",
            fg="white", 
            font=("Helvetica", 12, "bold"),
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2"
        )
        close_button.pack(side="left", padx=10)

        # Botón para jugar una partida de práctica
        practice_button = tk.Button(
            buttons_frame,
            text="🎯 Reiniciar Partida",
            command=lambda: [tutorial_window.destroy(), self.restart_game()],
            bg="#3498db",
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2"
        )
        practice_button.pack(side="left", padx=10)

        # Hacer la ventana modal y centrada
        tutorial_window.transient(self.root)
        tutorial_window.grab_set()

        # Centrar la ventana
        tutorial_window.update_idletasks()
        x = (tutorial_window.winfo_screenwidth() // 2) - (700 // 2)
        y = (tutorial_window.winfo_screenheight() // 2) - (550 // 2)
        tutorial_window.geometry(f"700x550+{x}+{y}")

        # Bind mouse wheel para scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        # Bind eventos de scroll
        tutorial_window.bind("<MouseWheel>", _on_mousewheel)  # Windows
        tutorial_window.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        tutorial_window.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux

    def create_position_indicator(self):
        """Crear indicador de posición del cursor (opcional)"""
        if not hasattr(self, 'cursor_label'):
            self.cursor_label = tk.Label(
                self.info_frame,
                text="Cursor: Tablero (2,2) - Celda (2,2)",
                font=("Arial", 10),
                fg="#666666"
            )
            self.cursor_label.grid(row=2, column=0, columnspan=4, pady=5)
    
    def create_match_in_db(self):
        """Crear una nueva partida en la base de datos"""
        try:
            match_repo = MatchRepository(self.session)
            self.match = match_repo.create(self.player1_id, self.player2_id)
            self.match_id = self.match.id
            self.match_created = True
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la partida en la base de datos: {str(e)}")
            self.match_created = False
    
    def register_move_in_db(self, board_i, board_j, cell_i, cell_j, time_taken):
        """Registrar movimiento en la base de datos"""
        if not self.match_created:
            return
        
        try:
            match_repo = MatchRepository(self.session)
            
            # Convertir coordenadas del tablero a índices (0-8)
            sub_board_index = board_i * 3 + board_j
            cell_index = cell_i * 3 + cell_j
            
            # Determinar qué jugador está moviendo
            player_id = self.player1_id if self.current_player == "X" else self.player2_id
            
            match_repo.register_move(
                self.match_id,
                player_id,
                sub_board_index,
                cell_index,
                time_taken
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo registrar el movimiento: {str(e)}")
    
    def finish_match_in_db(self):
        """Finalizar la partida en la base de datos"""
        if not self.match_created:
            return
        
        try:
            match_repo = MatchRepository(self.session)
            
            # Determinar el ganador (si lo hay)
            winner_id = None
            if self.game_winner == "X":
                winner_id = self.player1_id
            elif self.game_winner == "O":
                winner_id = self.player2_id
            
            match_repo.finish_match(self.match_id, winner_id)
            
            # Mostrar estadísticas del ranking
            self.show_ranking_stats()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo finalizar la partida: {str(e)}")
    
    def show_ranking_stats(self):
        """Mostrar estadísticas del ranking después de la partida"""
        if not self.match_created:
            return
        
        try:
            # Obtener información actualizada de los jugadores
            player_repo = PlayerRepository(self.session)
            player1 = player_repo.get_by_id(self.player1_id)
            player2 = player_repo.get_by_id(self.player2_id)
            
            if player1 and player2 and player1.rankings and player2.rankings:
                stats_message = "Estadísticas del Ranking:\n\n"
                
                # Jugador 1
                stats_message += f"Jugador X ({player1.username}):\n"
                stats_message += f"MMR: {player1.rankings.current_mmr} ({player1.rankings.rank_label})\n"
                stats_message += f"Ratio de victorias: {player1.rankings.win_ratio:.2f}\n\n"
                
                # Jugador 2
                stats_message += f"Jugador O ({player2.username}):\n"
                stats_message += f"MMR: {player2.rankings.current_mmr} ({player2.rankings.rank_label})\n"
                stats_message += f"Ratio de victorias: {player2.rankings.win_ratio:.2f}\n"
                
                messagebox.showinfo("Estadísticas del Ranking", stats_message)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener las estadísticas: {str(e)}")
    
    def create_boards(self):
        for i in range(3):
            for j in range(3):
                # Crear marco para cada tablero 3x3
                self.frames[i][j] = tk.Frame(self.main_frame, bg=self.bg_color, padx=3, pady=3)
                self.frames[i][j].grid(row=i, column=j, padx=5, pady=5)
                
                # Crear botones para cada casilla
                for x in range(3):
                    for y in range(3):
                        self.buttons[i][j][x][y] = tk.Button(
                            self.frames[i][j],
                            text="",
                            width=3,
                            height=1,
                            font=("Arial", 14, "bold"),
                            bg=self.bg_color,
                            command=lambda i=i, j=j, x=x, y=y: self.make_move(i, j, x, y)
                        )
                        self.buttons[i][j][x][y].grid(row=x, column=y)
        
        # Destacar inicialmente todos los tableros como disponibles
        self.highlight_active_board()
    
    def make_move(self, board_i, board_j, cell_i, cell_j):
        # Verificar si el juego ya terminó
        if self.game_winner:
            return
        
        # Verificar si el tablero está disponible para jugar
        if self.next_board is not None and (self.next_board[0] != board_i or self.next_board[1] != board_j):
            messagebox.showinfo("Movimiento inválido", "Debes jugar en el tablero resaltado.")
            return
        
        # Verificar si el tablero ya tiene un ganador
        if self.board_winners[board_i][board_j]:
            messagebox.showinfo("Tablero completado", "Este tablero ya está ganado. Juega en otro tablero disponible.")
            return
        
        # Verificar si la celda ya está ocupada
        if self.game_boards[board_i][board_j][cell_i][cell_j] is not None:
            return
        
        # Registrar el tiempo de esta jugada
        current_time = time.time()
        move_time = current_time - self.move_start_time
        
        if self.current_player == "X":
            self.player_X_times.append(move_time)
        else:
            self.player_O_times.append(move_time)
        
        # Reiniciar el temporizador para la siguiente jugada
        self.move_start_time = current_time
        
        # Registrar el movimiento en la base de datos
        self.register_move_in_db(board_i, board_j, cell_i, cell_j, move_time)
        
        # Realizar el movimiento
        self.game_boards[board_i][board_j][cell_i][cell_j] = self.current_player
        self.buttons[board_i][board_j][cell_i][cell_j].config(
            text=self.current_player,
            bg=self.player_X_color if self.current_player == "X" else self.player_O_color
        )
        
        # Verificar si hay un ganador en este tablero
        if self.check_win(self.game_boards[board_i][board_j]):
            self.board_winners[board_i][board_j] = self.current_player
            self.mark_board_as_won(board_i, board_j)
            
            # Verificar si hay un ganador del juego completo
            if self.check_win(self.board_winners):
                self.game_winner = self.current_player
                self.finish_match_in_db()  # Registrar fin de partida
                self.show_game_stats()
                return
        # Verificar si hay empate en este tablero
        elif self.check_draw(self.game_boards[board_i][board_j]):
            self.board_winners[board_i][board_j] = "Empate"
            self.mark_board_as_draw(board_i, board_j)
        
        # Verificar si el juego completo está empatado
        if self.check_draw(self.board_winners):
            self.game_winner = "Empate"
            self.finish_match_in_db()  # Registrar fin de partida
            self.show_game_stats()
            return
        
        # Cambiar al siguiente jugador
        self.current_player = "O" if self.current_player == "X" else "X"
        self.player_label.config(text=f"Turno del Jugador: {self.current_player}")
        
        # Determinar el siguiente tablero
        if self.board_winners[cell_i][cell_j] is None:
            self.next_board = (cell_i, cell_j)
            self.next_board_label.config(text=f"Tablero activo: ({cell_i+1}, {cell_j+1})")
        else:
            # Si el tablero ya está ganado o empatado, el jugador puede elegir cualquier tablero
            self.next_board = None
            self.next_board_label.config(text="Tablero activo: Cualquiera")
        
        # Actualizar la visualización de los tableros activos
        self.highlight_active_board()
        
        if hasattr(self, 'accessibility_manager'):
            self.accessibility_manager.board_focus_row = board_i
            self.accessibility_manager.board_focus_col = board_j
            self.accessibility_manager.cell_focus_row = cell_i
            self.accessibility_manager.cell_focus_col = cell_j
        
    
    def check_win(self, board):
        # Verificar filas
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] and board[i][0] is not None and board[i][0] != "Empate":
                return True
        
        # Verificar columnas
        for j in range(3):
            if board[0][j] == board[1][j] == board[2][j] and board[0][j] is not None and board[0][j] != "Empate":
                return True
        
        # Verificar diagonales
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] is not None and board[0][0] != "Empate":
            return True
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] is not None and board[0][2] != "Empate":
            return True
        
        return False
    
    def check_draw(self, board):
        # Verificar si todas las celdas están ocupadas y no hay ganador
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    return False
        return True
    
    def mark_board_as_won(self, board_i, board_j):
        # Marcar visualmente que un tablero ha sido ganado
        winner = self.board_winners[board_i][board_j]
        color = self.player_X_color if winner == "X" else self.player_O_color
        
        # Deshabilitar todos los botones en este tablero
        for i in range(3):
            for j in range(3):
                self.buttons[board_i][board_j][i][j].config(state=tk.DISABLED)
        
        # Colorear el fondo del tablero
        self.frames[board_i][board_j].config(bg=color)
        
        # Mostrar quién ganó este tablero
        label = tk.Label(
            self.frames[board_i][board_j],
            text=winner,
            font=("Arial", 36, "bold"),
            fg="white",
            bg=color
        )
        label.place(relx=0.5, rely=0.5, anchor="center")
    
    def mark_board_as_draw(self, board_i, board_j):
        # Marcar visualmente que un tablero ha terminado en empate
        # Deshabilitar todos los botones en este tablero
        for i in range(3):
            for j in range(3):
                self.buttons[board_i][board_j][i][j].config(state=tk.DISABLED)
        
        # Colorear el fondo del tablero
        self.frames[board_i][board_j].config(bg="#999999")  # Gris para empate
    
    def highlight_active_board(self):
        # Obtener el color del jugador actual
        active_color = self.player_X_color if self.current_player == "X" else self.player_O_color
        active_color_light = self.lighten_color(active_color)
        
        # Quitar el resaltado de todos los tableros
        for i in range(3):
            for j in range(3):
                if self.board_winners[i][j] is None:
                    self.frames[i][j].config(bg=self.bg_color)
        
        # Resaltar el tablero activo con el color del jugador actual
        if self.next_board is not None:
            i, j = self.next_board
            if self.board_winners[i][j] is None:
                self.frames[i][j].config(bg=active_color_light)
        else:
            # Si cualquier tablero es válido, resaltar todos los disponibles
            for i in range(3):
                for j in range(3):
                    if self.board_winners[i][j] is None:
                        self.frames[i][j].config(bg=active_color_light)
    
    def lighten_color(self, hex_color):
        # Convertir el color hex a RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Aclarar el color (mezclar con blanco)
        r = min(255, r + 100)
        g = min(255, g + 100)
        b = min(255, b + 100)
        
        # Convertir de nuevo a hex
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def show_game_stats(self):
        # Calcular estadísticas de tiempo
        x_avg_time = sum(self.player_X_times) / len(self.player_X_times) if self.player_X_times else 0
        o_avg_time = sum(self.player_O_times) / len(self.player_O_times) if self.player_O_times else 0
        total_avg_time = (sum(self.player_X_times) + sum(self.player_O_times)) / (len(self.player_X_times) + len(self.player_O_times)) if (self.player_X_times or self.player_O_times) else 0
        
        # Crear mensaje con estadísticas
        stats_message = f"¡El jugador {self.current_player} ha ganado el juego!\n\n" if self.game_winner != "Empate" else "¡El juego ha terminado en empate!\n\n"
        stats_message += f"Estadísticas de tiempo:\n"
        stats_message += f"Jugador X - Tiempo promedio: {x_avg_time:.2f}s\n"
        stats_message += f"Jugador O - Tiempo promedio: {o_avg_time:.2f}s\n"
        stats_message += f"Tiempo promedio total: {total_avg_time:.2f}s"
        
        messagebox.showinfo("¡Fin del juego!", stats_message)
    
    def update_time(self):
        # Actualizar el tiempo transcurrido desde el último movimiento
        elapsed_time = time.time() - self.move_start_time
        self.time_label.config(text=f"Tiempo: {elapsed_time:.1f}s")
        
        # Programar la próxima actualización (cada 100ms)
        if not self.game_winner:
            self.root.after(100, self.update_time)
    
    def restart_game(self):
        # Reiniciar el estado del juego
        self.current_player = "X"
        self.next_board = None
        self.game_boards = [[[[None for _ in range(3)] for _ in range(3)] for _ in range(3)] for _ in range(3)]
        self.board_winners = [[None for _ in range(3)] for _ in range(3)]
        self.game_winner = None
        
        # Reiniciar las variables de tiempo
        self.move_start_time = time.time()
        self.player_X_times = []
        self.player_O_times = []
        
        # Reiniciar las etiquetas
        self.player_label.config(text=f"Turno del Jugador: {self.current_player}")
        self.next_board_label.config(text="Tablero activo: Cualquiera")
        
        # Destruir todos los widgets y recrear el tablero
        for i in range(3):
            for j in range(3):
                self.frames[i][j].destroy()
        
        self.create_boards()
        
        # Reiniciar el temporizador
        self.update_time()
        
        # Crear nueva partida en la base de datos si hay jugadores
        if self.session and self.player1_id and self.player2_id:
            self.create_match_in_db()

# =============================================================================
# GUI INTERFACE (TKINTER)
# =============================================================================

class App(tk.Tk):
    def __init__(self, session=None):
        super().__init__()
        
        # Guardar la sesión de base de datos
        self.session = session
        

        self.title("Ranking System - Advanced Tic Tac Toe")
        self.geometry("1200x800")
        
        self.accessibility_manager = add_accessibility_to_app(self)
        self.configure(bg=COLORS["bg_light"])
        
        # State variables
        self.logged_in = False
        self.current_user = None
        self.is_admin = False
        self.current_page = 1
        self.items_per_page = 20
        
        # Create database if it doesn't exist
        Base.metadata.create_all(engine)
        
        # Create session
        self.session = SessionLocal()
        
        # Initialize repositories and services
        self.player_repo = PlayerRepository(self.session)
        self.server_repo = ServerRepository(self.session)
        self.match_repo = MatchRepository(self.session)
        self.ranking_service = RankingService(self.session)
        self.mmr_service = MMRService(self.session)
        self.analytics_gui = add_analytics_to_app(self)
        
        # Initialize minimum data if database is empty
        self.initialize_base_data()
        
        # Show login screen
        self.show_login()
    
    def initialize_base_data(self):
        """Initialize base data if it doesn't exist in the database"""
        # Check if there are servers
        if self.session.query(Server).count() == 0:
            # Create default servers
            regions = ["America", "Europa", "Asia", "Oceania"]
            for region in regions:
                server = Server(name=f"Server {region}", region=region)
                self.session.add(server)
            
            self.session.commit()
        
        # Check if admin exists
        if not self.session.query(Player).filter(Player.username == "admin").first():
            # Create admin user
            admin = Player(
                username="admin",
                hashed_password=hash_password("admin"),
                level=99,
                server_id=1
            )
            self.session.add(admin)
            self.session.flush()
            
            # Create stats and ranking for admin
            stats = PlayerStats(player_id=admin.id)
            ranking = PlayerRanking(player_id=admin.id)
            
            self.session.add(stats)
            self.session.add(ranking)
            self.session.commit()
    
    def show_login(self):
        """Show login screen"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create main frame
        frame = ttk.Frame(self)
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title
        ttk.Label(frame, text="Advanced Tic Tac Toe", font=("Helvetica", 24, "bold")).pack(pady=(0, 20))
        ttk.Label(frame, text="Ranking and Management System", font=("Helvetica", 16)).pack(pady=(0, 40))
        
        # Login frame
        login_frame = ttk.Frame(frame)
        login_frame.pack(pady=20)
        
        # Login fields
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky="w", pady=5)
        username_entry = ValidatedEntry(login_frame, width=30, validate_func=validate_required, 
                                      error_msg="Username is required")
        username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        password_entry = ValidatedEntry(login_frame, width=30, show="*", validate_func=validate_required,
                                      error_msg="Password is required")
        password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Login button
        login_button = ttk.Button(
            login_frame, 
            text="Login", 
            command=lambda: self.login(username_entry.var.get(), password_entry.var.get())
        )
        login_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Button to create server (for initialization only)
        ttk.Button(
            frame,
            text="Create Server",
            command=self.create_server_dialog
        )
        
        # Button to create user (for initialization only)
        ttk.Button(
            frame,
            text="Create User",
            command=self.create_user_dialog
        ).pack(pady=10)
    
    def login(self, username: str, password: str):
        """Process login"""
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        
        user = self.player_repo.authenticate(username, password)
        
        if not user:
            messagebox.showerror("Error", "Invalid username or password")
            return
        
        self.current_user = user
        self.logged_in = True
        self.is_admin = user.level >= 90
        
        # Show appropriate interface
        if self.is_admin:
            self.show_admin_interface()
        else:
            self.show_player_interface()
    
    def logout(self):
        """Close current session"""
        self.current_user = None
        self.logged_in = False
        self.is_admin = False
        self.show_login()
    
    def create_server_dialog(self):
        """Show dialog to create a new server"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Create Server")
        dialog.geometry("300x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Name:").pack(pady=(20, 5))
        name_entry = ValidatedEntry(dialog, width=30, validate_func=validate_required,
                                  error_msg="Server name is required")
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Region:").pack(pady=5)
        region_entry = ValidatedEntry(dialog, width=30, validate_func=validate_required,
                                    error_msg="Region is required")
        region_entry.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save",
            command=lambda: self.save_server(
                name_entry.var.get(),
                region_entry.var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def save_server(self, name: str, region: str, dialog: tk.Toplevel):
        """Save a new server to the database"""
        if not name or not region:
            messagebox.showerror("Error", "All fields are required", parent=dialog)
            return
        
        try:
            self.server_repo.create(name, region)
            messagebox.showinfo("Success", "Server created successfully", parent=dialog)
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create server: {str(e)}", parent=dialog)
    
    def create_user_dialog(self):
        """Show dialog to create a new user"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Create User")
        dialog.geometry("350x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Username:").pack(pady=(20, 5))
        username_entry = ValidatedEntry(dialog, width=30, validate_func=validate_required,
                                      error_msg="Username is required")
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ValidatedEntry(dialog, width=30, show="*", validate_func=validate_required,
                                      error_msg="Password is required")
        password_entry.pack(pady=5)
        
        # Server selector
        ttk.Label(dialog, text="Server:").pack(pady=5)
        
        servers = self.server_repo.list_all()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        if server_names:
            server_var.set(server_names[0])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save",
            command=lambda: self.save_user(
                username_entry.var.get(),
                password_entry.var.get(),
                server_ids[server_names.index(server_var.get())],
                dialog
            )
        ).pack(pady=20)
    
    def save_user(self, username: str, password: str, server_id: int, dialog: tk.Toplevel):
        """Save a new user to the database"""
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required", parent=dialog)
            return
        
        try:
            player = self.player_repo.create(username, password, server_id)
            if player:
                messagebox.showinfo("Success", "User created successfully", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Username already exists", parent=dialog)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create user: {str(e)}", parent=dialog)
    
    def show_admin_interface(self):
        """Show admin interface with improved button labeling"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()

        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")

        # Create notebook (tabs)
        notebook = ttk.Notebook(main_frame)

        # Tabs
        tab_analytics = ttk.Frame(notebook)
        tab_players = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_ranking = ttk.Frame(notebook)
        tab_game = ttk.Frame(notebook)

        notebook.add(tab_analytics, text="📊 Analytics")
        notebook.add(tab_players, text="👥 Players")
        notebook.add(tab_game, text="🎮 Play")
        notebook.add(tab_matches, text="⚔ Matches")
        notebook.add(tab_ranking, text="🏆 Rankings")

        notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # Top bar with improved buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Left side - user info
        user_info_frame = ttk.Frame(top_frame)
        user_info_frame.pack(side="left")

        ttk.Label(
            user_info_frame, 
            text=f"🔐 Connected as: {self.current_user.username} (Admin)",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")

        # Right side - action buttons
        action_buttons_frame = ttk.Frame(top_frame)
        action_buttons_frame.pack(side="right")

        # Sync all data button (renamed from "Update")
        sync_btn = ttk.Button(
            action_buttons_frame,
            text="🔄 Sync All Data",
            command=self.sync_data
        )
        sync_btn.pack(side="left", padx=5)

        # Logout button
        logout_btn = ttk.Button(
            action_buttons_frame,
            text="🚪 Logout",
            command=self.logout
        )
        logout_btn.pack(side="left", padx=5)

        # Fill tabs
        self.fill_analytics_tab(tab_analytics)
        self.fill_game_tab(tab_game)
        self.fill_players_tab(tab_players)
        self.fill_matches_tab(tab_matches)
        self.fill_ranking_tab(tab_ranking)
    
    def sync_data(self):
        """Synchronize all data with the database"""
        try:
            # Refresh session
            self.session.expire_all()

            # Show loading indicator
            self.show_loading_message("Synchronizing all data...")

            # Update current tab data
            self.refresh_current_tab_data()

            # Hide loading and show success
            self.hide_loading_message()
            messagebox.showinfo("Success", "All data synchronized successfully")

        except Exception as e:
            self.hide_loading_message()
            messagebox.showerror("Error", f"Could not synchronize data: {str(e)}")
    
    def show_loading_message(self, message):
        """Show a loading message"""
        # You can implement a proper loading spinner here
        # For now, we'll just update the window title
        original_title = self.title()
        self.title(f"{original_title} - {message}")
        self.update()

    def hide_loading_message(self):
        """Hide loading message"""
        # Restore original title
        if " - " in self.title():
            original_title = self.title().split(" - ")[0]
            self.title(original_title)
    
    def refresh_current_tab_data(self):
        """Refresh data for the currently active tab"""
        try:
            # Find the active notebook and tab
            main_frame = self.winfo_children()[0]
            if not main_frame.winfo_children():
                return

            notebook = main_frame.winfo_children()[0]
            if not hasattr(notebook, 'index') or not hasattr(notebook, 'select'):
                return

            current_tab_index = notebook.index(notebook.select())

            if self.is_admin:
                # Admin interface tabs: Players, Play, Matches, Rankings
                if current_tab_index == 0:  # Players
                    tree = self.find_widget_by_type(notebook, 'Treeview', 'players')
                    if tree:
                        self.load_players(tree)
                elif current_tab_index == 2:  # Matches  
                    tree = self.find_widget_by_type(notebook, 'Treeview', 'matches')
                    if tree:
                        self.load_matches(tree)
                elif current_tab_index == 3:  # Rankings
                    tree = self.find_widget_by_type(notebook, 'Treeview', 'ranking')
                    if tree:
                        self.update_ranking(tree)
            else:
                # Player interface tabs: My Profile, My Matches, Ranking, Play
                if current_tab_index == 1:  # My Matches
                    tree = self.find_widget_by_type(notebook, 'Treeview', 'player_matches')
                    if tree:
                        self.load_player_matches(tree)
                elif current_tab_index == 2:  # Ranking
                    tree = self.find_widget_by_type(notebook, 'Treeview', 'player_ranking')
                    if tree:
                        self.update_player_ranking(tree)

        except Exception as e:
            print(f"Error refreshing current tab: {e}")
    
    def find_widget_by_type(self, parent, widget_type, context=None):
        """Find widget by type in the widget tree"""
        try:
            if parent.winfo_class() == widget_type:
                return parent

            for child in parent.winfo_children():
                result = self.find_widget_by_type(child, widget_type, context)
                if result:
                    return result
        except:
            pass
        return None
    
    def get_players_tree(self):
        """Get the players treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[1].winfo_children()[1].winfo_children()[0]
    
    def get_matches_tree(self):
        """Get the matches treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0]
    
    def get_ranking_tree(self):
        """Get the ranking treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[3].winfo_children()[1].winfo_children()[0]
    
    def fill_game_tab(self, tab):
        """fill the tap to start the game"""
        # Frame principal
        main_frame = ttk.Frame(tab)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Título
        ttk.Label(main_frame, text="Iniciar Partida de Ultimate Tic Tac Toe", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Selector de jugadores
        players_frame = ttk.Frame(main_frame)
        players_frame.pack(pady=10)
        
        # Jugador 1 (X)
        ttk.Label(players_frame, text="Jugador 1 (X):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        players = self.player_repo.list_all()[0]  # Todos los jugadores
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        self.player1_var = tk.StringVar()
        if player_names:
            self.player1_var.set(player_names[0])
        
        self.player1_menu = ttk.OptionMenu(players_frame, self.player1_var, *player_names)
        self.player1_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Jugador 2 (O)
        ttk.Label(players_frame, text="Jugador 2 (O):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.player2_var = tk.StringVar()
        if len(player_names) > 1:
            self.player2_var.set(player_names[1])
        elif player_names:
            self.player2_var.set(player_names[0])
        
        self.player2_menu = ttk.OptionMenu(players_frame, self.player2_var, *player_names)
        self.player2_menu.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Botón para iniciar el juego
        ttk.Button(
            main_frame,
            text="Iniciar Partida",
            command=self.start_game
        ).pack(pady=20)
    
    def fill_players_tab(self, tab):
        """Fill players tab with improved UI"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Search controls
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(search_frame, text="Search:").pack(side="left", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side="left", padx=5)

        # Server filter
        ttk.Label(search_frame, text="Server:").pack(side="left", padx=(20, 5))

        servers = self.server_repo.list_all()
        server_names = ["All"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]

        server_var = tk.StringVar(value=server_names[0])
        server_menu = ttk.OptionMenu(search_frame, server_var, *server_names)
        server_menu.pack(side="left", padx=5)

        # Create sort manager
        sort_manager = SortManager()
        sort_manager.current_sort_column = "username"

        # Action buttons frame
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(side="right", padx=(20, 0))

        # Search button
        search_btn = ttk.Button(
            action_frame,
            text="🔍 Search",
            command=lambda: self.search_players(
                search_var.get(),
                None if server_var.get() == "All" else server_ids[server_names.index(server_var.get())],
                sort_manager.current_sort_column,
                sort_manager.current_sort_direction,
                players_tree
            )
        )
        search_btn.pack(side="left", padx=5)

        # Refresh table button
        refresh_btn = ttk.Button(
            action_frame,
            text="🔄 Refresh Table",
            command=lambda: self.load_players(
                players_tree, 
                sort_manager.current_sort_column,
                sort_manager.current_sort_direction
            )
        )
        refresh_btn.pack(side="left", padx=5)

        # Create player button
        create_btn = ttk.Button(
            action_frame,
            text="➕ Create Player",
            command=self.create_player_dialog
        )
        create_btn.pack(side="left", padx=5)

        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="bottom", pady=(10, 0))

        self.prev_page_btn = ttk.Button(
            pagination_frame,
            text="◀ Previous",
            command=lambda: self.change_page(-1, lambda: self.load_players(
                players_tree, 
                sort_manager.current_sort_column,
                sort_manager.current_sort_direction
            ))
        )
        self.prev_page_btn.pack(side="left", padx=5)

        self.page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.page_label.pack(side="left", padx=15)

        self.next_page_btn = ttk.Button(
            pagination_frame,
            text="Next ▶",
            command=lambda: self.change_page(1, lambda: self.load_players(
                players_tree,
                sort_manager.current_sort_column,
                sort_manager.current_sort_direction
            ))
        )
        self.next_page_btn.pack(side="left", padx=5)

        # Create a frame with scrollbar for the table
        table_container = ttk.Frame(tab)
        table_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Players table
        players_tree = ttk.Treeview(
            table_container,
            columns=("id", "username", "level", "server", "games", "mmr", "rank", "win_ratio"),
            show="headings"
        )

        # Configure columns with sorting
        def setup_column_sort(column, text, width, anchor="w"):
            players_tree.heading(column, text=text, command=lambda: self.sort_treeview(players_tree, column, sort_manager))
            players_tree.column(column, width=width, anchor=anchor)

        setup_column_sort("id", "ID", 50, "center")
        setup_column_sort("username", "Username", 150)
        setup_column_sort("level", "Level", 50, "center")
        setup_column_sort("server", "Server", 150)
        setup_column_sort("games", "Games", 70, "center")
        setup_column_sort("mmr", "MMR", 70, "center")
        setup_column_sort("rank", "Rank", 100)
        setup_column_sort("win_ratio", "Win Ratio", 70, "center")

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=players_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=players_tree.xview)
        players_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Pack everything
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        players_tree.pack(side="left", expand=True, fill="both")

        # Context menu
        def show_context_menu(event):
            item = players_tree.identify_row(event.y)
            if item:
                players_tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)

        context_menu = tk.Menu(players_tree, tearoff=0)
        context_menu.add_command(label="👁 View Details", command=lambda: self.view_player_details(players_tree))
        context_menu.add_command(label="✏ Edit", command=lambda: self.edit_player_dialog(players_tree))
        context_menu.add_separator()
        context_menu.add_command(label="🗑 Delete", command=lambda: self.delete_player(players_tree))

        players_tree.bind("<Button-3>", show_context_menu)

        # Load initial data
        self.load_players(players_tree, "username", "asc")

    def start_game(self):
        """Iniciar una nueva partida del juego"""
        # Obtener los IDs de los jugadores seleccionados
        players = self.player_repo.list_all()[0]  # Todos los jugadores
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        try:
            player1_name = self.player1_var.get()
            player2_name = self.player2_var.get()
            
            player1_id = player_ids[player_names.index(player1_name)]
            player2_id = player_ids[player_names.index(player2_name)]
            
            if player1_id == player2_id:
                messagebox.showerror("Error", "Debes seleccionar dos jugadores diferentes")
                return
            
            # Crear ventana para el juego
            game_window = tk.Toplevel(self)
            game_window.title(f"Ultimate Tic Tac Toe: {player1_name} (X) vs {player2_name} (O)")
            
            # Iniciar el juego con la sesión de base de datos y los IDs de los jugadores
            UltimateTicTacToe(game_window, self.session, player1_id, player2_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el juego: {str(e)}")
    def change_page(self, delta, callback):
        """Change current page with improved validation and refresh"""
        try:
            # Calculate new page
            new_page = max(1, self.current_page + delta)

            # Validate if the new page has data
            has_data = self.validate_page_has_data(new_page)

            if delta > 0 and not has_data:
                messagebox.showinfo("Information", "No more pages available")
                return

            if delta < 0 and new_page < 1:
                messagebox.showinfo("Information", "You are already on the first page")
                return

            # Update page
            old_page = self.current_page
            self.current_page = new_page

            # Update all page labels safely
            self.update_all_page_labels()

            # Try to refresh data
            try:
                callback()
                # If successful, update pagination buttons
                self.update_pagination_buttons()
            except Exception as e:
                # If refresh fails, rollback page change
                self.current_page = old_page
                self.update_all_page_labels()
                messagebox.showerror("Error", f"Could not load page data: {str(e)}")

        except Exception as e:
            print(f"Error in change_page: {e}")
            
    
    def validate_page_has_data(self, page_num):
        """Validate if a page has data before navigating to it"""
        try:
            if self.is_admin:
                notebook = self.winfo_children()[0].winfo_children()[0]
                current_tab = notebook.index(notebook.select())

                if current_tab == 0:  # Players tab
                    players, total = self.player_repo.list_all(page=page_num, per_page=self.items_per_page)
                    return len(players) > 0
                elif current_tab == 2:  # Matches tab
                    matches, total = self.match_repo.list_all(page=page_num, per_page=self.items_per_page)
                    return len(matches) > 0
                elif current_tab == 3:  # Rankings tab
                    ranking, total = self.ranking_service.get_global_ranking(page=page_num, per_page=self.items_per_page)
                    return len(ranking) > 0
            else:
                notebook = self.winfo_children()[0].winfo_children()[0]
                current_tab = notebook.index(notebook.select())

                if current_tab == 1:  # My Matches tab
                    matches, total = self.match_repo.list_by_player(self.current_user.id, page=page_num, per_page=self.items_per_page)
                    return len(matches) > 0
                elif current_tab == 2:  # Ranking tab
                    ranking, total = self.ranking_service.get_global_ranking(page=page_num, per_page=self.items_per_page)
                    return len(ranking) > 0

            return True  # Default to true for safety

        except Exception:
            return True  # Default to true if we can't validate
    
    def update_all_page_labels(self):
        """Update all page labels safely"""
        try:
            page_text = f"Page {self.current_page}"

            # Update all possible page labels
            labels_to_update = [
                'page_label', 'matches_page_label', 'ranking_page_label',
                'player_matches_page_label', 'player_ranking_page_label'
            ]

            for label_name in labels_to_update:
                if hasattr(self, label_name):
                    label = getattr(self, label_name)
                    if label and label.winfo_exists():
                        label.config(text=page_text)

        except Exception as e:
            print(f"Error updating page labels: {e}")


    
    def update_pagination_buttons(self):
        """Update pagination buttons with better validation"""
        try:
            # Always enable Previous button if not on first page
            prev_buttons = ['prev_page_btn', 'matches_prev_btn', 'ranking_prev_btn', 
                           'player_matches_prev_btn', 'player_ranking_prev_btn']

            next_buttons = ['next_page_btn', 'matches_next_btn', 'ranking_next_btn',
                           'player_matches_next_btn', 'player_ranking_next_btn']

            # Update Previous buttons
            for btn_name in prev_buttons:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    if btn and btn.winfo_exists():
                        if self.current_page <= 1:
                            btn.config(state="disabled")
                        else:
                            btn.config(state="normal")

            # Update Next buttons - check if next page has data
            has_next_data = self.validate_page_has_data(self.current_page + 1)

            for btn_name in next_buttons:
                if hasattr(self, btn_name):
                    btn = getattr(self, btn_name)
                    if btn and btn.winfo_exists():
                        if has_next_data:
                            btn.config(state="normal")
                        else:
                            btn.config(state="disabled")

        except Exception as e:
            print(f"Error updating pagination buttons: {e}")
    
    def load_players(self, tree, sort_by="username", sort_dir="asc"):
        """Load player list into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Get players with pagination and sorting
        players, total = self.player_repo.list_all(
            page=self.current_page, 
            per_page=self.items_per_page,
            sort_by=sort_by,
            sort_dir=sort_dir
        )
        
        for player in players:
            # Get related data
            stats = player.stats
            ranking = player.rankings
            server = player.server
            
            tree.insert(
                "",
                "end",
                values=(
                    player.id,
                    player.username,
                    player.level,
                    server.name if server else "N/A",
                    stats.games_played if stats else 0,
                    ranking.current_mmr if ranking else 0,
                    ranking.rank_label if ranking else "Unranked",
                    f"{stats.win_ratio:.2f}" if stats else "0.00"
                )
            )
        
        # Update pagination buttons
        self.update_pagination_buttons()
    
    def search_players(self, search: str, server_id: Optional[int], sort_by="username", sort_dir="asc", tree=None):
        """Search players according to criteria and update treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Reset pagination
        self.current_page = 1
        self.page_label.config(text=f"Page {self.current_page}")
        
        # Get players according to filters
        if search:
            players = self.player_repo.search_by_username(search)
            if server_id:
                players = [p for p in players if p.server_id == server_id]
            total = len(players)
        else:
            players, total = self.player_repo.list_all(
                server_id=server_id, 
                page=self.current_page, 
                per_page=self.items_per_page,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
        
        # Insert into table
        for player in players:
            # Get related data
            stats = player.stats
            ranking = player.rankings
            server = player.server
            
            tree.insert(
                "",
                "end",
                values=(
                    player.id,
                    player.username,
                    player.level,
                    server.name if server else "N/A",
                    stats.games_played if stats else 0,
                    ranking.current_mmr if ranking else 0,
                    ranking.rank_label if ranking else "Unranked",
                    f"{stats.win_ratio:.2f}" if stats else "0.00"
                )
            )
        
        # Update pagination buttons
        self.update_pagination_buttons()
    
    def create_player_dialog(self):
        """Show dialog to create a new player"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Create Player")
        dialog.geometry("400x350")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Username:").pack(pady=(20, 5))
        username_entry = ValidatedEntry(dialog, width=30, validate_func=validate_required,
                                      error_msg="Username is required")
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ValidatedEntry(dialog, width=30, show="*", validate_func=validate_required,
                                      error_msg="Password is required")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Level:").pack(pady=5)
        level_var = tk.IntVar(value=1)
        level_entry = ValidatedSpinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
        level_entry.pack(pady=5)
        
        # Server selector
        ttk.Label(dialog, text="Server:").pack(pady=5)
        
        servers = self.server_repo.list_all()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        if server_names:
            server_var.set(server_names[0])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save",
            command=lambda: self.save_new_player(
                username_entry.var.get(),
                password_entry.var.get(),
                server_ids[server_names.index(server_var.get())] if server_names else 1,
                dialog
            )
        ).pack(pady=20)
    
    def save_new_player(self, username: str, password: str, level: int, server_id: int, dialog: tk.Toplevel):
        """Save a new player to the database"""
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required", parent=dialog)
            return
        
        try:
            # Create player
            player = self.player_repo.create(username, password, server_id)
            
            if not player:
                messagebox.showerror("Error", "Username already exists", parent=dialog)
                return
            
            # Update level
            player.level = level
            self.session.commit()
            
            messagebox.showinfo("Success", "Player created successfully", parent=dialog)
            dialog.destroy()
            
            # Update player list
            self.load_players(self.get_players_tree())
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not create player: {str(e)}", parent=dialog)
    
    def edit_player_dialog(self, tree):
        """Show dialog to edit an existing player"""
        # Get selected player
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a player to edit")
            return
        
        # Get player ID
        player_id = tree.item(selected[0], "values")[0]
        player = self.player_repo.get_by_id(player_id)
        
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Player: {player.username}")
        dialog.geometry("400x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Username:").pack(pady=(20, 5))
        username_var = tk.StringVar(value=player.username)
        username_entry = ValidatedEntry(dialog, textvariable=username_var, width=30, 
                                  validate_func=validate_required, error_msg="Username is required")
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="New Password (leave blank to keep current):").pack(pady=5)
        password_var = tk.StringVar()
        password_entry = ttk.Entry(dialog, textvariable=password_var, width=30, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Level:").pack(pady=5)
        level_var = tk.IntVar(value=player.level)
        level_entry = ValidatedSpinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
        level_entry.pack(pady=5)
        
        # Server selector
        ttk.Label(dialog, text="Server:").pack(pady=5)
        
        servers = self.server_repo.list_all()
        server_names = [f"{s.name} ({s.region})" for s in servers]
        server_ids = [s.id for s in servers]
        
        server_var = tk.StringVar()
        current_server_index = 0
        
        for i, s_id in enumerate(server_ids):
            if s_id == player.server_id:
                current_server_index = i
                break
        
        if server_names:
            server_var.set(server_names[current_server_index])
        
        server_menu = ttk.OptionMenu(dialog, server_var, *server_names)
        server_menu.pack(pady=5)
        
        # MMR editing
        ttk.Label(dialog, text="Current MMR:").pack(pady=(15, 5))
        
        mmr_frame = ttk.Frame(dialog)
        mmr_frame.pack(pady=5)
        
        current_mmr = 1000
        if player.rankings:
            current_mmr = player.rankings.current_mmr
        
        ttk.Label(mmr_frame, text=f"Current: {current_mmr}").pack(side="left", padx=5)
        
        mmr_var = tk.IntVar(value=current_mmr)
        mmr_entry = ValidatedSpinbox(mmr_frame, from_=0, to=5000, textvariable=mmr_var, width=10)
        mmr_entry.pack(side="left", padx=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save Changes",
            command=lambda: self.save_player_edit(
                player.id,
                {
                    "username": username_var.get(),
                    "password": password_var.get(),
                    "level": level_var.get(),
                    "server_id": server_ids[server_names.index(server_var.get())] if server_names else 1,
                    "mmr": mmr_var.get()
                },
                dialog,
                tree
            )
        ).pack(pady=20)
    
    def save_player_edit(self, player_id: int, data: Dict, dialog: tk.Toplevel, tree):
        """Save player changes to the database"""
        try:
            # Validate level
            if not validate_integer(data["level"]):
                messagebox.showerror("Error", "Level must be a valid number", parent=dialog)
                return
            
            # Check if MMR has changed
            player = self.player_repo.get_by_id(player_id)
            current_mmr = 1000
            if player.rankings:
                current_mmr = player.rankings.current_mmr
        
            mmr_changed = "mmr" in data and int(data["mmr"]) != current_mmr
        
            # Update player
            result = self.player_repo.update(player_id, data)
        
            if not result:
                messagebox.showerror("Error", "Could not edit player. Username may already exist.", parent=dialog)
                return
            
            # Asegurar que el cambio de servidor se guarde en la base de datos
            if "server_id" in data:
                player.server_id = data["server_id"]
                self.session.commit()
        
            # Update MMR if changed
            if mmr_changed:
                mmr_change = int(data["mmr"]) - current_mmr
                self.mmr_service.modify_mmr_manual(
                    player_id, 
                    mmr_change, 
                    f"Manual adjustment from player edit"
                )
        
            messagebox.showinfo("Success", "Player updated successfully", parent=dialog)
            dialog.destroy()
        
            # Update player list
            self.load_players(tree)
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not edit player: {str(e)}", parent=dialog)
    
    def delete_player(self, tree):
        """Delete a player from the database"""
        # Get selected player
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a player to delete")
            return
        
        # Get player ID
        player_id = tree.item(selected[0], "values")[0]
        player = self.player_repo.get_by_id(player_id)
        
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Confirm deletion
        confirmation = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete player {player.username}?\nThis action cannot be undone."
        )
        
        if not confirmation:
            return
        
        try:
            # Delete player
            self.player_repo.delete(player)
            self.session.commit()
            
            messagebox.showinfo("Success", "Player deleted successfully")
            
            # Update player list
            self.load_players(tree)
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete player: {str(e)}")
    
    def view_player_details(self, tree):
        """Show player details"""
        # Get selected player
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a player to view details")
            return
        
        # Get player ID
        player_id = tree.item(selected[0], "values")[0]
        player = self.player_repo.get_by_id(player_id)
        
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Create details window
        dialog = tk.Toplevel(self)
        dialog.title(f"Details for {player.username}")
        dialog.geometry("600x500")
        dialog.transient(self)
        
        # Notebook for details tabs
        notebook = ttk.Notebook(dialog)
        
        # Tabs
        tab_info = ttk.Frame(notebook)
        tab_stats = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_mmr = ttk.Frame(notebook)
        
        notebook.add(tab_info, text="Information")
        notebook.add(tab_stats, text="Statistics")
        notebook.add(tab_matches, text="Matches")
        notebook.add(tab_mmr, text="MMR")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Information tab
        info_frame = ttk.Frame(tab_info, padding=20)
        info_frame.pack(fill="both", expand=True)
        
        ttk.Label(info_frame, text="ID:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(player.id)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Username:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=player.username).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Level:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(player.level)).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Creation date:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=player.created_at.strftime("%Y-%m-%d %H:%M")).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Last login:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=player.last_login.strftime("%Y-%m-%d %H:%M") if player.last_login else "Never").grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Server:", anchor="e").grid(row=5, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=f"{player.server.name} ({player.server.region})" if player.server else "N/A").grid(row=5, column=1, padx=5, pady=5, sticky="w")
        
        # Statistics tab
        if player.stats:
            stats = player.stats
            stats_frame = ttk.Frame(tab_stats, padding=20)
            stats_frame.pack(fill="both", expand=True)
            
            ttk.Label(stats_frame, text="Games played:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_played)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Wins:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_won)).grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Draws:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_drawn)).grid(row=2, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Losses:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.games_lost)).grid(row=3, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Win ratio:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=f"{stats.win_ratio:.2f}").grid(row=4, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Average move time:", anchor="e").grid(row=6, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=f"{stats.average_move_time:.2f}s").grid(row=6, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_frame, text="Max win streak:", anchor="e").grid(row=7, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_frame, text=str(stats.max_win_streak)).grid(row=7, column=1, padx=5, pady=5, sticky="w")
        
        # Matches tab
        matches_frame = ttk.Frame(tab_matches)
        matches_frame.pack(fill="both", expand=True)
        
        # Match list
        matches_tree = ttk.Treeview(
            matches_frame,
            columns=("id", "date", "opponent", "result", "duration"),
            show="headings"
        )
        
        matches_tree.heading("id", text="ID")
        matches_tree.heading("date", text="Date")
        matches_tree.heading("opponent", text="Opponent")
        matches_tree.heading("result", text="Result")
        matches_tree.heading("duration", text="Duration")
        
        matches_tree.column("id", width=50, anchor="center")
        matches_tree.column("date", width=120)
        matches_tree.column("opponent", width=150)
        matches_tree.column("result", width=100, anchor="center")
        matches_tree.column("duration", width=100, anchor="center")
        
        scrollbar = ttk.Scrollbar(matches_frame, orient="vertical", command=matches_tree.yview)
        matches_tree.configure(yscrollcommand=scrollbar.set)
        
        matches_tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Load player's matches
        matches, _ = self.match_repo.list_by_player(player.id)
        
        for match in matches:
            # Determine opponent and result
            opponent = ""
            result = ""
            
            for mp in match.match_players:
                if mp.player_id != player.id:
                    opponent = self.player_repo.get_by_id(mp.player_id).username
                
                if mp.player_id == player.id:
                    if match.winner_id is None:
                        result = "Draw"
                    elif match.winner_id == player.id:
                        result = "Victory"
                    else:
                        result = "Defeat"
            
            # Calculate duration
            duration = format_duration(match.duration_seconds) if match.finished_at else "In progress"
            
            matches_tree.insert(
                "",
                "end",
                values=(
                    match.id,
                    match.created_at.strftime("%Y-%m-%d %H:%M"),
                    opponent,
                    result,
                    duration
                )
            )
        
        # MMR tab
        mmr_frame = ttk.Frame(tab_mmr)
        mmr_frame.pack(fill="both", expand=True)
        
        if player.rankings:
            ranking = player.rankings
            
            # MMR information
            info_mmr_frame = ttk.Frame(mmr_frame)
            info_mmr_frame.pack(fill="x", padx=10, pady=10)
            
            ttk.Label(info_mmr_frame, text="Current MMR:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_mmr_frame, text=str(ranking.current_mmr)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(info_mmr_frame, text="Rank:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_mmr_frame, text=ranking.rank_label).grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            # MMR history
            ttk.Label(mmr_frame, text="MMR History", font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
            
            history_frame = ttk.Frame(mmr_frame)
            history_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            history_tree = ttk.Treeview(
                history_frame,
                columns=("date", "before", "after", "change", "reason"),
                show="headings"
            )
            
            history_tree.heading("date", text="Date")
            history_tree.heading("before", text="Previous MMR")
            history_tree.heading("after", text="New MMR")
            history_tree.heading("change", text="Change")
            history_tree.heading("reason", text="Reason")
            
            history_tree.column("date", width=120)
            history_tree.column("before", width=80, anchor="center")
            history_tree.column("after", width=80, anchor="center")
            history_tree.column("change", width=80, anchor="center")
            history_tree.column("reason", width=200)
            
            scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=history_tree.yview)
            history_tree.configure(yscrollcommand=scrollbar.set)
            
            history_tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Load MMR history
            history, _ = self.mmr_service.get_mmr_history(player.id)
            
            for h in history:
                change = h.mmr_after - h.mmr_before
                change_str = f"+{change}" if change > 0 else str(change)
                
                history_tree.insert(
                    "",
                    "end",
                    values=(
                        h.timestamp.strftime("%Y-%m-%d %H:%M"),
                        h.mmr_before,
                        h.mmr_after,
                        change_str,
                        h.change_reason
                    )
                )
            
            # MMR evolution graph
            try:
                dates, mmr = self.mmr_service.get_mmr_graph_data(player.id)
                
                if dates and mmr:
                    ttk.Label(mmr_frame, text="MMR Evolution", font=("Helvetica", 12, "bold")).pack(pady=(20, 10))
                    
                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(dates, mmr, marker='o', linestyle='-', color='blue')
                    ax.set_ylabel('MMR')
                    ax.grid(True, linestyle='--', alpha=0.7)
                    
                    # Rotate x-axis labels
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Integrate graph in Tkinter
                    canvas = FigureCanvasTkAgg(fig, master=mmr_frame)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
            except:
                # If there's an error with matplotlib, ignore
                pass
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=10)
    
    def fill_matches_tab(self, tab):
        """Fill matches tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Buttons
        ttk.Button(
            control_frame,
            text="Create Match",
            command=self.create_match_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Generate Simulated Match",
            command=self.generate_simulated_match_dialog
        ).pack(side="left", padx=5)
        
        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        # Create sort manager
        sort_manager = SortManager()
        sort_manager.current_sort_column = "created_at"
        sort_manager.current_sort_direction = "desc"
        
        self.matches_prev_btn = ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.load_matches(matches_tree))
        )
        self.matches_prev_btn.pack(side="left", padx=5)
        
        self.matches_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.matches_page_label.pack(side="left", padx=5)
        
        self.matches_next_btn = ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.load_player_matches(
            matches_tree,
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction))
        )
        self.matches_next_btn.pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.load_matches(matches_tree)
        ).pack(side="right", padx=5)
        
        # Create a frame with scrollbar for the table
        table_container = ttk.Frame(tab)
        table_container.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Matches table
        matches_tree = ttk.Treeview(
            table_container,
            columns=("id", "date", "player1", "player2", "winner", "status", "duration", "moves"),
            show="headings"
        )
        
        # Configure columns with sorting
        def setup_column_sort(column, text, width, anchor="w"):
            matches_tree.heading(column, text=text, command=lambda: self.sort_treeview(matches_tree, column, sort_manager))
            matches_tree.column(column, width=width, anchor=anchor)
        
        setup_column_sort("id", "ID", 50, "center")
        setup_column_sort("date", "Date", 120)
        setup_column_sort("player1", "Player 1", 100)
        setup_column_sort("player2", "Player 2", 100)
        setup_column_sort("winner", "Winner", 100)
        setup_column_sort("status", "Status", 80, "center")
        setup_column_sort("duration", "Duration", 80, "center")
        setup_column_sort("moves", "Moves", 80, "center")
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=matches_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=matches_tree.xview)
        matches_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack everything
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        matches_tree.pack(side="left", expand=True, fill="both")
        
        # Context menu
        def show_context_menu(event):
            item = matches_tree.identify_row(event.y)
            if item:
                matches_tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)
        
        context_menu = tk.Menu(matches_tree, tearoff=0)
        context_menu.add_command(label="View Details", command=lambda: self.view_match_details(matches_tree))
        context_menu.add_command(label="Add Move", command=lambda: self.add_move_dialog(matches_tree))
        context_menu.add_separator()
        context_menu.add_command(label="Finish Match", command=lambda: self.finish_match_dialog(matches_tree))
        
        matches_tree.bind("<Button-3>", show_context_menu)
        
        # Load initial data
        self.load_matches(matches_tree, "created_at", "desc")

    
    def load_matches(self, tree, sort_by="created_at", sort_dir="desc"):
        """Load match list into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Get matches with pagination
        matches, total = self.match_repo.list_all(page=self.current_page, per_page=self.items_per_page, sort_by=sort_by, sort_dir=sort_dir)
        
        for match in matches:
            # Get players
            players = []
            for mp in match.match_players:
                player = self.player_repo.get_by_id(mp.player_id)
                if player:
                    players.append((mp.player_order, player.username))
            
            # Sort players by order
            players.sort(key=lambda x: x[0])
            
            # Determine names
            player1 = players[0][1] if len(players) > 0 else "N/A"
            player2 = players[1][1] if len(players) > 1 else "N/A"
            
            # Determine winner
            winner = "Draw"
            if match.winner_id:
                for player_order, username in players:
                    if self.player_repo.get_by_id(match.winner_id).username == username:
                        winner = username
                        break
            elif not match.finished_at:
                winner = "Pending"
            
            # Duration
            duration = format_duration(match.duration_seconds) if match.finished_at else "In progress"
            
            tree.insert(
                "",
                "end",
                values=(
                    match.id,
                    match.created_at.strftime("%Y-%m-%d %H:%M"),
                    player1,
                    player2,
                    winner,
                    match.status,
                    duration,
                    match.total_moves
                )
            )
        
        # Update pagination buttons
        self.update_pagination_buttons()
    
    def create_match_dialog(self):
        """Show dialog to create a new match"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Create Match")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Player 1 selector
        ttk.Label(dialog, text="Player 1 (X):").pack(pady=(20, 5))
        
        players = self.player_repo.list_all()[0]  # Get all players without pagination
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        player1_var = tk.StringVar()
        if player_names:
            player1_var.set(player_names[0])
        
        player1_menu = ttk.OptionMenu(dialog, player1_var, *player_names)
        player1_menu.pack(pady=5)
        
        # Player 2 selector
        ttk.Label(dialog, text="Player 2 (O):").pack(pady=5)
        
        player2_var = tk.StringVar()
        if len(player_names) > 1:
            player2_var.set(player_names[1])
        elif player_names:
            player2_var.set(player_names[0])
        
        player2_menu = ttk.OptionMenu(dialog, player2_var, *player_names)
        player2_menu.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Create Match",
            command=lambda: self.save_match(
                player_ids[player_names.index(player1_var.get())] if player_names else 0,
                player_ids[player_names.index(player2_var.get())] if player_names else 0,
                dialog
            )
        ).pack(pady=20)
    
    def save_match(self, player1_id: int, player2_id: int, dialog: tk.Toplevel):
        """Save a new match to the database"""
        if player1_id == player2_id:
            messagebox.showerror("Error", "You must select two different players", parent=dialog)
            return
        
        try:
            # Create match
            match = self.match_repo.create(player1_id, player2_id)
            
            messagebox.showinfo("Success", f"Match #{match.id} created successfully", parent=dialog)
            dialog.destroy()
            
            # Update match list
            self.load_matches(self.get_matches_tree())
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not create match: {str(e)}", parent=dialog)
    
    def generate_simulated_match_dialog(self):
        """Show dialog to generate a simulated match"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Generate Simulated Match")
        dialog.geometry("400x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Player 1 selector
        ttk.Label(dialog, text="Player 1 (X):").pack(pady=(20, 5))
        
        players = self.player_repo.list_all()[0]  # Get all players without pagination
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        player1_var = tk.StringVar()
        if player_names:
            player1_var.set(player_names[0])
        
        player1_menu = ttk.OptionMenu(dialog, player1_var, *player_names)
        player1_menu.pack(pady=5)
        
        # Player 2 selector
        ttk.Label(dialog, text="Player 2 (O):").pack(pady=5)
        
        player2_var = tk.StringVar()
        if len(player_names) > 1:
            player2_var.set(player_names[1])
        elif player_names:
            player2_var.set(player_names[0])
        
        player2_menu = ttk.OptionMenu(dialog, player2_var, *player_names)
        player2_menu.pack(pady=5)
        
        # Number of moves
        ttk.Label(dialog, text="Number of moves:").pack(pady=5)
        moves_var = tk.IntVar(value=20)
        moves_spin = ValidatedSpinbox(dialog, from_=4, to=100, textvariable=moves_var, width=10)
        moves_spin.pack(pady=5)
        
        # Winner
        ttk.Label(dialog, text="Winner:").pack(pady=5)
        winner_var = tk.StringVar(value="Random")
        winner_options = ["Random", "Player 1", "Player 2", "Draw"]
        winner_menu = ttk.OptionMenu(dialog, winner_var, *winner_options)
        winner_menu.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Generate Match",
            command=lambda: self.generate_simulated_match(
                player_ids[player_names.index(player1_var.get())] if player_names else 0,
                player_ids[player_names.index(player2_var.get())] if player_names else 0,
                moves_var.get(),
                winner_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def generate_simulated_match(self, player1_id: int, player2_id: int, moves: int, 
                               winner: str, dialog: tk.Toplevel):
        """Generate a simulated match"""
        if player1_id == player2_id:
            messagebox.showerror("Error", "You must select two different players", parent=dialog)
            return
        
        try:
            # Determine winner
            winner_id = None
            if winner == "Player 1":
                winner_id = player1_id
            elif winner == "Player 2":
                winner_id = player2_id
            elif winner == "Random" and random.random() > 0.3:  # 70% chance of having a winner
                winner_id = player1_id if random.random() > 0.5 else player2_id
            
            # Generate simulated match
            match = self.match_repo.generate_simulated_match(
                player1_id, player2_id, moves, winner_id
            )
            
            messagebox.showinfo("Success", f"Match #{match.id} generated successfully", parent=dialog)
            dialog.destroy()
            
            # Update match list
            self.load_matches(self.get_matches_tree())
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not generate match: {str(e)}", parent=dialog)
    
    def view_match_details(self, tree):
        """Show match details"""
        # Get selected match
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a match to view details")
            return
        
        # Get match ID
        match_id = tree.item(selected[0], "values")[0]
        match = self.match_repo.get_by_id(match_id)
        
        if not match:
            messagebox.showerror("Error", "Match not found")
            return
        
        # Create details window
        dialog = tk.Toplevel(self)
        dialog.title(f"Match Details #{match.id}")
        dialog.geometry("800x600")
        dialog.transient(self)
        
        # Notebook for details tabs
        notebook = ttk.Notebook(dialog)
        
        # Tabs
        tab_info = ttk.Frame(notebook)
        tab_moves = ttk.Frame(notebook)
        
        notebook.add(tab_info, text="Information")
        notebook.add(tab_moves, text="Moves")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Information tab
        info_frame = ttk.Frame(tab_info, padding=20)
        info_frame.pack(fill="both", expand=True)
        
        # General information
        ttk.Label(info_frame, text="ID:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(match.id)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Creation date:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=match.created_at.strftime("%Y-%m-%d %H:%M")).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(info_frame, text="Status:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=match.status).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        if match.finished_at:
            ttk.Label(info_frame, text="Finish date:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_frame, text=match.finished_at.strftime("%Y-%m-%d %H:%M")).grid(row=3, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(info_frame, text="Duration:", anchor="e").grid(row=4, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(info_frame, text=format_duration(match.duration_seconds)).grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Player information
        ttk.Label(info_frame, text="Players:", anchor="e", font=("Helvetica", 11, "bold")).grid(row=5, column=0, padx=5, pady=(20, 5), sticky="e")
        
        row = 6
        for mp in match.match_players:
            player = self.player_repo.get_by_id(mp.player_id)
            if player:
                symbol = "X" if mp.player_order == 1 else "O"
                result = ""
                
                if match.finished_at:
                    if match.winner_id is None:
                        result = "Draw"
                    elif match.winner_id == mp.player_id:
                        result = "Victory"
                    else:
                        result = "Defeat"
                
                ttk.Label(info_frame, text=f"Player {mp.player_order} ({symbol}):", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                ttk.Label(info_frame, text=f"{player.username} - {result}").grid(row=row, column=1, padx=5, pady=5, sticky="w")
                
                row += 1
                
                if mp.average_move_time > 0:
                    ttk.Label(info_frame, text="Average move time:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
                    ttk.Label(info_frame, text=f"{mp.average_move_time:.2f}s").grid(row=row, column=1, padx=5, pady=5, sticky="w")
                    row += 1
        
        # Statistics
        ttk.Label(info_frame, text="Statistics:", anchor="e", font=("Helvetica", 11, "bold")).grid(row=row, column=0, padx=5, pady=(20, 5), sticky="e")
        row += 1
        
        ttk.Label(info_frame, text="Total moves:", anchor="e").grid(row=row, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(info_frame, text=str(match.total_moves)).grid(row=row, column=1, padx=5, pady=5, sticky="w")
        
        # Moves tab
        moves_frame = ttk.Frame(tab_moves)
        moves_frame.pack(fill="both", expand=True)
        
        # Moves table
        moves_tree = ttk.Treeview(
            moves_frame,
            columns=("id", "order", "player", "sub_board", "cell", "time", "timestamp"),
            show="headings"
        )
        
        moves_tree.heading("id", text="ID")
        moves_tree.heading("order", text="Order")
        moves_tree.heading("player", text="Player")
        moves_tree.heading("sub_board", text="Sub-Board")
        moves_tree.heading("cell", text="Cell")
        moves_tree.heading("time", text="Time")
        moves_tree.heading("timestamp", text="Timestamp")
        
        moves_tree.column("id", width=50, anchor="center")
        moves_tree.column("order", width=50, anchor="center")
        moves_tree.column("player", width=100)
        moves_tree.column("sub_board", width=80, anchor="center")
        moves_tree.column("cell", width=80, anchor="center")
        moves_tree.column("time", width=80, anchor="center")
        moves_tree.column("timestamp", width=150)
        
        scrollbar = ttk.Scrollbar(moves_frame, orient="vertical", command=moves_tree.yview)
        moves_tree.configure(yscrollcommand=scrollbar.set)
        
        moves_tree.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        
        # Load moves
        for move in match.moves:
            # Get player
            player = self.player_repo.get_by_id(move.player_id)
            
            moves_tree.insert(
                "",
                "end",
                values=(
                    move.id,
                    move.move_number,
                    player.username if player else "N/A",
                    move.sub_board_index,
                    move.cell_index,
                    f"{move.time_taken_seconds:.2f}s",
                    move.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )
            )
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=10)
    
    def add_move_dialog(self, tree):
        """Show dialog to add a move to a match"""
        # Get selected match
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a match to add a move")
            return
        
        # Get match ID
        match_id = tree.item(selected[0], "values")[0]
        match = self.match_repo.get_by_id(match_id)
        
        if not match:
            messagebox.showerror("Error", "Match not found")
            return
        
        if match.finished_at:
            messagebox.showwarning("Warning", "Cannot add moves to a finished match")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Add Move to Match #{match.id}")
        dialog.geometry("400x450")
        dialog.transient(self)
        dialog.grab_set()
        
        # Player selector
        ttk.Label(dialog, text="Player:").pack(pady=(20, 5))
        
        # Get match players
        players = []
        for mp in match.match_players:
            player = self.player_repo.get_by_id(mp.player_id)
            if player:
                players.append((mp.player_id, player.username))
        
        player_names = [p[1] for p in players]
        player_ids = [p[0] for p in players]
        
        player_var = tk.StringVar()
        if player_names:
            player_var.set(player_names[0])
        
        player_menu = ttk.OptionMenu(dialog, player_var, *player_names)
        player_menu.pack(pady=5)
        
        # Sub-board and cell
        ttk.Label(dialog, text="Sub-board (0-8):").pack(pady=5)
        sub_board_var = tk.IntVar(value=0)
        sub_board_spin = ValidatedSpinbox(dialog, from_=0, to=8, textvariable=sub_board_var, width=10)
        sub_board_spin.pack(pady=5)
        
        ttk.Label(dialog, text="Cell (0-8):").pack(pady=5)
        cell_var = tk.IntVar(value=0)
        cell_spin = ValidatedSpinbox(dialog, from_=0, to=8, textvariable=cell_var, width=10)
        cell_spin.pack(pady=5)
        
        # Move time
        ttk.Label(dialog, text="Time (seconds):").pack(pady=5)
        time_var = tk.DoubleVar(value=2.0)
        time_spin = ValidatedSpinbox(dialog, from_=0.1, to=60.0, increment=0.1, textvariable=time_var, width=10)
        time_spin.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Add Move",
            command=lambda: self.save_move(
                match.id,
                player_ids[player_names.index(player_var.get())] if player_names else 0,
                sub_board_var.get(),
                cell_var.get(),
                time_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def save_move(self, match_id: int, player_id: int, sub_board: int, cell: int, 
                time_taken: float, dialog: tk.Toplevel):
        """Save a new move to the database"""
        try:
            # Validate inputs
            if not validate_integer(sub_board) or not (0 <= int(sub_board) <= 8):
                messagebox.showerror("Error", "Sub-board must be a number between 0 and 8", parent=dialog)
                return
                
            if not validate_integer(cell) or not (0 <= int(cell) <= 8):
                messagebox.showerror("Error", "Cell must be a number between 0 and 8", parent=dialog)
                return
                
            if not validate_float(time_taken) or float(time_taken) <= 0:
                messagebox.showerror("Error", "Time must be a positive number", parent=dialog)
                return
            
            # Register move
            move = self.match_repo.register_move(
                match_id, player_id, int(sub_board), int(cell), float(time_taken)
            )
            
            messagebox.showinfo("Success", f"Move #{move.move_number} added successfully", parent=dialog)
            dialog.destroy()
            
            # Update match list
            self.load_matches(self.get_matches_tree())
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not add move: {str(e)}", parent=dialog)
    
    def finish_match_dialog(self, tree):
        """Show dialog to finish a match"""
        # Get selected match
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a match to finish")
            return
        
        # Get match ID
        match_id = tree.item(selected[0], "values")[0]
        match = self.match_repo.get_by_id(match_id)
        
        if not match:
            messagebox.showerror("Error", "Match not found")
            return
        
        if match.finished_at:
            messagebox.showwarning("Warning", "Match is already finished")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Finish Match #{match.id}")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Result selector
        ttk.Label(dialog, text="Result:").pack(pady=(20, 5))
        
        # Get match players
        players = []
        for mp in match.match_players:
            player = self.player_repo.get_by_id(mp.player_id)
            if player:
                players.append((mp.player_id, player.username))
        
        # Result options
        result_options = ["Draw"] + [f"{p[1]} wins" for p in players]
        result_var = tk.StringVar(value=result_options[0])
        
        result_menu = ttk.OptionMenu(dialog, result_var, *result_options)
        result_menu.pack(pady=5)
        
        # Final description
        ttk.Label(dialog, text="Final state description (optional):").pack(pady=5)
        description = ttk.Entry(dialog, width=50)
        description.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Finish Match",
            command=lambda: self.save_match_finish(
                match.id,
                None if result_var.get() == "Draw" else players[[i for i, p in enumerate(players) if f"{p[1]} wins" == result_var.get()][0]][0],
                description.get(),
                dialog
            )
        ).pack(pady=20)
    
    def save_match_finish(self, match_id: int, winner_id: Optional[int], 
                       description: str, dialog: tk.Toplevel):
        """Save match finish"""
        try:
            # Update description if exists
            if description:
                match = self.match_repo.get_by_id(match_id)
                if match:
                    match.final_state_description = description
                    self.session.commit()
            
            # Finish match
            self.match_repo.finish_match(match_id, winner_id)
            
            messagebox.showinfo("Success", "Match finished successfully", parent=dialog)
            dialog.destroy()
            
            # Update match list
            self.load_matches(self.get_matches_tree())
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not finish match: {str(e)}", parent=dialog)
    
    def fill_ranking_tab(self, tab):
        """Fill ranking tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Server selector
        ttk.Label(control_frame, text="Server:").pack(side="left", padx=5)
        
        servers = self.server_repo.list_all()
        server_names = ["Global"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]
        
        server_var = tk.StringVar(value=server_names[0])
        
        # Create sort manager
        sort_manager = SortManager()
        sort_manager.current_sort_column = "mmr"
        sort_manager.current_sort_direction = "desc"
        
        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.update_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        )
    )
        server_menu.pack(side="left", padx=5)
        
        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        self.ranking_prev_btn = ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.update_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.ranking_prev_btn.pack(side="left", padx=5)
        
        self.ranking_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.ranking_page_label.pack(side="left", padx=5)
        
        self.ranking_next_btn = ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.update_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.ranking_next_btn.pack(side="left", padx=5)
        
        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.update_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        )
    ).pack(side="right", padx=5)
        
        # Create a frame with scrollbar for the table
        table_container = ttk.Frame(tab)
        table_container.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Ranking table
        ranking_tree = ttk.Treeview(
            table_container,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )
        
        # Configure columns with sorting
        def setup_column_sort(column, text, width, anchor="w"):
            ranking_tree.heading(column, text=text, command=lambda: self.sort_treeview(ranking_tree, column, sort_manager))
            ranking_tree.column(column, width=width, anchor=anchor)
        
        setup_column_sort("pos", "#", 50, "center")
        setup_column_sort("id", "ID", 50, "center")
        setup_column_sort("username", "Username", 150)
        setup_column_sort("mmr", "MMR", 70, "center")
        setup_column_sort("rank", "Rank", 100)
        setup_column_sort("win_ratio", "Win Ratio", 70, "center")
        
        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=ranking_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=ranking_tree.xview)
        ranking_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack everything
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        ranking_tree.pack(side="left", expand=True, fill="both")
        
        # Load initial data (global ranking)
        self.update_ranking(ranking_tree, sort_by="mmr", sort_dir="desc")
    
    def fill_mmr_tab(self, tab):
        """Fill MMR tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Player selector
        ttk.Label(control_frame, text="Player:").pack(side="left", padx=5)
        
        players = self.player_repo.list_all()[0]  # Get all players without pagination
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        player_var = tk.StringVar()
        if player_names:
            player_var.set(player_names[0])
        
        player_menu = ttk.OptionMenu(control_frame, player_var, *player_names)
        player_menu.pack(side="left", padx=5)
        
        # Buttons
        ttk.Button(
            control_frame,
            text="Modify MMR",
            command=lambda: self.modify_mmr_dialog(
                player_ids[player_names.index(player_var.get())] if player_names else 0
            )
        ).pack(side="left", padx=20)
        
        ttk.Button(
            control_frame,
            text="Reset MMR",
            command=lambda: self.reset_mmr(
                player_ids[player_names.index(player_var.get())] if player_names else 0
            )
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="View History",
            command=lambda: self.view_mmr_history(
                player_ids[player_names.index(player_var.get())] if player_names else 0
            )
        ).pack(side="left", padx=5)
    
    def modify_mmr_dialog(self, player_id: int):
        """Show dialog to modify a player's MMR"""
        if not player_id:
            messagebox.showwarning("Warning", "Select a player")
            return
        
        player = self.player_repo.get_by_id(player_id)
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Get current MMR
        ranking = player.rankings
        if not ranking:
            messagebox.showerror("Error", "Player does not have a ranking")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"Modify MMR for {player.username}")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Current information
        ttk.Label(dialog, text=f"Current MMR: {ranking.current_mmr}", font=("Helvetica", 12, "bold")).pack(pady=(20, 5))
        ttk.Label(dialog, text=f"Rank: {ranking.rank_label}").pack(pady=5)
        
        # MMR change
        ttk.Label(dialog, text="MMR Change:").pack(pady=(20, 5))
        change_var = tk.IntVar(value=0)
        change_spin = ValidatedSpinbox(dialog, from_=-500, to=500, increment=10, textvariable=change_var, width=10)
        change_spin.pack(pady=5)
        
        # Reason
        ttk.Label(dialog, text="Reason:").pack(pady=5)
        reason_var = tk.StringVar()
        reason_entry = ValidatedEntry(dialog, textvariable=reason_var, width=50, 
                                    validate_func=validate_required, error_msg="Reason is required")
        reason_entry.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save Changes",
            command=lambda: self.save_mmr_modification(
                player_id,
                change_var.get(),
                reason_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def save_mmr_modification(self, player_id: int, change: int, reason: str, dialog: tk.Toplevel):
        """Save MMR modification"""
        if not reason:
            messagebox.showerror("Error", "You must provide a reason for the change", parent=dialog)
            return
        
        try:
            # Validate change
            if not validate_integer(change):
                messagebox.showerror("Error", "MMR change must be a valid number", parent=dialog)
                return
                
            # Modify MMR
            new_mmr = self.mmr_service.modify_mmr_manual(player_id, int(change), reason)
            
            messagebox.showinfo("Success", f"MMR modified successfully. New MMR: {new_mmr}", parent=dialog)
            dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not modify MMR: {str(e)}")
    
    def reset_mmr(self, player_id: int):
        """Reset a player's MMR to 1000"""
        if not player_id:
            messagebox.showwarning("Warning", "Select a player")
            return
        
        player = self.player_repo.get_by_id(player_id)
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Confirm
        confirmation = messagebox.askyesno(
            "Confirm Reset",
            f"Are you sure you want to reset {player.username}'s MMR to 1000?"
        )
        
        if not confirmation:
            return
        
        try:
            # Reset MMR
            new_mmr = self.mmr_service.reset_mmr(player_id)
            
            messagebox.showinfo("Success", f"MMR reset successfully. New MMR: {new_mmr}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not reset MMR: {str(e)}")
    
    def view_mmr_history(self, player_id: int):
        """Show MMR history for a player"""
        if not player_id:
            messagebox.showwarning("Warning", "Select a player")
            return
        
        player = self.player_repo.get_by_id(player_id)
        if not player:
            messagebox.showerror("Error", "Player not found")
            return
        
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title(f"MMR History for {player.username}")
        dialog.geometry("800x500")
        dialog.transient(self)
        
        # Current information
        info_frame = ttk.Frame(dialog)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ranking = player.rankings
        if ranking:
            ttk.Label(info_frame, text=f"Current MMR: {ranking.current_mmr}", font=("Helvetica", 12, "bold")).pack(side="left", padx=20)
            ttk.Label(info_frame, text=f"Rank: {ranking.rank_label}", font=("Helvetica", 12)).pack(side="left", padx=20)
        
        # History table
        table_frame = ttk.Frame(dialog)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create treeview (table)
        history_tree = ttk.Treeview(
            table_frame,
            columns=("date", "before", "after", "change", "reason", "match"),
            show="headings"
        )
        
        # Configure columns
        history_tree.heading("date", text="Date")
        history_tree.heading("before", text="Previous MMR")
        history_tree.heading("after", text="New MMR")
        history_tree.heading("change", text="Change")
        history_tree.heading("reason", text="Reason")
        history_tree.heading("match", text="Match")
        
        history_tree.column("date", width=150)
        history_tree.column("before", width=80, anchor="center")
        history_tree.column("after", width=80, anchor="center")
        history_tree.column("change", width=80, anchor="center")
        history_tree.column("reason", width=300)
        history_tree.column("match", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        history_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Evolution graph
        try:
            dates, mmr = self.mmr_service.get_mmr_graph_data(player.id)
            
            if dates and mmr:
                graph_frame = ttk.Frame(dialog)
                graph_frame.pack(fill="x", padx=10, pady=10)
                
                fig, ax = plt.subplots(figsize=(10, 3))
                ax.plot(dates, mmr, marker='o', linestyle='-', color='blue')
                ax.set_title(f"MMR Evolution for {player.username}")
                ax.set_ylabel('MMR')
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Rotate x-axis labels
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                # Integrate graph in Tkinter
                canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
        except:
            # If there's an error with matplotlib, ignore
            pass
        
        # Close button
        ttk.Button(
            dialog,
            text="Close",
            command=dialog.destroy
        ).pack(pady=10)
    
    def show_player_interface(self):
        """Show player interface with improved button labeling"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        
        # Tabs with icons
        tab_profile = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_tutorial = ttk.Frame(notebook) 
        tab_ranking = ttk.Frame(notebook)
        tab_game = ttk.Frame(notebook)
        
        notebook.add(tab_profile, text="👤 My Profile")
        notebook.add(tab_matches, text="⚔ My Matches")
        notebook.add(tab_tutorial, text="🖥️ Tutorial") 
        notebook.add(tab_ranking, text="🏆 Ranking")
        notebook.add(tab_game, text="🎮 Play")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Top bar with improved buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - user info
        user_info_frame = ttk.Frame(top_frame)
        user_info_frame.pack(side="left")
        
        ttk.Label(
            user_info_frame, 
            text=f"👤 Connected as: {self.current_user.username}",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")
        
        # Right side - action buttons  
        action_buttons_frame = ttk.Frame(top_frame)
        action_buttons_frame.pack(side="right")
        
        # Refresh data button (renamed from "Update")
        refresh_btn = ttk.Button(
            action_buttons_frame,
            text="🔄 Refresh Data",
            command=self.sync_data
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Logout button
        logout_btn = ttk.Button(
            action_buttons_frame,
            text="🚪 Logout",
            command=self.logout
        )
        logout_btn.pack(side="left", padx=5)
        
        # Fill tabs
        self.fill_player_game_tab(tab_game)
        self.fill_player_profile_tab(tab_profile)
        self.fill_tutorial_tab(tab_tutorial)
        self.fill_player_matches_tab(tab_matches)
        self.fill_player_ranking_tab(tab_ranking)
    
    def fill_tutorial_tab(self, tab_tutorial):
        """Fill tutorial tab with interactive tutorial content"""
        # Datos del tutorial con texto mejorado y más detalles
        tutorial_data = [
            (
                "🎯 Paso 1: Objetivo del Juego", 
                "Ultimate Tic Tac Toe es un juego estratégico donde debes ganar 3 tableros pequeños en línea (horizontal, vertical o diagonal) para ganar la partida global. Cada tablero pequeño es un triqui tradicional de 3x3.",
                "sql/assets/tutorial1.png"
            ),
            (
                "📍 Paso 2: Cómo Hacer una Jugada", 
                "Haz clic en una celda vacía dentro del tablero resaltado. Tu jugada determina en qué tablero debe jugar tu oponente. Si haces clic en la celda superior-izquierda, envías al oponente al tablero superior-izquierdo.",
                "sql/assets/tutorial2.png"
            ),
            (
                "🏆 Paso 3: Ganar un Tablero", 
                "Para ganar un tablero pequeño, debes hacer una línea de 3 símbolos iguales (horizontal, vertical o diagonal). Una vez ganado, ese tablero cuenta como tuyo en el juego global.",
                "sql/assets/tutorial3.png"
            ),
            (
                "🎮 Paso 4: Estrategia Global", 
                "Piensa en dos niveles: local (ganar el tablero actual) y global (controlar la posición estratégica). Cada movimiento debe considerar ambos aspectos para maximizar tus oportunidades.",
                "sql/assets/tutorial4.png"
            ),
            (
                "🔄 Paso 5: Tableros Bloqueados", 
                "Si te envían a un tablero ya ganado o empatado, puedes elegir jugar en cualquier tablero disponible. ¡Aprovecha esta oportunidad estratégica!",
                "sql/assets/tutorial5.png"
            )
        ]
        

        # Inicializar listas para almacenar elementos del tutorial
        self.tutorial_images = []
        self.tutorial_titles = []
        self.tutorial_texts = []

        # Frame principal con estilo mejorado
        main_frame = tk.Frame(tab_tutorial, bg="#f8f9fa", pady=20)
        main_frame.pack(fill="both", expand=True)

        # Título principal con estilo
        title_frame = tk.Frame(main_frame, bg="#f8f9fa")
        title_frame.pack(fill="x", padx=20, pady=(0, 20))

        title_label = tk.Label(
            title_frame, 
            text="🎮 Tutorial Interactive: Ultimate Tic Tac Toe", 
            font=("Helvetica", 18, "bold"),
            bg="#f8f9fa", 
            fg="#2c3e50"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            title_frame,
            text="Aprende las reglas y estrategias paso a paso",
            font=("Helvetica", 12, "italic"),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        subtitle_label.pack()

        # Cargar y procesar imágenes del tutorial
        for title, text, img_path in tutorial_data:
            if os.path.exists(img_path):
                try:
                    img = tk.PhotoImage(file=img_path)
                    # Redimensionar imagen si es necesario
                    img = img.subsample(2, 2)
                    self.tutorial_images.append(img)
                    self.tutorial_titles.append(title)
                    self.tutorial_texts.append(text)
                except tk.TclError as e:
                    print(f"ERROR: No se pudo cargar la imagen '{img_path}': {e}")
                    # Agregar placeholder si la imagen falla
                    self.tutorial_images.append(None)
                    self.tutorial_titles.append(title)
                    self.tutorial_texts.append(text)
            else:
                print(f"WARNING: La imagen '{img_path}' no se encontró. Se usará placeholder.")
                # Agregar con placeholder
                self.tutorial_images.append(None)
                self.tutorial_titles.append(title)
                self.tutorial_texts.append(text)

        # Si no hay imágenes válidas, mostrar mensaje
        if not any(self.tutorial_images):
            error_label = tk.Label(
                main_frame,
                text="⚠️ Imágenes del tutorial no encontradas\nAsegúrate de que la carpeta 'assets' existe y contiene las imágenes tutorial1.png a tutorial6.png",
                font=("Helvetica", 12),
                bg="#f8f9fa",
                fg="#e74c3c",
                justify="center"
            )
            error_label.pack(expand=True)
            return

        # Índice actual del tutorial
        self.current_tutorial_index = 0

        # Frame para el contenido del tutorial
        content_frame = tk.Frame(main_frame, bg="#ffffff", relief="ridge", bd=2)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame para la imagen
        image_frame = tk.Frame(content_frame, bg="#ffffff", pady=20)
        image_frame.pack(fill="x")

        # Label para la imagen o placeholder
        if self.tutorial_images[0]:
            self.tutorial_image_label = tk.Label(image_frame, image=self.tutorial_images[0], bg="#ffffff")
        else:
            self.tutorial_image_label = tk.Label(
                image_frame, 
                text="🖼️ Imagen del Tutorial\n(No disponible)", 
                font=("Helvetica", 14),
                bg="#ecf0f1", 
                fg="#7f8c8d",
                width=30,
                height=10,
                relief="sunken",
                bd=1
            )
        self.tutorial_image_label.pack()

        # Frame para el texto
        text_frame = tk.Frame(content_frame, bg="#ffffff", pady=20)
        text_frame.pack(fill="both", expand=True, padx=20)

        # Título del paso actual
        self.tutorial_title_label = tk.Label(
            text_frame, 
            text=self.tutorial_titles[0], 
            font=("Helvetica", 16, "bold"),
            bg="#ffffff",
            fg="#2c3e50",
            wraplength=600
        )
        self.tutorial_title_label.pack(pady=(0, 15))

        # Texto explicativo
        self.tutorial_text_label = tk.Label(
            text_frame, 
            text=self.tutorial_texts[0], 
            wraplength=600, 
            justify="left",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#34495e",
            anchor="w"
        )
        self.tutorial_text_label.pack(fill="x")

        # Frame para navegación con estilo mejorado
        nav_frame = tk.Frame(main_frame, bg="#f8f9fa", pady=15)
        nav_frame.pack(fill="x", padx=20)

        # Botón anterior
        self.prev_tutorial_btn = tk.Button(
            nav_frame, 
            text="⟵ Anterior", 
            command=self.show_previous_tutorial,
            font=("Helvetica", 11, "bold"),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.prev_tutorial_btn.pack(side="left", padx=10)

        # Indicador de progreso
        self.progress_label = tk.Label(
            nav_frame,
            text=f"Paso 1 de {len(self.tutorial_titles)}",
            font=("Helvetica", 11, "bold"),
            bg="#f8f9fa",
            fg="#2c3e50"
        )
        self.progress_label.pack(side="left", expand=True)

        # Botón siguiente
        self.next_tutorial_btn = tk.Button(
            nav_frame, 
            text="Siguiente ⟶", 
            command=self.show_next_tutorial,
            font=("Helvetica", 11, "bold"),
            bg="#3498db",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        self.next_tutorial_btn.pack(side="right", padx=10)

        # Actualizar estado inicial de botones
        self.update_tutorial_buttons()
    
    def show_next_tutorial(self):
        """Show next tutorial step"""
        if self.current_tutorial_index < len(self.tutorial_images) - 1:
            self.current_tutorial_index += 1
            self.update_tutorial_display()
            self.update_tutorial_buttons()
        else:
            # Si ya estamos en el último paso y se hace clic, mostrar felicitaciones
            self.show_tutorial_completion_message()
    
    def show_previous_tutorial(self):
        """Show previous tutorial step"""
        if self.current_tutorial_index > 0:
            self.current_tutorial_index -= 1
            self.update_tutorial_display()
            self.update_tutorial_buttons()
    
    def show_tutorial_completion_message(self):
        """Show completion message in a floating window when tutorial ends"""
        # Crear ventana flotante de felicitaciones
        completion_window = tk.Toplevel()
        completion_window.title("🎉 Tutorial Completado")
        completion_window.geometry("400x250")
        completion_window.configure(bg="#f8f9fa")
        completion_window.resizable(False, False)

        # Hacer la ventana modal
        completion_window.transient(self.winfo_toplevel())
        completion_window.grab_set()

        # Centrar la ventana
        completion_window.update_idletasks()
        parent = completion_window.master
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (250 // 2)
        completion_window.geometry(f"400x250+{x}+{y}")

        # Header con icono de celebración
        header_frame = tk.Frame(completion_window, bg="#27ae60", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        celebration_label = tk.Label(
            header_frame,
            text="🎉",
            font=("Arial", 36),
            bg="#27ae60",
            fg="white"
        )
        celebration_label.pack(pady=10)

        title_label = tk.Label(
            header_frame,
            text="¡Tutorial Completado!",
            font=("Helvetica", 14, "bold"),
            bg="#27ae60",
            fg="white"
        )
        title_label.pack()

        # Contenido del mensaje
        content_frame = tk.Frame(completion_window, bg="#f8f9fa")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        message_label = tk.Label(
            content_frame,
            text="¡Felicitaciones! Has completado el tutorial.\n\nAhora ya conoces todas las reglas y estrategias\nbásicas del Ultimate Tic Tac Toe.\n\n¡Ve a la pestaña 'Play' para poner en práctica\nlo aprendido!",
            font=("Helvetica", 11),
            bg="#f8f9fa",
            fg="#2c3e50",
            justify="center"
        )
        message_label.pack(expand=True)

        # Botón para cerrar
        button_frame = tk.Frame(completion_window, bg="#f8f9fa")
        button_frame.pack(fill="x", pady=(0, 20))

        close_button = tk.Button(
            button_frame,
            text="✅ ¡Entendido!",
            command=completion_window.destroy,
            bg="#3498db",
            fg="white",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        close_button.pack()

        # Auto-cerrar después de 5 segundos (opcional)
        completion_window.after(8000, completion_window.destroy)
    
    def update_tutorial_display(self):
        """Update tutorial display with current step"""
        index = self.current_tutorial_index
        
        # Actualizar imagen
        if self.tutorial_images[index]:
            self.tutorial_image_label.configure(image=self.tutorial_images[index])
        else:
            self.tutorial_image_label.configure(
                image="",
                text="🖼️ Imagen del Tutorial\n(No disponible)",
                compound="none"
            )
        
        # Actualizar título y texto
        self.tutorial_title_label.configure(text=self.tutorial_titles[index])
        self.tutorial_text_label.configure(text=self.tutorial_texts[index])
        
        # Actualizar indicador de progreso
        self.progress_label.configure(
            text=f"Paso {index + 1} de {len(self.tutorial_titles)}"
        )
    
    def update_tutorial_buttons(self):
        """Update tutorial navigation buttons state"""
        # Botón anterior
        if self.current_tutorial_index == 0:
            self.prev_tutorial_btn.configure(state="disabled", bg="#bdc3c7")
        else:
            self.prev_tutorial_btn.configure(state="normal", bg="#95a5a6")

        # Botón siguiente
        if self.current_tutorial_index >= len(self.tutorial_images) - 1:
            self.next_tutorial_btn.configure(
                text="🎉 Finalizar Tutorial",  # CAMBIAR TEXTO
                bg="#27ae60",
                state="normal"  # MANTENER HABILITADO para mostrar ventana flotante
            )
        else:
            self.next_tutorial_btn.configure(
                text="Siguiente ⟶",
                bg="#3498db",
                state="normal"
            )

    
    def fill_player_game_tab(self, tab):
        """Llenar la pestaña de juego para jugadores normales"""
        # Frame principal
        main_frame = ttk.Frame(tab)
        main_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Título
        ttk.Label(main_frame, text="Iniciar Partida de Ultimate Tic Tac Toe", 
                 font=("Helvetica", 14, "bold")).pack(pady=(0, 20))
        
        # Selector de oponente
        players_frame = ttk.Frame(main_frame)
        players_frame.pack(pady=10)
        
        ttk.Label(players_frame, text="Jugador 2 (O):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        # Listar todos los jugadores excepto el actual
        players = [p for p in self.player_repo.list_all()[0] if p.id != self.current_user.id]
        player_names = [p.username for p in players]
        player_ids = [p.id for p in players]
        
        self.opponent_var = tk.StringVar()
        if player_names:
            self.opponent_var.set(player_names[0])
        
        self.opponent_menu = ttk.OptionMenu(players_frame, self.opponent_var, *player_names)
        self.opponent_menu.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Botón para iniciar el juego
        ttk.Button(
            main_frame,
            text="Iniciar Partida (Tú serás X)",
            command=self.start_player_game
        ).pack(pady=20)
        
    def fill_player_profile_tab(self, tab):
        """Fill player profile tab with improved layout"""
        # Get player data
        player = self.current_user
        stats = player.stats
        ranking = player.rankings

        # Main frame
        main_frame = ttk.Frame(tab, padding=20)
        main_frame.pack(expand=True, fill="both")

        # Create top section with profile info and stats side by side
        top_section = ttk.Frame(main_frame)
        top_section.pack(fill="x", pady=(0, 20))

        # LEFT SIDE: Basic information
        info_frame = ttk.Frame(top_section)
        info_frame.pack(side="left", fill="both", expand=True, padx=(0, 20))

        ttk.Label(info_frame, text="Profile Information", font=("Helvetica", 16, "bold")).pack(anchor="w", pady=(0, 15))

        # Basic data in a grid
        data_frame = ttk.Frame(info_frame)
        data_frame.pack(fill="x")

        # Profile information in two columns for better space usage
        ttk.Label(data_frame, text="Username:", anchor="e", font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")
        ttk.Label(data_frame, text=player.username, font=("Helvetica", 11)).grid(row=0, column=1, padx=(0, 30), pady=5, sticky="w")

        ttk.Label(data_frame, text="Level:", anchor="e", font=("Helvetica", 10, "bold")).grid(row=0, column=2, padx=(0, 10), pady=5, sticky="e")
        ttk.Label(data_frame, text=str(player.level), font=("Helvetica", 11)).grid(row=0, column=3, pady=5, sticky="w")

        ttk.Label(data_frame, text="Member since:", anchor="e", font=("Helvetica", 10, "bold")).grid(row=1, column=0, padx=(0, 10), pady=5, sticky="e")
        ttk.Label(data_frame, text=player.created_at.strftime("%Y-%m-%d"), font=("Helvetica", 11)).grid(row=1, column=1, padx=(0, 30), pady=5, sticky="w")

        ttk.Label(data_frame, text="Server:", anchor="e", font=("Helvetica", 10, "bold")).grid(row=2, column=0, padx=(0, 10), pady=5, sticky="e")
        server_text = f"{player.server.name} ({player.server.region})" if player.server else "N/A"
        ttk.Label(data_frame, text=server_text, font=("Helvetica", 11)).grid(row=2, column=1, columnspan=3, pady=5, sticky="w")

        # RIGHT SIDE: Statistics in a compact card
        stats_card = ttk.LabelFrame(top_section, text="Statistics", padding=15)
        stats_card.pack(side="right", padx=(10, 0))

        if stats:
            # Create a 3x2 grid for stats
            stats_grid = ttk.Frame(stats_card)
            stats_grid.pack()

            # Row 1
            ttk.Label(stats_grid, text="Games:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=str(stats.games_played), font=("Helvetica", 12, "bold"), foreground="#2c3e50").grid(row=0, column=1, padx=5, pady=2)

            ttk.Label(stats_grid, text="Wins:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=0, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=str(stats.games_won), font=("Helvetica", 12, "bold"), foreground="#27ae60").grid(row=0, column=3, padx=5, pady=2)

            # Row 2
            ttk.Label(stats_grid, text="Losses:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=1, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=str(stats.games_lost), font=("Helvetica", 12, "bold"), foreground="#e74c3c").grid(row=1, column=1, padx=5, pady=2)

            ttk.Label(stats_grid, text="Draws:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=1, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=str(stats.games_drawn), font=("Helvetica", 12, "bold"), foreground="#f39c12").grid(row=1, column=3, padx=5, pady=2)

            # Row 3 - Win ratio and streak (centered)
            separator = ttk.Separator(stats_grid, orient='horizontal')
            separator.grid(row=2, column=0, columnspan=4, sticky="ew", pady=5)

            ttk.Label(stats_grid, text="Win Ratio:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=3, column=0, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=f"{stats.win_ratio:.2f}", font=("Helvetica", 12, "bold"), foreground="#3498db").grid(row=3, column=1, padx=5, pady=2)

            ttk.Label(stats_grid, text="Max Streak:", font=("Helvetica", 9, "bold"), foreground="#555").grid(row=3, column=2, padx=5, pady=2, sticky="w")
            ttk.Label(stats_grid, text=str(stats.max_win_streak), font=("Helvetica", 12, "bold"), foreground="#9b59b6").grid(row=3, column=3, padx=5, pady=2)
        else:
            ttk.Label(stats_card, text="No statistics available", font=("Helvetica", 10), foreground="#7f8c8d").pack()

        # BOTTOM SECTION: Ranking (full width)
        ranking_section = ttk.Frame(main_frame)
        ranking_section.pack(fill="x", pady=(10, 20))

        # Ranking header and info in one row
        ranking_header = ttk.Frame(ranking_section)
        ranking_header.pack(fill="x", pady=(0, 10))

        ttk.Label(ranking_header, text="Ranking", font=("Helvetica", 14, "bold")).pack(side="left")

        if ranking:
            # Ranking info in the same row as header
            ranking_info = ttk.Frame(ranking_header)
            ranking_info.pack(side="right")

            ttk.Label(ranking_info, text="MMR:", font=("Helvetica", 10, "bold"), foreground="#555").pack(side="left", padx=(0, 5))
            ttk.Label(ranking_info, text=str(ranking.current_mmr), font=("Helvetica", 14, "bold"), foreground="#e74c3c").pack(side="left", padx=(0, 20))

            ttk.Label(ranking_info, text="Rank:", font=("Helvetica", 10, "bold"), foreground="#555").pack(side="left", padx=(0, 5))

            # Color code ranks
            rank_colors = {
                "Sin Clasificar": "#95a5a6",
                "Bronce": "#cd7f32",
                "Plata": "#c0c0c0", 
                "Oro": "#ffd700",
                "Platino": "#e5e4e2",
                "Diamante": "#b9f2ff",
                "Maestro": "#ff6b6b"
            }
            rank_color = rank_colors.get(ranking.rank_label, "#2c3e50")

            ttk.Label(ranking_info, text=ranking.rank_label, font=("Helvetica", 14, "bold"), foreground=rank_color).pack(side="left")

        # MMR Evolution Graph (if data exists)
        try:
            dates, mmr = self.mmr_service.get_mmr_graph_data(player.id)

            if dates and mmr and len(dates) > 1:  # Only show if there's meaningful data
                graph_frame = ttk.LabelFrame(ranking_section, text="MMR Evolution", padding=10)
                graph_frame.pack(fill="x", pady=(10, 0))

                fig, ax = plt.subplots(figsize=(10, 3))
                ax.plot(dates, mmr, marker='o', linestyle='-', color='#3498db', linewidth=2, markersize=4)
                ax.set_ylabel('MMR', fontweight='bold')
                ax.grid(True, linestyle='--', alpha=0.3)
                ax.set_facecolor('#f8f9fa')

                # Style improvements
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#bdc3c7')
                ax.spines['bottom'].set_color('#bdc3c7')

                # Rotate x-axis labels
                plt.xticks(rotation=45, fontsize=8)
                plt.yticks(fontsize=8)
                plt.tight_layout()

                # Integrate graph in Tkinter
                canvas = FigureCanvasTkAgg(fig, master=graph_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception as e:
            # If there's an error with matplotlib, show a message
            print(f"Could not load MMR graph: {e}")

        # Action Buttons (horizontal layout)
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(20, 0))

        # Left side buttons
        left_buttons = ttk.Frame(buttons_frame)
        left_buttons.pack(side="left")

        change_pw_btn = ttk.Button(
            left_buttons,
            text="Change Password",
            command=self.change_password_dialog
        )
        change_pw_btn.pack(side="left", padx=(0, 10))

        mmr_history_btn = ttk.Button(
            left_buttons,
            text="View MMR History",
            command=lambda: self.view_mmr_history(player.id)
        )
        mmr_history_btn.pack(side="left", padx=(0, 10))

        # Right side info
        info_label = ttk.Label(
            buttons_frame,
            text=f"Last login: {player.last_login.strftime('%Y-%m-%d %H:%M') if player.last_login else 'First time'}",
            font=("Helvetica", 9),
            foreground="#7f8c8d"
        )
        info_label.pack(side="right")
    
    
    def start_player_game(self):
        """Iniciar una nueva partida como jugador normal"""
        try:
            # Obtener el ID del oponente seleccionado
            players = [p for p in self.player_repo.list_all()[0] if p.id != self.current_user.id]
            player_names = [p.username for p in players]
            player_ids = [p.id for p in players]
            
            opponent_name = self.opponent_var.get()
            opponent_id = player_ids[player_names.index(opponent_name)]
            
            # Crear ventana para el juego
            game_window = tk.Toplevel(self)
            game_window.title(f"Ultimate Tic Tac Toe: {self.current_user.username} (X) vs {opponent_name} (O)")
            
            # Iniciar el juego con la sesión de base de datos y los IDs de los jugadores
            UltimateTicTacToe(game_window, self.session, self.current_user.id, opponent_id)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo iniciar el juego: {str(e)}")
            
    def change_password_dialog(self):
        """Show dialog to change current user's password"""
        # Create dialog window
        dialog = tk.Toplevel(self)
        dialog.title("Change Password")
        dialog.geometry("400x250")
        dialog.transient(self)
        dialog.grab_set()

        # Fields
        ttk.Label(dialog, text="Current Password:").pack(pady=(20, 5))
        current_pw_var = tk.StringVar()
        current_pw = ValidatedEntry(dialog, textvariable=current_pw_var, width=30, show="*", 
                                  validate_func=validate_required, error_msg="Current password is required")
        current_pw.pack(pady=5)

        ttk.Label(dialog, text="New Password:").pack(pady=5)
        new_pw_var = tk.StringVar()
        new_pw = ValidatedEntry(dialog, textvariable=new_pw_var, width=30, show="*", 
                              validate_func=validate_required, error_msg="New password is required")
        new_pw.pack(pady=5)

        ttk.Label(dialog, text="Confirm New Password:").pack(pady=5)
        confirm_pw_var = tk.StringVar()
        confirm_pw = ValidatedEntry(dialog, textvariable=confirm_pw_var, width=30, show="*", 
                                  validate_func=validate_required, error_msg="Password confirmation is required")
        confirm_pw.pack(pady=5)

        # Save button
        ttk.Button(
            dialog,
            text="Change Password",
            command=lambda: self.change_password(
                current_pw_var.get(),
                new_pw_var.get(),
                confirm_pw_var.get(),
                dialog
            )
        ).pack(pady=20)
    
    def change_password(self, current_pw: str, new_pw: str, confirm_pw: str, dialog: tk.Toplevel):
        """Change current user's password"""
        if not current_pw or not new_pw or not confirm_pw:
            messagebox.showerror("Error", "All fields are required", parent=dialog)
            return

        if new_pw != confirm_pw:
            messagebox.showerror("Error", "New passwords do not match", parent=dialog)
            return

        # Verify current password
        if not verify_password(current_pw, self.current_user.hashed_password):
            messagebox.showerror("Error", "Current password is incorrect", parent=dialog)
            return

        try:
            # Update password
            self.current_user.hashed_password = hash_password(new_pw)
            self.session.commit()

            messagebox.showinfo("Success", "Password updated successfully", parent=dialog)
            dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Could not update password: {str(e)}")
    
    def fill_player_matches_tab(self, tab):
        """Fill player matches tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Create sort manager
        sort_manager = SortManager()
        sort_manager.current_sort_column = "created_at"
        sort_manager.current_sort_direction = "desc"

        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        self.player_matches_prev_btn = ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.load_player_matches(
            matches_tree,
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.player_matches_prev_btn.pack(side="left", padx=5)
        
        self.player_matches_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.player_matches_page_label.pack(side="left", padx=5)
        
        self.player_matches_next_btn = ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.load_player_matches(
            matches_tree,
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.player_matches_next_btn.pack(side="left", padx=5)

        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.load_player_matches(
            matches_tree,
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        )
    ).pack(side="right", padx=5)

        # Create a frame with scrollbar for the table
        table_container = ttk.Frame(tab)
        table_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Matches table
        matches_tree = ttk.Treeview(
            table_container,
            columns=("id", "date", "opponent", "result", "duration", "moves"),
            show="headings"
        )

        # Configure columns with sorting
        def setup_column_sort(column, text, width, anchor="w"):
            matches_tree.heading(column, text=text, command=lambda: self.sort_treeview(matches_tree, column, sort_manager))
            matches_tree.column(column, width=width, anchor=anchor)
        
        setup_column_sort("id", "ID", 50, "center")
        setup_column_sort("date", "Date", 120)
        setup_column_sort("opponent", "Opponent", 120)
        setup_column_sort("result", "Result", 80, "center")
        setup_column_sort("duration", "Duration", 80, "center")
        setup_column_sort("moves", "Moves", 80, "center")

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=matches_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=matches_tree.xview)
        matches_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack everything
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        matches_tree.pack(side="left", expand=True, fill="both")

        # Context menu
        def show_context_menu(event):
            item = matches_tree.identify_row(event.y)
            if item:
                matches_tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)

        context_menu = tk.Menu(matches_tree, tearoff=0)
        context_menu.add_command(label="View Details", command=lambda: self.view_match_details(matches_tree))

        matches_tree.bind("<Button-3>", show_context_menu)

        # Load initial data
        self.load_player_matches(matches_tree, "created_at", "desc")
    
    def load_player_matches(self, tree, sort_by="created_at", sort_dir="desc"):
        """Load current player's matches into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)

        # Get matches with pagination
        matches, total = self.match_repo.list_by_player(
            self.current_user.id, 
            page=self.current_page, 
            per_page=self.items_per_page, 
            sort_by=sort_by, 
            sort_dir=sort_dir
        )

        for match in matches:  # Este bucle estaba mal indentado
            # Determine opponent and result
            opponent = ""
            result = ""

            for mp in match.match_players:
                if mp.player_id != self.current_user.id:
                    player = self.player_repo.get_by_id(mp.player_id)
                    if player:
                        opponent = player.username

                if mp.player_id == self.current_user.id:
                    if match.winner_id is None:
                        result = "Draw"
                    elif match.winner_id == self.current_user.id:
                        result = "Victory"
                    else:
                        result = "Defeat"

            # Calculate duration
            duration = format_duration(match.duration_seconds) if match.finished_at else "In progress"

            tree.insert(
                "",
                "end",
                values=(
                    match.id,
                    match.created_at.strftime("%Y-%m-%d %H:%M"),
                    opponent,
                    result,
                    duration,
                    match.total_moves
                )
            )

        # Update pagination buttons
        self.update_pagination_buttons()

    def fill_player_ranking_tab(self, tab):
        """Fill player ranking tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Server selector
        ttk.Label(control_frame, text="Server:").pack(side="left", padx=5)

        servers = self.server_repo.list_all()
        server_names = ["Global"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]

        server_var = tk.StringVar(value=server_names[0])
        
        # Create sort manager
        sort_manager = SortManager()
        sort_manager.current_sort_column = "mmr"
        sort_manager.current_sort_direction = "desc"

        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.update_player_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        )
    )
        server_menu.pack(side="left", padx=5)
        
        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        self.player_ranking_prev_btn = ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.update_player_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.player_ranking_prev_btn.pack(side="left", padx=5)
        
        self.player_ranking_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.player_ranking_page_label.pack(side="left", padx=5)
        
        self.player_ranking_next_btn = ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.update_player_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        ))
    )
        self.player_ranking_next_btn.pack(side="left", padx=5)

        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.update_player_ranking(
            ranking_tree,
            None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())],
            sort_manager.current_sort_column,
            sort_manager.current_sort_direction
        )
    ).pack(side="right", padx=5)

        # Create a frame with scrollbar for the table
        table_container = ttk.Frame(tab)
        table_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Ranking table
        ranking_tree = ttk.Treeview(
            table_container,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )

        # Configure columns with sorting
        def setup_column_sort(column, text, width, anchor="w"):
            ranking_tree.heading(column, text=text, command=lambda: self.sort_treeview(ranking_tree, column, sort_manager))
            ranking_tree.column(column, width=width, anchor=anchor)
        
        setup_column_sort("pos", "#", 50, "center")
        setup_column_sort("id", "ID", 50, "center")
        setup_column_sort("username", "Username", 150)
        setup_column_sort("mmr", "MMR", 70, "center")
        setup_column_sort("rank", "Rank", 100)
        setup_column_sort("win_ratio", "Win Ratio", 70, "center")

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=ranking_tree.yview)
        x_scrollbar = ttk.Scrollbar(table_container, orient="horizontal", command=ranking_tree.xview)
        ranking_tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

        # Pack everything
        y_scrollbar.pack(side="right", fill="y")
        x_scrollbar.pack(side="bottom", fill="x")
        ranking_tree.pack(side="left", expand=True, fill="both")

        # Load initial data (global ranking)
        self.update_player_ranking(ranking_tree, sort_by="mmr", sort_dir="desc")

    def update_player_ranking(self, tree, server_id=None, sort_by="mmr", sort_dir="desc"):
        """Update player ranking view"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)

        # Get ranking data
        if server_id:
            ranking_data, total = self.ranking_service.get_server_ranking(
                server_id, 
                page=self.current_page, 
                per_page=self.items_per_page,
                sort_by=sort_by,
                sort_dir=sort_dir)
        else:
            ranking_data, total = self.ranking_service.get_global_ranking(
                page=self.current_page, 
                per_page=self.items_per_page,
                sort_by=sort_by,
                sort_dir=sort_dir
            )

        # Insert into table
        for player_rank in ranking_data:
            # Highlight current user
            tags = ("current_user",) if player_rank["player_id"] == self.current_user.id else ()

            tree.insert(
                "",
                "end",
                values=(
                    player_rank["position"],
                    player_rank["player_id"],
                    player_rank["username"],
                    player_rank["mmr"],
                    player_rank["rank_label"],
                    f"{player_rank['win_ratio']:.2f}"
                ),
                tags=tags
            )

        # Configure tag for current user
        tree.tag_configure("current_user", background="#e6f7ff")

        # Update pagination buttons
        self.update_pagination_buttons()

    def update_ranking(self, tree, server_id=None, sort_by="mmr", sort_dir="desc"):
        """Update admin ranking view"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)

        # Get ranking data
        if server_id:
            ranking_data, total = self.ranking_service.get_server_ranking(
                server_id, 
                page=self.current_page, 
                per_page=self.items_per_page,
                sort_by=sort_by,
                sort_dir=sort_dir
            )
        else:
            ranking_data, total = self.ranking_service.get_global_ranking(
                page=self.current_page, 
                per_page=self.items_per_page,
                sort_by=sort_by,
                sort_dir=sort_dir
            )

        # Insert into table
        for player_rank in ranking_data:
            tree.insert(
                "",
                "end",
                values=(
                    player_rank["position"],
                    player_rank["player_id"],
                    player_rank["username"],
                    player_rank["mmr"],
                    player_rank["rank_label"],
                    f"{player_rank['win_ratio']:.2f}"
                )
            )

        # Update pagination buttons
        self.update_pagination_buttons()
        
    def sort_treeview(self, tree, column, sort_manager):
        """Sort treeview by column and update headers with sort indicators"""
        # Map treeview columns to database fields
        column_mapping = {
            "id": "id",
            "username": "username",
            "level": "level",
            "mmr": "mmr",
            "win_ratio": "win_ratio",
            "date": "created_at",
            "moves": "total_moves",
            "duration": "duration_seconds",
            "pos": "position"
        }
        
        # Toggle sort direction for this column
        sort_dir = sort_manager.toggle_sort(column)
        
        # Get the database field name for this column
        field = column_mapping.get(column, column)
        
        # Update all column headers to show sort direction
        for col in tree["columns"]:
            # Get current heading text without any sort indicators
            heading_text = tree.heading(col, "text").replace(" ↑", "").replace(" ↓", "")
            
            # Add sort indicator if this is the sorted column
            if col == column:
                heading_text += " ↑" if sort_dir == "asc" else " ↓"
            
            # Update the heading
            tree.heading(col, text=heading_text)
        
        # Determine which refresh method to call based on the tree
        # This is a bit of a hack, but it works to identify which table we're sorting
        if "player1" in tree["columns"]:  # Matches table
            self.load_matches(tree, field, sort_dir)
        elif "opponent" in tree["columns"]:  # Player matches table
            self.load_player_matches(tree, field, sort_dir)
        elif "rank" in tree["columns"] and "pos" in tree["columns"]:  # Ranking table
            if self.is_admin:
                self.update_ranking(tree, None, field, sort_dir)
            else:
                self.update_player_ranking(tree, None, field, sort_dir)
        else:  # Players table
            self.load_players(tree, field, sort_dir)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        # Crear la sesión de base de datos
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Iniciar la aplicación con la sesión
        app = App(session)
        app.mainloop()
        
    finally:
        # Cerrar la sesión al salir
        if 'session' in locals():
            session.close()