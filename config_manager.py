#!/usr/bin/env python3
"""
Gestionnaire de configuration pour TikTok_Auto
Permet de configurer les clés API et paramètres
"""

import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from config import Config

def create_env_file():
    """Crée le fichier .env à partir du template"""
    if os.path.exists('.env'):
        if not Confirm.ask("Le fichier .env existe déjà. Voulez-vous le remplacer ?"):
            return False
    
    if os.path.exists('env.example'):
        shutil.copy('env.example', '.env')
        print("✅ Fichier .env créé à partir du template")
        return True
    else:
        print("❌ Fichier env.example non trouvé")
        return False

def configure_api_keys():
    """Configure les clés API interactivement"""
    console = Console()
    
    print("\n🔑 Configuration des clés API")
    print("=" * 40)
    
    # Pexels API
    print("\n📸 Pexels API (optionnel)")
    print("Obtenez votre clé sur: https://www.pexels.com/api/")
    pexels_key = Prompt.ask("Clé API Pexels", default="")
    if pexels_key:
        os.environ['PEXELS_API_KEY'] = pexels_key
    
    # Pixabay API
    print("\n🎨 Pixabay API (optionnel)")
    print("Obtenez votre clé sur: https://pixabay.com/api/docs/")
    pixabay_key = Prompt.ask("Clé API Pixabay", default="")
    if pixabay_key:
        os.environ['PIXABAY_API_KEY'] = pixabay_key
    
    # Ollama
    print("\n🤖 Configuration Ollama")
    ollama_host = Prompt.ask("Hôte Ollama", default="http://localhost:11434")
    ollama_model = Prompt.ask("Modèle Ollama", default="llama3.2")
    os.environ['OLLAMA_HOST'] = ollama_host
    os.environ['OLLAMA_MODEL'] = ollama_model
    
    # Bark TTS
    print("\n🎙️ Configuration Bark TTS")
    bark_voice = Prompt.ask("Voix Bark par défaut", default="v2/fr_speech_01")
    os.environ['BARK_VOICE'] = bark_voice
    
    # Sauvegarder dans .env
    save_to_env_file()

def save_to_env_file():
    """Sauvegarde les variables dans le fichier .env"""
    env_content = []
    
    # APIs
    if os.getenv('PEXELS_API_KEY'):
        env_content.append(f"PEXELS_API_KEY={os.getenv('PEXELS_API_KEY')}")
    else:
        env_content.append("PEXELS_API_KEY=your_pexels_api_key_here")
    
    if os.getenv('PIXABAY_API_KEY'):
        env_content.append(f"PIXABAY_API_KEY={os.getenv('PIXABAY_API_KEY')}")
    else:
        env_content.append("PIXABAY_API_KEY=your_pixabay_api_key_here")
    
    # Ollama
    env_content.append(f"OLLAMA_HOST={os.getenv('OLLAMA_HOST', 'http://localhost:11434')}")
    env_content.append(f"OLLAMA_MODEL={os.getenv('OLLAMA_MODEL', 'llama3.2')}")
    
    # Bark
    env_content.append(f"BARK_VOICE={os.getenv('BARK_VOICE', 'v2/fr_speech_01')}")
    
    # Chemins
    env_content.append(f"OUTPUT_DIR={os.getenv('OUTPUT_DIR', 'output')}")
    env_content.append(f"ASSETS_DIR={os.getenv('ASSETS_DIR', 'assets')}")
    env_content.append(f"DATAS_DIR={os.getenv('DATAS_DIR', 'datas')}")
    
    with open('.env', 'w') as f:
        f.write('\n'.join(env_content))
    
    print("✅ Configuration sauvegardée dans .env")

def show_config_status():
    """Affiche le statut de la configuration"""
    console = Console()
    
    status = Config.get_api_status()
    
    table = Table(title="📊 Statut de la Configuration")
    table.add_column("Service", style="cyan")
    table.add_column("Statut", style="green")
    table.add_column("Détails", style="white")
    
    # APIs
    table.add_row(
        "Pexels API",
        "✅ Configuré" if status['pexels'] else "❌ Non configuré",
        "Téléchargement de fonds vidéos" if status['pexels'] else "Clé API manquante"
    )
    
    table.add_row(
        "Pixabay API",
        "✅ Configuré" if status['pixabay'] else "❌ Non configuré",
        "Téléchargement de fonds vidéos" if status['pixabay'] else "Clé API manquante"
    )
    
    table.add_row(
        "Ollama",
        "✅ Disponible" if status['ollama'] else "❌ Non disponible",
        f"Hôte: {Config.OLLAMA_HOST}, Modèle: {Config.OLLAMA_MODEL}"
    )
    
    table.add_row(
        "FFmpeg",
        "✅ Installé" if status['ffmpeg'] else "❌ Non installé",
        "Montage vidéo" if status['ffmpeg'] else "Installation requise"
    )
    
    console.print(table)

def main():
    """Menu principal de configuration"""
    console = Console()
    
    title = Panel.fit(
        "⚙️ Gestionnaire de Configuration TikTok_Auto",
        style="bold blue"
    )
    console.print(title)
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        
        table.add_row("1", "📋 Créer fichier .env")
        table.add_row("2", "🔑 Configurer les clés API")
        table.add_row("3", "📊 Afficher le statut")
        table.add_row("4", "✅ Valider la configuration")
        table.add_row("0", "❌ Retour")
        
        console.print(table)
        
        choice = Prompt.ask("Votre choix", choices=["0", "1", "2", "3", "4"])
        
        if choice == "0":
            break
        elif choice == "1":
            create_env_file()
        elif choice == "2":
            configure_api_keys()
        elif choice == "3":
            show_config_status()
        elif choice == "4":
            Config.validate_config()

if __name__ == "__main__":
    main() 