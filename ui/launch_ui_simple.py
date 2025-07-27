#!/usr/bin/env python3
"""
Script de lancement pour l'interface Streamlit simplifiée TikTok_Auto
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Lance l'interface Streamlit simplifiée"""
    print("🎵 TikTok_Auto - Interface Graphique Simplifiée")
    print("=" * 60)
    
    # Vérifier que Streamlit est installé
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__} détecté")
    except ImportError:
        print("❌ Streamlit non installé")
        print("Installez avec: pip install streamlit")
        return
    
    # Vérifier que l'app existe
    app_path = Path("app_simple.py")
    if not app_path.exists():
        print("❌ Fichier app_simple.py non trouvé")
        return
    
    print("🚀 Lancement de l'interface simplifiée...")
    print("📱 L'interface sera disponible sur: http://localhost:8501")
    print("⏹️  Appuyez sur Ctrl+C pour arrêter")
    print("-" * 60)
    
    try:
        # Lancer Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app_simple.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Interface arrêtée")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main() 