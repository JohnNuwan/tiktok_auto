#!/usr/bin/env python3
"""
Pipeline d'automatisation complet pour TikTok_Auto
Intègre toutes les fonctionnalités : téléchargement → classification → traduction → TTS → montage
"""

import os
import sys
from pathlib import Path
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import VideoDatabase
from core.downloader import download_all_channel_audios
from ollama.theme_classifier import ThemeClassifier
from translation.whisper_simple import WhisperSimple
from translation.text_translator import TextTranslator
from translation.tts_simple import TTSSimple
from montage.video_builder import VideoBuilder

class CompletePipeline:
    """Pipeline complet d'automatisation TikTok"""
    
    def __init__(self):
        self.console = Console()
        self.db = VideoDatabase()
        
        # Initialiser tous les modules
        self.classifier = ThemeClassifier()
        self.whisper = WhisperSimple()
        self.translator = TextTranslator()
        self.tts = TTSSimple()
        self.video_builder = VideoBuilder()
        
    def download_channel(self, channel_url: str):
        """Étape 1: Téléchargement d'une chaîne YouTube"""
        print(f"\n📺 Étape 1: Téléchargement de la chaîne")
        print(f"🔗 URL: {channel_url}")
        
        try:
            download_all_channel_audios(channel_url)
            print("✅ Téléchargement terminé")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement: {e}")
            return False
    
    def classify_videos(self, force_reclassify: bool = False):
        """Étape 2: Classification thématique des vidéos"""
        print(f"\n🧠 Étape 2: Classification thématique")
        
        try:
            self.classifier.classify_all_videos(force_reclassify=force_reclassify)
            print("✅ Classification terminée")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la classification: {e}")
            return False
    
    def transcribe_videos(self, limit: int = 10):
        """Étape 3: Transcription des vidéos avec Whisper"""
        print(f"\n🎤 Étape 3: Transcription Whisper")
        
        try:
            # Récupérer les vidéos sans transcription
            videos = self.whisper.get_videos_without_transcription()
            if not videos:
                print("✅ Toutes les vidéos sont déjà transcrites")
                return True
            
            videos = videos[:limit]
            print(f"🎯 Transcription de {len(videos)} vidéos...")
            
            success_count = 0
            for video_id, title in videos:
                print(f"🎤 Transcription: {title[:50]}...")
                if self.whisper.process_single_audio(video_id):
                    success_count += 1
            
            print(f"✅ Transcription terminée: {success_count}/{len(videos)} réussies")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la transcription: {e}")
            return False
    
    def translate_videos(self, limit: int = 10):
        """Étape 4: Traduction des textes"""
        print(f"\n🌍 Étape 4: Traduction des textes")
        
        try:
            # Récupérer les vidéos sans traduction
            videos = self.translator.get_videos_without_translation()
            if not videos:
                print("✅ Toutes les vidéos sont déjà traduites")
                return True
            
            videos = videos[:limit]
            print(f"🎯 Traduction de {len(videos)} vidéos...")
            
            success_count = 0
            for video_id, title in videos:
                print(f"🌍 Traduction: {title[:50]}...")
                if self.translator.process_single_translation(video_id):
                    success_count += 1
            
            print(f"✅ Traduction terminée: {success_count}/{len(videos)} réussies")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la traduction: {e}")
            return False
    
    def generate_tts(self, limit: int = 10):
        """Étape 5: Génération audio TTS"""
        print(f"\n🎵 Étape 5: Génération audio TTS")
        
        try:
            # Récupérer les vidéos sans TTS
            videos = self.tts.get_videos_without_tts()
            if not videos:
                print("✅ Toutes les vidéos ont déjà un TTS")
                return True
            
            videos = videos[:limit]
            print(f"🎯 Génération TTS pour {len(videos)} vidéos...")
            
            success_count = 0
            for video_id, title in videos:
                print(f"🎵 TTS: {title[:50]}...")
                if self.tts.process_single_tts(video_id):
                    success_count += 1
            
            print(f"✅ Génération TTS terminée: {success_count}/{len(videos)} réussies")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la génération TTS: {e}")
            return False
    
    def build_videos(self, limit: int = 10):
        """Étape 6: Montage des vidéos finales"""
        print(f"\n🎬 Étape 6: Montage des vidéos")
        
        try:
            # Récupérer les vidéos avec TTS pour montage
            videos = self.video_builder.get_videos_with_tts()
            if not videos:
                print("❌ Aucune vidéo avec TTS trouvée")
                return False
            
            videos = videos[:limit]
            print(f"🎯 Montage de {len(videos)} vidéos...")
            
            success_count = 0
            for video_data in videos:
                video_id = video_data['video_id']
                title = video_data['title']
                print(f"🎬 Montage: {title[:50]}...")
                if self.video_builder.process_single_video(video_data):
                    success_count += 1
            
            print(f"✅ Montage terminé: {success_count}/{len(videos)} réussies")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du montage: {e}")
            return False
    
    def run_complete_pipeline(self, channel_url: str, limit: int = 10):
        """Exécute le pipeline complet"""
        print(Panel.fit("🚀 Pipeline Complet TikTok_Auto", style="bold blue"))
        
        steps = [
            ("📺 Téléchargement", lambda: self.download_channel(channel_url)),
            ("🧠 Classification", lambda: self.classify_videos()),
            ("🎤 Transcription", lambda: self.transcribe_videos(limit)),
            ("🌍 Traduction", lambda: self.translate_videos(limit)),
            ("🎵 TTS", lambda: self.generate_tts(limit)),
            ("🎬 Montage", lambda: self.build_videos(limit))
        ]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🚀 Pipeline en cours...", total=len(steps))
            
            for step_name, step_func in steps:
                progress.update(task, description=f"🚀 {step_name}...")
                
                try:
                    success = step_func()
                    if not success:
                        print(f"⚠️ Étape '{step_name}' a échoué, mais le pipeline continue...")
                except Exception as e:
                    print(f"❌ Erreur à l'étape '{step_name}': {e}")
                    continue_choice = input("Continuer le pipeline ? (y/N): ").strip().lower()
                    if continue_choice != 'y':
                        break
                
                progress.advance(task)
        
        print("\n🎉 Pipeline terminé !")
        self.show_final_statistics()
    
    def show_final_statistics(self):
        """Affiche les statistiques finales"""
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
                
                # Statistiques par thème
                cursor.execute("""
                    SELECT theme, COUNT(*) as count 
                    FROM videos 
                    WHERE theme IS NOT NULL 
                    GROUP BY theme 
                    ORDER BY count DESC
                """)
                theme_stats = cursor.fetchall()
                
                print("\n📊 Statistiques finales:")
                print(f"📹 Vidéos totales: {total_videos}")
                print(f"🎤 Transcrites: {transcribed}")
                print(f"🌍 Traduites: {translated}")
                print(f"🎵 TTS générés: {tts_generated}")
                print(f"🎬 Vidéos finales: {final_videos}")
                
                if theme_stats:
                    print("\n🎨 Répartition par thème:")
                    for theme, count in theme_stats:
                        print(f"  • {theme}: {count} vidéos")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'affichage des statistiques: {e}")

def main():
    """Interface principale"""
    console = Console()
    
    console.print(Panel.fit(
        "🎬 Pipeline Complet TikTok_Auto",
        style="bold magenta"
    ))
    
    pipeline = CompletePipeline()
    
    while True:
        print("\nOptions disponibles:")
        print("1. 🚀 Pipeline complet (nouvelle chaîne)")
        print("2. 🧠 Classification thématique uniquement")
        print("3. 🎤 Transcription uniquement")
        print("4. 🌍 Traduction uniquement")
        print("5. 🎵 TTS uniquement")
        print("6. 🎬 Montage uniquement")
        print("7. 📊 Afficher les statistiques")
        print("0. ❌ Quitter")
        
        choice = input("\n🎯 Votre choix (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            channel_url = input("📺 URL de la chaîne YouTube: ").strip()
            if channel_url:
                limit = input("📊 Nombre de vidéos à traiter (Enter pour 10): ").strip() or "10"
                pipeline.run_complete_pipeline(channel_url, int(limit))
            else:
                print("❌ URL requise")
        elif choice == "2":
            force = input("🔄 Forcer la reclassification ? (y/N): ").strip().lower() == 'y'
            pipeline.classify_videos(force_reclassify=force)
        elif choice == "3":
            limit = input("📊 Nombre de vidéos (Enter pour 10): ").strip() or "10"
            pipeline.transcribe_videos(int(limit))
        elif choice == "4":
            limit = input("📊 Nombre de vidéos (Enter pour 10): ").strip() or "10"
            pipeline.translate_videos(int(limit))
        elif choice == "5":
            limit = input("📊 Nombre de vidéos (Enter pour 10): ").strip() or "10"
            pipeline.generate_tts(int(limit))
        elif choice == "6":
            limit = input("📊 Nombre de vidéos (Enter pour 10): ").strip() or "10"
            pipeline.build_videos(int(limit))
        elif choice == "7":
            pipeline.show_final_statistics()
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 