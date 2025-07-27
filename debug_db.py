import sqlite3
from database.manager import VideoDatabase

def debug_database():
    db = VideoDatabase()
    
    print("🔍 Debug de la base de données...")
    print(f"📁 Chemin de la DB: {db.db_path}")
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Vérifier les tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Tables disponibles: {[table[0] for table in tables]}")
            
            # Vérifier la structure de tts_files
            cursor.execute("PRAGMA table_info(tts_files)")
            tts_structure = cursor.fetchall()
            print(f"🎵 Structure de tts_files: {tts_structure}")
            
            # Compter les enregistrements TTS
            cursor.execute("SELECT COUNT(*) FROM tts_files")
            tts_count = cursor.fetchone()[0]
            print(f"🎵 Nombre d'enregistrements TTS: {tts_count}")
            
            # Vérifier les traductions
            cursor.execute("SELECT COUNT(*) FROM translations")
            translations_count = cursor.fetchone()[0]
            print(f"🌐 Nombre de traductions: {translations_count}")
            
            # Vérifier les vidéos avec traductions mais sans TTS
            cursor.execute("""
                SELECT COUNT(*) FROM videos v
                JOIN translations t ON v.video_id = t.video_id
                LEFT JOIN tts_files tts ON v.video_id = tts.video_id
                WHERE tts.video_id IS NULL
            """)
            videos_without_tts = cursor.fetchone()[0]
            print(f"⚠️ Vidéos avec traductions mais sans TTS: {videos_without_tts}")
            
            # Afficher quelques exemples
            cursor.execute("""
                SELECT v.video_id, v.title, t.language
                FROM videos v
                JOIN translations t ON v.video_id = t.video_id
                LEFT JOIN tts_files tts ON v.video_id = tts.video_id
                WHERE tts.video_id IS NULL
                LIMIT 5
            """)
            examples = cursor.fetchall()
            print(f"📝 Exemples de vidéos sans TTS: {examples}")
            
    except Exception as e:
        print(f"❌ Erreur lors du debug: {e}")

if __name__ == "__main__":
    debug_database() 