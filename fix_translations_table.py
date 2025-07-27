#!/usr/bin/env python3
"""
Script pour corriger la structure de la table whisper_translations
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import VideoDatabase
import sqlite3

def fix_translations_table():
    """Corrige la structure de la table whisper_translations"""
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Supprimer la table si elle existe (pour la recréer proprement)
            cursor.execute("DROP TABLE IF EXISTS whisper_translations")
            
            # Créer la table avec la bonne structure
            cursor.execute('''
                CREATE TABLE whisper_translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    french_text TEXT NOT NULL,
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
            print("✅ Table whisper_translations recréée avec succès")
                
    except Exception as e:
        print(f"❌ Erreur lors de la correction de la table: {e}")

if __name__ == "__main__":
    fix_translations_table() 