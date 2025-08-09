#!/usr/bin/env python3
"""
Script pour créer la table audio_translations dans la base de données
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import VideoDatabase

def create_audio_translations_table():
    """Crée la table audio_translations"""
    db = VideoDatabase()
    
    try:
        import sqlite3
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table audio_translations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    audio_path TEXT NOT NULL,
                    voice_preset TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            
            # Créer un index pour améliorer les performances
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_audio_translations_video_id 
                ON audio_translations (video_id)
            ''')
            
            conn.commit()
            print("✅ Table audio_translations créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")

if __name__ == "__main__":
    create_audio_translations_table() 