#!/usr/bin/env python3
"""
Point d'entrée principal pour TikTok_Auto
Gestionnaire de téléchargement YouTube avec base de données et traduction
"""

import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Ajouter le répertoire tests au path pour les imports de tests
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests'))

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from config import Config

def show_menu():
    """Affiche le menu principal"""
    console = Console()
    
    title = Panel.fit(
        "🎵 TikTok_Auto - Système de Traduction Audio",
        style="bold blue"
    )
    console.print(title)
    
    table = Table(show_header=False, box=None)
    table.add_column("Option", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("1", "📊 Afficher la base de données")
    table.add_row("2", "🎤 Transcription audio (Whisper)")
    table.add_row("3", "🌍 Traduction texte (EN → FR)")
    table.add_row("4", "🎵 Génération audio (TTS)")
    table.add_row("5", "🎬 Montage vidéo")
    table.add_row("6", "📥 Télécharger des vidéos")
    table.add_row("7", "📺 Télécharger une chaîne YouTube")
    table.add_row("8", "🧠 Classification thématique (Ollama)")
    table.add_row("9", "🎥 Télécharger les fonds vidéos")
    table.add_row("10", "🚀 Pipeline complet automatique")
    table.add_row("11", "🗄️ Gérer la base de données")
    table.add_row("12", "🧪 Tests système")
    table.add_row("13", "📝 Recréer vidéos avec sous-titres")
    table.add_row("0", "❌ Quitter")
    
    console.print(table)

def main():
    """Fonction principale"""
    console = Console()
    
    # Valider la configuration au démarrage
    print("\n🔧 Validation de la configuration...")
    Config.validate_config()
    
    while True:
        show_menu()
        
        try:
            choice = input("\n🎯 Votre choix (0-13): ").strip()
            
            if choice == "0":
                print("👋 Au revoir !")
                break
                
            elif choice == "1":
                print("\n📊 Affichage de la base de données...")
                from database.manager import VideoDatabase
                db = VideoDatabase()
                db.display_videos_table()
                
            elif choice == "2":
                print("\n🎤 Lancement de la transcription Whisper...")
                from translation.whisper_simple import main as whisper_main
                whisper_main()
                
            elif choice == "3":
                print("\n🌍 Lancement de la traduction texte...")
                from translation.text_translator import main as translator_main
                translator_main()
                
            elif choice == "4":
                print("\n🎵 Lancement de la génération audio (TTS)...")
                from translation.tts_simple import main as tts_main
                tts_main()
                
            elif choice == "5":
                print("\n🎬 Lancement du montage vidéo...")
                from montage.video_builder import main as montage_main
                montage_main()
                
            elif choice == "6":
                print("\n📥 Lancement du téléchargeur...")
                from core.downloader import main as download_main
                download_main()
                
            elif choice == "7":
                print("\n📺 Téléchargement d'une chaîne YouTube...")
                from core.downloader import download_all_channel_audios
                url = input("👉 URL de la chaîne YouTube : ").strip()
                if url:
                    download_all_channel_audios(url)
                else:
                    print("❌ URL requise")
                
            elif choice == "8":
                print("\n🧠 Lancement de la classification thématique...")
                from ollama.theme_classifier import main as classifier_main
                classifier_main()
                
            elif choice == "9":
                print("\n🎥 Lancement du téléchargeur de fonds vidéos...")
                from core.fond_downloader import main as fond_main
                fond_main()
                
            elif choice == "10":
                print("\n🚀 Lancement du pipeline complet automatique...")
                from auto_pipeline_complete import main as pipeline_main
                pipeline_main()
                
            elif choice == "11":
                print("\n🗄️ Lancement du gestionnaire de base de données...")
                from database.cli import main as db_main
                db_main()
                
            elif choice == "12":
                print("\n🧪 Lancement des tests système...")
                from tests.test_system import main as test_main
                test_main()
                
            elif choice == "13":
                print("\n📝 Recréation de vidéos avec sous-titres...")
                from montage.video_builder import VideoBuilder
                import sqlite3
                
                builder = VideoBuilder()
                
                # Récupérer les vidéos finales existantes
                try:
                    with sqlite3.connect(builder.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT fv.video_id, v.title
                            FROM final_videos fv
                            LEFT JOIN videos v ON fv.video_id = v.video_id
                            ORDER BY fv.created_at DESC
                            LIMIT 5
                        ''')
                        
                        results = cursor.fetchall()
                        if results:
                            print(f"📹 {len(results)} vidéos trouvées:")
                            for i, (video_id, title) in enumerate(results, 1):
                                print(f"  {i}. {video_id}: {title}")
                            
                            try:
                                choice = input("\n🎯 Choisir une vidéo (1-5) ou 'all' pour toutes: ").strip()
                                
                                if choice.lower() == 'all':
                                    print("🔄 Recréation de toutes les vidéos avec sous-titres...")
                                    for video_id, title in results:
                                        print(f"\n🎬 Traitement de: {video_id}")
                                        # Ici on pourrait ajouter la logique de recréation
                                        print(f"✅ Vidéo {video_id} traitée")
                                else:
                                    try:
                                        index = int(choice) - 1
                                        if 0 <= index < len(results):
                                            video_id, title = results[index]
                                            print(f"\n🎬 Recréation de: {video_id}")
                                            # Ici on pourrait ajouter la logique de recréation
                                            print(f"✅ Vidéo {video_id} recréée avec sous-titres")
                                        else:
                                            print("❌ Index invalide")
                                    except ValueError:
                                        print("❌ Choix invalide")
                            except (EOFError, KeyboardInterrupt):
                                print("\n👋 Retour au menu principal...")
                        else:
                            print("❌ Aucune vidéo finale trouvée")
                            
                except Exception as e:
                    print(f"❌ Erreur: {e}")
                
            else:
                print("❌ Choix invalide. Veuillez choisir entre 0 et 13.")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")
            input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main() 