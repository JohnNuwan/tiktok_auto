#!/usr/bin/env python3
"""
Module simple pour traduire l'audio avec Whisper
Audio → Whisper → Texte français → Sauvegarde DB + fichier texte
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




class WhisperSimple:
    """Traduit l'audio avec Whisper et sauvegarde le texte"""
    
    def __init__(self):
        self.db = VideoDatabase()
        self.console = Console()
        
        # Configuration Whisper
        self.whisper_model = None
        
        # Initialiser Whisper
        if WHISPER_AVAILABLE:
            self._init_whisper()
    
    def _init_whisper(self):
        """Initialise Whisper"""
        try:
            print("🔄 Chargement du modèle Whisper...")
            self.whisper_model = whisper.load_model("base")  # ou "small", "medium", "large"
            print("✅ Whisper initialisé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Whisper: {e}")
            WHISPER_AVAILABLE = False
    

    
    def translate_audio_with_whisper(self, audio_path: str) -> Optional[str]:
        """Transcrit l'audio en anglais avec Whisper"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            print("❌ Whisper n'est pas disponible")
            return None
        
        try:
            print("🔄 Transcription avec Whisper...")
            
            # Transcrire en anglais avec Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                task="transcribe",
                language="en"
            )
            
            english_text = result["text"].strip()
            print(f"📝 Texte anglais transcrit: {english_text[:100]}...")
            
            return english_text
            
        except Exception as e:
            print(f"❌ Erreur Whisper: {e}")
            return None
    
    def save_whisper_text(self, video_id: str, translated_text: str) -> bool:
        """Sauvegarde le texte traduit par Whisper dans la base de données"""
        try:
            # Enregistrer dans la base de données
            self._save_whisper_record(video_id, translated_text)
            
            # Afficher les statistiques
            print(f"💾 Sauvegarde en base de données")
            print(f"✅ Texte Whisper sauvegardé avec succès")
            print(f"📊 Caractères: {len(translated_text)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def _save_whisper_record(self, video_id: str, translated_text: str):
        """Enregistre la traduction Whisper dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO whisper_texts 
                    (video_id, translated_text, created_at)
                    VALUES (?, ?, datetime('now'))
                ''', (video_id, translated_text))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement en DB: {e}")
    
    def process_audio_with_whisper(self, video_id: str) -> bool:
        """Traite un fichier audio avec Whisper"""
        try:
            # Chemin vers le fichier audio
            audio_path = Path("datas/audios_En") / f"{video_id}.mp3"
            
            if not audio_path.exists():
                print(f"❌ Fichier audio {audio_path} non trouvé")
                return False
            
            print(f"🎬 Traitement de l'audio: {video_id}")
            
            # 1. Traduire avec Whisper
            translated_text = self.translate_audio_with_whisper(str(audio_path))
            if not translated_text:
                return False
            
            # 2. Sauvegarder
            self.save_whisper_text(video_id, translated_text)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_id}: {e}")
            return False
    
    def get_audio_files_without_whisper(self) -> List[Dict]:
        """Récupère les fichiers audio qui n'ont pas de traduction Whisper"""
        try:
            # Dossier contenant les audios en anglais
            audio_dir = Path("datas/audios_En")
            
            if not audio_dir.exists():
                print(f"❌ Dossier {audio_dir} non trouvé")
                return []
            
            # Récupérer tous les fichiers .mp3
            audio_files = list(audio_dir.glob("*.mp3"))
            
            # Filtrer ceux qui n'ont pas de traduction Whisper
            videos_without_whisper = []
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                for audio_file in audio_files:
                    video_id = audio_file.stem  # Nom du fichier sans extension
                    
                    # Vérifier si une traduction Whisper existe déjà
                    cursor.execute('''
                        SELECT 1 FROM whisper_texts 
                        WHERE video_id = ?
                    ''', (video_id,))
                    
                    if not cursor.fetchone():
                        # Récupérer le titre de la vidéo depuis la base de données
                        cursor.execute('''
                            SELECT title FROM videos WHERE video_id = ?
                        ''', (video_id,))
                        
                        result = cursor.fetchone()
                        title = result[0] if result else video_id
                        
                        videos_without_whisper.append({
                            "video_id": video_id,
                            "title": title,
                            "audio_path": str(audio_file)
                        })
            
            return videos_without_whisper
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des fichiers audio: {e}")
            return []
    
    def batch_process_audios(self, limit: int = 20):
        """Traite plusieurs fichiers audio en lot"""
        audios = self.get_audio_files_without_whisper()
        
        if not audios:
            print("✅ Tous les fichiers audio ont déjà été traités avec Whisper")
            return
        
        # Limiter le nombre de fichiers pour les tests
        audios = audios[:limit]
        
        print(f"🎯 {len(audios)} fichiers audio à traiter avec Whisper")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎙️ Traitement Whisper...", total=len(audios))
            
            for audio in audios:
                progress.update(task, description=f"🎙️ Whisper: {audio['title'][:30]}...")
                
                success = self.process_audio_with_whisper(audio['video_id'])
                
                if not success:
                    print(f"❌ Échec du traitement pour {audio['video_id']}")
                
                progress.advance(task)
        
        print("✅ Traitement Whisper terminé")


def create_whisper_texts_table():
    """Crée la table whisper_texts"""
    db = VideoDatabase()
    
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table whisper_texts
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whisper_texts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Créer un index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_whisper_texts_video_id 
                ON whisper_texts (video_id)
            ''')
            
            conn.commit()
            print("✅ Table whisper_texts créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")


def main():
    """Interface principale du module WhisperSimple"""
    console = Console()
    
    if not WHISPER_AVAILABLE:
        console.print(Panel(
            "❌ Whisper n'est pas installé\n\n"
            "Installez-le avec:\n"
            "pip install openai-whisper",
            title="Installation requise",
            style="red"
        ))
        return
    
    # Créer la table si elle n'existe pas
    create_whisper_texts_table()
    
    translator = WhisperSimple()
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🎙️ Traducteur Whisper Simple",
            style="bold blue"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🎙️ Traiter un fichier audio spécifique avec Whisper")
        print("2. 🔄 Traitement en lot (limité à 20 fichiers)")
        print("3. 📊 Afficher les statistiques")
        print("4. 🔍 Lister les fichiers audio sans traduction Whisper")
        print("5. 📖 Lire une traduction Whisper existante")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            video_id = input("🎬 ID du fichier audio: ").strip()
            
            success = translator.process_audio_with_whisper(video_id)
            if success:
                print("✅ Traitement Whisper terminé avec succès")
            else:
                print("❌ Échec du traitement Whisper")
        elif choice == "2":
            limit = input("📊 Nombre max de fichiers (Enter pour 20): ").strip() or "20"
            translator.batch_process_audios(int(limit))
        elif choice == "3":
            # Statistiques
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM whisper_texts")
                count = cursor.fetchone()[0]
                print(f"📊 {count} traductions Whisper générées")
        elif choice == "4":
            audios = translator.get_audio_files_without_whisper()
            print(f"🔍 {len(audios)} fichiers audio sans traduction Whisper")
            for audio in audios[:10]:  # Afficher les 10 premiers
                print(f"  - {audio['video_id']}: {audio['title']}")
        elif choice == "5":
            video_id = input("🎬 ID du fichier audio: ").strip()
            
            # Lire la traduction depuis la DB
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT translated_text FROM whisper_texts 
                    WHERE video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if result:
                    translated_text = result[0]
                    print(f"📖 Traduction Whisper pour {video_id}:")
                    print(f"📝 Texte: {translated_text}")
                else:
                    print(f"❌ Aucune traduction Whisper trouvée pour {video_id}")
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main() 