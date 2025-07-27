#!/usr/bin/env python3
"""
Processeur VTT avec Ollama pour TikTok_Auto
Utilise Ollama pour traiter et traduire les fichiers VTT de manière robuste
"""

import os
import re
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.console import Console
from rich.panel import Panel
from database.manager import VideoDatabase
from config import Config

class VttOllamaProcessor:
    def __init__(self, db_path: str = "videos.db"):
        self.db = VideoDatabase(db_path)
        self.console = Console()
        self.ollama_host = Config.OLLAMA_HOST
        self.ollama_model = Config.OLLAMA_MODEL
        
    def parse_vtt_file(self, vtt_path: str) -> List[Dict[str, Any]]:
        """Parse un fichier VTT et extrait les segments avec timing"""
        segments = []
        
        if not os.path.exists(vtt_path):
            print(f"❌ Fichier VTT non trouvé: {vtt_path}")
            return segments
            
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern pour capturer les segments VTT
            # Format: timestamp --> timestamp\ntexte\n\n
            pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})(?:\s+[^\n]*)?\n((?:[^\n]+\n?)*?)(?=\n\n|\n\d{2}:\d{2}:\d{2}\.\d{3}|\Z)'
            
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            
            for start_time, end_time, text in matches:
                # Nettoyer le texte
                text = text.strip()
                if text:
                    segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text,
                        'original_text': text
                    })
            
            print(f"✅ {len(segments)} segments extraits du VTT")
            return segments
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing VTT: {e}")
            return segments
    
    def time_to_seconds(self, time_str: str) -> float:
        """Convertit un timestamp VTT en secondes"""
        try:
            # Format: HH:MM:SS.mmm
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0.0
    
    def seconds_to_time(self, seconds: float) -> str:
        """Convertit des secondes en format VTT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def translate_with_ollama(self, text: str, target_lang: str = "French") -> str:
        """Traduit un texte avec Ollama"""
        try:
            prompt = f"""Traduis ce texte en {target_lang}. 
            Retourne uniquement la traduction, sans explications ni commentaires.
            
            Texte à traduire: "{text}"
            
            Traduction:"""
            
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                translation = result.get('response', '').strip()
                return translation
            else:
                print(f"❌ Erreur Ollama: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"❌ Erreur de traduction Ollama: {e}")
            return text
    
    def translate_segments_with_ollama(self, segments: List[Dict[str, Any]], 
                                     target_lang: str = "French") -> List[Dict[str, Any]]:
        """Traduit tous les segments avec Ollama"""
        translated_segments = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Traduction avec Ollama...", total=len(segments))
            
            for segment in segments:
                if segment['text'].strip():
                    try:
                        # Traduire le texte
                        translation = self.translate_with_ollama(segment['text'], target_lang)
                        
                        translated_segment = segment.copy()
                        translated_segment['translated_text'] = translation
                        translated_segments.append(translated_segment)
                        
                    except Exception as e:
                        print(f"⚠️ Erreur de traduction: {e}")
                        # Garder le texte original en cas d'erreur
                        translated_segment = segment.copy()
                        translated_segment['translated_text'] = segment['text']
                        translated_segments.append(translated_segment)
                
                progress.update(task, advance=1)
        
        return translated_segments
    
    def save_translated_vtt(self, segments: List[Dict[str, Any]], 
                           output_path: str) -> bool:
        """Sauvegarde les segments traduits en format VTT"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for segment in segments:
                    f.write(f"{segment['start_time']} --> {segment['end_time']}\n")
                    f.write(f"{segment['translated_text']}\n\n")
            
            print(f"✅ VTT traduit sauvegardé: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def process_video_vtt(self, video_id: str, target_lang: str = "French") -> bool:
        """Traite la traduction VTT d'une vidéo avec Ollama"""
        
        # Récupérer les informations de la vidéo
        video_info = self.db.get_video_info(video_id)
        if not video_info:
            print(f"❌ Vidéo {video_id} non trouvée dans la base de données")
            return False
        
        video = video_info['video']
        subtitle_files = video_info['subtitle_files']
        audio_files = video_info['audio_files']
        
        print(f"📹 Traitement de: {video[2]}")
        
        # Trouver le fichier VTT anglais
        vtt_path = None
        for subtitle in subtitle_files:
            if subtitle[3] == 'en':  # language
                vtt_path = subtitle[2]  # file_path
                break
        
        # Si pas de VTT, utiliser Whisper
        if not vtt_path or not os.path.exists(vtt_path):
            print(f"📝 Aucun VTT trouvé, utilisation de Whisper...")
            return self.process_with_whisper(video_id, audio_files, target_lang)
        
        # Créer le dossier de sortie
        output_dir = f"datas/translations/{target_lang.lower()}"
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/{video_id}.vtt"
        
        # Parser le VTT
        print("📝 Parsing du fichier VTT...")
        segments = self.parse_vtt_file(vtt_path)
        
        if not segments:
            print("❌ Aucun segment trouvé dans le VTT")
            return False
        
        # Traduire avec Ollama
        print("🤖 Traduction avec Ollama...")
        translated_segments = self.translate_segments_with_ollama(segments, target_lang)
        
        # Sauvegarder le VTT traduit
        if self.save_translated_vtt(translated_segments, output_path):
            # Enregistrer dans la base de données
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            self.db.add_translation(
                video_id=video_id,
                file_path=output_path,
                language=target_lang.lower(),
                translation_method="ollama_vtt",
                original_language="en",
                segment_count=len(translated_segments),
                file_size=file_size
            )
            return True
        
        return False
    
    def batch_translate_videos(self, video_ids: List[str], target_lang: str = "French") -> Dict[str, bool]:
        """Traduit plusieurs vidéos en lot"""
        results = {}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Traduction en lot...", total=len(video_ids))
            
            for video_id in video_ids:
                progress.update(task, description=f"Traduction de {video_id}...")
                
                try:
                    success = self.process_video_vtt(video_id, target_lang)
                    results[video_id] = success
                    
                    if success:
                        print(f"✅ {video_id} traduit avec succès")
                    else:
                        print(f"❌ Échec de traduction pour {video_id}")
                        
                except Exception as e:
                    print(f"❌ Erreur pour {video_id}: {e}")
                    results[video_id] = False
                
                progress.update(task, advance=1)
        
        return results
    
    def process_with_whisper(self, video_id: str, audio_files: List, target_lang: str = "French") -> bool:
        """Traite la traduction avec Whisper quand il n'y a pas de VTT"""
        try:
            # Trouver le fichier audio
            audio_path = None
            for audio in audio_files:
                if audio[3] == 'mp3':  # format
                    audio_path = audio[2]  # file_path
                    break
            
            if not audio_path or not os.path.exists(audio_path):
                print(f"❌ Fichier audio non trouvé pour {video_id}")
                return False
            
            print(f"🎙️ Transcription avec Whisper...")
            
            # Importer Whisper
            try:
                import whisper
            except ImportError:
                print("❌ Whisper non installé. Installez avec: pip install openai-whisper")
                return False
            
            # Charger le modèle Whisper
            model = whisper.load_model("base")
            
            # Transcrire l'audio
            result = model.transcribe(audio_path, language="en")
            
            # Extraire les segments avec timing
            segments = []
            for segment in result["segments"]:
                start_time = self.seconds_to_time(segment["start"])
                end_time = self.seconds_to_time(segment["end"])
                text = segment["text"].strip()
                
                if text:
                    segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': text,
                        'original_text': text
                    })
            
            print(f"✅ {len(segments)} segments transcrits avec Whisper")
            
            # Traduire avec Ollama
            print("🤖 Traduction avec Ollama...")
            translated_segments = self.translate_segments_with_ollama(segments, target_lang)
            
            # Sauvegarder le VTT traduit
            output_dir = f"datas/translations/{target_lang.lower()}"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/{video_id}.vtt"
            
            if self.save_translated_vtt(translated_segments, output_path):
                # Enregistrer dans la base de données
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                self.db.add_translation(
                    video_id=video_id,
                    file_path=output_path,
                    language=target_lang.lower(),
                    translation_method="whisper_ollama",
                    original_language="en",
                    segment_count=len(translated_segments),
                    file_size=file_size
                )
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement Whisper: {e}")
            return False

def main():
    """Interface principale du processeur VTT Ollama"""
    console = Console()
    
    console.print(Panel.fit(
        "🤖 Processeur VTT avec Ollama",
        style="bold blue"
    ))
    
    processor = VttOllamaProcessor()
    
    while True:
        console.print("\n" + "="*60)
        console.print("📋 Options du processeur VTT Ollama:")
        console.print("="*60)
        console.print(" 1  🎯 Traduire une vidéo spécifique")
        console.print(" 2  🔄 Traduire TOUTES les vidéos")
        console.print(" 3  📊 Statistiques de traduction")
        console.print(" 4  🔍 Vidéos non traduites")
        console.print(" 0  ❌ Retour au menu principal")
        
        choice = input("\n🎯 Votre choix (0-4): ").strip()
        
        if choice == "0":
            break
            
        elif choice == "1":
            video_id = input("🎯 ID de la vidéo: ").strip()
            if video_id:
                processor.process_video_vtt(video_id)
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == "2":
            # Récupérer toutes les vidéos
            videos = processor.db.list_all_videos()
            video_ids = [video[0] for video in videos]
            
            if video_ids:
                console.print(f"\n🔄 Traduction de {len(video_ids)} vidéos")
                confirm = input("⚠️  Êtes-vous sûr ? (oui/non): ").strip().lower()
                
                if confirm == "oui":
                    results = processor.batch_translate_videos(video_ids)
                    success_count = sum(1 for success in results.values() if success)
                    console.print(f"\n✅ {success_count}/{len(video_ids)} vidéos traduites avec succès")
            else:
                console.print("❌ Aucune vidéo trouvée")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == "3":
            # Statistiques
            stats = processor.db.get_stats()
            console.print(f"\n📊 Statistiques:")
            console.print(f"• Vidéos totales: {stats['videos']}")
            console.print(f"• Chaînes: {stats['channels']}")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        elif choice == "4":
            # Vidéos non traduites
            videos = processor.db.list_all_videos()
            untranslated = [v for v in videos if v[6] == 0]  # translation_count == 0
            
            if untranslated:
                console.print(f"\n🔍 {len(untranslated)} vidéos non traduites:")
                for video in untranslated[:10]:  # Afficher les 10 premières
                    console.print(f"• {video[0]}: {video[1][:50]}...")
            else:
                console.print("✅ Toutes les vidéos sont traduites")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        else:
            console.print("❌ Choix invalide")

if __name__ == "__main__":
    main() 