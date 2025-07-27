#!/usr/bin/env python3
"""
Module pour traduire les textes Whisper de l'anglais vers le français
Lit les textes depuis la DB et les traduit avec une API de traduction
"""

import os
import sys
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# Import de la traduction
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests n'est pas installé. Installez-le avec: pip install requests")


class TextTranslator:
    """Traduit les textes Whisper de l'anglais vers le français"""
    
    def __init__(self):
        self.db = VideoDatabase()
        self.console = Console()
        
        # Configuration de l'API de traduction (LibreTranslate)
        self.translate_api_url = "https://libretranslate.de/translate"
        
    def translate_text(self, english_text: str) -> Optional[str]:
        """Traduit un texte anglais en français"""
        if not REQUESTS_AVAILABLE:
            print("❌ Requests n'est pas disponible")
            return None
        
        try:
            print("🔄 Traduction en français...")
            
            # Utiliser Google Translate (méthode simple)
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "en",
                "tl": "fr",
                "dt": "t",
                "q": english_text
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                # Parse la réponse de Google Translate
                data = response.json()
                french_text = ""
                
                # Extraire le texte traduit
                if data and len(data) > 0 and len(data[0]) > 0:
                    for segment in data[0]:
                        if segment[0]:  # Le texte traduit
                            french_text += segment[0]
                
                if french_text:
                    print(f"✅ Traduction: {french_text[:100]}...")
                    return french_text
                else:
                    print("❌ Aucun texte traduit reçu")
                    return None
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur de traduction: {e}")
            return None
    
    def save_french_translation(self, video_id: str, french_text: str) -> bool:
        """Sauvegarde la traduction française dans la base de données"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Insérer ou mettre à jour l'enregistrement
                cursor.execute('''
                    INSERT OR REPLACE INTO whisper_translations 
                    (video_id, french_text, created_at)
                    VALUES (?, ?, datetime('now'))
                ''', (video_id, french_text))
                
                conn.commit()
                
            print(f"💾 Traduction française sauvegardée pour {video_id}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def get_whisper_texts_without_translation(self) -> List[Dict]:
        """Récupère les textes Whisper qui n'ont pas de traduction française"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Récupérer les textes Whisper sans traduction française
                cursor.execute('''
                    SELECT w.video_id, w.translated_text, v.title
                    FROM whisper_texts w
                    LEFT JOIN videos v ON w.video_id = v.video_id
                    LEFT JOIN whisper_translations wt ON w.video_id = wt.video_id
                    WHERE wt.video_id IS NULL
                    ORDER BY w.created_at DESC
                ''')
                
                results = cursor.fetchall()
                
                texts_without_translation = []
                for video_id, english_text, title in results:
                    texts_without_translation.append({
                        "video_id": video_id,
                        "english_text": english_text,
                        "title": title or video_id
                    })
                
                return texts_without_translation
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return []
    
    def process_single_translation(self, video_id: str) -> bool:
        """Traite la traduction d'un seul texte"""
        try:
            # Récupérer le texte anglais depuis la DB
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT translated_text FROM whisper_texts 
                    WHERE video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if not result:
                    print(f"❌ Aucun texte Whisper trouvé pour {video_id}")
                    return False
                
                english_text = result[0]
            
            print(f"🎬 Traduction de: {video_id}")
            print(f"📝 Texte anglais: {english_text[:100]}...")
            
            # Traduire en français
            french_text = self.translate_text(english_text)
            if not french_text:
                return False
            
            # Sauvegarder
            return self.save_french_translation(video_id, french_text)
            
        except Exception as e:
            print(f"❌ Erreur lors du traitement de {video_id}: {e}")
            return False
    
    def batch_translate_texts(self, limit: int = 20):
        """Traduit plusieurs textes en lot"""
        texts = self.get_whisper_texts_without_translation()
        
        if not texts:
            print("✅ Tous les textes Whisper ont déjà été traduits en français")
            return
        
        # Limiter le nombre pour les tests
        texts = texts[:limit]
        
        print(f"🎯 {len(texts)} textes à traduire en français")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🌐 Traduction française...", total=len(texts))
            
            for text in texts:
                progress.update(task, description=f"🌐 Traduction: {text['title'][:30]}...")
                
                success = self.process_single_translation(text['video_id'])
                
                if not success:
                    print(f"❌ Échec de la traduction pour {text['video_id']}")
                
                progress.advance(task)
        
        print("✅ Traduction française terminée")
    
    def read_french_translation(self, video_id: str):
        """Lit une traduction française existante"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT french_text FROM whisper_translations 
                    WHERE video_id = ?
                ''', (video_id,))
                
                result = cursor.fetchone()
                if result:
                    french_text = result[0]
                    print(f"📖 Traduction française pour {video_id}:")
                    print(f"🇫🇷 Texte: {french_text}")
                else:
                    print(f"❌ Aucune traduction française trouvée pour {video_id}")
                    
        except Exception as e:
            print(f"❌ Erreur lors de la lecture: {e}")


def create_whisper_translations_table():
    """Crée la table whisper_translations"""
    db = VideoDatabase()
    
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            
            # Créer la table whisper_translations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS whisper_translations (
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
            print("✅ Table whisper_translations créée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")


def main():
    """Interface principale du module TextTranslator"""
    console = Console()
    
    if not REQUESTS_AVAILABLE:
        console.print(Panel(
            "❌ Requests n'est pas installé\n\n"
            "Installez-le avec:\n"
            "pip install requests",
            title="Installation requise",
            style="red"
        ))
        return
    
    # Créer la table si elle n'existe pas
    create_whisper_translations_table()
    
    translator = TextTranslator()
    
    while True:
        console.print("\n" + "="*50)
        console.print(Panel(
            "🌐 Traducteur de Textes Whisper",
            style="bold green"
        ))
        
        print("\nOptions disponibles:")
        print("1. 🌐 Traduire un texte spécifique")
        print("2. 🔄 Traduction en lot (limité à 20 textes)")
        print("3. 📊 Afficher les statistiques")
        print("4. 🔍 Lister les textes sans traduction française")
        print("5. 📖 Lire une traduction française existante")
        print("0. ❌ Retour")
        
        choice = input("\n🎯 Votre choix (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            video_id = input("🎬 ID du fichier audio: ").strip()
            
            success = translator.process_single_translation(video_id)
            if success:
                print("✅ Traduction française terminée avec succès")
            else:
                print("❌ Échec de la traduction française")
        elif choice == "2":
            limit = input("📊 Nombre max de textes (Enter pour 20): ").strip() or "20"
            translator.batch_translate_texts(int(limit))
        elif choice == "3":
            # Statistiques
            with sqlite3.connect(translator.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM whisper_translations")
                count = cursor.fetchone()[0]
                print(f"📊 {count} traductions françaises générées")
        elif choice == "4":
            texts = translator.get_whisper_texts_without_translation()
            print(f"🔍 {len(texts)} textes sans traduction française")
            for text in texts[:10]:  # Afficher les 10 premiers
                print(f"  - {text['video_id']}: {text['title']}")
        elif choice == "5":
            video_id = input("🎬 ID du fichier audio: ").strip()
            translator.read_french_translation(video_id)
        else:
            print("❌ Choix invalide")


if __name__ == "__main__":
    main() 