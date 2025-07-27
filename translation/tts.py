#!/usr/bin/env python3
"""
Module de synthèse vocale (TTS) utilisant Bark
Convertit les fichiers VTT traduits en audio français
"""

import os
import sys
import re
import json
import sqlite3
import librosa
import numpy as np
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

# Import Bark
try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    from bark.generation import generate_text_semantic
    from bark.api import semantic_to_waveform
    BARK_AVAILABLE = True
except ImportError:
    BARK_AVAILABLE = False
    print("⚠️  Bark n'est pas installé. Installez-le avec: pip install git+https://github.com/suno-ai/bark.git")

# Import ElevenLabs
try:
    from elevenlabs import voices, client
    from elevenlabs.text_to_speech.client import TextToSpeechClient, SyncClientWrapper
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️  ElevenLabs n'est pas installé. Installez-le avec: pip install elevenlabs")

from database.manager import VideoDatabase
from config import Config

class TTSManager:
    """Gestionnaire de synthèse vocale utilisant Bark et ElevenLabs"""
    
    def __init__(self, output_dir: str = "datas/tts/fr"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db = VideoDatabase()
        self.console = Console()

        # Configuration des moteurs TTS
        self.tts_engine = Config.DEFAULT_TTS_ENGINE  # Utilise la configuration centralisée
        
        # Voix françaises disponibles dans Bark
        self.bark_french_voices = [
            "v2/fr_speaker_0",  # Voix française féminine
            "v2/fr_speaker_1",  # Voix française masculine
            "v2/fr_speaker_2",  # Voix française féminine 2
            "v2/fr_speaker_3",  # Voix française masculine 2
            "v2/fr_speaker_4",  # Voix française féminine 3
            "v2/fr_speaker_5",  # Voix française masculine 3
            "v2/fr_speaker_6",  # Voix française féminine 4
            "v2/fr_speaker_7",  # Voix française masculine 4
        ]

        # Voix disponibles dans ElevenLabs (voix publiques par défaut)
        self.elevenlabs_french_voices = [
            "21m00Tcm4TlvDq8ikWAM",  # Rachel (voix féminine anglaise)
            "AZnzlk1XvdvUeBnXmlld",  # Domi (voix féminine anglaise)
            "EXAVITQu4vr4xnSDxMaL",  # Bella (voix féminine anglaise)
            "VR6AewLTigWG4xSOukaG",  # Sam (voix masculine anglaise)
            "pNInz6obpgDQGcFmaJgB",  # Adam (voix masculine anglaise)
            "MF3mGyEYCl7XYWbV9V6O",  # Echo (voix masculine anglaise)
        ]

        # Voix par défaut selon le moteur
        self.default_bark_voice = "v2/fr_speaker_7"
        self.default_elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
        # Initialiser les moteurs si disponibles
        if BARK_AVAILABLE:
            self._init_bark()
        
        if ELEVENLABS_AVAILABLE:
            self._init_elevenlabs()
    
    def _init_bark(self):
        """Initialise Bark (sans précharger les modèles)"""
        try:
            print("✅ Bark disponible (modèles chargés à la demande)")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Bark: {e}")
            BARK_AVAILABLE = False
    
    def _init_elevenlabs(self):
        """Initialise ElevenLabs avec la clé API"""
        try:
            # Vérifier si la clé API est configurée
            api_key = Config.ELEVENLABS_API_KEY
            if api_key and api_key != "your_elevenlabs_api_key_here":
                # Configurer le client avec la clé API
                client.api_key = api_key
                print("✅ ElevenLabs initialisé avec succès")
            else:
                print("⚠️  Clé API ElevenLabs non configurée dans .env")
                ELEVENLABS_AVAILABLE = False
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation d'ElevenLabs: {e}")
            ELEVENLABS_AVAILABLE = False
    
    def parse_vtt(self, vtt_path: str) -> List[Dict[str, any]]:
        """Parse un fichier VTT et extrait les segments avec timing"""
        segments = []
        
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern pour extraire les segments VTT
            pattern = r'(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n([\s\S]*?)(?=\n\n|\n\d{2}:\d{2}:\d{2}\.\d{3} -->|\Z)'
            matches = re.findall(pattern, content)
            
            for match in matches:
                start_time, end_time, text = match
                # Nettoyer le texte
                text = re.sub(r'<[^>]+>', '', text).strip()  # Supprimer les tags HTML
                text = re.sub(r'\n+', ' ', text).strip()     # Remplacer les sauts de ligne
                
                if text:  # Ignorer les segments vides
                    segments.append({
                        'start': start_time,
                        'end': end_time,
                        'text': text
                    })
            
            return segments
            
        except Exception as e:
            print(f"❌ Erreur lors du parsing du fichier VTT {vtt_path}: {e}")
            return []
    
    def time_to_seconds(self, time_str: str) -> float:
        """Convertit un timestamp VTT en secondes"""
        try:
            h, m, s = time_str.split(':')
            return float(h) * 3600 + float(m) * 60 + float(s)
        except:
            return 0.0
    
    def generate_audio_segment(self, text: str, voice_preset: str = None) -> Optional[np.ndarray]:
        """Génère l'audio pour un segment de texte"""
        if voice_preset is None:
            if self.tts_engine == "bark":
                voice_preset = self.default_bark_voice
            else:
                voice_preset = self.default_elevenlabs_voice
        
        if self.tts_engine == "bark":
            return self._generate_bark_audio(text, voice_preset)
        else:
            return self._generate_elevenlabs_audio(text, voice_preset)
    
    def _generate_bark_audio(self, text: str, voice_preset: str) -> Optional[np.ndarray]:
        """Génère l'audio avec Bark"""
        if not BARK_AVAILABLE:
            print("❌ Bark n'est pas disponible")
            return None
        
        try:
            # Générer l'audio avec Bark
            audio_array = generate_audio(text, history_prompt=voice_preset)
            return audio_array
        except Exception as e:
            print(f"❌ Erreur Bark pour '{text[:50]}...': {e}")
            return None
    
    def _generate_elevenlabs_audio(self, text: str, voice_preset: str) -> Optional[np.ndarray]:
        """Génère l'audio avec ElevenLabs"""
        if not ELEVENLABS_AVAILABLE:
            print("❌ ElevenLabs n'est pas disponible")
            return None
        
        try:
            # Créer le client wrapper et TTS
            import httpx
            httpx_client = httpx.Client()
            client_wrapper = SyncClientWrapper(
                base_url="https://api.elevenlabs.io",
                httpx_client=httpx_client
            )
            tts_client = TextToSpeechClient(client_wrapper=client_wrapper)
            
            # Générer l'audio avec ElevenLabs
            audio_stream = tts_client.convert(
                text=text,
                voice_id=voice_preset,
                model_id="eleven_multilingual_v2"
            )
            
            # Convertir le générateur en bytes
            audio_bytes = b''.join(audio_stream)
            
            # Convertir en numpy array
            import io
            import soundfile as sf
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            return audio_array
            
        except Exception as e:
            print(f"❌ Erreur ElevenLabs pour '{text[:50]}...': {e}")
            return None
    
    def combine_audio_segments(self, segments: List[np.ndarray], timings: List[Dict]) -> np.ndarray:
        """Combine les segments audio en respectant les timings"""
        if not segments:
            return np.array([])
        
        # Calculer la durée totale
        total_duration = 0
        for timing in timings:
            end_seconds = self.time_to_seconds(timing['end'])
            total_duration = max(total_duration, end_seconds)
        
        # Créer un array de silence de la durée totale
        total_samples = int(total_duration * SAMPLE_RATE)
        combined_audio = np.zeros(total_samples)
        
        # Placer chaque segment à sa position temporelle
        for i, (segment, timing) in enumerate(zip(segments, timings)):
            if segment is not None:
                start_seconds = self.time_to_seconds(timing['start'])
                start_sample = int(start_seconds * SAMPLE_RATE)
                end_sample = start_sample + len(segment)
                
                # S'assurer qu'on ne dépasse pas les limites
                if end_sample > total_samples:
                    segment = segment[:total_samples - start_sample]
                    end_sample = total_samples
                
                combined_audio[start_sample:end_sample] = segment
        
        return combined_audio
    
    def convert_vtt_to_audio(self, video_id: str, vtt_path: str, 
                           voice_preset: str = "v2/fr_speaker_7",
                           output_filename: Optional[str] = None) -> Optional[str]:
        """Convertit un fichier VTT en audio français"""
        if not BARK_AVAILABLE:
            print("❌ Bark n'est pas disponible")
            return None
        
        try:
            # Vérifier que le fichier VTT existe
            if not os.path.exists(vtt_path):
                print(f"❌ Fichier VTT introuvable: {vtt_path}")
                return None
            
            # Parser le fichier VTT
            print(f"📖 Parsing du fichier VTT: {vtt_path}")
            segments = self.parse_vtt(vtt_path)
            
            if not segments:
                print("❌ Aucun segment trouvé dans le fichier VTT")
                return None
            
            print(f"✅ {len(segments)} segments trouvés")
            
            # Générer le nom de fichier de sortie
            if output_filename is None:
                output_filename = f"{video_id}.wav"
            
            output_path = self.output_dir / output_filename
            
            # Générer l'audio pour chaque segment (version limitée pour test)
            audio_segments = []
            max_segments = 3  # Limiter à 3 segments pour test
            segments_to_process = segments[:max_segments]
            
            print(f"🎙️ Génération audio pour {len(segments_to_process)} segments (sur {len(segments)} total)...")
            
            for i, segment in enumerate(segments_to_process):
                print(f"🎙️ Segment {i+1}/{len(segments_to_process)}: {segment['text'][:50]}...")
                audio = self.generate_audio_segment(segment['text'], voice_preset)
                if audio is not None:
                    audio_segments.append(audio)
                else:
                    print(f"⚠️ Échec segment {i+1}, utilisation d'un segment vide")
                    # Créer un segment de silence de 1 seconde
                    silence = np.zeros(int(SAMPLE_RATE))
                    audio_segments.append(silence)
            
            if not audio_segments:
                print("❌ Aucun audio généré")
                return None
            
            # Combiner les segments
            print("🔗 Combinaison des segments audio...")
            combined_audio = self.combine_audio_segments(audio_segments, segments)
            
            if len(combined_audio) == 0:
                print("❌ Aucun audio généré")
                return None
            
            # Sauvegarder le fichier audio
            print(f"💾 Sauvegarde: {output_path}")
            import soundfile as sf
            sf.write(str(output_path), combined_audio, SAMPLE_RATE)
            
            # Calculer les métadonnées
            duration = len(combined_audio) / SAMPLE_RATE
            file_size = os.path.getsize(output_path)
            
            # Enregistrer dans la base de données
            self.db.add_tts_file(
                video_id=video_id,
                file_path=str(output_path),
                language="fr",
                tts_engine="bark",
                voice_preset=voice_preset,
                duration=int(duration),
                file_size=file_size,
                source_vtt_path=vtt_path
            )
            
            print(f"✅ Audio généré avec succès: {output_path}")
            print(f"📊 Durée: {duration:.2f}s, Taille: {file_size/1024/1024:.2f} MB")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la conversion VTT vers audio: {e}")
            return None
    
    def list_available_voices(self):
        """Affiche les voix françaises disponibles"""
        print(f"🎤 Moteur TTS actuel: {self.tts_engine.upper()}")
        print(f"🎯 Moteur par défaut: ElevenLabs (plus rapide et meilleure qualité)")
        
        if self.tts_engine == "bark":
            table = Table(title="🎤 Voix françaises disponibles dans Bark")
            table.add_column("Index", style="cyan")
            table.add_column("Voix", style="green")
            table.add_column("Description", style="yellow")
            
            descriptions = [
                "Voix féminine 1",
                "Voix masculine 1", 
                "Voix féminine 2",
                "Voix masculine 2",
                "Voix féminine 3",
                "Voix masculine 3",
                "Voix féminine 4",
                "Voix masculine 4"
            ]
            
            for i, voice in enumerate(self.bark_french_voices):
                table.add_row(str(i+1), voice, descriptions[i])
            
            self.console.print(table)
        else:
            table = Table(title="🎤 Voix disponibles dans ElevenLabs")
            table.add_column("Index", style="cyan")
            table.add_column("Voix", style="green")
            table.add_column("Type", style="yellow")

            voice_names = ["Adam", "Sam", "Bella", "Rachel", "Domi", "Echo"]
            voice_types = ["Masculine", "Masculine", "Féminine", "Féminine", "Féminine", "Masculine"]

            for i, (voice_id, name, voice_type) in enumerate(zip(self.elevenlabs_french_voices, voice_names, voice_types)):
                table.add_row(str(i+1), f"{name} ({voice_id[:8]}...)", voice_type)
            
            self.console.print(table)
    
    def switch_engine(self, engine: str):
        """Change le moteur TTS"""
        if engine in ["bark", "elevenlabs"]:
            self.tts_engine = engine
            print(f"✅ Moteur TTS changé vers: {engine.upper()}")
        else:
            print("❌ Moteur invalide. Utilisez 'bark' ou 'elevenlabs'")
    
    def get_videos_with_translations(self) -> List[Dict]:
        """Récupère les vidéos qui ont des traductions françaises"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT v.video_id, v.title, t.file_path as translation_path
                    FROM videos v
                    JOIN translations t ON v.video_id = t.video_id
                    WHERE t.language = 'french'
                    AND NOT EXISTS (
                        SELECT 1 FROM tts_files tf 
                        WHERE tf.video_id = v.video_id 
                        AND tf.language = 'french'
                    )
                    ORDER BY v.created_at DESC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des vidéos: {e}")
            return []
    
    def batch_convert_translations(self, voice_preset: str = "v2/fr_speaker_7"):
        """Convertit en lot toutes les traductions françaises en audio"""
        videos = self.get_videos_with_translations()
        
        if not videos:
            print("✅ Toutes les traductions ont déjà été converties en audio")
            return
        
        print(f"🎯 {len(videos)} vidéos à convertir en audio")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎙️ Conversion en lot...", total=len(videos))
            
            for video_id, title, translation_path in videos:
                progress.update(task, description=f"🎙️ Conversion: {title[:30]}...")
                
                self.convert_vtt_to_audio(
                    video_id=video_id,
                    vtt_path=translation_path,
                    voice_preset=voice_preset
                )
                
                progress.advance(task)
        
        print("✅ Conversion en lot terminée")

def main():
    """Interface principale du module TTS"""
    console = Console()
    
    if not BARK_AVAILABLE:
        console.print(Panel(
            "❌ Bark n'est pas installé\n\n"
            "Installez-le avec:\n"
            "pip install git+https://github.com/suno-ai/bark.git\n\n"
            "Assurez-vous d'avoir PyTorch installé pour GPU:\n"
            "pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118",
            title="Installation requise",
            style="red"
        ))
        return
    
    tts = TTSManager()
    
    while True:
        console.print(Panel.fit(
            "🎙️ Gestionnaire de Synthèse Vocale (TTS)",
            style="bold blue"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🎤 Lister les voix disponibles")
        print("2. 🎙️ Convertir une traduction spécifique")
        print("3. 🔄 Conversion en lot (toutes les traductions)")
        print("4. 📊 Afficher les statistiques TTS")
        print("5. 🔍 Lister les vidéos traduites sans TTS")
        print("6. ⚙️ Changer le moteur TTS (Bark/ElevenLabs)")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            tts.list_available_voices()
        elif choice == "2":
            video_id = input("📹 ID de la vidéo: ").strip()
            if video_id:
                # Récupérer les traductions de la vidéo
                translations = tts.db.get_video_translations(video_id)
                if translations:
                    print(f"📖 Traductions disponibles pour {video_id}:")
                    for i, trans in enumerate(translations):
                        print(f"{i+1}. {trans[3]} ({trans[4]}) - {trans[2]}")
                    
                    try:
                        trans_choice = int(input("🎯 Choisir la traduction (numéro): ")) - 1
                        if 0 <= trans_choice < len(translations):
                            vtt_path = translations[trans_choice][2]
                            voice_preset = input("🎤 Voix (Enter pour défaut): ").strip() or "v2/fr_speaker_7"
                            tts.convert_vtt_to_audio(video_id, vtt_path, voice_preset)
                    except (ValueError, IndexError):
                        print("❌ Choix invalide")
                else:
                    print("❌ Aucune traduction trouvée pour cette vidéo")
        elif choice == "3":
            voice_preset = input("🎤 Voix pour le lot (Enter pour défaut): ").strip() or "v2/fr_speaker_7"
            tts.batch_convert_translations(voice_preset)
        elif choice == "4":
            # Afficher les statistiques TTS
            tts_files = tts.db.get_video_tts_files("")  # Tous les fichiers
            if tts_files:
                total_duration = sum(f[6] or 0 for f in tts_files)
                total_size = sum(f[7] or 0 for f in tts_files)
                print(f"📊 Statistiques TTS:")
                print(f"   Fichiers: {len(tts_files)}")
                print(f"   Durée totale: {total_duration//60}:{total_duration%60:02d}")
                print(f"   Taille totale: {total_size/1024/1024:.2f} MB")
            else:
                print("📊 Aucun fichier TTS trouvé")
        elif choice == "5":
            print("\n🔍 Vidéos traduites sans TTS")
            print("-" * 40)
            
            # Récupérer toutes les vidéos avec traductions mais sans TTS
            all_videos = tts.db.list_all_videos()
            videos_with_translations = [video for video in all_videos if video[6] > 0]  # translation_count > 0
            videos_without_tts = [video for video in videos_with_translations if video[7] == 0]  # tts_count == 0
            
            if not videos_without_tts:
                print("✅ Toutes les vidéos traduites ont déjà un fichier TTS !")
            else:
                print(f"📋 {len(videos_without_tts)} vidéos traduites sans TTS:")
                for i, video in enumerate(videos_without_tts[:10], 1):
                    print(f"{i}. {video[0]} - {video[1][:50]}...")
                
                if len(videos_without_tts) > 10:
                    print(f"... et {len(videos_without_tts) - 10} autres")
        elif choice == "6":
            print("\n⚙️ Changer le moteur TTS")
            print("Moteurs disponibles:")
            print("1. ElevenLabs (recommandé - rapide et haute qualité)")
            print("2. Bark (plus lent mais gratuit)")
            
            engine_choice = input("🎯 Votre choix (1-2): ").strip()
            if engine_choice == "1":
                tts.switch_engine("elevenlabs")
            elif engine_choice == "2":
                tts.switch_engine("bark")
            else:
                print("❌ Choix invalide")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 