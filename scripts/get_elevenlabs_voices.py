#!/usr/bin/env python3
"""
Script pour récupérer les voix disponibles dans ElevenLabs
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from elevenlabs import voices, client
    from elevenlabs.text_to_speech.client import TextToSpeechClient, SyncClientWrapper
    import httpx
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.table import Table
    
    # Charger les variables d'environnement
    load_dotenv()
    
    console = Console()
    
    # Configurer la clé API
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key or api_key == "your_elevenlabs_api_key_here":
        console.print("❌ Clé API ElevenLabs non configurée dans .env")
        sys.exit(1)
    
    client.api_key = api_key
    
    # Créer le client wrapper
    httpx_client = httpx.Client()
    client_wrapper = SyncClientWrapper(
        base_url="https://api.elevenlabs.io",
        httpx_client=httpx_client
    )
    
    # Récupérer toutes les voix via l'API REST
    console.print("🔄 Récupération des voix ElevenLabs...")
    
    import requests
    
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    
    response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers)
    
    if response.status_code == 200:
        all_voices = response.json()["voices"]
    else:
        console.print(f"❌ Erreur API: {response.status_code} - {response.text}")
        sys.exit(1)
    
    # Filtrer les voix françaises ou multilingues
    french_voices = []
    for voice in all_voices:
        # Chercher les voix qui supportent le français
        if hasattr(voice, 'labels') and voice.labels:
            if 'french' in voice.labels.get('language', '').lower():
                french_voices.append(voice)
        elif hasattr(voice, 'name') and voice.name:
            # Si pas de labels, on prend toutes les voix disponibles
            french_voices.append(voice)
    
    # Afficher les résultats
    table = Table(title="🎤 Voix disponibles dans ElevenLabs")
    table.add_column("Index", style="cyan")
    table.add_column("Nom", style="green")
    table.add_column("ID", style="yellow")
    table.add_column("Type", style="magenta")
    table.add_column("Langue", style="blue")
    
    for i, voice in enumerate(all_voices[:10]):  # Limiter à 10 voix pour l'affichage
        voice_name = voice.get('name', 'N/A')
        voice_id = voice.get('voice_id', 'N/A')
        voice_type = "Clonée" if voice.get('category', '') == 'cloned' else "Prédéfinie"
        
        # Récupérer la langue
        language = "N/A"
        if 'labels' in voice and voice['labels']:
            language = voice['labels'].get('language', 'N/A')
        
        table.add_row(str(i+1), voice_name, voice_id, voice_type, language)
    
    console.print(table)
    
    # Afficher les IDs pour copier-coller
    console.print("\n📋 IDs des voix (pour copier-coller dans le code):")
    for i, voice in enumerate(all_voices[:6]):  # Prendre les 6 premières
        voice_name = voice.get('name', f'Voice_{i+1}')
        voice_id = voice.get('voice_id', 'N/A')
        console.print(f'"{voice_id}",  # {voice_name}')
    
    console.print(f"\n✅ {len(all_voices)} voix trouvées au total")
    
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Installez ElevenLabs avec: pip install elevenlabs")
except Exception as e:
    print(f"❌ Erreur: {e}") 