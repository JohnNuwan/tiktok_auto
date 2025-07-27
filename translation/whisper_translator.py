#!/usr/bin/env python3
"""
Module pour traduire l'audio avec Whisper et générer du TTS complet
Approche directe : Audio → Whisper → Texte français → TTS complet
"""

import os
import sys
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

# Import Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️  Whisper n'est pas installé. Installez-le avec: pip install openai-whisper")

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


class WhisperTranslator:
    """Traduit l'audio avec Whisper et génère du TTS complet"""
    
    def __init__(self, output_dir: str = "datas/whisper_translations"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.db = VideoDatabase()
        self.console = Console()
        
        # Configuration des moteurs
        self.whisper_model = None
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
        if WHISPER_AVAILABLE:
            self._init_whisper()
        
        if BARK_AVAILABLE:
            self._init_bark()
        
        if ELEVENLABS_AVAILABLE:
            self._init_elevenlabs()
    
    def _init_whisper(self):
        """Initialise Whisper"""
        try:
            print("🔄 Chargement du modèle Whisper...")
            self.whisper_model = whisper.load_model("base")  # ou "small", "medium", "large"
            print("✅ Whisper initialisé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de Whisper: {e}")
            WHISPER_AVAILABLE = False
    
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
    

    
    def translate_audio_with_whisper(self, audio_path: str) -> Optional[str]:
        """Traduit l'audio en français avec Whisper"""
        if not WHISPER_AVAILABLE or not self.whisper_model:
            print("❌ Whisper n'est pas disponible")
            return None
        
        try:
            print("🔄 Traduction avec Whisper...")
            
            # Transcribe et traduire en français
            result = self.whisper_model.transcribe(
                audio_path,
                task="translate",  # Traduire en anglais d'abord
                language="fr"      # Puis en français
            )
            
            french_text = result["text"].strip()
            print(f"✅ Traduction Whisper: {french_text[:100]}...")
            
            return french_text
            
        except Exception as e:
            print(f"❌ Erreur Whisper: {e}")
            return None
    
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
    
    def save_whisper_translation(self, video_id: str, original_text: str, translated_text: str, 
                               audio_array: np.ndarray, voice_preset: str, 
                               output_filename: Optional[str] = None) -> Optional[str]:
        """Sauvegarde la traduction Whisper complète"""
        try:
            if output_filename is None:
                output_filename = f"{video_id}_whisper_complete.wav"
            
            output_path = self.output_dir / output_filename
            
            # Sauvegarder l'audio
            sf.write(output_path, audio_array, SAMPLE_RATE)
            
            # Enregistrer dans la base de données
            self._save_whisper_record(video_id, original_text, translated_text, str(output_path), voice_preset)
            
            # Afficher les statistiques
            duration = len(audio_array) / SAMPLE_RATE
            size_mb = output_path.stat().st_size / (1024 * 1024)
            
            print(f"💾 Sauvegarde: {output_path}")
            print(f"✅ Audio Whisper généré avec succès: {output_path}")
            print(f"📊 Durée: {duration:.2f}s, Taille: {size_mb:.2f} MB")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return None
    
    def _save_whisper_record(self, video_id: str, original_text: str, translated_text: str, 
                           audio_path: str, voice_preset: str):
        """Enregistre la traduction Whisper dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO whisper_translations 
                    (video_id, original_text, translated_text, audio_path, voice_preset, created_at)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                ''', (video_id, original_text, translated_text, audio_path, voice_preset))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement en DB: {e}")
    
    def process_audio_with_whisper(self, video_id: str, voice_preset: str = None) -> bool:
        """Traite un fichier audio avec Whisper"""
        try:
            # Chemin vers le fichier audio
            audio_path = Path("datas/audios_En") / f"{video_id}.mp3"
            
            if not audio_path.exists():
                print(f"❌ Fichier audio {audio_path} non trouvé")
                return False
            
            print(f"🎬 Traitement de l'audio: {video_id}")
            
            # 1. Traduire avec Whisper
            translated_text = self.translate_audio_with_whisper(str(audio_path))
            if not translated_text:
                return False
            
            # 2. Générer l'audio TTS
            audio_array = self.generate_complete_audio(translated_text, voice_preset)
            if audio_array is None:
                return False
            
            # 3. Sauvegarder
            self.save_whisper_translation(
                video_id=video_id,
                original_text="",  # On pourrait extraire le texte original si nécessaire
                translated_text=translated_text,
                audio_array=audio_array,
                voice_preset=voice_preset or self.default_bark_voice
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_id}: {e}")
            return False
    
    def get_audio_files_without_whisper(self) -> List[Dict]:
        """Récupère les fichiers audio qui n'ont pas de traduction Whisper"""
        try:
            # Dossier contenant les audios en anglais
            audio_dir = Path("datas/audios_En")
            
            if not audio_dir.exists():
                print(f"❌ Dossier {audio_dir} non trouvé")
                return []
            
            # Récupérer tous les fichiers .mp3
            audio_files = list(audio_dir.glob("*.mp3"))
            
            # Filtrer ceux qui n'ont pas de traduction Whisper
            videos_without_whisper = []
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                for audio_file in audio_files:
                    video_id = audio_file.stem  # Nom du fichier sans extension
                    
                    # Vérifier si une traduction Whisper existe déjà
                    cursor.execute('''
                        SELECT 1 FROM whisper_translations 
                        WHERE video_id = ?
                    ''', (video_id,))
                    
                    if not cursor.fetchone():
                        # Récupérer le titre de la vidéo depuis la base de données
                        cursor.execute('''
                            SELECT title FROM videos WHERE video_id = ?
                        ''', (video_id,))
                        
                        result = cursor.fetchone()
                        title = result[0] if result else video_id
                        
                        videos_without_whisper.append({
                            "video_id": video_id,
                            "title": title,
                            "audio_path": str(audio_file)
                        })
            
            return videos_without_whisper
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des fichiers audio: {e}")
            return []
    
    def batch_process_audios(self, voice_preset: str = None, limit: int = 5):
        """Traite plusieurs fichiers audio en lot"""
        audios = self.get_audio_files_without_whisper()
        
        if not audios:
            print("✅ Tous les fichiers audio ont déjà été traités avec Whisper")
            return
        
        # Limiter le nombre de fichiers pour les tests
        audios = audios[:limit]
        
        print(f"🎯 {len(audios)} fichiers audio à traiter avec Whisper")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎙️ Traitement Whisper...", total=len(audios))
            
            for audio in audios:
                progress.update(task, description=f"🎙️ Whisper: {audio['title'][:30]}...")
                
                success = self.process_audio_with_whisper(audio['video_id'], voice_preset)
                
                if not success:
                    print(f"❌ Échec du traitement pour {audio['video_id']}")
                
                progress.advance(task)
        
        print("✅ Traitement Whisper terminé")
    
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


def create_whisper_table():
    """Crée la table whisper_translations"""
    db = VideoDatabase()
    
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table whisper_translations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whisper_translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    original_text TEXT,
                    translated_text TEXT NOT NULL,
                    audio_path TEXT NOT NULL,
                    voice_preset TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Créer un index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_whisper_translations_video_id 
                ON whisper_translations (video_id)
            ''')
            
            conn.commit()
            print("✅ Table whisper_translations créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")


def main():
    """Interface principale du module WhisperTranslator"""
    console = Console()
    
    if not WHISPER_AVAILABLE:
        console.print(Panel(
            "❌ Whisper n'est pas installé\n\n"
            "Installez-le avec:\n"
            "pip install openai-whisper",
            title="Installation requise",
            style="red"
        ))
        return
    
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
    
    # Créer la table si elle n'existe pas
    create_whisper_table()
    
    translator = WhisperTranslator()
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🎙️ Traducteur Whisper Complet",
            style="bold blue"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🎤 Lister les voix disponibles")
        print("2. 🎙️ Traiter un fichier audio spécifique avec Whisper")
        print("3. 🔄 Traitement en lot (limité à 5 fichiers)")
        print("4. 📊 Afficher les statistiques")
        print("5. 🔍 Lister les fichiers audio sans traduction Whisper")
        print("6. ⚙️ Changer le moteur TTS (Bark/ElevenLabs)")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            translator.list_available_voices()
        elif choice == "2":
            video_id = input("🎬 ID du fichier audio: ").strip()
            voice_preset = input("🎤 Voix (Enter pour défaut): ").strip() or None
            
            success = translator.process_audio_with_whisper(video_id, voice_preset)
            if success:
                print("✅ Traitement Whisper terminé avec succès")
            else:
                print("❌ Échec du traitement Whisper")
        elif choice == "3":
            voice_preset = input("🎤 Voix pour le lot (Enter pour défaut): ").strip() or None
            limit = input("📊 Nombre max de fichiers (Enter pour 5): ").strip() or "5"
            translator.batch_process_audios(voice_preset, int(limit))
        elif choice == "4":
            # Statistiques
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM whisper_translations")
                count = cursor.fetchone()[0]
                print(f"📊 {count} traductions Whisper générées")
        elif choice == "5":
            audios = translator.get_audio_files_without_whisper()
            print(f"🔍 {len(audios)} fichiers audio sans traduction Whisper")
            for audio in audios[:10]:  # Afficher les 10 premiers
                print(f"  - {audio['video_id']}: {audio['title']}")
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