#!/usr/bin/env python3
"""
Module pour traduire l'audio complet et générer du TTS complet
Approche alternative au système VTT segmenté
"""

import os
import sys
import re
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List
import numpy as np
import soundfile as sf

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from config import Config
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Import Bark
try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    BARK_AVAILABLE = True
except ImportError:
    BARK_AVAILABLE = False
    print("⚠️  Bark n'est pas installé. Installez-le avec: pip install git+https://github.com/suno-ai/bark.git")

# Import ElevenLabs
try:
    from elevenlabs import voices, client
    from elevenlabs.text_to_speech.client import TextToSpeechClient, SyncClientWrapper
    import httpx
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️  ElevenLabs n'est pas installé. Installez-le avec: pip install elevenlabs")


class AudioTranslator:
    """Traduit l'audio complet et génère du TTS complet"""
    
    def __init__(self, output_dir: str = "datas/audio_translations"):
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
        
        # Voix disponibles dans ElevenLabs
        self.elevenlabs_french_voices = [
            "21m00Tcm4TlvDq8ikWAM",  # Rachel (voix féminine anglaise)
            "AZnzlk1XvdvUeBnXmlld",  # Domi (voix féminine anglaise)
            "EXAVITQu4vr4xnSDxMaL",  # Bella (voix féminine anglaise)
            "VR6AewLTigWG4xSOukaG",  # Sam (voix masculine anglaise)
            "pNInz6obpgDQGcFmaJgB",  # Adam (voix masculine anglaise)
            "MF3mGyEYCl7XYWbV9V6O",  # Echo (voix masculine anglaise)
        ]
        
        # Voix par défaut
        self.default_bark_voice = "v2/fr_speaker_7"
        self.default_elevenlabs_voice = "21m00Tcm4TlvDq8ikWAM"
        
        # Initialiser les moteurs
        if BARK_AVAILABLE:
            self._init_bark()
        
        if ELEVENLABS_AVAILABLE:
            self._init_elevenlabs()
    
    def _init_bark(self):
        """Initialise Bark"""
        try:
            print("✅ Bark disponible (modèles chargés à la demande)")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Bark: {e}")
            BARK_AVAILABLE = False
    
    def _init_elevenlabs(self):
        """Initialise ElevenLabs"""
        try:
            api_key = Config.ELEVENLABS_API_KEY
            if api_key and api_key != "your_elevenlabs_api_key_here":
                client.api_key = api_key
                print("✅ ElevenLabs initialisé avec succès")
            else:
                print("⚠️  Clé API ElevenLabs non configurée dans .env")
                ELEVENLABS_AVAILABLE = False
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation d'ElevenLabs: {e}")
            ELEVENLABS_AVAILABLE = False
    
    def extract_full_text_from_vtt(self, vtt_path: str) -> str:
        """Extrait le texte complet d'un fichier VTT"""
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Supprimer les timestamps et garder seulement le texte
            # Pattern pour extraire le texte entre les timestamps
            pattern = r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}\n([\s\S]*?)(?=\n\n|\n\d{2}:\d{2}:\d{2}\.\d{3} -->|\Z)'
            matches = re.findall(pattern, content)
            
            # Combiner tous les segments
            full_text = ""
            for match in matches:
                # Nettoyer le texte
                text = re.sub(r'<[^>]+>', '', match).strip()  # Supprimer les tags HTML
                text = re.sub(r'\n+', ' ', text).strip()     # Remplacer les sauts de ligne
                
                if text:
                    full_text += text + " "
            
            return full_text.strip()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'extraction du texte de {vtt_path}: {e}")
            return ""
    
    def generate_complete_audio(self, text: str, voice_preset: str = None) -> Optional[np.ndarray]:
        """Génère l'audio complet pour un texte"""
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
            # Précharger les modèles si nécessaire
            preload_models()
            
            # Générer l'audio
            audio_array = generate_audio(text, voice_preset)
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
            audio_array, sample_rate = sf.read(io.BytesIO(audio_bytes))
            return audio_array
            
        except Exception as e:
            print(f"❌ Erreur ElevenLabs pour '{text[:50]}...': {e}")
            return None
    
    def save_audio_translation(self, video_id: str, text: str, audio_array: np.ndarray, 
                             voice_preset: str, output_filename: Optional[str] = None) -> Optional[str]:
        """Sauvegarde la traduction audio complète"""
        try:
            if output_filename is None:
                output_filename = f"{video_id}_complete.wav"
            
            output_path = self.output_dir / output_filename
            
            # Sauvegarder l'audio
            sf.write(output_path, audio_array, SAMPLE_RATE)
            
            # Enregistrer dans la base de données
            self._save_translation_record(video_id, text, str(output_path), voice_preset)
            
            # Afficher les statistiques
            duration = len(audio_array) / SAMPLE_RATE
            size_mb = output_path.stat().st_size / (1024 * 1024)
            
            print(f"💾 Sauvegarde: {output_path}")
            print(f"✅ Audio généré avec succès: {output_path}")
            print(f"📊 Durée: {duration:.2f}s, Taille: {size_mb:.2f} MB")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None
    
    def _save_translation_record(self, video_id: str, text: str, audio_path: str, voice_preset: str):
        """Enregistre la traduction dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO audio_translations 
                    (video_id, text, audio_path, voice_preset, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (video_id, text, audio_path, voice_preset))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement en DB: {e}")
    
    def get_videos_with_vtt_translations(self) -> List[Dict]:
        """Récupère les vidéos qui ont des traductions VTT mais pas d'audio complet"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT v.video_id, v.title, t.file_path as translation_path
                    FROM videos v
                    JOIN translations t ON v.video_id = t.video_id
                    WHERE t.language = 'french'
                    AND NOT EXISTS (
                        SELECT 1 FROM audio_translations at 
                        WHERE at.video_id = v.video_id
                    )
                    ORDER BY v.created_at DESC
                ''')
                
                results = cursor.fetchall()
                return [{"video_id": r[0], "title": r[1], "translation_path": r[2]} for r in results]
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des vidéos: {e}")
            return []
    
    def batch_convert_vtt_to_audio(self, voice_preset: str = None):
        """Convertit en lot toutes les traductions VTT en audio complet"""
        videos = self.get_videos_with_vtt_translations()
        
        if not videos:
            print("✅ Toutes les traductions VTT ont déjà été converties en audio complet")
            return
        
        print(f"🎯 {len(videos)} vidéos à convertir en audio complet")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎙️ Conversion en lot...", total=len(videos))
            
            for video in videos:
                progress.update(task, description=f"🎙️ Conversion: {video['title'][:30]}...")
                
                # Extraire le texte complet
                full_text = self.extract_full_text_from_vtt(video['translation_path'])
                
                if not full_text:
                    print(f"⚠️  Texte vide pour {video['video_id']}")
                    progress.advance(task)
                    continue
                
                # Générer l'audio complet
                audio_array = self.generate_complete_audio(full_text, voice_preset)
                
                if audio_array is not None:
                    # Sauvegarder
                    self.save_audio_translation(
                        video_id=video['video_id'],
                        text=full_text,
                        audio_array=audio_array,
                        voice_preset=voice_preset or self.default_bark_voice
                    )
                else:
                    print(f"❌ Échec de génération audio pour {video['video_id']}")
                
                progress.advance(task)
        
        print("✅ Conversion en lot terminée")
    
    def list_available_voices(self):
        """Affiche les voix disponibles"""
        print(f"🎤 Moteur TTS actuel: {self.tts_engine.upper()}")
        
        if self.tts_engine == "bark":
            table = Table(title="🎤 Voix françaises disponibles dans Bark")
            table.add_column("Index", style="cyan")
            table.add_column("Voix", style="green")
            table.add_column("Description", style="yellow")
            
            descriptions = [
                "Voix féminine 1", "Voix masculine 1", "Voix féminine 2",
                "Voix masculine 2", "Voix féminine 3", "Voix masculine 3",
                "Voix féminine 4", "Voix masculine 4"
            ]
            
            for i, voice in enumerate(self.bark_french_voices):
                table.add_row(str(i+1), voice, descriptions[i])
            
            self.console.print(table)
        else:
            table = Table(title="🎤 Voix disponibles dans ElevenLabs")
            table.add_column("Index", style="cyan")
            table.add_column("Voix", style="green")
            table.add_column("Type", style="yellow")
            
            voice_names = ["Rachel", "Domi", "Bella", "Sam", "Adam", "Echo"]
            voice_types = ["Féminine", "Féminine", "Féminine", "Masculine", "Masculine", "Masculine"]
            
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


def main():
    """Interface principale du module AudioTranslator"""
    console = Console()
    
    if not BARK_AVAILABLE and not ELEVENLABS_AVAILABLE:
        console.print(Panel(
            "❌ Aucun moteur TTS disponible\n\n"
            "Installez Bark avec:\n"
            "pip install git+https://github.com/suno-ai/bark.git\n\n"
            "Ou ElevenLabs avec:\n"
            "pip install elevenlabs",
            title="Installation requise",
            style="red"
        ))
        return
    
    translator = AudioTranslator()
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🎙️ Traducteur Audio Complet",
            style="bold blue"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🎤 Lister les voix disponibles")
        print("2. 🎙️ Convertir une traduction VTT spécifique")
        print("3. 🔄 Conversion en lot (toutes les traductions VTT)")
        print("4. 📊 Afficher les statistiques")
        print("5. 🔍 Lister les vidéos avec VTT sans audio complet")
        print("6. ⚙️ Changer le moteur TTS (Bark/ElevenLabs)")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            translator.list_available_voices()
        elif choice == "2":
            video_id = input("🎬 ID de la vidéo: ").strip()
            voice_preset = input("🎤 Voix (Enter pour défaut): ").strip() or None
            
            # Récupérer le chemin VTT
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT file_path FROM translations 
                    WHERE video_id = ? AND language = 'french'
                ''', (video_id,))
                result = cursor.fetchone()
                
                if result:
                    vtt_path = result[0]
                    full_text = translator.extract_full_text_from_vtt(vtt_path)
                    
                    if full_text:
                        print(f"📖 Texte extrait ({len(full_text)} caractères): {full_text[:100]}...")
                        
                        audio_array = translator.generate_complete_audio(full_text, voice_preset)
                        if audio_array is not None:
                            translator.save_audio_translation(
                                video_id=video_id,
                                text=full_text,
                                audio_array=audio_array,
                                voice_preset=voice_preset or translator.default_bark_voice
                            )
                    else:
                        print("❌ Impossible d'extraire le texte du fichier VTT")
                else:
                    print("❌ Traduction VTT non trouvée pour cette vidéo")
        elif choice == "3":
            voice_preset = input("🎤 Voix pour le lot (Enter pour défaut): ").strip() or None
            translator.batch_convert_vtt_to_audio(voice_preset)
        elif choice == "4":
            # Statistiques
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM audio_translations")
                count = cursor.fetchone()[0]
                print(f"📊 {count} traductions audio complètes générées")
        elif choice == "5":
            videos = translator.get_videos_with_vtt_translations()
            print(f"🔍 {len(videos)} vidéos avec VTT sans audio complet")
            for video in videos[:10]:  # Afficher les 10 premières
                print(f"  - {video['video_id']}: {video['title']}")
        elif choice == "6":
            print("\n⚙️ Changer le moteur TTS")
            print("Moteurs disponibles:")
            print("1. Bark (plus lent mais gratuit)")
            print("2. ElevenLabs (recommandé - rapide et haute qualité)")
            
            engine_choice = input("🎯 Votre choix (1-2): ").strip()
            if engine_choice == "1":
                translator.switch_engine("bark")
            elif engine_choice == "2":
                translator.switch_engine("elevenlabs")
            else:
                print("❌ Choix invalide")
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main() 