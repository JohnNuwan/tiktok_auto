#!/usr/bin/env python3
"""
Script de Diagnostic pour la Génération de Shorts
Vérifie quelles vidéos ont tous les prérequis nécessaires
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

def main():
    console = Console()
    title = Panel.fit("🔍 Diagnostic - Génération de Shorts", style="bold blue")
    console.print(title)
    
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Statistiques générales
            console.print("\n📊 Statistiques Générales:")
            cursor.execute('SELECT COUNT(*) FROM videos')
            total_videos = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM whisper_texts')
            total_whisper = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM whisper_translations')
            total_translations = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM tts_outputs')
            total_tts = cursor.fetchone()[0]
            
            stats_table = Table(title="📈 Statistiques")
            stats_table.add_column("Métrique", style="cyan")
            stats_table.add_column("Valeur", style="green")
            
            stats_table.add_row("Total vidéos", str(total_videos))
            stats_table.add_row("Transcriptions Whisper", str(total_whisper))
            stats_table.add_row("Traductions", str(total_translations))
            stats_table.add_row("TTS générés", str(total_tts))
            
            console.print(stats_table)
            
            # Vidéos prêtes pour les shorts
            console.print("\n🎯 Vidéos Prêtes pour les Shorts:")
            cursor.execute('''
                SELECT v.video_id, v.title, 
                       CASE WHEN w.video_id IS NOT NULL THEN '✅' ELSE '❌' END as whisper,
                       CASE WHEN t.video_id IS NOT NULL THEN '✅' ELSE '❌' END as translation,
                       CASE WHEN tts.video_id IS NOT NULL THEN '✅' ELSE '❌' END as tts
                FROM videos v
                LEFT JOIN whisper_texts w ON v.video_id = w.video_id
                LEFT JOIN whisper_translations t ON v.video_id = t.video_id
                LEFT JOIN tts_outputs tts ON v.video_id = tts.video_id
                WHERE w.video_id IS NOT NULL 
                  AND t.video_id IS NOT NULL 
                  AND tts.video_id IS NOT NULL
                ORDER BY v.created_at DESC
                LIMIT 10
            ''')
            
            ready_videos = cursor.fetchall()
            
            if ready_videos:
                ready_table = Table(title="✅ Vidéos Prêtes")
                ready_table.add_column("ID", style="cyan")
                ready_table.add_column("Titre", style="green")
                ready_table.add_column("Whisper", style="yellow")
                ready_table.add_column("Traduction", style="blue")
                ready_table.add_column("TTS", style="magenta")
                
                for video in ready_videos:
                    video_id, title, whisper, translation, tts = video
                    ready_table.add_row(
                        video_id,
                        title[:40] + "..." if len(title) > 40 else title,
                        whisper,
                        translation,
                        tts
                    )
                
                console.print(ready_table)
                console.print(f"✅ {len(ready_videos)} vidéos prêtes pour la génération de shorts")
            else:
                console.print("❌ Aucune vidéo n'a tous les prérequis nécessaires")
            
            # Vidéos avec des prérequis manquants
            console.print("\n⚠️ Vidéos avec Prérequis Manquants:")
            cursor.execute('''
                SELECT v.video_id, v.title, 
                       CASE WHEN w.video_id IS NOT NULL THEN '✅' ELSE '❌' END as whisper,
                       CASE WHEN t.video_id IS NOT NULL THEN '✅' ELSE '❌' END as translation,
                       CASE WHEN tts.video_id IS NOT NULL THEN '✅' ELSE '❌' END as tts
                FROM videos v
                LEFT JOIN whisper_texts w ON v.video_id = w.video_id
                LEFT JOIN whisper_translations t ON v.video_id = t.video_id
                LEFT JOIN tts_outputs tts ON v.video_id = tts.video_id
                WHERE w.video_id IS NULL 
                   OR t.video_id IS NULL 
                   OR tts.video_id IS NULL
                ORDER BY v.created_at DESC
                LIMIT 10
            ''')
            
            missing_videos = cursor.fetchall()
            
            if missing_videos:
                missing_table = Table(title="⚠️ Vidéos avec Prérequis Manquants")
                missing_table.add_column("ID", style="cyan")
                missing_table.add_column("Titre", style="green")
                missing_table.add_column("Whisper", style="yellow")
                missing_table.add_column("Traduction", style="blue")
                missing_table.add_column("TTS", style="magenta")
                
                for video in missing_videos:
                    video_id, title, whisper, translation, tts = video
                    missing_table.add_row(
                        video_id,
                        title[:40] + "..." if len(title) > 40 else title,
                        whisper,
                        translation,
                        tts
                    )
                
                console.print(missing_table)
                console.print(f"⚠️ {len(missing_videos)} vidéos avec des prérequis manquants")
            
            # Recommandations
            console.print("\n💡 Recommandations:")
            if len(ready_videos) > 0:
                console.print("✅ Vous pouvez lancer la génération de shorts maintenant !")
                console.print(f"   Utilisez: python scripts/auto_shorts_pipeline.py")
            else:
                console.print("❌ Aucune vidéo prête pour les shorts")
                console.print("   Étapes nécessaires:")
                console.print("   1. Lancer la transcription Whisper")
                console.print("   2. Lancer la traduction des textes")
                console.print("   3. Lancer la génération TTS")
                console.print("   4. Puis lancer la génération de shorts")
            
    except Exception as e:
        console.print(f"❌ Erreur lors du diagnostic: {e}")

if __name__ == "__main__":
    main() 