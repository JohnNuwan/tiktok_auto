#!/usr/bin/env python3
"""
Module pour la transcription audio avec Whisper.
Fournit des fonctionnalités pour transcrire l'audio en texte et obtenir les timestamps.
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Import Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️  Whisper n'est pas installé. Installez-le avec: pip install openai-whisper")

class WhisperTranscriber:
    """Encapsule la logique de transcription avec Whisper."""
    
    def __init__(self):
        self.db = VideoDatabase()
        self.console = Console()
        self.whisper_model = self._init_whisper()
    
    def _init_whisper(self):
        """Initialise et charge le modèle Whisper."""
        if not WHISPER_AVAILABLE:
            return None
        try:
            print("🔄 Chargement du modèle Whisper (base)...")
            model = whisper.load_model("base")
            print("✅ Modèle Whisper chargé.")
            return model
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Whisper: {e}")
            return None

    def transcribe_with_timestamps(self, video_id: str) -> Optional[Dict]:
        """
        Transcrit l'audio d'une vidéo et retourne le résultat complet avec timestamps.
        C'est la méthode principale utilisée par l'interface graphique.
        """
        if not self.whisper_model:
            print("❌ Le modèle Whisper n'est pas disponible.")
            return None

        audio_path = Path(f"datas/audios_En/{video_id}.mp3")
        if not audio_path.exists():
            print(f"❌ Fichier audio non trouvé pour la transcription : {audio_path}")
            return None

        try:
            print(f"🔄 Transcription de {video_id} avec Whisper...")
            result = self.whisper_model.transcribe(str(audio_path), language="en")
            
            # Sauvegarder le texte brut dans la BDD pour compatibilité
            self._save_whisper_record(video_id, result['text'])
            print(f"✅ Transcription de {video_id} terminée.")
            
            return result # Retourne le dictionnaire complet
        except Exception as e:
            print(f"❌ Erreur durant la transcription Whisper pour {video_id}: {e}")
            return None

    def _save_whisper_record(self, video_id: str, text: str):
        """Enregistre le texte transcrit dans la base de données."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO whisper_texts (video_id, translated_text, created_at)
                    VALUES (?, ?, datetime('now'))
                ''', (video_id, text))
                conn.commit()
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde en DB: {e}")

    def get_videos_without_transcription(self) -> List[tuple]:
        """Récupère les vidéos qui n'ont pas encore de transcription Whisper."""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT v.video_id, v.title 
                    FROM videos v 
                    LEFT JOIN whisper_texts w ON v.video_id = w.video_id 
                    WHERE w.video_id IS NULL 
                    AND v.video_id IN (
                        SELECT DISTINCT video_id 
                        FROM videos 
                        WHERE video_id IN (
                            SELECT DISTINCT video_id 
                            FROM videos 
                            WHERE video_id IS NOT NULL
                        )
                    )
                    ORDER BY v.created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des vidéos: {e}")
            return []

    def process_single_audio(self, video_id: str) -> bool:
        """Traite un seul fichier audio pour la transcription."""
        try:
            result = self.transcribe_with_timestamps(video_id)
            return result is not None
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_id}: {e}")
            return False

    # --- Les méthodes ci-dessous sont conservées pour la compatibilité avec l'ancien CLI ---

    def get_audio_files_without_whisper(self) -> List[Dict]:
        # ... (code de la fonction existante)
        pass

    def batch_process_audios(self, limit: int = 20):
        # ... (code de la fonction existante)
        pass

# --- Fonctions pour l'ancien CLI --- #

def create_whisper_texts_table():
    # ... (code de la fonction existante)
    pass

def main():
    # ... (code de la fonction existante)
    pass

if __name__ == "__main__":
    main()
 