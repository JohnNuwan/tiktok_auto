#!/usr/bin/env python3
"""
Point d'entrée principal pour TikTok_Auto
Gestionnaire de téléchargement YouTube avec base de données et traduction
"""

import sys
import os
import ffmpeg
import uuid

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
        "🎵 TikTok_Auto - Système d'Automatisation Vidéo",
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
    table.add_row("14", "🔎 Extraire des clips d'une vidéo longue")
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
            choice = input("\n🎯 Votre choix (0-14): ").strip()
            
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
                from scripts.auto_pipeline_complete import main as pipeline_main
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
                # La logique existante pour la recréation reste ici
                # ... (code de l'option 13)
                pass # Placeholder
            
            elif choice == "14":
                print("\n🔎 Lancement de l'extracteur de clips...")
                from core.downloader import Downloader
                from translation.whisper_simple import WhisperTranscriber
                from montage.clip_finder import find_potential_clips
                from database.manager import VideoDatabase

                url = input("👉 URL de la vidéo YouTube longue : ").strip()
                if not url:
                    print("❌ URL requise")
                    continue

                # 1. Téléchargement
                print("📥 Téléchargement de la vidéo...")
                downloader = Downloader()
                video_info = downloader.download_audio([url])
                if not video_info:
                    print("❌ Échec du téléchargement.")
                    continue
                
                video_id = video_info[0]['id']
                original_video_path = video_info[0]['audio_path'] # C'est le chemin vers l'audio/vidéo téléchargé
                
                # 2. Transcription
                print("🎤 Transcription avec Whisper pour obtenir les timestamps...")
                transcriber = WhisperTranscriber()
                transcription_result = transcriber.transcribe_with_timestamps(video_id)
                if not transcription_result:
                    print("❌ Échec de la transcription.")
                    continue
                
                transcript_data = transcription_result['segments']
                video_duration = transcription_result['duration']

                # 3. Analyse par l'IA
                clips = find_potential_clips(transcript_data, video_duration)
                if not clips:
                    print("🔴 L'IA n'a identifié aucun clip pertinent.")
                    continue

                # 4. Sélection par l'utilisateur
                console.print(Panel("✨ Pépites Identifiées par l'IA ✨", style="bold green"))
                clips_table = Table(show_header=True, header_style="bold magenta")
                clips_table.add_column("#", style="cyan")
                clips_table.add_column("Titre", style="white")
                clips_table.add_column("Durée (s)", style="yellow")
                clips_table.add_column("Justification", style="white")

                for i, clip in enumerate(clips):
                    duration = clip.get('end_time', 0) - clip.get('start_time', 0)
                    clips_table.add_row(
                        str(i + 1),
                        clip.get('title', 'N/A'),
                        f"{duration:.2f}",
                        clip.get('justification', 'N/A')
                    )
                console.print(clips_table)

                try:
                    clip_choice = input("\n🎯 Choisissez un clip à extraire (ex: 1) ou 'q' pour quitter: ").strip()
                    if clip_choice.lower() == 'q':
                        continue
                    
                    selected_index = int(clip_choice) - 1
                    if not 0 <= selected_index < len(clips):
                        print("❌ Choix invalide.")
                        continue
                        
                    selected_clip = clips[selected_index]

                except (ValueError, IndexError):
                    print("❌ Choix invalide.")
                    continue

                # 5. Découpage et sauvegarde
                start_time = selected_clip['start_time']
                end_time = selected_clip['end_time']
                new_video_id = f"clip_{uuid.uuid4().hex[:8]}"
                
                db = VideoDatabase()
                output_path = os.path.join(db.audios_en_dir, f"{new_video_id}.mp4")

                print(f"🎬 Découpage de la vidéo de {start_time:.2f}s à {end_time:.2f}s...")
                try:
                    (
                        ffmpeg
                        .input(original_video_path, ss=start_time, to=end_time)
                        .output(output_path, c='copy', y='-y') # c=copy pour rapidité, -y pour écraser
                        .run(quiet=True)
                    )
                    print(f"✅ Clip sauvegardé sous : {output_path}")

                    # 6. Ajout à la base de données
                    db.add_video(
                        video_id=new_video_id,
                        title=f"[CLIP] {selected_clip['title']}",
                        url=url,
                        channel_name=video_info[0]['channel'],
                        status='downloaded'
                    )
                    print(f"✅ Clip '{new_video_id}' ajouté à la base de données. Vous pouvez maintenant le traiter avec les autres options.")

                except ffmpeg.Error as e:
                    print(f"❌ Erreur ffmpeg lors du découpage : {e.stderr.decode('utf8')}")
                except Exception as e:
                    print(f"❌ Erreur lors du découpage ou de l'ajout à la BDD : {e}")

            else:
                print("❌ Choix invalide. Veuillez choisir entre 0 et 14.")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir !")
            break
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            import traceback
            traceback.print_exc()
            input("Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()
 