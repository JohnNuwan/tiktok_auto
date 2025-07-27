"""
Module de configuration centralisé
Gestion des variables d'environnement et configurations
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

class Config:
    """Configuration centralisée de l'application"""
    
    # APIs
    PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
    PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')
    
    # Ollama
    OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2')
    
    # Bark TTS
    BARK_VOICE = os.getenv('BARK_VOICE', 'v2/fr_speech_01')
    
    # ElevenLabs TTS
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    
    # Moteur TTS par défaut
    DEFAULT_TTS_ENGINE = os.getenv('DEFAULT_TTS_ENGINE', 'elevenlabs')  # 'bark' ou 'elevenlabs'
    
    # FFmpeg
    FFMPEG_PATH = os.getenv('FFMPEG_PATH')
    
    # Chemins
    OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', 'output'))
    ASSETS_DIR = Path(os.getenv('ASSETS_DIR', 'assets'))
    DATAS_DIR = Path(os.getenv('DATAS_DIR', 'datas'))
    
    @classmethod
    def validate_config(cls):
        """Valide la configuration et affiche les avertissements"""
        warnings = []
        
        if not cls.PEXELS_API_KEY:
            warnings.append("⚠️  PEXELS_API_KEY non configurée - téléchargement Pexels désactivé")
        
        if not cls.PIXABAY_API_KEY:
            warnings.append("⚠️  PIXABAY_API_KEY non configurée - téléchargement Pixabay désactivé")
        
        if not cls.ELEVENLABS_API_KEY:
            warnings.append("⚠️  ELEVENLABS_API_KEY non configurée - TTS ElevenLabs désactivé")
        
        if warnings:
            print("\n".join(warnings))
            print("\n💡 Copiez env.example vers .env et configurez vos clés API")
        
        return len(warnings) == 0
    
    @classmethod
    def get_api_status(cls):
        """Retourne le statut des APIs configurées"""
        return {
            'pexels': bool(cls.PEXELS_API_KEY),
            'pixabay': bool(cls.PIXABAY_API_KEY),
            'ollama': True,  # Ollama est local
            'ffmpeg': bool(cls.FFMPEG_PATH) or cls._check_ffmpeg_system()
        }
    
    @classmethod
    def _check_ffmpeg_system(cls):
        """Vérifie si FFmpeg est disponible dans le PATH système"""
        import subprocess
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False 