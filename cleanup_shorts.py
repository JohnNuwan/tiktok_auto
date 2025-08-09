#!/usr/bin/env python3
"""
Script de nettoyage et réorganisation du dossier shorts
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_shorts_directory():
    """Nettoie et réorganise le dossier shorts"""
    shorts_dir = Path("datas/shorts")
    
    if not shorts_dir.exists():
        print("❌ Dossier shorts non trouvé")
        return
    
    print("🧹 Nettoyage et réorganisation du dossier shorts...")
    
    # Créer la nouvelle structure
    final_dir = shorts_dir / "final"
    temp_dir = shorts_dir / "temp"
    thumbnails_dir = shorts_dir / "thumbnails"
    platforms_dir = shorts_dir / "platforms"
    
    for dir_path in [final_dir, temp_dir, thumbnails_dir, platforms_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Créer les sous-dossiers des plateformes
    for platform in ["tiktok", "youtube", "instagram"]:
        (platforms_dir / platform).mkdir(parents=True, exist_ok=True)
    
    # Déplacer les fichiers existants
    moved_count = 0
    
    for file_path in shorts_dir.iterdir():
        if file_path.is_file():
            try:
                # Déplacer les thumbnails
                if file_path.name.startswith("thumbnail_"):
                    shutil.move(str(file_path), str(thumbnails_dir / file_path.name))
                    moved_count += 1
                    print(f"📁 Déplacé thumbnail: {file_path.name}")
                
                # Déplacer les shorts finaux
                elif file_path.name.startswith("final_short_"):
                    shutil.move(str(file_path), str(final_dir / file_path.name))
                    moved_count += 1
                    print(f"📁 Déplacé short final: {file_path.name}")
                
                # Déplacer les shorts par plateforme
                elif file_path.name.startswith("short_"):
                    if "tiktok" in file_path.name:
                        shutil.move(str(file_path), str(platforms_dir / "tiktok" / file_path.name))
                    elif "youtube" in file_path.name:
                        shutil.move(str(file_path), str(platforms_dir / "youtube" / file_path.name))
                    elif "instagram" in file_path.name:
                        shutil.move(str(file_path), str(platforms_dir / "instagram" / file_path.name))
                    else:
                        shutil.move(str(file_path), str(platforms_dir / "tiktok" / file_path.name))
                    moved_count += 1
                    print(f"📁 Déplacé short: {file_path.name}")
                
                # Déplacer les fichiers temporaires
                elif any(file_path.name.startswith(prefix) for prefix in ["extended_", "trimmed_", "concat_list_"]):
                    shutil.move(str(file_path), str(temp_dir / file_path.name))
                    moved_count += 1
                    print(f"📁 Déplacé fichier temporaire: {file_path.name}")
                
            except Exception as e:
                print(f"⚠️ Erreur lors du déplacement de {file_path.name}: {e}")
    
    print(f"✅ {moved_count} fichiers déplacés")
    
    # Nettoyer les fichiers temporaires
    temp_files = list(temp_dir.glob("*"))
    cleaned_count = 0
    
    for file_path in temp_files:
        try:
            if file_path.is_file():
                file_path.unlink()
                cleaned_count += 1
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {file_path.name}: {e}")
    
    print(f"🧹 {cleaned_count} fichiers temporaires supprimés")
    
    # Afficher la nouvelle structure
    print("\n📁 Nouvelle structure du dossier shorts:")
    for root, dirs, files in os.walk(shorts_dir):
        level = root.replace(str(shorts_dir), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:  # Afficher seulement les 5 premiers fichiers
            print(f"{subindent}{file}")
        if len(files) > 5:
            print(f"{subindent}... et {len(files) - 5} autres fichiers")

if __name__ == "__main__":
    cleanup_shorts_directory()
