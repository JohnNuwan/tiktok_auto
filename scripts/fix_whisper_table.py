#!/usr/bin/env python3
"""
Script pour corriger la structure de la table whisper_texts
Supprime la colonne text_path qui n'est plus nécessaire
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent))

from database.manager import VideoDatabase
import sqlite3

def fix_whisper_table():
    """Corrige la structure de la table whisper_texts"""
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier si la colonne text_path existe
            cursor.execute("PRAGMA table_info(whisper_texts)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'text_path' in columns:
                print("🔄 Suppression de la colonne text_path...")
                
                # Créer une nouvelle table avec la bonne structure
                cursor.execute('''
                    CREATE TABLE whisper_texts_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT NOT NULL,
                        translated_text TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (video_id) REFERENCES videos (video_id)
                    )
                ''')
                
                # Copier les données existantes (sans text_path)
                cursor.execute('''
                    INSERT INTO whisper_texts_new (video_id, translated_text, created_at)
                    SELECT video_id, translated_text, created_at FROM whisper_texts
                ''')
                
                # Supprimer l'ancienne table
                cursor.execute('DROP TABLE whisper_texts')
                
                # Renommer la nouvelle table
                cursor.execute('ALTER TABLE whisper_texts_new RENAME TO whisper_texts')
                
                # Recréer l'index
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_whisper_texts_video_id 
                    ON whisper_texts (video_id)
                ''')
                
                conn.commit()
                print("✅ Table whisper_texts corrigée avec succès")
            else:
                print("✅ La table whisper_texts a déjà la bonne structure")
                
    except Exception as e:
        print(f"❌ Erreur lors de la correction de la table: {e}")

if __name__ == "__main__":
    fix_whisper_table() 