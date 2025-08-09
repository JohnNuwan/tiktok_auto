#!/usr/bin/env python3
"""
Pipeline Automatique de Génération de Shorts
Orchestre tout le processus de création de shorts viraux
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from database.manager import VideoDatabase
from montage.shorts_generator import ShortsGenerator
from montage.viral_detector import ViralDetector
from montage.subtitle_generator import SubtitleGenerator
from translation.whisper_simple import WhisperTranscriber
from translation.text_translator import TextTranslator
from translation.tts_simple import TTSSimple

class AutoShortsPipeline:
    """Pipeline automatique pour la génération de shorts"""
    
    def __init__(self):
        self.console = Console()
        self.db = VideoDatabase()
        
        # Initialiser tous les modules
        self.shorts_generator = ShortsGenerator()
        self.viral_detector = ViralDetector()
        self.subtitle_generator = SubtitleGenerator()
        self.whisper = WhisperTranscriber()
        self.translator = TextTranslator()
        self.tts = TTSSimple()
        
        # Statistiques
        self.stats = {
            'videos_processed': 0,
            'shorts_created': 0,
            'errors': 0
        }
    
    def run_complete_pipeline(self, platform: str = 'tiktok', limit: int = 10):
        """Exécute le pipeline complet de génération de shorts"""
        self.console.print(Panel.fit("🎬 Pipeline Automatique de Shorts", style="bold blue"))
        
        try:
            # Étape 1: Récupérer les vidéos à traiter
            videos = self._get_videos_to_process(platform, limit)
            if not videos:
                self.console.print("✅ Toutes les vidéos ont déjà des shorts")
                return
            
            self.console.print(f"🎯 Traitement de {len(videos)} vidéos pour {platform}")
            
            # Étape 2: Traiter chaque vidéo
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                for video_id, title in videos:
                    task = progress.add_task(f"🎬 {title[:50]}...", total=1)
                    
                    try:
                        # Vérifier si la vidéo a tous les prérequis
                        if self._check_video_requirements(video_id):
                            # Générer le short
                            if self._generate_short_for_video(video_id, platform):
                                self.stats['shorts_created'] += 1
                                self.console.print(f"✅ Short créé pour {video_id}")
                            else:
                                self.stats['errors'] += 1
                                self.console.print(f"❌ Erreur lors de la création du short pour {video_id}")
                        else:
                            self.console.print(f"⚠️ Prérequis manquants pour {video_id}")
                            self.stats['errors'] += 1
                        
                        self.stats['videos_processed'] += 1
                        progress.update(task, completed=1)
                        
                    except Exception as e:
                        self.console.print(f"❌ Erreur lors du traitement de {video_id}: {e}")
                        self.stats['errors'] += 1
                        progress.update(task, completed=1)
            
            # Afficher les statistiques finales
            self._show_final_statistics()
            
        except Exception as e:
            self.console.print(f"❌ Erreur lors de l'exécution du pipeline: {e}")
    
    def _get_videos_to_process(self, platform: str, limit: int) -> List[tuple]:
        """Récupère les vidéos à traiter"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT v.video_id, v.title
                    FROM videos v
                    INNER JOIN tts_outputs tts ON v.video_id = tts.video_id
                    LEFT JOIN shorts s ON v.video_id = s.video_id AND s.platform = ?
                    WHERE s.video_id IS NULL
                    ORDER BY v.created_at DESC
                    LIMIT ?
                ''', (platform, limit))
                
                return cursor.fetchall()
                
        except Exception as e:
            self.console.print(f"❌ Erreur lors de la récupération des vidéos: {e}")
            return []
    
    def _check_video_requirements(self, video_id: str) -> bool:
        """Vérifie si une vidéo a tous les prérequis"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Vérifier la transcription
                cursor.execute('SELECT 1 FROM whisper_texts WHERE video_id = ?', (video_id,))
                if not cursor.fetchone():
                    return False
                
                # Vérifier la traduction
                cursor.execute('SELECT 1 FROM whisper_translations WHERE video_id = ?', (video_id,))
                if not cursor.fetchone():
                    return False
                
                # Vérifier le TTS
                cursor.execute('SELECT 1 FROM tts_outputs WHERE video_id = ?', (video_id,))
                if not cursor.fetchone():
                    return False
                
                return True
                
        except Exception as e:
            self.console.print(f"❌ Erreur lors de la vérification des prérequis: {e}")
            return False
    
    def _generate_short_for_video(self, video_id: str, platform: str) -> bool:
        """Génère un short pour une vidéo spécifique"""
        try:
            # Étape 1: Détecter les moments viraux
            viral_moments = self.viral_detector.analyze_viral_potential(video_id)
            if not viral_moments:
                self.console.print(f"⚠️ Aucun moment viral trouvé pour {video_id}")
                return False
            
            # Prendre le moment le plus viral
            best_moment = viral_moments[0]
            
            # Étape 2: Générer les sous-titres
            subtitle_path = self.subtitle_generator.generate_subtitles(
                best_moment['text'], 
                style=platform
            )
            
            if not subtitle_path:
                self.console.print(f"❌ Erreur lors de la génération des sous-titres pour {video_id}")
                return False
            
            # Étape 3: Créer le short
            short_path = self.shorts_generator.create_short(video_id, platform)
            
            if short_path:
                self.console.print(f"✅ Short créé: {short_path}")
                return True
            else:
                self.console.print(f"❌ Erreur lors de la création du short pour {video_id}")
                return False
                
        except Exception as e:
            self.console.print(f"❌ Erreur lors de la génération du short: {e}")
            return False
    
    def _show_final_statistics(self):
        """Affiche les statistiques finales"""
        self.console.print("\n" + "="*50)
        self.console.print("📊 Statistiques Finales")
        self.console.print("="*50)
        
        table = Table(show_header=True)
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("Vidéos traitées", str(self.stats['videos_processed']))
        table.add_row("Shorts créés", str(self.stats['shorts_created']))
        table.add_row("Erreurs", str(self.stats['errors']))
        table.add_row("Taux de succès", f"{(self.stats['shorts_created']/max(self.stats['videos_processed'], 1)*100):.1f}%")
        
        self.console.print(table)
    
    def list_created_shorts(self, platform: Optional[str] = None):
        """Liste les shorts créés"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute('''
                        SELECT s.video_id, s.title, s.platform, s.short_path, s.created_at
                        FROM shorts s
                        WHERE s.platform = ?
                        ORDER BY s.created_at DESC
                    ''', (platform,))
                else:
                    cursor.execute('''
                        SELECT s.video_id, s.title, s.platform, s.short_path, s.created_at
                        FROM shorts s
                        ORDER BY s.created_at DESC
                    ''')
                
                shorts = cursor.fetchall()
                
                if not shorts:
                    self.console.print("📭 Aucun short créé")
                    return
                
                table = Table(title="🎬 Shorts Créés")
                table.add_column("ID", style="cyan")
                table.add_column("Titre", style="green")
                table.add_column("Plateforme", style="yellow")
                table.add_column("Chemin", style="blue")
                table.add_column("Date", style="magenta")
                
                for short in shorts:
                    video_id, title, platform, short_path, created_at = short
                    table.add_row(
                        video_id,
                        title[:30] + "..." if len(title) > 30 else title,
                        platform,
                        os.path.basename(short_path),
                        created_at
                    )
                
                self.console.print(table)
                
        except Exception as e:
            self.console.print(f"❌ Erreur lors de la récupération des shorts: {e}")
    
    def cleanup_old_files(self, days: int = 7):
        """Nettoie les anciens fichiers temporaires"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            # Nettoyer les fichiers temporaires
            temp_dirs = [
                "datas/subtitles",
                "datas/shorts"
            ]
            
            files_removed = 0
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for file in os.listdir(temp_dir):
                        file_path = os.path.join(temp_dir, file)
                        if os.path.isfile(file_path):
                            file_time = os.path.getmtime(file_path)
                            if file_time < cutoff_time:
                                os.remove(file_path)
                                files_removed += 1
            
            self.console.print(f"🧹 {files_removed} fichiers temporaires supprimés")
            
        except Exception as e:
            self.console.print(f"❌ Erreur lors du nettoyage: {e}")

def main():
    """Interface CLI pour le pipeline automatique"""
    console = Console()
    title = Panel.fit("🎬 Pipeline Automatique de Shorts", style="bold blue")
    console.print(title)
    
    pipeline = AutoShortsPipeline()
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "🎬 Pipeline complet TikTok")
        table.add_row("2", "📺 Pipeline complet YouTube Shorts")
        table.add_row("3", "📱 Pipeline complet Instagram Reels")
        table.add_row("4", "📊 Lister les shorts créés")
        table.add_row("5", "🧹 Nettoyer les fichiers temporaires")
        table.add_row("0", "❌ Quitter")
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            limit = int(input("🎬 Nombre de vidéos (défaut: 10): ").strip() or "10")
            pipeline.run_complete_pipeline('tiktok', limit)
        elif choice == "2":
            limit = int(input("🎬 Nombre de vidéos (défaut: 10): ").strip() or "10")
            pipeline.run_complete_pipeline('youtube_shorts', limit)
        elif choice == "3":
            limit = int(input("🎬 Nombre de vidéos (défaut: 10): ").strip() or "10")
            pipeline.run_complete_pipeline('instagram_reels', limit)
        elif choice == "4":
            platform = input("🎬 Plateforme (Enter pour toutes): ").strip() or None
            pipeline.list_created_shorts(platform)
        elif choice == "5":
            days = int(input("🧹 Jours (défaut: 7): ").strip() or "7")
            pipeline.cleanup_old_files(days)
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 