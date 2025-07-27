#!/usr/bin/env python3
"""
Pipeline complet TikTok_Auto
Automatise tout le processus de téléchargement à export final
"""

import argparse
import sys
from pathlib import Path
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Ajouter le répertoire courant au path
sys.path.insert(0, str(Path(__file__).parent))

from core.downloader import YouTubeDownloader
from translation.manager import TranslationManager
from translation.tts import TTSManager
from ollama.theme_classifier import ThemeClassifier
from core.fond_downloader import FondDownloader
from montage.build_video import VideoBuilder

class TikTokAutoPipeline:
    """Pipeline complet pour l'automatisation TikTok"""

    def __init__(self):
        self.console = Console()
        
        # Initialiser tous les composants
        self.downloader = YouTubeDownloader()
        self.translator = TranslationManager()
        self.tts_manager = TTSManager()
        self.theme_classifier = ThemeClassifier()
        self.fond_downloader = FondDownloader()
        self.video_builder = VideoBuilder()

    def run_full_pipeline(self, channel_url: str, theme_auto: bool = True):
        """Exécute le pipeline complet"""
        print(Panel.fit("🚀 Pipeline Complet TikTok_Auto", style="bold blue"))
        
        try:
            # Étape 1: Téléchargement des vidéos
            print("\n📥 Étape 1: Téléchargement des vidéos YouTube")
            self.downloader.download_channel(channel_url)
            
            # Étape 2: Classification thématique
            if theme_auto:
                print("\n🧠 Étape 2: Classification thématique automatique")
                self.theme_classifier.classify_all_videos()
            
            # Étape 3: Traduction des vidéos
            print("\n🌍 Étape 3: Traduction automatique")
            self.translator.batch_translate()
            
            # Étape 4: Synthèse vocale
            print("\n🎙️ Étape 4: Synthèse vocale")
            self.tts_manager.batch_convert_translations()
            
            # Étape 5: Téléchargement des fonds vidéos
            print("\n🎥 Étape 5: Téléchargement des fonds vidéos")
            self.fond_downloader.download_fonds_for_all_themes()
            
            # Étape 6: Montage automatique
            print("\n🎬 Étape 6: Montage automatique")
            self.video_builder.build_all_videos()
            
            print("\n✅ Pipeline terminé avec succès !")
            self.display_final_statistics()
            
        except Exception as e:
            print(f"\n❌ Erreur lors de l'exécution du pipeline: {e}")
            return False
        
        return True

    def run_step_by_step(self):
        """Exécute le pipeline étape par étape avec confirmation"""
        print(Panel.fit("🎯 Pipeline Étape par Étape", style="bold blue"))
        
        steps = [
            ("📥 Téléchargement YouTube", self._step_download),
            ("🧠 Classification thématique", self._step_classification),
            ("🌍 Traduction", self._step_translation),
            ("🎙️ Synthèse vocale", self._step_tts),
            ("🎥 Fonds vidéos", self._step_fonds),
            ("🎬 Montage", self._step_montage)
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n--- Étape {i}/{len(steps)}: {step_name} ---")
            
            choice = input(f"Exécuter cette étape ? (y/N/s pour sauter): ").strip().lower()
            
            if choice == 'y':
                try:
                    step_func()
                    print(f"✅ Étape {i} terminée")
                except Exception as e:
                    print(f"❌ Erreur à l'étape {i}: {e}")
                    continue_choice = input("Continuer le pipeline ? (y/N): ").strip().lower()
                    if continue_choice != 'y':
                        break
            elif choice == 's':
                print(f"⏭️  Étape {i} ignorée")
            else:
                print(f"⏭️  Étape {i} ignorée")

    def _step_download(self):
        """Étape de téléchargement"""
        channel_url = input("URL de la chaîne YouTube: ").strip()
        if channel_url:
            self.downloader.download_channel(channel_url)

    def _step_classification(self):
        """Étape de classification"""
        self.theme_classifier.classify_all_videos()

    def _step_translation(self):
        """Étape de traduction"""
        self.translator.batch_translate()

    def _step_tts(self):
        """Étape de synthèse vocale"""
        self.tts_manager.batch_convert_translations()

    def _step_fonds(self):
        """Étape de téléchargement des fonds"""
        self.fond_downloader.download_fonds_for_all_themes()

    def _step_montage(self):
        """Étape de montage"""
        self.video_builder.build_all_videos()

    def display_final_statistics(self):
        """Affiche les statistiques finales"""
        print("\n📊 Statistiques Finales")
        print("=" * 50)
        
        # Statistiques de la base de données
        from database.manager import VideoDatabase
        db = VideoDatabase()
        videos = db.list_all_videos()
        
        if videos:
            total_videos = len(videos)
            translated_count = sum(1 for v in videos if v[6] > 0)  # translation_count
            tts_count = sum(1 for v in videos if v[7] > 0)  # tts_count
            
            print(f"📹 Vidéos téléchargées: {total_videos}")
            print(f"🌍 Vidéos traduites: {translated_count}")
            print(f"🎙️ Vidéos avec TTS: {tts_count}")
        
        # Statistiques des fonds
        fonds = self.fond_downloader.get_available_fonds()
        print(f"🎥 Fonds vidéos disponibles: {len(fonds)}")
        
        # Statistiques de construction
        build_stats = self.video_builder.get_build_statistics()
        print(f"🎬 Vidéos construites: {build_stats['total_builds']}")
        
        print("\n🎉 Pipeline terminé ! Les vidéos sont dans output/final_videos/")

def main():
    """Point d'entrée principal"""
    parser = argparse.ArgumentParser(description="Pipeline complet TikTok_Auto")
    parser.add_argument("--channel", help="URL de la chaîne YouTube")
    parser.add_argument("--theme-auto", action="store_true", help="Classification thématique automatique")
    parser.add_argument("--step-by-step", action="store_true", help="Exécution étape par étape")
    
    args = parser.parse_args()
    
    pipeline = TikTokAutoPipeline()
    
    if args.step_by_step:
        pipeline.run_step_by_step()
    elif args.channel:
        pipeline.run_full_pipeline(args.channel, args.theme_auto)
    else:
        # Mode interactif
        print(Panel.fit("🎵 TikTok_Auto - Pipeline Complet", style="bold blue"))
        
        print("\nOptions disponibles:")
        print("1. 🚀 Pipeline complet automatique")
        print("2. 🎯 Pipeline étape par étape")
        print("3. 📊 Afficher les statistiques")
        print("0. ❌ Quitter")
        
        choice = input("\n🎯 Votre choix (0-3): ").strip()
        
        if choice == "1":
            channel_url = input("URL de la chaîne YouTube: ").strip()
            if channel_url:
                theme_auto = input("Classification thématique automatique ? (y/N): ").strip().lower() == 'y'
                pipeline.run_full_pipeline(channel_url, theme_auto)
            else:
                print("❌ URL requise")
        elif choice == "2":
            pipeline.run_step_by_step()
        elif choice == "3":
            pipeline.display_final_statistics()
        elif choice == "0":
            print("👋 Au revoir !")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 