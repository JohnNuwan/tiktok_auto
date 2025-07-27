import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from rich import print
from rich.table import Table
from rich.console import Console

class VideoDatabase:
    def __init__(self, db_path: str = "videos.db"):
        self.db_path = db_path
        self.initialized = self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        try:
            # Créer le répertoire parent si nécessaire
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
            
            # Table des chaînes YouTube
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE NOT NULL,
                    channel_name TEXT NOT NULL,
                    channel_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des vidéos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    duration INTEGER,
                    upload_date DATE,
                    view_count INTEGER,
                    channel_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                )
            ''')
            
            # Table des fichiers audio
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    duration INTEGER,
                    format TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Table des fichiers de sous-titres
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtitle_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    is_auto_generated BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Table des traductions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    translation_method TEXT NOT NULL,
                    original_language TEXT NOT NULL,
                    segment_count INTEGER,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Table des fichiers TTS (synthèse vocale)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tts_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    language TEXT NOT NULL,
                    tts_engine TEXT NOT NULL,
                    voice_preset TEXT,
                    duration INTEGER,
                    file_size INTEGER,
                    source_vtt_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Table des vidéos construites
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS video_builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    output_path TEXT NOT NULL,
                    duration REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Index pour video_builds
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_video_builds_video_id 
                ON video_builds (video_id)
            ''')
            
            conn.commit()
            print("✅ Base de données initialisée avec succès")
        except sqlite3.OperationalError as e:
            print(f"❌ Erreur opérationnelle de la base de données: {e}")
            return False
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")
            return False
    
    def add_channel(self, channel_id: str, channel_name: str, channel_url: str) -> bool:
        """Ajoute une nouvelle chaîne à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO channels (channel_id, channel_name, channel_url)
                    VALUES (?, ?, ?)
                ''', (channel_id, channel_name, channel_url))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de la chaîne: {e}")
            return False
    
    def add_video(self, video_data: Dict[str, Any]) -> bool:
        """Ajoute une nouvelle vidéo à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO videos 
                    (video_id, title, description, duration, upload_date, view_count, channel_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_data.get('video_id'),
                    video_data.get('title'),
                    video_data.get('description'),
                    video_data.get('duration'),
                    video_data.get('upload_date'),
                    video_data.get('view_count'),
                    video_data.get('channel_id')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de la vidéo: {e}")
            return False
    
    def add_audio_file(self, video_id: str, file_path: str, file_size: Optional[int] = None, 
                      duration: Optional[int] = None, format: str = "mp3") -> bool:
        """Ajoute un fichier audio à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO audio_files 
                    (video_id, file_path, file_size, duration, format)
                    VALUES (?, ?, ?, ?, ?)
                ''', (video_id, file_path, file_size, duration, format))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du fichier audio: {e}")
            return False
    
    def add_subtitle_file(self, video_id: str, file_path: str, language: str, 
                         is_auto_generated: bool = False) -> bool:
        """Ajoute un fichier de sous-titres à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO subtitle_files 
                    (video_id, file_path, language, is_auto_generated)
                    VALUES (?, ?, ?, ?)
                ''', (video_id, file_path, language, is_auto_generated))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du fichier de sous-titres: {e}")
            return False
    
    def add_translation(self, video_id: str, file_path: str, language: str, 
                       translation_method: str, original_language: str = "en",
                       segment_count: Optional[int] = None, file_size: Optional[int] = None) -> bool:
        """Ajoute une traduction à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO translations 
                    (video_id, file_path, language, translation_method, original_language, segment_count, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (video_id, file_path, language, translation_method, original_language, segment_count, file_size))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de la traduction: {e}")
            return False
    
    def add_tts_file(self, video_id: str, file_path: str, language: str, 
                     tts_engine: str, voice_preset: Optional[str] = None,
                     duration: Optional[int] = None, file_size: Optional[int] = None,
                     source_vtt_path: Optional[str] = None) -> bool:
        """Ajoute un fichier TTS à la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO tts_files 
                    (video_id, file_path, language, tts_engine, voice_preset, duration, file_size, source_vtt_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (video_id, file_path, language, tts_engine, voice_preset, duration, file_size, source_vtt_path))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du fichier TTS: {e}")
            return False
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Récupère toutes les informations d'une vidéo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Informations de la vidéo
                cursor.execute('''
                    SELECT v.*, c.channel_name 
                    FROM videos v 
                    LEFT JOIN channels c ON v.channel_id = c.channel_id 
                    WHERE v.video_id = ?
                ''', (video_id,))
                video_row = cursor.fetchone()
                
                if not video_row:
                    return None
                
                # Fichiers audio
                cursor.execute('SELECT * FROM audio_files WHERE video_id = ?', (video_id,))
                audio_files = cursor.fetchall()
                
                # Fichiers de sous-titres
                cursor.execute('SELECT * FROM subtitle_files WHERE video_id = ?', (video_id,))
                subtitle_files = cursor.fetchall()
                
                # Traductions
                cursor.execute('SELECT * FROM translations WHERE video_id = ?', (video_id,))
                translations = cursor.fetchall()
                
                # Fichiers TTS
                cursor.execute('SELECT * FROM tts_files WHERE video_id = ?', (video_id,))
                tts_files = cursor.fetchall()
                
                return {
                    'video': video_row,
                    'audio_files': audio_files,
                    'subtitle_files': subtitle_files,
                    'translations': translations,
                    'tts_files': tts_files
                }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des informations: {e}")
            return None
    
    def list_all_videos(self) -> List[Dict[str, Any]]:
        """Liste toutes les vidéos avec leurs fichiers"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT v.video_id, v.title, v.duration, c.channel_name,
                           COUNT(DISTINCT af.id) as audio_count,
                           COUNT(DISTINCT sf.id) as subtitle_count,
                           COUNT(DISTINCT t.id) as translation_count,
                           COUNT(DISTINCT tf.id) as tts_count
                    FROM videos v
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    LEFT JOIN audio_files af ON v.video_id = af.video_id
                    LEFT JOIN subtitle_files sf ON v.video_id = sf.video_id
                    LEFT JOIN translations t ON v.video_id = t.video_id
                    LEFT JOIN tts_files tf ON v.video_id = tf.video_id
                    GROUP BY v.video_id
                    ORDER BY v.created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération de la liste: {e}")
            return []
    
    def display_videos_table(self):
        """Affiche un tableau formaté de toutes les vidéos"""
        videos = self.list_all_videos()
        
        table = Table(title="📹 Vidéos dans la base de données")
        table.add_column("ID Vidéo", style="cyan")
        table.add_column("Titre", style="green")
        table.add_column("Durée", style="yellow")
        table.add_column("Chaîne", style="blue")
        table.add_column("Audios", style="magenta")
        table.add_column("Sous-titres", style="red")
        table.add_column("Traductions", style="green")
        table.add_column("TTS", style="blue")
        
        for video in videos:
            duration_str = f"{video[2]//60}:{video[2]%60:02d}" if video[2] else "N/A"
            table.add_row(
                video[0],
                video[1][:50] + "..." if len(video[1]) > 50 else video[1],
                duration_str,
                video[3] or "N/A",
                str(video[4]),
                str(video[5]),
                str(video[6]),
                str(video[7])
            )
        
        console = Console()
        console.print(table)
    
    def search_videos(self, search_term: str) -> List[Dict[str, Any]]:
        """Recherche des vidéos par titre ou description"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT v.video_id, v.title, v.description, c.channel_name
                    FROM videos v
                    LEFT JOIN channels c ON v.channel_id = c.channel_id
                    WHERE v.title LIKE ? OR v.description LIKE ?
                    ORDER BY v.created_at DESC
                ''', (f'%{search_term}%', f'%{search_term}%'))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
            return []
    
    def get_video_files(self, video_id: str) -> Dict[str, List[str]]:
        """Récupère tous les fichiers associés à une vidéo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Fichiers audio
                cursor.execute('SELECT file_path FROM audio_files WHERE video_id = ?', (video_id,))
                audio_files = [row[0] for row in cursor.fetchall()]
                
                # Fichiers de sous-titres
                cursor.execute('SELECT file_path FROM subtitle_files WHERE video_id = ?', (video_id,))
                subtitle_files = [row[0] for row in cursor.fetchall()]
                
                return {
                    'audio_files': audio_files,
                    'subtitle_files': subtitle_files
                }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des fichiers: {e}")
            return {'audio_files': [], 'subtitle_files': []}
    
    def get_video_translations(self, video_id: str) -> List[Dict[str, Any]]:
        """Récupère toutes les traductions d'une vidéo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM translations 
                    WHERE video_id = ? 
                    ORDER BY language, translation_method
                ''', (video_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des traductions: {e}")
            return []
    
    def get_video_tts_files(self, video_id: str) -> List[Dict[str, Any]]:
        """Récupère tous les fichiers TTS d'une vidéo"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM tts_files 
                    WHERE video_id = ? 
                    ORDER BY language, tts_engine
                ''', (video_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des fichiers TTS: {e}")
            return []
    
    def get_tables(self) -> List[str]:
        """Récupère la liste des tables de la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des tables: {e}")
            return []
    
    def get_stats(self) -> Dict[str, int]:
        """Récupère les statistiques de la base de données"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Compter les vidéos
                cursor.execute("SELECT COUNT(*) FROM videos")
                videos_count = cursor.fetchone()[0]
                
                # Compter les chaînes
                cursor.execute("SELECT COUNT(*) FROM channels")
                channels_count = cursor.fetchone()[0]
                
                # Compter les traductions
                cursor.execute("SELECT COUNT(*) FROM translations")
                translation_count = cursor.fetchone()[0]
                
                # Compter les fichiers TTS
                cursor.execute("SELECT COUNT(*) FROM tts_files")
                tts_count = cursor.fetchone()[0]
                
                return {
                    'videos': videos_count,
                    'channels': channels_count,
                    'translations': translation_count,
                    'tts': tts_count
                }
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return {'videos': 0, 'channels': 0, 'translations': 0, 'tts': 0}
    
    def execute(self, query: str, params: tuple = ()) -> Any:
        """Exécute une requête SQL et retourne le résultat"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de la requête: {e}")
            return None

# Fonction utilitaire pour obtenir les métadonnées d'une vidéo
def get_video_metadata(video_id: str) -> Dict[str, Any]:
    """Récupère les métadonnées d'une vidéo via yt-dlp"""
    import subprocess
    import json
    
    try:
        command = [
            "yt-dlp",
            "--dump-json",
            f"https://www.youtube.com/watch?v={video_id}"
        ]
        
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        metadata = json.loads(result.stdout)
        
        return {
            'video_id': video_id,
            'title': metadata.get('title'),
            'description': metadata.get('description'),
            'duration': metadata.get('duration'),
            'upload_date': metadata.get('upload_date'),
            'view_count': metadata.get('view_count'),
            'channel_id': metadata.get('channel_id'),
            'channel_name': metadata.get('channel')
        }
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des métadonnées: {e}")
        return {}

if __name__ == "__main__":
    # Test de la base de données
    db = VideoDatabase()
    db.display_videos_table() 