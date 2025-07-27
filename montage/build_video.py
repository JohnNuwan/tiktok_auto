#!/usr/bin/env python3
"""
Module de montage automatique des vidéos
Génère des vidéos TikTok/YouTube Shorts avec FFmpeg
"""

import os
import sys
import json
import subprocess
import sqlite3
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from database.manager import VideoDatabase
from core.fond_downloader import FondDownloader
from config import Config

class VideoBuilder:
    """Constructeur de vidéos automatique"""

    def __init__(self, output_dir: str = "output/final_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        
        # Initialiser les composants
        self.db = VideoDatabase()
        self.fond_downloader = FondDownloader()
        
        # Configuration vidéo
        self.target_duration = 65  # 1 minute 05 secondes
        self.resolution = "1080x1920"  # Portrait pour TikTok/Shorts
        self.fps = 30
        
        # Vérifier FFmpeg
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """Vérifie que FFmpeg est installé"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode == 0:
                print("✅ FFmpeg détecté")
            else:
                print("❌ FFmpeg non trouvé")
        except Exception as e:
            print(f"❌ Erreur FFmpeg: {e}")
            print("💡 Installez FFmpeg: https://ffmpeg.org/download.html")

    def get_videos_with_tts(self) -> List[Dict]:
        """Récupère les vidéos qui ont un fichier TTS"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT DISTINCT v.video_id, v.title, v.theme, t.file_path as tts_path
                    FROM videos v
                    JOIN tts_files t ON v.video_id = t.video_id
                    WHERE t.language = 'fr'
                    AND NOT EXISTS (
                        SELECT 1 FROM video_builds vb
                        WHERE vb.video_id = v.video_id
                    )
                    ORDER BY v.created_at DESC
                """)
                
                columns = ["video_id", "title", "theme", "tts_path"]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des vidéos: {e}")
            return []

    def select_fonds_for_video(self, theme: str, duration_needed: int) -> List[str]:
        """Sélectionne des fonds vidéos pour une vidéo"""
        try:
            fonds = self.fond_downloader.get_available_fonds(theme)
            
            if not fonds:
                print(f"⚠️  Aucun fond disponible pour le thème '{theme}'")
                return []

            selected_fonds = []
            current_duration = 0
            
            # Sélectionner des fonds jusqu'à atteindre la durée nécessaire
            for fond in fonds:
                if current_duration >= duration_needed:
                    break
                    
                fond_path = Path(self.fond_downloader.output_dir) / theme / fond['filename']
                if fond_path.exists():
                    selected_fonds.append(str(fond_path))
                    current_duration += fond.get('duration', 30)  # Durée par défaut 30s
                    
                    # Mettre à jour le compteur d'utilisation
                    self.fond_downloader._update_usage_count(fond['id'])

            return selected_fonds

        except Exception as e:
            print(f"❌ Erreur lors de la sélection des fonds: {e}")
            return []

    def create_fond_sequence(self, fond_paths: List[str], output_path: str, duration: int):
        """Crée une séquence de fonds vidéos"""
        try:
            if not fond_paths:
                print("❌ Aucun fond vidéo fourni")
                return False

            # Créer un fichier de liste pour FFmpeg
            list_file = output_path.parent / "fond_list.txt"
            
            with open(list_file, "w") as f:
                for fond_path in fond_paths:
                    f.write(f"file '{fond_path}'\n")

            # Commande FFmpeg pour concaténer les fonds
            cmd = [
                "ffmpeg", "-y",  # Écraser le fichier de sortie
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                "-t", str(duration),  # Limiter à la durée cible
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Nettoyer le fichier temporaire
            list_file.unlink(missing_ok=True)

            if result.returncode == 0:
                print(f"✅ Séquence de fonds créée: {output_path}")
                return True
            else:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de la création de la séquence: {e}")
            return False

    def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str):
        """Ajoute l'audio TTS à la vidéo"""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",  # S'arrêter quand le plus court se termine
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print(f"✅ Audio ajouté: {output_path}")
                return True
            else:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de l'audio: {e}")
            return False

    def add_cta_to_video(self, video_path: str, output_path: str):
        """Ajoute un Call-To-Action à la fin de la vidéo"""
        try:
            # Créer un CTA simple avec FFmpeg
            cta_duration = 5  # 5 secondes
            
            # Générer un texte animé
            cta_text = "Abonne-toi pour plus de motivation !"
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"drawtext=text='{cta_text}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{self.target_duration-cta_duration},{self.target_duration})'",
                "-c:a", "copy",
                str(output_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                print(f"✅ CTA ajouté: {output_path}")
                return True
            else:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'ajout du CTA: {e}")
            return False

    def build_video(self, video_id: str, title: str, theme: str, tts_path: str) -> Optional[str]:
        """Construit une vidéo complète"""
        try:
            print(f"🎬 Construction de la vidéo: {title}")
            
            # Créer les chemins de fichiers temporaires
            temp_dir = self.output_dir / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            fond_sequence_path = temp_dir / f"{video_id}_fonds.mp4"
            audio_added_path = temp_dir / f"{video_id}_with_audio.mp4"
            final_path = self.output_dir / f"{video_id}_final.mp4"

            # 1. Sélectionner les fonds vidéos
            print("🎥 Sélection des fonds vidéos...")
            fond_paths = self.select_fonds_for_video(theme, self.target_duration)
            
            if not fond_paths:
                print("❌ Impossible de sélectionner des fonds vidéos")
                return None

            # 2. Créer la séquence de fonds
            print("🔗 Création de la séquence de fonds...")
            if not self.create_fond_sequence(fond_paths, fond_sequence_path, self.target_duration):
                return None

            # 3. Ajouter l'audio TTS
            print("🎵 Ajout de l'audio TTS...")
            if not self.add_audio_to_video(fond_sequence_path, tts_path, audio_added_path):
                return None

            # 4. Ajouter le CTA
            print("🎯 Ajout du Call-To-Action...")
            if not self.add_cta_to_video(audio_added_path, final_path):
                return None

            # 5. Nettoyer les fichiers temporaires
            fond_sequence_path.unlink(missing_ok=True)
            audio_added_path.unlink(missing_ok=True)

            # 6. Enregistrer dans la base de données
            self._save_build_record(video_id, str(final_path))

            print(f"✅ Vidéo construite avec succès: {final_path}")
            return str(final_path)

        except Exception as e:
            print(f"❌ Erreur lors de la construction de la vidéo: {e}")
            return None

    def _save_build_record(self, video_id: str, output_path: str):
        """Sauvegarde un enregistrement de construction"""
        try:
            import sqlite3
            # Créer la table si elle n'existe pas
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS video_builds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        output_path TEXT NOT NULL,
                        build_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        file_size INTEGER,
                        duration INTEGER,
                        FOREIGN KEY (video_id) REFERENCES videos (video_id)
                    )
                """)
                
                # Calculer la taille du fichier
                file_size = Path(output_path).stat().st_size if Path(output_path).exists() else 0
                
                # Insérer l'enregistrement
                cursor.execute("""
                    INSERT INTO video_builds (video_id, output_path, file_size, duration)
                    VALUES (?, ?, ?, ?)
                """, (video_id, output_path, file_size, self.target_duration))
                
                conn.commit()

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")

    def build_all_videos(self):
        """Construit toutes les vidéos disponibles"""
        videos = self.get_videos_with_tts()
        
        if not videos:
            print("✅ Toutes les vidéos ont déjà été construites")
            return

        print(f"🎬 {len(videos)} vidéos à construire")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎬 Construction en cours...", total=len(videos))

            for video in videos:
                progress.update(task, description=f"🎬 Construction: {video['title'][:30]}...")

                self.build_video(
                    video_id=video['video_id'],
                    title=video['title'],
                    theme=video['theme'] or 'motivation',  # Thème par défaut
                    tts_path=video['tts_path']
                )

                progress.advance(task)

        print("✅ Construction terminée")

    def get_build_statistics(self) -> Dict:
        """Récupère les statistiques de construction"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as total_builds,
                           SUM(file_size) as total_size,
                           AVG(file_size) as avg_size
                    FROM video_builds
                """)
                
                result = cursor.fetchone()
                if result:
                    return {
                        'total_builds': result[0],
                        'total_size': result[1] or 0,
                        'avg_size': result[2] or 0
                    }
                return {'total_builds': 0, 'total_size': 0, 'avg_size': 0}

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return {'total_builds': 0, 'total_size': 0, 'avg_size': 0}

    def display_build_statistics(self):
        """Affiche les statistiques de construction"""
        stats = self.get_build_statistics()
        
        table = Table(title="📊 Statistiques de construction")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("Vidéos construites", str(stats['total_builds']))
        table.add_row("Taille totale", f"{stats['total_size']/1024/1024:.2f} MB")
        table.add_row("Taille moyenne", f"{stats['avg_size']/1024/1024:.2f} MB")
        
        self.console.print(table)

def main():
    """Interface principale du constructeur de vidéos"""
    console = Console()

    builder = VideoBuilder()

    while True:
        console.print(Panel.fit(
            "🎬 Constructeur de Vidéos Automatique",
            style="bold blue"
        ))

        print("\nOptions disponibles:")
        print("1. 🎯 Construire une vidéo spécifique")
        print("2. 🔄 Construire toutes les vidéos")
        print("3. 📊 Afficher les statistiques")
        print("4. 🔍 Lister les vidéos à construire")
        print("0. ❌ Retour")

        choice = input("\n🎯 Votre choix (0-4): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            video_id = input("📹 ID de la vidéo: ").strip()
            if video_id:
                videos = builder.get_videos_with_tts()
                target_video = None
                
                for video in videos:
                    if video['video_id'] == video_id:
                        target_video = video
                        break
                
                if target_video:
                    builder.build_video(
                        video_id=target_video['video_id'],
                        title=target_video['title'],
                        theme=target_video['theme'] or 'motivation',
                        tts_path=target_video['tts_path']
                    )
                else:
                    print("❌ Vidéo non trouvée ou déjà construite")
        elif choice == "2":
            builder.build_all_videos()
        elif choice == "3":
            builder.display_build_statistics()
        elif choice == "4":
            videos = builder.get_videos_with_tts()
            if videos:
                print(f"\n🔍 {len(videos)} vidéos à construire:")
                for i, video in enumerate(videos[:10], 1):
                    print(f"{i}. {video['video_id']} - {video['title'][:50]}...")
                if len(videos) > 10:
                    print(f"... et {len(videos) - 10} autres")
            else:
                print("✅ Toutes les vidéos ont déjà été construites")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 