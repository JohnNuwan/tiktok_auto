#!/usr/bin/env python3
"""
Gestionnaire de base de données pour les vidéos YouTube
Permet de gérer facilement la base de données SQLite
"""

import argparse
import sys
from rich import print
from rich.console import Console
from rich.table import Table
from .manager import VideoDatabase
import os

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de base de données YouTube")
    parser.add_argument("command", choices=["list", "search", "info", "stats", "clean"], 
                       help="Commande à exécuter")
    parser.add_argument("--search", "-s", help="Terme de recherche")
    parser.add_argument("--video-id", "-v", help="ID de la vidéo")
    parser.add_argument("--output", "-o", help="Fichier de sortie")
    
    args = parser.parse_args()
    
    db = VideoDatabase()
    console = Console()
    
    if args.command == "list":
        print("📹 Liste de toutes les vidéos:")
        db.display_videos_table()
        
    elif args.command == "search":
        if not args.search:
            search_term = input("🔍 Terme de recherche: ")
        else:
            search_term = args.search
            
        results = db.search_videos(search_term)
        if results:
            table = Table(title=f"🔍 Résultats pour '{search_term}'")
            table.add_column("ID Vidéo", style="cyan")
            table.add_column("Titre", style="green")
            table.add_column("Chaîne", style="blue")
            table.add_column("Description", style="yellow")
            
            for result in results:
                description = result[2][:100] + "..." if result[2] and len(result[2]) > 100 else result[2] or ""
                table.add_row(result[0], result[1], result[3] or "N/A", description)
            
            console.print(table)
        else:
            print("❌ Aucun résultat trouvé")
            
    elif args.command == "info":
        if not args.video_id:
            video_id = input("📹 ID de la vidéo: ")
        else:
            video_id = args.video_id
            
        info = db.get_video_info(video_id)
        if info:
            video = info['video']
            audio_files = info['audio_files']
            subtitle_files = info['subtitle_files']
            translations = info['translations']
            
            print(f"\n📹 Informations de la vidéo {video_id}:")
            print(f"Titre: {video[2]}")
            print(f"Chaîne: {video[8] if video[8] else 'N/A'}")
            print(f"Durée: {video[4]//60}:{video[4]%60:02d}" if video[4] else "N/A")
            print(f"Date d'upload: {video[5]}")
            print(f"Vues: {video[6]:,}" if video[6] else "N/A")
            
            print(f"\n🎵 Fichiers audio ({len(audio_files)}):")
            for audio in audio_files:
                print(f"  - {audio[2]} ({audio[5]})")
                
            print(f"\n📝 Fichiers de sous-titres ({len(subtitle_files)}):")
            for subtitle in subtitle_files:
                auto_gen = " (auto)" if subtitle[4] else ""
                print(f"  - {subtitle[2]} ({subtitle[3]}){auto_gen}")
            
            print(f"\n🌍 Traductions ({len(translations)}):")
            for translation in translations:
                print(f"  - {translation[2]} ({translation[3]}) - {translation[4]}")
        else:
            print(f"❌ Vidéo {video_id} non trouvée")
            
    elif args.command == "stats":
        videos = db.list_all_videos()
        total_videos = len(videos)
        total_audio = sum(video[4] for video in videos)
        total_subtitles = sum(video[5] for video in videos)
        total_translations = sum(video[6] for video in videos)
        
        print("📊 Statistiques de la base de données:")
        print(f"Total vidéos: {total_videos}")
        print(f"Total fichiers audio: {total_audio}")
        print(f"Total fichiers sous-titres: {total_subtitles}")
        print(f"Total traductions: {total_translations}")
        print(f"Taux de couverture audio: {total_audio/total_videos*100:.1f}%" if total_videos > 0 else "N/A")
        print(f"Taux de couverture sous-titres: {total_subtitles/total_videos*100:.1f}%" if total_videos > 0 else "N/A")
        print(f"Taux de couverture traductions: {total_translations/total_videos*100:.1f}%" if total_videos > 0 else "N/A")
        
    elif args.command == "clean":
        # Vérifier les fichiers manquants
        videos = db.list_all_videos()
        missing_files = []
        
        for video in videos:
            video_id = video[0]
            files = db.get_video_files(video_id)
            
            for audio_file in files['audio_files']:
                if not os.path.exists(audio_file):
                    missing_files.append(('audio', video_id, audio_file))
                    
            for subtitle_file in files['subtitle_files']:
                if not os.path.exists(subtitle_file):
                    missing_files.append(('subtitle', video_id, subtitle_file))
        
        if missing_files:
            print(f"⚠️ {len(missing_files)} fichiers manquants détectés:")
            for file_type, video_id, file_path in missing_files:
                print(f"  - {file_type}: {video_id} -> {file_path}")
        else:
            print("✅ Tous les fichiers sont présents")

if __name__ == "__main__":
    main() 