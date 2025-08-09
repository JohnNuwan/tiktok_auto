#!/usr/bin/env python3
"""
Script d'automatisation pour créer des vidéos TikTok complètes
Automatise tout le processus : téléchargement → transcription → traduction → TTS → montage
"""

import os
import sys
from pathlib import Path
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import VideoDatabase
from translation.whisper_simple import WhisperSimple
from translation.text_translator import TextTranslator
from translation.tts_simple import TTSSimple
from montage.video_builder import VideoBuilder

class AutoVideoCreator:
    """Automatise la création complète de vidéos TikTok"""
    
    def __init__(self):
        self.console = Console()
        self.db = VideoDatabase()
        
        # Initialiser les modules
        self.whisper = WhisperSimple()
        self.translator = TextTranslator()
        self.tts = TTSSimple()
        self.video_builder = VideoBuilder()
        
    def get_videos_without_processing(self):
        """Récupère les vidéos qui n'ont pas encore été traitées"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                
                # Vidéos sans transcription
                cursor.execute('''
                    SELECT v.video_id, v.title, v.duration
                    FROM videos v
                    LEFT JOIN whisper_texts wt ON v.video_id = wt.video_id
                    WHERE wt.video_id IS NULL
                    ORDER BY v.created_at DESC
                    LIMIT 10
                ''')
                
                return cursor.fetchall()
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return []
    
    def process_single_video(self, video_id: str, title: str):
        """Traite une vidéo complète : transcription → traduction → TTS → montage"""
        print(f"\n🎬 Traitement de: {title} ({video_id})")
        
        try:
            # Étape 1: Transcription Whisper
            print("🎤 Étape 1: Transcription Whisper...")
            success = self.whisper.process_single_audio(video_id)
            if not success:
                print(f"❌ Échec de la transcription pour {video_id}")
                return False
            
            # Étape 2: Traduction du texte
            print("🌍 Étape 2: Traduction du texte...")
            success = self.translator.process_single_translation(video_id)
            if not success:
                print(f"❌ Échec de la traduction pour {video_id}")
                return False
            
            # Étape 3: Génération TTS
            print("🎵 Étape 3: Génération audio TTS...")
            success = self.tts.process_single_tts(video_id)
            if not success:
                print(f"❌ Échec du TTS pour {video_id}")
                return False
            
            # Étape 4: Montage vidéo
            print("🎬 Étape 4: Montage vidéo...")
            videos_with_tts = self.video_builder.get_videos_with_tts()
            video_data = next((v for v in videos_with_tts if v['video_id'] == video_id), None)
            
            if video_data:
                success = self.video_builder.process_single_video(video_data)
                if success:
                    print(f"✅ Vidéo complète créée pour {video_id}")
                    return True
                else:
                    print(f"❌ Échec du montage pour {video_id}")
                    return False
            else:
                print(f"⚠️ Données vidéo non trouvées pour {video_id}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_id}: {e}")
            return False
    
    def batch_process_videos(self, limit: int = 5):
        """Traite plusieurs vidéos en lot"""
        videos = self.get_videos_without_processing()
        
        if not videos:
            print("✅ Toutes les vidéos ont déjà été traitées")
            return
        
        videos = videos[:limit]
        print(f"🎯 Traitement de {len(videos)} vidéos...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎬 Traitement des vidéos...", total=len(videos))
            
            success_count = 0
            for video_id, title, duration in videos:
                progress.update(task, description=f"🎬 {title[:30]}...")
                
                success = self.process_single_video(video_id, title)
                if success:
                    success_count += 1
                
                progress.advance(task)
        
        print(f"\n✅ Traitement terminé: {success_count}/{len(videos)} vidéos réussies")
    
    def show_status(self):
        """Affiche le statut actuel du système"""
        try:
            with self.db.connect() as conn:
                cursor = conn.cursor()
                
                # Statistiques générales
                cursor.execute("SELECT COUNT(*) FROM videos")
                total_videos = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM whisper_texts")
                transcribed = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM whisper_translations")
                translated = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tts_outputs")
                tts_generated = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM final_videos")
                final_videos = cursor.fetchone()[0]
                
                print("\n📊 Statut du système:")
                print(f"📹 Vidéos totales: {total_videos}")
                print(f"🎤 Transcrites: {transcribed}")
                print(f"🌍 Traduites: {translated}")
                print(f"🎵 TTS générés: {tts_generated}")
                print(f"🎬 Vidéos finales: {final_videos}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'affichage du statut: {e}")

def main():
    """Interface principale"""
    console = Console()
    
    console.print(Panel(
        "🎬 Créateur Automatique de Vidéos TikTok",
        style="bold magenta"
    ))
    
    creator = AutoVideoCreator()
    
    while True:
        print("\nOptions disponibles:")
        print("1. 🎬 Traiter des vidéos automatiquement")
        print("2. 📊 Afficher le statut")
        print("3. 🎯 Traiter une vidéo spécifique")
        print("0. ❌ Quitter")
        
        choice = input("\n🎯 Votre choix (0-3): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            limit = input("📊 Nombre de vidéos à traiter (Enter pour 5): ").strip() or "5"
            creator.batch_process_videos(int(limit))
        elif choice == "2":
            creator.show_status()
        elif choice == "3":
            video_id = input("🎬 ID de la vidéo: ").strip()
            if video_id:
                # Récupérer les infos de la vidéo
                try:
                    with creator.db.connect() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT title FROM videos WHERE video_id = ?", (video_id,))
                        result = cursor.fetchone()
                        if result:
                            creator.process_single_video(video_id, result[0])
                        else:
                            print(f"❌ Vidéo {video_id} non trouvée")
                except Exception as e:
                    print(f"❌ Erreur: {e}")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 