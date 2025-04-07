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
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from typing import List, Dict, Optional, Union, Tuple

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "tictactoe_advanced")

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
        return self.session.query(Player).get(player_id)
    
    def get_by_username(self, username: str) -> Optional[Player]:
        """Get a player by username"""
        return self.session.query(Player).filter(Player.username == username).first()
    
    def search_by_username(self, username: str) -> List[Player]:
        """Search players by username (partial match)"""
        return self.session.query(Player).filter(Player.username.like(f"%{username}%")).all()
    
    def list_all(self, server_id: Optional[int] = None, page: int = 1, per_page: int = 20) -> Tuple[List[Player], int]:
        """List players, optionally filtered by server, with pagination"""
        query = self.session.query(Player)
        if server_id:
            query = query.filter(Player.server_id == server_id)
        
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
        return self.session.query(Server).get(server_id)
    
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
        return self.session.query(Match).get(match_id)
    
    def list_all(self, page: int = 1, per_page: int = 20) -> Tuple[List[Match], int]:
        """List matches with pagination"""
        query = self.session.query(Match).order_by(desc(Match.created_at))
        
        # Get total count for pagination
        total = query.count()
        
        # Apply pagination
        matches = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return matches, total
    
    def list_by_player(self, player_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Match], int]:
        """List matches for a player with pagination"""
        query = self.session.query(Match).join(MatchPlayer).filter(
            MatchPlayer.player_id == player_id
        ).order_by(desc(Match.created_at))
        
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
    
    def get_global_ranking(self, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """Get global player ranking ordered by MMR with pagination"""
        query = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        ).order_by(
            desc(PlayerRanking.current_mmr)
        )
        
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
    
    def get_server_ranking(self, server_id: int, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int]:
        """Get server player ranking ordered by MMR with pagination"""
        query = self.session.query(
            Player, PlayerRanking
        ).join(
            PlayerRanking
        ).filter(
            Player.server_id == server_id
        ).order_by(
            desc(PlayerRanking.current_mmr)
        )
        
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
        match = self.session.query(Match).get(match_id)
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
        
        # Update win ratio in rankings
        self.ranking_service.update_ranking_stats(p1_id)
        self.ranking_service.update_ranking_stats(p2_id)
        
        self.session.commit()
    
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


# =============================================================================
# GUI INTERFACE (TKINTER)
# =============================================================================

class App(tk.Tk):
    """Main application"""
    
    def __init__(self):
        super().__init__()
        
        # Initial configuration
        self.title("Ranking System - Advanced Tic Tac Toe")
        self.geometry("1200x800")
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
        username_entry = ttk.Entry(login_frame, width=30)
        username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="w", pady=5)
        password_entry = ttk.Entry(login_frame, width=30, show="*")
        password_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # Login button
        login_button = ttk.Button(
            login_frame, 
            text="Login", 
            command=lambda: self.login(username_entry.get(), password_entry.get())
        )
        login_button.grid(row=2, column=0, columnspan=2, pady=20)
        
        # Button to create server (for initialization only)
        ttk.Button(
            frame,
            text="Create Server",
            command=self.create_server_dialog
        ).pack(pady=10)
        
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
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Region:").pack(pady=5)
        region_entry = ttk.Entry(dialog, width=30)
        region_entry.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save",
            command=lambda: self.save_server(
                name_entry.get(),
                region_entry.get(),
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
        dialog.geometry("300x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Username:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
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
                username_entry.get(),
                password_entry.get(),
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
        """Show admin interface"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        
        # Tabs
        tab_players = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_ranking = ttk.Frame(notebook)
        tab_mmr = ttk.Frame(notebook)
        
        notebook.add(tab_players, text="Players")
        notebook.add(tab_matches, text="Matches")
        notebook.add(tab_ranking, text="Rankings")
        notebook.add(tab_mmr, text="MMR")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Top bar
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(
            top_frame, 
            text=f"Connected as: {self.current_user.username} (Admin)",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")
        
        # Sync button
        ttk.Button(
            top_frame,
            text="Update",
            command=self.sync_data
        ).pack(side="left", padx=20)
        
        ttk.Button(
            top_frame,
            text="Logout",
            command=self.logout
        ).pack(side="right")
        
        # Fill tabs
        self.fill_players_tab(tab_players)
        self.fill_matches_tab(tab_matches)
        self.fill_ranking_tab(tab_ranking)
        self.fill_mmr_tab(tab_mmr)
    
    def sync_data(self):
        """Synchronize data with the database"""
        try:
            # Refresh session
            self.session.expire_all()
            
            # Update all open tabs
            notebook = self.winfo_children()[0].winfo_children()[0]
            current_tab = notebook.index(notebook.select())
            
            if current_tab == 0:  # Players tab
                self.load_players(self.get_players_tree())
            elif current_tab == 1:  # Matches tab
                self.load_matches(self.get_matches_tree())
            elif current_tab == 2:  # Ranking tab
                self.update_ranking(self.get_ranking_tree())
            
            messagebox.showinfo("Success", "Data updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update data: {str(e)}")
    
    def get_players_tree(self):
        """Get the players treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[1].winfo_children()[1].winfo_children()[0]
    
    def get_matches_tree(self):
        """Get the matches treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[2].winfo_children()[1].winfo_children()[0]
    
    def get_ranking_tree(self):
        """Get the ranking treeview from the current interface"""
        return self.winfo_children()[0].winfo_children()[0].winfo_children()[3].winfo_children()[1].winfo_children()[0]
    
    def fill_players_tab(self, tab):
        """Fill players tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        # Search
        ttk.Label(control_frame, text="Search:").pack(side="left", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(control_frame, textvariable=search_var, width=30)
        search_entry.pack(side="left", padx=5)
        
        # Server filter
        ttk.Label(control_frame, text="Server:").pack(side="left", padx=(20, 5))
        
        servers = self.server_repo.list_all()
        server_names = ["All"] + [f"{s.name} ({s.region})" for s in servers]
        server_ids = [None] + [s.id for s in servers]
        
        server_var = tk.StringVar(value=server_names[0])
        server_menu = ttk.OptionMenu(control_frame, server_var, *server_names)
        server_menu.pack(side="left", padx=5)
        
        # Buttons
        ttk.Button(
            control_frame,
            text="Search",
            command=lambda: self.search_players(
                search_var.get(),
                None if server_var.get() == "All" else server_ids[server_names.index(server_var.get())],
                players_tree
            )
        ).pack(side="left", padx=20)
        
        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.load_players(players_tree))
        ).pack(side="left", padx=5)
        
        self.page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.page_label.pack(side="left", padx=5)
        
        ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.load_players(players_tree))
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Create Player",
            command=self.create_player_dialog
        ).pack(side="right", padx=5)
        
        # Players table
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create treeview (table)
        players_tree = ttk.Treeview(
            table_frame,
            columns=("id", "username", "level", "server", "games", "mmr", "rank", "win_ratio"),
            show="headings"
        )
        
        # Configure columns
        players_tree.heading("id", text="ID")
        players_tree.heading("username", text="Username")
        players_tree.heading("level", text="Level")
        players_tree.heading("server", text="Server")
        players_tree.heading("games", text="Games")
        players_tree.heading("mmr", text="MMR")
        players_tree.heading("rank", text="Rank")
        players_tree.heading("win_ratio", text="Win Ratio")
        
        players_tree.column("id", width=50, anchor="center")
        players_tree.column("username", width=150)
        players_tree.column("level", width=50, anchor="center")
        players_tree.column("server", width=150)
        players_tree.column("games", width=70, anchor="center")
        players_tree.column("mmr", width=70, anchor="center")
        players_tree.column("rank", width=100)
        players_tree.column("win_ratio", width=70, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=players_tree.yview)
        players_tree.configure(yscrollcommand=scrollbar.set)
        
        players_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
        # Context menu
        def show_context_menu(event):
            item = players_tree.identify_row(event.y)
            if item:
                players_tree.selection_set(item)
                context_menu.post(event.x_root, event.y_root)
        
        context_menu = tk.Menu(players_tree, tearoff=0)
        context_menu.add_command(label="View Details", command=lambda: self.view_player_details(players_tree))
        context_menu.add_command(label="Edit", command=lambda: self.edit_player_dialog(players_tree))
        context_menu.add_separator()
        context_menu.add_command(label="Delete", command=lambda: self.delete_player(players_tree))
        
        players_tree.bind("<Button-3>", show_context_menu)
        
        # Load initial data
        self.load_players(players_tree)
    
    def change_page(self, delta, callback):
        """Change current page and refresh data"""
        new_page = self.current_page + delta
        if new_page < 1:
            return

        # Obtener el total de items para validar
        notebook = self.winfo_children()[0].winfo_children()[0]
        current_tab = notebook.index(notebook.select())

        if current_tab == 0:  # Players tab
            _, total = self.player_repo.list_all(page=new_page, per_page=self.items_per_page)
        elif current_tab == 1:  # Matches tab
            _, total = self.match_repo.list_all(page=new_page, per_page=self.items_per_page)
        elif current_tab == 2:  # Ranking tab
            _, total = self.ranking_service.get_global_ranking(page=new_page, per_page=self.items_per_page)

        # Calcular máximo de páginas
        max_page = (total + self.items_per_page - 1) // self.items_per_page

        if new_page > max_page:
            return

        self.current_page = new_page

        # Actualizar etiqueta de página
        if current_tab == 0:
            self.page_label.config(text=f"Page {self.current_page}/{max_page}")
        elif current_tab == 1:
            self.matches_page_label.config(text=f"Page {self.current_page}/{max_page}")
        elif current_tab == 2:
            self.ranking_page_label.config(text=f"Page {self.current_page}/{max_page}")
        elif current_tab == 3 and hasattr(self, 'player_matches_page_label'):
            self.player_matches_page_label.config(text=f"Page {self.current_page}/{max_page}")
        elif current_tab == 4 and hasattr(self, 'player_ranking_page_label'):
            self.player_ranking_page_label.config(text=f"Page {self.current_page}/{max_page}")

        callback()

        # Deshabilitar botones si es necesario
        self.update_pagination_buttons(max_page)
    def load_players(self, tree):
        """Load player list into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Get players with pagination
        players, total = self.player_repo.list_all(page=self.current_page, per_page=self.items_per_page)
        
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
    
    def search_players(self, search: str, server_id: Optional[int], tree):
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
            players, total = self.player_repo.list_all(server_id=server_id, page=self.current_page, per_page=self.items_per_page)
        
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
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Password:").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Level:").pack(pady=5)
        level_var = tk.IntVar(value=1)
        level_entry = ttk.Spinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
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
                username_entry.get(),
                password_entry.get(),
                level_var.get(),
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
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        # Fields
        ttk.Label(dialog, text="Username:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog, width=30)
        username_entry.insert(0, player.username)
        username_entry.pack(pady=5)
        
        ttk.Label(dialog, text="New Password (leave blank to keep current):").pack(pady=5)
        password_entry = ttk.Entry(dialog, width=30, show="*")
        password_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Level:").pack(pady=5)
        level_var = tk.IntVar(value=player.level)
        level_entry = ttk.Spinbox(dialog, from_=1, to=99, textvariable=level_var, width=10)
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
        
        # Save button
        ttk.Button(
            dialog,
            text="Save Changes",
            command=lambda: self.save_player_edit(
                player.id,
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
    
    def save_player_edit(self, player_id: int, data: Dict, dialog: tk.Toplevel, tree):
        """Save player changes to the database"""
        try:
            # Update player
            result = self.player_repo.update(player_id, data)
            
            if not result:
                messagebox.showerror("Error", "Could not edit player", parent=dialog)
                return
            
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
        
        ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.load_matches(matches_tree))
        ).pack(side="left", padx=5)
        
        self.matches_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.matches_page_label.pack(side="left", padx=5)
        
        ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.load_matches(matches_tree))
        ).pack(side="left", padx=5)
        
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.load_matches(matches_tree)
        ).pack(side="right", padx=5)
        
        # Matches table
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create treeview (table)
        matches_tree = ttk.Treeview(
            table_frame,
            columns=("id", "date", "player1", "player2", "winner", "status", "duration", "moves"),
            show="headings"
        )
        
        # Configure columns
        matches_tree.heading("id", text="ID")
        matches_tree.heading("date", text="Date")
        matches_tree.heading("player1", text="Player 1")
        matches_tree.heading("player2", text="Player 2")
        matches_tree.heading("winner", text="Winner")
        matches_tree.heading("status", text="Status")
        matches_tree.heading("duration", text="Duration")
        matches_tree.heading("moves", text="Moves")
        
        matches_tree.column("id", width=50, anchor="center")
        matches_tree.column("date", width=120)
        matches_tree.column("player1", width=100)
        matches_tree.column("player2", width=100)
        matches_tree.column("winner", width=100)
        matches_tree.column("status", width=80, anchor="center")
        matches_tree.column("duration", width=80, anchor="center")
        matches_tree.column("moves", width=80, anchor="center")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=matches_tree.yview)
        matches_tree.configure(yscrollcommand=scrollbar.set)
        
        matches_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")
        
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
        self.load_matches(matches_tree)
    
    def load_matches(self, tree):
        """Load match list into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Get matches with pagination
        matches, total = self.match_repo.list_all(page=self.current_page, per_page=self.items_per_page)
        
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
        moves_spin = ttk.Spinbox(dialog, from_=4, to=100, textvariable=moves_var, width=10)
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
        sub_board_spin = ttk.Spinbox(dialog, from_=0, to=8, textvariable=sub_board_var, width=10)
        sub_board_spin.pack(pady=5)
        
        ttk.Label(dialog, text="Cell (0-8):").pack(pady=5)
        cell_var = tk.IntVar(value=0)
        cell_spin = ttk.Spinbox(dialog, from_=0, to=8, textvariable=cell_var, width=10)
        cell_spin.pack(pady=5)
        
        # Move time
        ttk.Label(dialog, text="Time (seconds):").pack(pady=5)
        time_var = tk.DoubleVar(value=2.0)
        time_spin = ttk.Spinbox(dialog, from_=0.1, to=60.0, increment=0.1, textvariable=time_var, width=10)
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
            # Register move
            move = self.match_repo.register_move(
                match_id, player_id, sub_board, cell, time_taken
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
        
        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.update_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        )
        server_menu.pack(side="left", padx=5)
        
        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.update_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            ))
        ).pack(side="left", padx=5)
        
        self.ranking_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.ranking_page_label.pack(side="left", padx=5)
        
        ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.update_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            ))
        ).pack(side="left", padx=5)
        
        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.update_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        ).pack(side="right", padx=5)
        
        # Ranking table
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Create treeview (table)
        ranking_tree = ttk.Treeview(
            table_frame,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )
        
        # Configure columns
        ranking_tree.heading("pos", text="#")
        ranking_tree.heading("id", text="ID")
        ranking_tree.heading("username", text="Username")
        ranking_tree.heading("mmr", text="MMR")
        ranking_tree.heading("rank", text="Rank")
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
        
        # Load initial data (global ranking)
        self.update_ranking(ranking_tree)
    
    def update_ranking(self, tree, server_id: Optional[int] = None):
        """Update ranking table with latest data"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)
        
        # Get ranking with pagination
        if server_id:
            ranking, total = self.ranking_service.get_server_ranking(server_id, page=self.current_page, per_page=self.items_per_page)
        else:
            ranking, total = self.ranking_service.get_global_ranking(page=self.current_page, per_page=self.items_per_page)
        
        # Insert data in table
        for player in ranking:
            tree.insert(
                "",
                "end",
                values=(
                    player["position"],
                    player["player_id"],
                    player["username"],
                    player["mmr"],
                    player["rank_label"],
                    f"{player['win_ratio']:.2f}"
                )
            )
    
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
        change_spin = ttk.Spinbox(dialog, from_=-500, to=500, increment=10, textvariable=change_var, width=10)
        change_spin.pack(pady=5)
        
        # Reason
        ttk.Label(dialog, text="Reason:").pack(pady=5)
        reason_entry = ttk.Entry(dialog, width=50)
        reason_entry.pack(pady=5)
        
        # Save button
        ttk.Button(
            dialog,
            text="Save Changes",
            command=lambda: self.save_mmr_modification(
                player_id,
                change_var.get(),
                reason_entry.get(),
                dialog
            )
        ).pack(pady=20)
    
    def save_mmr_modification(self, player_id: int, change: int, reason: str, dialog: tk.Toplevel):
        """Save MMR modification"""
        if not reason:
            messagebox.showerror("Error", "You must provide a reason for the change", parent=dialog)
            return
        
        try:
            # Modify MMR
            new_mmr = self.mmr_service.modify_mmr_manual(player_id, change, reason)
            
            messagebox.showinfo("Success", f"MMR modified successfully. New MMR: {new_mmr}", parent=dialog)
            dialog.destroy()
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not modify MMR: {str(e)}", parent=dialog)
    
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
        
        # Load data
        history, _ = self.mmr_service.get_mmr_history(player_id)
        
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
                    h.change_reason,
                    h.match_id if h.match_id else "-"
                )
            )
        
        # Evolution graph
        try:
            dates, mmr = self.mmr_service.get_mmr_graph_data(player_id)
            
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
        """Show player interface"""
        # Clear window
        for widget in self.winfo_children():
            widget.destroy()
        
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(expand=True, fill="both")
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(main_frame)
        
        # Tabs
        tab_profile = ttk.Frame(notebook)
        tab_matches = ttk.Frame(notebook)
        tab_ranking = ttk.Frame(notebook)
        
        notebook.add(tab_profile, text="My Profile")
        notebook.add(tab_matches, text="My Matches")
        notebook.add(tab_ranking, text="Ranking")
        
        notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Top bar
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(
            top_frame, 
            text=f"Connected as: {self.current_user.username}",
            font=("Helvetica", 10, "italic")
        ).pack(side="left")
        
        # Update button
        ttk.Button(
            top_frame,
            text="Update",
            command=self.sync_data
        ).pack(side="left", padx=20)
        
        ttk.Button(
            top_frame,
            text="Logout",
            command=self.logout
        ).pack(side="right")
        
        # Fill tabs
        self.fill_player_profile_tab(tab_profile)
        self.fill_player_matches_tab(tab_matches)
        self.fill_player_ranking_tab(tab_ranking)
    
    def fill_player_profile_tab(self, tab):
        """Fill player profile tab"""
        # Get player data
        player = self.current_user
        stats = player.stats
        ranking = player.rankings
        
        # Main frame
        main_frame = ttk.Frame(tab, padding=20)
        main_frame.pack(expand=True, fill="both")
        
        # Basic information
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="x", pady=10)
        
        ttk.Label(info_frame, text="Profile Information", font=("Helvetica", 16, "bold")).pack(anchor="w")
        
        # Basic data
        data_frame = ttk.Frame(main_frame)
        data_frame.pack(fill="x", pady=10)
        
        ttk.Label(data_frame, text="Username:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(data_frame, text=player.username, font=("Helvetica", 11, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(data_frame, text="Level:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(data_frame, text=str(player.level)).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(data_frame, text="Member since:", anchor="e").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(data_frame, text=player.created_at.strftime("%Y-%m-%d")).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(data_frame, text="Server:", anchor="e").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        ttk.Label(data_frame, text=f"{player.server.name} ({player.server.region})" if player.server else "N/A").grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Statistics
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(20, 10))
        
        ttk.Label(stats_frame, text="Statistics", font=("Helvetica", 14, "bold")).pack(anchor="w")
        
        if stats:
            stats_data = ttk.Frame(stats_frame)
            stats_data.pack(fill="x", pady=5)
            
            # First row (summary)
            ttk.Label(stats_data, text="Games played:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_played)).grid(row=0, column=1, padx=5, pady=5, sticky="w")
          
            ttk.Label(stats_data, text="Wins:", anchor="e").grid(row=0, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_won)).grid(row=0, column=3, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_data, text="Losses:", anchor="e").grid(row=0, column=4, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.games_lost)).grid(row=0, column=5, padx=5, pady=5, sticky="w")
            
            # Second row
            ttk.Label(stats_data, text="Win ratio:", anchor="e").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(stats_data, text=f"{stats.win_ratio:.2f}").grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            ttk.Label(stats_data, text="Max win streak:", anchor="e").grid(row=1, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(stats_data, text=str(stats.max_win_streak)).grid(row=1, column=3, padx=5, pady=5, sticky="w")
      
        # Ranking
        ranking_frame = ttk.Frame(main_frame)
        ranking_frame.pack(fill="x", pady=(20, 10))

        ttk.Label(ranking_frame, text="Ranking", font=("Helvetica", 14, "bold")).pack(anchor="w")

        if ranking:
            ranking_data = ttk.Frame(ranking_frame)
            ranking_data.pack(fill="x", pady=5)

            ttk.Label(ranking_data, text="MMR:", anchor="e").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            ttk.Label(ranking_data, text=str(ranking.current_mmr), font=("Helvetica", 12, "bold")).grid(row=0, column=1, padx=5, pady=5, sticky="w")

            ttk.Label(ranking_data, text="Rank:", anchor="e").grid(row=0, column=2, padx=(20, 5), pady=5, sticky="e")
            ttk.Label(ranking_data, text=ranking.rank_label, font=("Helvetica", 12, "bold")).grid(row=0, column=3, padx=5, pady=5, sticky="w")

            # Try to show MMR evolution graph
            try:
                dates, mmr = self.mmr_service.get_mmr_graph_data(player.id)

                if dates and mmr:
                    graph_frame = ttk.Frame(ranking_frame)
                    graph_frame.pack(fill="x", pady=10)

                    fig, ax = plt.subplots(figsize=(8, 3))
                    ax.plot(dates, mmr, marker='o', linestyle='-', color='blue')
                    ax.set_title("Your MMR Evolution")
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
              
        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill="x", pady=(30, 10))

        ttk.Button(
            buttons_frame,
            text="Change Password",
            command=self.change_password_dialog
        ).pack(side="left", padx=10)

        ttk.Button(
            buttons_frame,
            text="View MMR History",
            command=lambda: self.view_mmr_history(player.id)
        ).pack(side="left", padx=10)
    
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
        current_pw = ttk.Entry(dialog, width=30, show="*")
        current_pw.pack(pady=5)

        ttk.Label(dialog, text="New Password:").pack(pady=5)
        new_pw = ttk.Entry(dialog, width=30, show="*")
        new_pw.pack(pady=5)

        ttk.Label(dialog, text="Confirm New Password:").pack(pady=5)
        confirm_pw = ttk.Entry(dialog, width=30, show="*")
        confirm_pw.pack(pady=5)

        # Save button
        ttk.Button(
            dialog,
            text="Change Password",
            command=lambda: self.change_password(
                current_pw.get(),
                new_pw.get(),
                confirm_pw.get(),
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
            messagebox.showerror("Error", f"Could not update password: {str(e)}", parent=dialog)
    
    def fill_player_matches_tab(self, tab):
        """Fill player matches tab"""
        # Top frame with controls
        control_frame = ttk.Frame(tab)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.load_player_matches(matches_tree))
        ).pack(side="left", padx=5)
        
        self.player_matches_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.player_matches_page_label.pack(side="left", padx=5)
        
        ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.load_player_matches(matches_tree))
        ).pack(side="left", padx=5)

        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.load_player_matches(matches_tree)
        ).pack(side="right", padx=5)

        # Matches table
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Create treeview (table)
        matches_tree = ttk.Treeview(
            table_frame,
            columns=("id", "date", "opponent", "result", "duration", "moves"),
            show="headings"
        )

        # Configure columns
        matches_tree.heading("id", text="ID")
        matches_tree.heading("date", text="Date")
        matches_tree.heading("opponent", text="Opponent")
        matches_tree.heading("result", text="Result")
        matches_tree.heading("duration", text="Duration")
        matches_tree.heading("moves", text="Moves")

        matches_tree.column("id", width=50, anchor="center")
        matches_tree.column("date", width=120)
        matches_tree.column("opponent", width=120)
        matches_tree.column("result", width=80, anchor="center")
        matches_tree.column("duration", width=80, anchor="center")
        matches_tree.column("moves", width=80, anchor="center")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=matches_tree.yview)
        matches_tree.configure(yscrollcommand=scrollbar.set)

        matches_tree.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

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
        self.load_player_matches(matches_tree)
    
    def load_player_matches(self, tree):
        """Load current player's matches into treeview"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)

        # Get matches with pagination
        matches, total = self.match_repo.list_by_player(self.current_user.id, page=self.current_page, per_page=self.items_per_page)

        for match in matches:
            # Determine opponent and result
            opponent = ""
            result = ""

            for mp in match.match_players:
                if mp.player_id != self.current_user.id:
                    opponent = self.player_repo.get_by_id(mp.player_id).username

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

        server_menu = ttk.OptionMenu(
            control_frame, 
            server_var, 
            *server_names,
            command=lambda _: self.update_player_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        )
        server_menu.pack(side="left", padx=5)

        # Pagination controls
        pagination_frame = ttk.Frame(control_frame)
        pagination_frame.pack(side="left", padx=20)
        
        ttk.Button(
            pagination_frame,
            text="Previous",
            command=lambda: self.change_page(-1, lambda: self.update_player_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            ))
        ).pack(side="left", padx=5)
        
        self.player_ranking_page_label = ttk.Label(pagination_frame, text=f"Page {self.current_page}")
        self.player_ranking_page_label.pack(side="left", padx=5)
        
        ttk.Button(
            pagination_frame,
            text="Next",
            command=lambda: self.change_page(1, lambda: self.update_player_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            ))
        ).pack(side="left", padx=5)

        # Update button
        ttk.Button(
            control_frame,
            text="Update",
            command=lambda: self.update_player_ranking(
                ranking_tree,
                None if server_var.get() == "Global" else server_ids[server_names.index(server_var.get())]
            )
        ).pack(side="right", padx=5)

        # Ranking table
        table_frame = ttk.Frame(tab)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # Create treeview (table)
        ranking_tree = ttk.Treeview(
            table_frame,
            columns=("pos", "id", "username", "mmr", "rank", "win_ratio"),
            show="headings"
        )

        # Configure columns
        ranking_tree.heading("pos", text="#")
        ranking_tree.heading("id", text="ID")
        ranking_tree.heading("username", text="Username")
        ranking_tree.heading("mmr", text="MMR")
        ranking_tree.heading("rank", text="Rank")
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

        # Load initial data (global ranking)
        self.update_player_ranking(ranking_tree)
    
    def update_player_ranking(self, tree, server_id: Optional[int] = None):
        """Update ranking table with latest data"""
        # Clear table
        for item in tree.get_children():
            tree.delete(item)

        # Get ranking with pagination
        if server_id:
            ranking, total = self.ranking_service.get_server_ranking(server_id, page=self.current_page, per_page=self.items_per_page)
        else:
            ranking, total = self.ranking_service.get_global_ranking(page=self.current_page, per_page=self.items_per_page)

        # Highlight current user
        current_user_id = self.current_user.id

        # Insert data in table
        for player in ranking:
            values = (
                player["position"],
                player["player_id"],
                player["username"],
                player["mmr"],
                player["rank_label"],
                f"{player['win_ratio']:.2f}"
            )

            item_id = tree.insert("", "end", values=values)

            # Highlight current user
            if player["player_id"] == current_user_id:
                tree.item(item_id, tags=("current_user",))

        # Configure style for current user
        tree.tag_configure("current_user", background=COLORS["accent"], foreground="white")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = App()
    app.mainloop()