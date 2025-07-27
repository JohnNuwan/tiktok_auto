#!/usr/bin/env python3
"""
Module de Montage Vidéo - Combine audio français avec vidéos de fond
Utilise les données de la base de données tts_outputs et videos
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
import subprocess
import shutil

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

class VideoBuilder:
    """Gestionnaire de montage vidéo pour TikTok"""
    
    def __init__(self, output_dir: str = "datas/final_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db = VideoDatabase()
        self.console = Console()
        
        # Initialiser le téléchargeur de fonds
        from core.fond_downloader import FondDownloader
        self.fond_downloader = FondDownloader()
        
        # Vérifier FFmpeg
        self.ffmpeg_available = self._check_ffmpeg()
        
    def _check_ffmpeg(self) -> bool:
        """Vérifie si FFmpeg est disponible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg disponible")
                return True
            else:
                print("❌ FFmpeg non disponible")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ FFmpeg non installé")
            print("   Installez FFmpeg: https://ffmpeg.org/download.html")
            return False
    
    def get_videos_with_tts(self) -> List[Dict]:
        """Récupère les vidéos qui ont du TTS généré"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupérer les vidéos avec TTS
                cursor.execute('''
                    SELECT v.video_id, v.title, tts.audio_path, tts.voice_used
                    FROM videos v
                    INNER JOIN tts_outputs tts ON v.video_id = tts.video_id
                    LEFT JOIN final_videos fv ON v.video_id = fv.video_id
                    WHERE fv.video_id IS NULL
                    ORDER BY tts.created_at DESC
                ''')
                
                results = cursor.fetchall()
                
                videos_with_tts = []
                for video_id, title, audio_path, voice_used in results:
                    # Chercher le fichier vidéo correspondant
                    video_path = self._find_video_file(video_id)
                    
                    if video_path:
                        videos_with_tts.append({
                            "video_id": video_id,
                            "title": title or video_id,
                            "video_path": video_path,
                            "audio_path": audio_path,
                            "voice_used": voice_used
                        })
                    else:
                        print(f"⚠️  Fichier vidéo non trouvé pour {video_id}")
                
                return videos_with_tts
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return []
    
    def _find_video_file(self, video_id: str) -> Optional[str]:
        """Trouve le fichier vidéo pour un ID de vidéo"""
        # Récupérer le thème de la vidéo depuis la base de données
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT theme FROM videos WHERE video_id = ?", (video_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    theme = result[0]
                    print(f"🎨 Thème trouvé pour {video_id}: {theme}")
                    
                    # Utiliser le téléchargeur de fonds pour sélectionner un fond
                    fond_path = self.fond_downloader.select_fond_for_video(theme)
                    if fond_path:
                        print(f"🎥 Fond sélectionné: {fond_path}")
                        return fond_path
                    else:
                        print(f"⚠️ Aucun fond trouvé pour le thème: {theme}")
                        # Télécharger des fonds pour ce thème
                        print(f"📥 Téléchargement de fonds pour le thème: {theme}")
                        self.fond_downloader.download_fonds_for_theme(theme, count_per_source=2)
                        fond_path = self.fond_downloader.select_fond_for_video(theme)
                        if fond_path:
                            return fond_path
                        
                        # Si toujours pas de fond, essayer avec un thème par défaut
                        print(f"🔄 Essai avec un thème par défaut (motivation)")
                        fond_path = self.fond_downloader.select_fond_for_video("motivation")
                        if fond_path:
                            print(f"✅ Fond par défaut utilisé: {fond_path}")
                            return fond_path
                else:
                    print(f"⚠️ Aucun thème trouvé pour {video_id}")
                    # Utiliser un thème par défaut
                    print(f"🔄 Utilisation du thème par défaut (motivation)")
                    fond_path = self.fond_downloader.select_fond_for_video("motivation")
                    if fond_path:
                        print(f"✅ Fond par défaut utilisé: {fond_path}")
                        return fond_path
        except Exception as e:
            print(f"❌ Erreur lors de la recherche du thème: {e}")
        
        return None
    
    def _get_french_text(self, video_id: str) -> Optional[str]:
        """Récupère le texte français pour un ID de vidéo"""
        try:
            import sqlite3
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Essayer d'abord la table whisper_translations
                cursor.execute("SELECT french_text FROM whisper_translations WHERE video_id = ?", (video_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    print(f"📝 Texte français trouvé pour {video_id}")
                    return result[0]
                
                # Essayer la table audio_translations
                cursor.execute("SELECT text FROM audio_translations WHERE video_id = ?", (video_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    print(f"📝 Texte français trouvé dans audio_translations pour {video_id}")
                    return result[0]
                
                print(f"⚠️ Aucun texte français trouvé pour {video_id}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération du texte: {e}")
            return None
    
    def _create_subtitle_file(self, video_id: str, french_text: str) -> Optional[str]:
        """Crée un fichier de sous-titres stylisé pour la vidéo avec Hook et CTA"""
        try:
            # Créer le dossier temporaire pour les sous-titres
            subtitle_dir = Path("datas/temp_subtitles")
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            
            # Nom du fichier de sous-titres
            subtitle_path = subtitle_dir / f"{video_id}.ass"
            
            # Diviser le texte en phrases pour l'animation
            sentences = [s.strip() for s in french_text.split('.') if s.strip()]
            
            # Créer le fichier ASS (Advanced SubStation Alpha) avec styles pour Hook et CTA
            ass_content = """[Script Info]
Title: TikTok Auto Subtitles
ScriptType: v4.00+
WrapStyle: 1
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.601

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,20,20,20,1
Style: Hook,Arial,64,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,20,20,20,1
Style: CTA,Arial,56,&H0000FF00,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
            
            # Structure de la vidéo : Hook (5s) + Contenu (60s) + CTA (5s) = 70s total
            hook_duration = 5.0
            content_duration = 60.0
            cta_duration = 5.0
            
            # HOOK (0-5 secondes)
            hook_text = "🎯 ATTENTION !"
            ass_content += f"Dialogue: 0,{self._format_time(0)},{self._format_time(hook_duration)},Hook,,0,0,0,,{hook_text}\n"
            
            # CONTENU PRINCIPAL (5-65 secondes)
            if sentences:
                # Calculer la durée par segment pour le contenu principal
                segment_duration = content_duration / len(sentences)
                current_time = hook_duration
                
                for i, sentence in enumerate(sentences):
                    if len(sentence) > 100:  # Diviser les longues phrases
                        words = sentence.split()
                        mid = len(words) // 2
                        part1 = ' '.join(words[:mid])
                        part2 = ' '.join(words[mid:])
                        
                        # Première partie
                        start_time = self._format_time(current_time)
                        end_time = self._format_time(current_time + segment_duration/2)
                        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{part1}\n"
                        
                        # Deuxième partie
                        start_time = self._format_time(current_time + segment_duration/2)
                        end_time = self._format_time(current_time + segment_duration)
                        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{part2}\n"
                    else:
                        start_time = self._format_time(current_time)
                        end_time = self._format_time(current_time + segment_duration)
                        ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{sentence}\n"
                    
                    current_time += segment_duration
            
            # CTA (65-70 secondes)
            cta_text = "👍 Likez et abonnez-vous !"
            ass_content += f"Dialogue: 0,{self._format_time(hook_duration + content_duration)},{self._format_time(70.0)},CTA,,0,0,0,,{cta_text}\n"
            
            # Écrire le fichier
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                f.write(ass_content)
            
            print(f"📝 Fichier de sous-titres créé avec Hook et CTA: {subtitle_path}")
            return str(subtitle_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la création des sous-titres: {e}")
            return None
    
    def _format_time(self, seconds: float) -> str:
        """Convertit les secondes en format HH:MM:SS.cc"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours:01d}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def create_final_video(self, video_id: str, video_path: str, audio_path: str) -> Optional[str]:
        """Crée la vidéo finale en combinant vidéo, audio et sous-titres"""
        try:
            if not self.ffmpeg_available:
                print("❌ FFmpeg requis pour le montage")
                return None
            
            # Vérifier que les fichiers existent
            if not Path(video_path).exists():
                print(f"❌ Vidéo non trouvée: {video_path}")
                return None
                
            if not Path(audio_path).exists():
                print(f"❌ Audio non trouvé: {audio_path}")
                return None
            
            # Nom du fichier de sortie
            output_filename = f"final_{video_id}.mp4"
            output_path = self.output_dir / output_filename
            
            print(f"🎬 Montage de: {video_id}")
            print(f"📹 Vidéo: {video_path}")
            print(f"🎵 Audio: {audio_path}")
            
            # Récupérer le texte français et créer les sous-titres
            french_text = self._get_french_text(video_id)
            subtitle_path = None
            
            if french_text:
                print(f"📝 Texte français récupéré: {len(french_text)} caractères")
                subtitle_path = self._create_subtitle_file(video_id, french_text)
                if subtitle_path:
                    print(f"📝 Sous-titres créés: {subtitle_path}")
                else:
                    print("⚠️ Impossible de créer les sous-titres")
            else:
                print("⚠️ Aucun texte français trouvé, montage sans sous-titres")
            
            # Construire la commande FFmpeg
            cmd = ['ffmpeg']
            
            # Entrées
            cmd.extend(['-i', str(video_path)])  # Vidéo d'entrée
            cmd.extend(['-i', str(audio_path)])  # Audio TTS d'entrée
            
            # Ajouter les sous-titres si disponibles
            if subtitle_path and Path(subtitle_path).exists():
                # Utiliser le chemin relatif simple
                subtitle_rel_path = str(subtitle_path).replace('\\', '/')
                # Boucler la vidéo si nécessaire et ajouter les sous-titres
                cmd.extend(['-vf', f'loop=loop=-1:size=1,ass={subtitle_rel_path}'])
                print(f"🎬 Montage avec sous-titres et boucle vidéo: {subtitle_rel_path}")
            else:
                # Boucler la vidéo si nécessaire
                cmd.extend(['-vf', 'loop=loop=-1:size=1'])
                print("🎬 Montage avec boucle vidéo")
            
            # Codecs et mapping
            cmd.extend([
                '-c:v', 'libx264',      # Codec vidéo H.264
                '-c:a', 'aac',          # Codec audio AAC
                '-map', '0:v:0',        # Utiliser la vidéo de la première entrée
                '-map', '1:a:0',        # Utiliser l'audio de la deuxième entrée (TTS)
                '-t', '70',             # Forcer la durée à 70 secondes (1min10)
                '-y',                   # Écraser si existe
                str(output_path)
            ])
            
            # Exécuter FFmpeg
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Vidéo finale créée avec sous-titres: {output_path}")
                
                # Nettoyer le fichier de sous-titres temporaire
                if subtitle_path and Path(subtitle_path).exists():
                    try:
                        Path(subtitle_path).unlink()
                        print(f"🧹 Fichier de sous-titres temporaire supprimé")
                    except:
                        pass
                
                return str(output_path)
            else:
                print(f"❌ Erreur FFmpeg: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout lors du montage")
            return None
        except Exception as e:
            print(f"❌ Erreur lors du montage: {e}")
            return None
    
    def save_final_video_record(self, video_id: str, final_video_path: str):
        """Sauvegarde l'enregistrement de la vidéo finale"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Créer la table si elle n'existe pas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS final_videos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        final_video_path TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (video_id) REFERENCES videos (video_id)
                    )
                ''')
                
                # Insérer l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO final_videos 
                    (video_id, final_video_path, created_at)
                    VALUES (?, ?, datetime('now'))
                ''', (video_id, final_video_path))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
    
    def process_single_video(self, video_data: Dict) -> bool:
        """Traite le montage d'une seule vidéo"""
        try:
            video_id = video_data['video_id']
            video_path = video_data['video_path']
            audio_path = video_data['audio_path']
            
            # Créer la vidéo finale
            final_video_path = self.create_final_video(video_id, video_path, audio_path)
            if not final_video_path:
                return False
            
            # Sauvegarder en base de données
            self.save_final_video_record(video_id, final_video_path)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_data['video_id']}: {e}")
            return False
    
    def batch_create_videos(self, limit: int = 20):
        """Crée plusieurs vidéos en lot"""
        videos = self.get_videos_with_tts()
        
        if not videos:
            print("✅ Toutes les vidéos ont déjà été montées")
            return
        
        # Limiter le nombre
        videos = videos[:limit]
        
        print(f"🎯 {len(videos)} vidéos à monter")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎬 Montage vidéo...", total=len(videos))
            
            for video in videos:
                progress.update(task, description=f"🎬 Montage: {video['title'][:30]}...")
                
                success = self.process_single_video(video)
                
                if not success:
                    print(f"❌ Échec du montage pour {video['video_id']}")
                
                progress.advance(task)
        
        print("✅ Montage vidéo terminé")
    
    def list_final_videos(self):
        """Liste les vidéos finales créées"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fv.video_id, fv.final_video_path, v.title, fv.created_at
                    FROM final_videos fv
                    LEFT JOIN videos v ON fv.video_id = v.video_id
                    ORDER BY fv.created_at DESC
                ''')
                
                results = cursor.fetchall()
                
                if not results:
                    print("📭 Aucune vidéo finale créée")
                    return
                
                print(f"📹 {len(results)} vidéos finales créées:")
                
                table = Table(title="Vidéos Finales")
                table.add_column("ID", style="cyan")
                table.add_column("Titre", style="white")
                table.add_column("Fichier", style="green")
                table.add_column("Créé le", style="yellow")
                
                for video_id, final_path, title, created_at in results:
                    table.add_row(
                        video_id,
                        title or video_id,
                        Path(final_path).name,
                        created_at
                    )
                
                self.console.print(table)
                
        except Exception as e:
            print(f"❌ Erreur lors de la lecture: {e}")


def create_final_videos_table():
    """Crée la table final_videos"""
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table final_videos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS final_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    final_video_path TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Créer un index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_final_videos_video_id 
                ON final_videos (video_id)
            ''')
            
            conn.commit()
            print("✅ Table final_videos créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")


def main():
    """Interface principale du module VideoBuilder"""
    console = Console()
    
    # Créer la table si elle n'existe pas
    create_final_videos_table()
    
    builder = VideoBuilder()
    
    if not builder.ffmpeg_available:
        console.print(Panel(
            "❌ FFmpeg requis pour le montage vidéo\n\n"
            "Installez FFmpeg:\n"
            "https://ffmpeg.org/download.html",
            title="FFmpeg requis",
            style="red"
        ))
        return
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🎬 Monteur Vidéo TikTok",
            style="bold magenta"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🎬 Monter une vidéo spécifique")
        print("2. 🔄 Montage en lot (limité à 20 vidéos)")
        print("3. 📊 Afficher les statistiques")
        print("4. 📹 Lister les vidéos finales")
        print("5. 🔍 Lister les vidéos avec TTS")
        print("0. ❌ Retour")
        
        try:
            choice = input("\n🎯 Votre choix (0-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Retour au menu principal...")
            break
        
        if choice == "0":
            break
        elif choice == "1":
            try:
                video_id = input("🎬 ID de la vidéo: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Retour au menu...")
                continue
            
            # Récupérer les données de la vidéo
            videos = builder.get_videos_with_tts()
            video_data = next((v for v in videos if v['video_id'] == video_id), None)
            
            if video_data:
                success = builder.process_single_video(video_data)
                if success:
                    print("✅ Montage terminé avec succès")
                else:
                    print("❌ Échec du montage")
            else:
                print(f"❌ Vidéo {video_id} non trouvée ou sans TTS")
                
        elif choice == "2":
            try:
                limit = input("📊 Nombre max de vidéos (Enter pour 20): ").strip() or "20"
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Retour au menu...")
                continue
            builder.batch_create_videos(int(limit))
            
        elif choice == "3":
            # Statistiques
            with sqlite3.connect(builder.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM final_videos")
                count = cursor.fetchone()[0]
                print(f"📊 {count} vidéos finales créées")
                
        elif choice == "4":
            builder.list_final_videos()
            
        elif choice == "5":
            videos = builder.get_videos_with_tts()
            print(f"🔍 {len(videos)} vidéos avec TTS prêtes pour le montage")
            for video in videos[:10]:  # Afficher les 10 premiers
                print(f"  - {video['video_id']}: {video['title']}")
                
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main() 