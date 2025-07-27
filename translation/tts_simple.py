#!/usr/bin/env python3
"""
Module TTS Simple - Génère de l'audio français depuis les textes traduits
Utilise les données de la base de données whisper_translations
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installé. Installez-le avec: pip install python-dotenv")

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from config import Config

# Import Bark
try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    BARK_AVAILABLE = True
except ImportError:
    BARK_AVAILABLE = False
    print("⚠️  Bark n'est pas installé. Installez-le avec: pip install bark")

# Import ElevenLabs
try:
    from elevenlabs import text_to_speech, save
    ELEVENLABS_AVAILABLE = True
except ImportError as e:
    ELEVENLABS_AVAILABLE = False
    print(f"⚠️  ElevenLabs n'est pas installé ou erreur d'import: {e}")
    print("   Installez-le avec: pip install elevenlabs")

class TTSSimple:
    """Gestionnaire TTS simple pour les textes français traduits"""
    
    def __init__(self, output_dir: str = "datas/tts_outputs"):
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
        
        # Voix ElevenLabs (voix publiques)
        self.elevenlabs_voices = [
            "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "AZnzlk1XvdvUeBnXmlld",  # Domi
            "EXAVITQu4vr4xnSDxMaL",  # Bella
            "VR6AewLTigWG4xSOukaG",  # Sam
            "pNInz6obpgDQGcFmaJgB",  # Adam
            "MF3mGyEYCl7XYWbV9V6O",  # Echo
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
            print("✅ Bark disponible")
        except Exception as e:
            print(f"❌ Erreur Bark: {e}")
            BARK_AVAILABLE = False
    
    def _init_elevenlabs(self):
        """Initialise ElevenLabs"""
        try:
            # Vérifier la clé API
            api_key = os.getenv("ELEVENLABS_API_KEY")
            if not api_key:
                print("⚠️  Clé API ElevenLabs non configurée")
                print("   Définissez ELEVENLABS_API_KEY dans les variables d'environnement")
                print("   ElevenLabs sera désactivé mais vous pouvez toujours utiliser Bark")
                ELEVENLABS_AVAILABLE = False
            else:
                # Configurer la clé API via la nouvelle API
                from elevenlabs import client
                self.elevenlabs_client = client.ElevenLabs(api_key=api_key)
                print("✅ ElevenLabs disponible")
        except Exception as e:
            print(f"❌ Erreur ElevenLabs: {e}")
            ELEVENLABS_AVAILABLE = False
    
    def generate_audio_from_text(self, text: str, voice_preset: str = None) -> Optional[str]:
        """Génère de l'audio à partir d'un texte français"""
        if not text or not text.strip():
            print("❌ Texte vide")
            return None
        
        try:
            if self.tts_engine == "bark" and BARK_AVAILABLE:
                return self._generate_bark_audio(text, voice_preset or self.default_bark_voice)
            elif self.tts_engine == "elevenlabs" and ELEVENLABS_AVAILABLE:
                return self._generate_elevenlabs_audio(text, voice_preset or self.default_elevenlabs_voice)
            else:
                print("❌ Aucun moteur TTS disponible")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération audio: {e}")
            return None
    
    def _generate_bark_audio(self, text: str, voice_preset: str) -> Optional[str]:
        """Génère de l'audio avec Bark"""
        try:
            print(f"🎵 Génération Bark avec voix: {voice_preset}")
            
            # Générer l'audio
            audio_array = generate_audio(text, history_prompt=voice_preset)
            
            # Sauvegarder le fichier avec un nom unique
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_path = self.output_dir / f"bark_{voice_preset.replace('/', '_')}_{unique_id}.wav"
            
            import soundfile as sf
            sf.write(str(output_path), audio_array, SAMPLE_RATE)
            
            print(f"✅ Audio Bark généré: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erreur Bark: {e}")
            return None
    
    def _generate_elevenlabs_audio(self, text: str, voice_id: str) -> Optional[str]:
        """Génère de l'audio avec ElevenLabs"""
        try:
            print(f"🎵 Génération ElevenLabs avec voix: {voice_id}")
            
            # Utiliser la nouvelle API d'ElevenLabs
            from elevenlabs import save
            
            # Générer l'audio avec le client
            audio = self.elevenlabs_client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )
            
            # Sauvegarder le fichier avec un nom unique
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            output_path = self.output_dir / f"elevenlabs_{voice_id}_{unique_id}.mp3"
            save(audio, str(output_path))
            
            print(f"✅ Audio ElevenLabs généré: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Erreur ElevenLabs: {e}")
            return None
    
    def save_tts_record(self, video_id: str, audio_path: str, voice_used: str):
        """Sauvegarde l'enregistrement TTS dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Créer la table si elle n'existe pas
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tts_outputs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        audio_path TEXT NOT NULL,
                        voice_used TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (video_id) REFERENCES videos (video_id)
                    )
                ''')
                
                # Insérer l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO tts_outputs 
                    (video_id, audio_path, voice_used, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (video_id, audio_path, voice_used))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde TTS: {e}")
    
    def process_single_tts(self, video_id: str, voice_preset: str = None) -> bool:
        """Traite la génération TTS d'un seul texte"""
        try:
            # Récupérer le texte français depuis la DB
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT french_text FROM whisper_translations 
                    WHERE video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if not result:
                    print(f"❌ Aucun texte français trouvé pour {video_id}")
                    return False
                
                french_text = result[0]
            
            print(f"🎬 TTS pour: {video_id}")
            print(f"📝 Texte français: {french_text[:100]}...")
            
            # Générer l'audio
            audio_path = self.generate_audio_from_text(french_text, voice_preset)
            if not audio_path:
                return False
            
            # Sauvegarder en base de données
            voice_used = voice_preset or (self.default_bark_voice if self.tts_engine == "bark" else self.default_elevenlabs_voice)
            self.save_tts_record(video_id, audio_path, voice_used)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement TTS de {video_id}: {e}")
            return False
    
    def get_french_texts_without_tts(self) -> List[Dict]:
        """Récupère les textes français qui n'ont pas de TTS"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupérer les textes français sans TTS
                cursor.execute('''
                    SELECT wt.video_id, wt.french_text, v.title
                    FROM whisper_translations wt
                    LEFT JOIN videos v ON wt.video_id = v.video_id
                    LEFT JOIN tts_outputs tts ON wt.video_id = tts.video_id
                    WHERE tts.video_id IS NULL
                    ORDER BY wt.created_at DESC
                ''')
                
                results = cursor.fetchall()
                
                texts_without_tts = []
                for video_id, french_text, title in results:
                    texts_without_tts.append({
                        "video_id": video_id,
                        "french_text": french_text,
                        "title": title or video_id
                    })
                
                return texts_without_tts
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return []
    
    def batch_generate_tts(self, limit: int = 20, voice_preset: str = None):
        """Génère du TTS pour plusieurs textes en lot"""
        texts = self.get_french_texts_without_tts()
        
        if not texts:
            print("✅ Tous les textes français ont déjà du TTS généré")
            return
        
        # Limiter le nombre pour les tests
        texts = texts[:limit]
        
        print(f"🎯 {len(texts)} textes à convertir en audio")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🎵 Génération TTS...", total=len(texts))
            
            for text in texts:
                progress.update(task, description=f"🎵 TTS: {text['title'][:30]}...")
                
                success = self.process_single_tts(text['video_id'], voice_preset)
                
                if not success:
                    print(f"❌ Échec du TTS pour {text['video_id']}")
                
                progress.advance(task)
        
        print("✅ Génération TTS terminée")
    
    def list_available_voices(self):
        """Liste les voix disponibles"""
        print("\n🎵 Voix disponibles:")
        
        if BARK_AVAILABLE:
            print("\n🔊 Bark (gratuit):")
            for i, voice in enumerate(self.bark_french_voices, 1):
                print(f"  {i}. {voice}")
        
        if ELEVENLABS_AVAILABLE:
            print("\n🎤 ElevenLabs (premium):")
            for i, voice in enumerate(self.elevenlabs_voices, 1):
                print(f"  {i}. {voice}")
        
        if not BARK_AVAILABLE and not ELEVENLABS_AVAILABLE:
            print("❌ Aucun moteur TTS disponible")
    
    def switch_engine(self, engine: str):
        """Change le moteur TTS"""
        if engine.lower() == "bark" and BARK_AVAILABLE:
            self.tts_engine = "bark"
            print("✅ Moteur TTS changé vers Bark")
        elif engine.lower() == "elevenlabs" and ELEVENLABS_AVAILABLE:
            self.tts_engine = "elevenlabs"
            print("✅ Moteur TTS changé vers ElevenLabs")
        else:
            print("❌ Moteur non disponible")
    
    def read_tts_output(self, video_id: str):
        """Lit une sortie TTS existante"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT audio_path, voice_used FROM tts_outputs 
                    WHERE video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if result:
                    audio_path, voice_used = result
                    print(f"🎵 TTS pour {video_id}:")
                    print(f"📁 Fichier: {audio_path}")
                    print(f"🎤 Voix: {voice_used}")
                else:
                    print(f"❌ Aucun TTS trouvé pour {video_id}")
                    
        except Exception as e:
            print(f"❌ Erreur lors de la lecture: {e}")


def create_tts_outputs_table():
    """Crée la table tts_outputs"""
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table tts_outputs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tts_outputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    audio_path TEXT NOT NULL,
                    voice_used TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Créer un index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tts_outputs_video_id 
                ON tts_outputs (video_id)
            ''')
            
            conn.commit()
            print("✅ Table tts_outputs créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")


def main():
    """Interface principale du module TTSSimple"""
    console = Console()
    
    if not BARK_AVAILABLE and not ELEVENLABS_AVAILABLE:
        console.print(Panel(
            "❌ Aucun moteur TTS disponible\n\n"
            "Installez au moins un moteur:\n"
            "pip install bark\n"
            "pip install elevenlabs",
            title="Installation requise",
            style="red"
        ))
        return
    
    # Créer la table si elle n'existe pas
    create_tts_outputs_table()
    
    tts = TTSSimple()
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🎵 Générateur TTS Simple",
            style="bold magenta"
        ))
        
        print(f"\nMoteur actuel: {tts.tts_engine.upper()}")
        print("\nOptions disponibles:")
        print("1. 🎵 Générer TTS pour un texte spécifique")
        print("2. 🔄 Génération TTS en lot (limité à 20 textes)")
        print("3. 📊 Afficher les statistiques")
        print("4. 🔍 Lister les textes sans TTS")
        print("5. 📖 Lire une sortie TTS existante")
        print("6. 🎤 Lister les voix disponibles")
        print("7. ⚙️ Changer de moteur TTS")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            video_id = input("🎬 ID du fichier audio: ").strip()
            
            # Demander la voix si nécessaire
            voice = None
            if tts.tts_engine == "bark":
                voice = input(f"🎤 Voix Bark (Enter pour {tts.default_bark_voice}): ").strip() or tts.default_bark_voice
            else:
                voice = input(f"🎤 Voix ElevenLabs (Enter pour {tts.default_elevenlabs_voice}): ").strip() or tts.default_elevenlabs_voice
            
            success = tts.process_single_tts(video_id, voice)
            if success:
                print("✅ Génération TTS terminée avec succès")
            else:
                print("❌ Échec de la génération TTS")
        elif choice == "2":
            limit = input("📊 Nombre max de textes (Enter pour 20): ").strip() or "20"
            
            # Demander la voix
            voice = None
            if tts.tts_engine == "bark":
                voice = input(f"🎤 Voix Bark (Enter pour {tts.default_bark_voice}): ").strip() or tts.default_bark_voice
            else:
                voice = input(f"🎤 Voix ElevenLabs (Enter pour {tts.default_elevenlabs_voice}): ").strip() or tts.default_elevenlabs_voice
            
            tts.batch_generate_tts(int(limit), voice)
        elif choice == "3":
            # Statistiques
            with sqlite3.connect(tts.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM tts_outputs")
                count = cursor.fetchone()[0]
                print(f"📊 {count} fichiers TTS générés")
        elif choice == "4":
            texts = tts.get_french_texts_without_tts()
            print(f"🔍 {len(texts)} textes sans TTS")
            for text in texts[:10]:  # Afficher les 10 premiers
                print(f"  - {text['video_id']}: {text['title']}")
        elif choice == "5":
            video_id = input("🎬 ID du fichier audio: ").strip()
            tts.read_tts_output(video_id)
        elif choice == "6":
            tts.list_available_voices()
        elif choice == "7":
            engine = input("⚙️ Nouveau moteur (bark/elevenlabs): ").strip()
            tts.switch_engine(engine)
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main() 