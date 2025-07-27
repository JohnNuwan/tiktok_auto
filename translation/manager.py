#!/usr/bin/env python3
"""
Gestionnaire de traduction pour les vidéos YouTube
Utilise les fichiers VTT existants et Whisper pour une traduction optimale
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from database.manager import VideoDatabase
import whisper
from deep_translator import GoogleTranslator

class TranslationManager:
    def __init__(self, db_path: str = "videos.db"):
        self.db = VideoDatabase(db_path)
        self.console = Console()
        self.translator = GoogleTranslator(source='auto', target='fr')
        
        # Initialiser Whisper (modèle petit pour la vitesse)
        print("🤖 Chargement du modèle Whisper...")
        self.whisper_model = whisper.load_model("base")
        print("✅ Modèle Whisper chargé")
    
    def parse_vtt_file(self, vtt_path: str) -> List[Dict[str, Any]]:
        """Parse un fichier VTT et extrait les segments avec timing"""
        if not os.path.exists(vtt_path):
            return []
        
        segments = []
        current_segment = {}
        
        with open(vtt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            
            # Ligne de timing (format: 00:00:00.000 --> 00:00:00.000)
            if '-->' in line:
                if current_segment:
                    segments.append(current_segment)
                
                times = line.split(' --> ')
                current_segment = {
                    'start': self._parse_time(times[0]),
                    'end': self._parse_time(times[1]),
                    'text': ''
                }
            
            # Ligne de texte (pas vide et pas un numéro)
            elif line and not line.isdigit() and not line.startswith('WEBVTT'):
                if current_segment:
                    current_segment['text'] += line + ' '
        
        # Ajouter le dernier segment
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _parse_time(self, time_str: str) -> float:
        """Convertit un timestamp VTT en secondes"""
        # Format: 00:00:00.000
        parts = time_str.replace(',', '.').split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds
    
    def translate_vtt_segments(self, segments: List[Dict[str, Any]], 
                             target_lang: str = 'fr') -> List[Dict[str, Any]]:
        """Traduit les segments VTT vers la langue cible"""
        translated_segments = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Traduction des segments...", total=len(segments))
            
            for segment in segments:
                if segment['text'].strip():
                    try:
                        # Traduire le texte
                        translation = self.translator.translate(segment['text'].strip())
                        
                        translated_segment = segment.copy()
                        translated_segment['translated_text'] = translation
                        translated_segment['original_text'] = segment['text'].strip()
                        translated_segments.append(translated_segment)
                        
                    except Exception as e:
                        print(f"⚠️ Erreur de traduction: {e}")
                        # Garder le texte original en cas d'erreur
                        translated_segment = segment.copy()
                        translated_segment['translated_text'] = segment['text'].strip()
                        translated_segment['original_text'] = segment['text'].strip()
                        translated_segments.append(translated_segment)
                
                progress.update(task, advance=1)
        
        return translated_segments
    
    def save_translated_vtt(self, segments: List[Dict[str, Any]], 
                           output_path: str, lang_code: str = 'fr') -> bool:
        """Sauvegarde les segments traduits en format VTT"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"WEBVTT\n\n")
                
                for i, segment in enumerate(segments, 1):
                    # Convertir les secondes en format VTT
                    start_time = self._format_time_vtt(segment['start'])
                    end_time = self._format_time_vtt(segment['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment['translated_text']}\n\n")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def _format_time_vtt(self, seconds: float) -> str:
        """Convertit les secondes en format VTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    def transcribe_with_whisper(self, audio_path: str, 
                               target_lang: str = 'fr') -> List[Dict[str, Any]]:
        """Transcrit et traduit l'audio avec Whisper"""
        if not os.path.exists(audio_path):
            print(f"❌ Fichier audio non trouvé: {audio_path}")
            return []
        
        print(f"🎵 Transcription avec Whisper: {audio_path}")
        
        try:
            # Transcrit et traduit en une seule fois
            result = self.whisper_model.transcribe(
                audio_path,
                task="translate",  # Traduit directement en anglais
                language="en"      # Langue source
            )
            
            # Si on veut du français, on traduit depuis l'anglais
            if target_lang == 'fr':
                segments = []
                for segment in result['segments']:
                    try:
                        translation = self.translator.translate(
                            segment['text'], 
                            dest='fr'
                        )
                        segment['translated_text'] = translation.text
                        segments.append(segment)
                    except:
                        segment['translated_text'] = segment['text']
                        segments.append(segment)
                return segments
            else:
                return result['segments']
                
        except Exception as e:
            print(f"❌ Erreur Whisper: {e}")
            return []
    
    def process_video_translation(self, video_id: str, 
                                method: str = "hybrid",
                                target_lang: str = "fr") -> bool:
        """Traite la traduction d'une vidéo avec la méthode choisie"""
        
        # Récupérer les informations de la vidéo
        video_info = self.db.get_video_info(video_id)
        if not video_info:
            print(f"❌ Vidéo {video_id} non trouvée dans la base de données")
            return False
        
        video = video_info['video']
        audio_files = video_info['audio_files']
        subtitle_files = video_info['subtitle_files']
        
        print(f"📹 Traitement de: {video[2]}")
        
        # Trouver les fichiers
        audio_path = None
        vtt_path = None
        
        for audio in audio_files:
            if audio[5] == 'mp3':  # format
                audio_path = audio[2]  # file_path
                break
        
        for subtitle in subtitle_files:
            if subtitle[3] == 'en':  # language
                vtt_path = subtitle[2]  # file_path
                break
        
        if not audio_path:
            print(f"❌ Fichier audio non trouvé pour {video_id}")
            return False
        
        # Créer le dossier de sortie organisé
        output_dir = f"datas/translations/{target_lang}"
        os.makedirs(output_dir, exist_ok=True)
        
        if method == "vtt_only":
            return self._translate_vtt_only(vtt_path, video_id, output_dir, target_lang)
        
        elif method == "whisper_only":
            return self._translate_whisper_only(audio_path, video_id, output_dir, target_lang)
        
        elif method == "hybrid":
            return self._translate_hybrid(vtt_path, audio_path, video_id, output_dir, target_lang)
        
        else:
            print(f"❌ Méthode inconnue: {method}")
            return False
    
    def _translate_vtt_only(self, vtt_path: str, video_id: str, 
                           output_dir: str, target_lang: str) -> bool:
        """Traduit uniquement avec les VTT existants"""
        if not vtt_path or not os.path.exists(vtt_path):
            print(f"❌ Fichier VTT non trouvé: {vtt_path}")
            return False
        
        print("📝 Traduction depuis le fichier VTT...")
        
        # Parser le VTT
        segments = self.parse_vtt_file(vtt_path)
        if not segments:
            print("❌ Aucun segment trouvé dans le VTT")
            return False
        
        # Traduire les segments
        translated_segments = self.translate_vtt_segments(segments, target_lang)
        
        # Sauvegarder
        output_path = os.path.join(output_dir, f"{video_id}.{target_lang}.vtt")
        success = self.save_translated_vtt(translated_segments, output_path, target_lang)
        
        if success:
            # Enregistrer dans la base de données
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
            self.db.add_translation(
                video_id=video_id,
                file_path=output_path,
                language=target_lang,
                translation_method="vtt_only",
                original_language="en",
                segment_count=len(translated_segments),
                file_size=file_size
            )
            print(f"✅ Traduction VTT sauvegardée: {output_path}")
            return True
        return False
    
    def _translate_whisper_only(self, audio_path: str, video_id: str, 
                               output_dir: str, target_lang: str) -> bool:
        """Traduit uniquement avec Whisper"""
        print("🤖 Transcription et traduction avec Whisper...")
        
        # Transcrit et traduit avec Whisper
        segments = self.transcribe_with_whisper(audio_path, target_lang)
        if not segments:
            print("❌ Échec de la transcription Whisper")
            return False
        
        # Convertir au format VTT
        vtt_segments = []
        for segment in segments:
            vtt_segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'translated_text': segment.get('translated_text', segment['text'])
            })
        
        # Sauvegarder
        output_path = os.path.join(output_dir, f"{video_id}.{target_lang}.whisper.vtt")
        success = self.save_translated_vtt(vtt_segments, output_path, target_lang)
        
        if success:
            # Enregistrer dans la base de données
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
            self.db.add_translation(
                video_id=video_id,
                file_path=output_path,
                language=target_lang,
                translation_method="whisper_only",
                original_language="en",
                segment_count=len(vtt_segments),
                file_size=file_size
            )
            print(f"✅ Traduction Whisper sauvegardée: {output_path}")
            return True
        return False
    
    def _translate_hybrid(self, vtt_path: str, audio_path: str, video_id: str, 
                         output_dir: str, target_lang: str) -> bool:
        """Méthode hybride : utilise VTT si disponible, sinon Whisper"""
        
        # Essayer d'abord avec VTT
        if vtt_path and os.path.exists(vtt_path):
            print("🔄 Méthode hybride : utilisation du VTT existant...")
            return self._translate_vtt_only(vtt_path, video_id, output_dir, target_lang)
        
        # Sinon, utiliser Whisper
        print("🔄 Méthode hybride : utilisation de Whisper...")
        return self._translate_whisper_only(audio_path, video_id, output_dir, target_lang)
    
    def batch_translate(self, method: str = "hybrid", 
                       target_lang: str = "fr",
                       video_ids: Optional[List[str]] = None) -> bool:
        """Traduit plusieurs vidéos en lot"""
        
        if video_ids:
            videos_to_process = video_ids
        else:
            # Toutes les vidéos de la base de données
            all_videos = self.db.list_all_videos()
            videos_to_process = [video[0] for video in all_videos]
        
        print(f"🚀 Traduction en lot de {len(videos_to_process)} vidéos...")
        
        success_count = 0
        for i, video_id in enumerate(videos_to_process, 1):
            print(f"\n📹 Vidéo {i}/{len(videos_to_process)}: {video_id}")
            
            if self.process_video_translation(video_id, method, target_lang):
                success_count += 1
        
        print(f"\n🎉 Traduction terminée: {success_count}/{len(videos_to_process)} succès")
        return success_count == len(videos_to_process)

def main():
    """Interface principale du gestionnaire de traduction"""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    
    console = Console()
    
    console.print(Panel.fit(
        "🌍 Gestionnaire de Traduction YouTube",
        style="bold blue"
    ))
    
    manager = TranslationManager()
    
    while True:
        print("\n" + "=" * 60)
        print("📋 Options de traduction disponibles:")
        print("=" * 60)
        
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("1", "🎯 Traduire une vidéo spécifique")
        table.add_row("2", "🔄 Traduire TOUTES les vidéos de la base de données")
        table.add_row("3", "📊 Afficher les statistiques de traduction")
        table.add_row("4", "🔍 Lister les vidéos non traduites")
        table.add_row("0", "❌ Retour au menu principal")
        
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-4): ").strip()
        
        if choice == "0":
            break
            
        elif choice == "1":
            print("\n🎯 Traduction d'une vidéo spécifique")
            print("-" * 40)
            
            # Afficher les vidéos disponibles
            all_videos = manager.db.list_all_videos()
            if not all_videos:
                print("❌ Aucune vidéo trouvée dans la base de données")
                continue
            
            print("📹 Vidéos disponibles:")
            for i, video in enumerate(all_videos[:10], 1):  # Limiter à 10 pour l'affichage
                print(f"{i}. {video[0]} - {video[1][:50]}...")
            
            if len(all_videos) > 10:
                print(f"... et {len(all_videos) - 10} autres vidéos")
            
            video_id = input("\n📹 ID de la vidéo à traduire: ").strip()
            if not video_id:
                print("❌ ID de vidéo requis")
                continue
            
            print("\n🔧 Méthodes de traduction:")
            print("1. VTT uniquement (rapide, utilise les sous-titres existants)")
            print("2. Whisper uniquement (précis, retranscrit tout)")
            print("3. Hybride (VTT si disponible, sinon Whisper)")
            
            method_choice = input("🎯 Méthode (1-3): ").strip()
            
            method_map = {
                "1": "vtt_only",
                "2": "whisper_only", 
                "3": "hybrid"
            }
            
            if method_choice in method_map:
                print(f"\n🚀 Traduction de {video_id} avec la méthode {method_map[method_choice]}...")
                manager.process_video_translation(video_id, method_map[method_choice], "fr")
            else:
                print("❌ Méthode invalide")
        
        elif choice == "2":
            print("\n🔄 Traduction de TOUTES les vidéos")
            print("-" * 40)
            
            all_videos = manager.db.list_all_videos()
            if not all_videos:
                print("❌ Aucune vidéo trouvée dans la base de données")
                continue
            
            print(f"📊 {len(all_videos)} vidéos trouvées dans la base de données")
            
            print("\n🔧 Méthodes de traduction:")
            print("1. VTT uniquement (rapide)")
            print("2. Whisper uniquement (précis)")
            print("3. Hybride (recommandé)")
            
            method_choice = input("🎯 Méthode (1-3): ").strip()
            
            method_map = {
                "1": "vtt_only",
                "2": "whisper_only", 
                "3": "hybrid"
            }
            
            if method_choice in method_map:
                confirm = input(f"\n⚠️  Êtes-vous sûr de vouloir traduire {len(all_videos)} vidéos ? (oui/non): ").strip().lower()
                if confirm in ['oui', 'o', 'yes', 'y']:
                    print(f"\n🚀 Lancement de la traduction en lot...")
                    manager.batch_translate(method_map[method_choice], "fr")
                else:
                    print("❌ Traduction annulée")
            else:
                print("❌ Méthode invalide")
        
        elif choice == "3":
            print("\n📊 Statistiques de traduction")
            print("-" * 40)
            
            all_videos = manager.db.list_all_videos()
            if not all_videos:
                print("❌ Aucune vidéo trouvée")
                continue
            
            total_videos = len(all_videos)
            translated_videos = sum(1 for video in all_videos if video[6] > 0)  # translation_count
            
            print(f"📹 Total vidéos: {total_videos}")
            print(f"🌍 Vidéos traduites: {translated_videos}")
            print(f"📈 Taux de traduction: {(translated_videos/total_videos*100):.1f}%")
            
            if translated_videos < total_videos:
                print(f"⏳ Vidéos restantes: {total_videos - translated_videos}")
        
        elif choice == "4":
            print("\n🔍 Vidéos non traduites")
            print("-" * 40)
            
            all_videos = manager.db.list_all_videos()
            untranslated = [video for video in all_videos if video[6] == 0]  # translation_count == 0
            
            if not untranslated:
                print("✅ Toutes les vidéos sont traduites !")
            else:
                print(f"📋 {len(untranslated)} vidéos non traduites:")
                for i, video in enumerate(untranslated[:10], 1):
                    print(f"{i}. {video[0]} - {video[1][:50]}...")
                
                if len(untranslated) > 10:
                    print(f"... et {len(untranslated) - 10} autres")
        
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 