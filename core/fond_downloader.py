#!/usr/bin/env python3
"""
Module de téléchargement automatique de fonds vidéos
Télécharge des vidéos de fond depuis Pexels, Pixabay, Mixkit
"""

import os
import sys
import json
import requests
import sqlite3
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from config import Config

class FondDownloader:
    """Téléchargeur de fonds vidéos depuis différentes plateformes"""

    def __init__(self, output_dir: str = "assets/videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.console = Console()
        
        # Créer la base de données pour le suivi des fonds
        self.fond_db_path = Path("database/fond_usage.db")
        self.fond_db_path.parent.mkdir(exist_ok=True)
        self._init_fond_database()

        # Mappings thème -> mots-clés de recherche
        self.theme_keywords = {
            "motivation": ["motivation", "inspiration", "success", "achievement", "determination"],
            "success": ["success", "achievement", "victory", "winning", "accomplishment"],
            "philosophy": ["philosophy", "wisdom", "meditation", "reflection", "thinking"],
            "discipline": ["discipline", "routine", "habits", "consistency", "perseverance"],
            "growth": ["growth", "development", "learning", "improvement", "progress"],
            "failure": ["failure", "resilience", "overcoming", "challenge", "struggle"],
            "leadership": ["leadership", "management", "team", "direction", "guidance"],
            "mindset": ["mindset", "attitude", "perspective", "thinking", "mental"],
            "business": ["business", "entrepreneurship", "startup", "office", "work"],
            "health": ["health", "fitness", "wellness", "exercise", "lifestyle"]
        }

        # Configuration des APIs via le module de configuration
        self.pexels_api_key = Config.PEXELS_API_KEY
        self.pixabay_api_key = Config.PIXABAY_API_KEY

    def _init_fond_database(self):
        """Initialise la base de données pour le suivi des fonds"""
        try:
            with sqlite3.connect(self.fond_db_path) as conn:
                cursor = conn.cursor()
                
                # Table pour les fonds téléchargés
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fonds (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        theme TEXT NOT NULL,
                        source TEXT NOT NULL,
                        url TEXT,
                        duration INTEGER,
                        file_size INTEGER,
                        download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP
                    )
                """)
                
                # Table pour l'historique d'utilisation
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS fond_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fond_id INTEGER,
                        video_id TEXT,
                        usage_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (fond_id) REFERENCES fonds (id)
                    )
                """)
                
                conn.commit()
                print("✅ Base de données des fonds initialisée")

        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la base de données: {e}")

    def download_from_pexels(self, theme: str, count: int = 5) -> List[str]:
        """Télécharge des vidéos depuis Pexels"""
        if not self.pexels_api_key:
            print("⚠️  Clé API Pexels non configurée")
            return []

        downloaded_files = []
        keywords = self.theme_keywords.get(theme, [theme])

        for keyword in keywords[:2]:  # Utiliser max 2 mots-clés
            try:
                import pexels
                pexels_client = pexels.Client(self.pexels_api_key)
                
                # Rechercher des vidéos
                videos = pexels_client.search(keyword, page=1, per_page=count)
                
                for video in videos:
                    if hasattr(video, 'video_files') and video.video_files:
                        # Prendre la première qualité disponible
                        video_file = video.video_files[0]
                        video_url = video_file.link
                        
                        # Télécharger la vidéo
                        filename = f"pexels_{theme}_{keyword}_{len(downloaded_files)}.mp4"
                        filepath = self.output_dir / theme / filename
                        filepath.parent.mkdir(exist_ok=True)
                        
                        response = requests.get(video_url, stream=True)
                        if response.status_code == 200:
                            with open(filepath, 'wb') as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            
                            # Enregistrer dans la base de données
                            self._save_fond_record(
                                filename=str(filepath),
                                theme=theme,
                                source="pexels",
                                url=video_url,
                                duration=0,  # Pexels ne fournit pas la durée
                                file_size=filepath.stat().st_size
                            )
                            
                            downloaded_files.append(str(filepath))
                            print(f"✅ Téléchargé: {filename}")
                            
                            if len(downloaded_files) >= count:
                                break
                                
            except ImportError:
                print("⚠️  Module pexels non disponible")
                return []
            except Exception as e:
                print(f"❌ Erreur lors du téléchargement depuis Pexels: {e}")
                continue
        
        return downloaded_files



    def download_from_pixabay(self, theme: str, count: int = 5) -> List[str]:
        """Télécharge des vidéos depuis Pixabay"""
        if not self.pixabay_api_key:
            print("⚠️  Clé API Pixabay non configurée")
            return []

        downloaded_files = []
        keywords = self.theme_keywords.get(theme, [theme])

        for keyword in keywords[:2]:
            try:
                url = "https://pixabay.com/api/videos/"
                params = {
                    "key": self.pixabay_api_key,
                    "q": keyword,
                    "per_page": min(count, 20),
                    "orientation": "vertical"
                }

                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("hits", [])

                    for video in videos[:count]:
                        video_url = video.get("videos", {}).get("large", {}).get("url")
                        
                        if video_url:
                            filename = f"pixabay_{theme}_{video['id']}.mp4"
                            filepath = self.output_dir / theme / filename

                            # Créer le dossier du thème
                            filepath.parent.mkdir(parents=True, exist_ok=True)

                            # Télécharger la vidéo
                            print(f"📥 Téléchargement: {filename}")
                            video_response = requests.get(video_url, timeout=30)
                            
                            if video_response.status_code == 200:
                                with open(filepath, "wb") as f:
                                    f.write(video_response.content)

                                # Enregistrer dans la base de données
                                self._save_fond_record(
                                    filename=filename,
                                    theme=theme,
                                    source="pixabay",
                                    url=video_url,
                                    duration=video.get("duration", 0),
                                    file_size=len(video_response.content)
                                )

                                downloaded_files.append(str(filepath))
                                print(f"✅ Téléchargé: {filename}")

                            else:
                                print(f"❌ Erreur téléchargement: {video_url}")

                else:
                    print(f"❌ Erreur API Pixabay: {response.status_code}")

            except Exception as e:
                print(f"❌ Erreur lors du téléchargement depuis Pixabay: {e}")

        return downloaded_files

    def download_from_mixkit(self, theme: str, count: int = 5) -> List[str]:
        """Télécharge des vidéos depuis Mixkit (gratuit, pas d'API)"""
        # Mixkit n'a pas d'API publique, on simule avec des URLs prédéfinies
        # En pratique, il faudrait faire du web scraping ou utiliser des URLs directes
        
        print("⚠️  Mixkit nécessite une implémentation manuelle (web scraping)")
        return []

    def _save_fond_record(self, filename: str, theme: str, source: str, 
                         url: str = "", duration: int = 0, file_size: int = 0):
        """Sauvegarde un enregistrement de fond dans la base de données"""
        try:
            with sqlite3.connect(self.fond_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO fonds (filename, theme, source, url, duration, file_size)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (filename, theme, source, url, duration, file_size))
                conn.commit()

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde du fond: {e}")

    def download_fonds_for_theme(self, theme: str, count_per_source: int = 3):
        """Télécharge des fonds pour un thème spécifique depuis toutes les sources"""
        print(f"🎥 Téléchargement de fonds pour le thème: {theme}")
        
        total_downloaded = 0
        
        # Pexels
        print(f"\n📡 Téléchargement depuis Pexels...")
        pexels_files = self.download_from_pexels(theme, count_per_source)
        total_downloaded += len(pexels_files)

        # Pixabay
        print(f"\n📡 Téléchargement depuis Pixabay...")
        pixabay_files = self.download_from_pixabay(theme, count_per_source)
        total_downloaded += len(pixabay_files)

        # Mixkit (placeholder)
        print(f"\n📡 Téléchargement depuis Mixkit...")
        mixkit_files = self.download_from_mixkit(theme, count_per_source)
        total_downloaded += len(mixkit_files)

        print(f"\n✅ Total téléchargé: {total_downloaded} fonds pour le thème '{theme}'")
        return total_downloaded

    def download_fonds_for_all_themes(self, count_per_theme: int = 3):
        """Télécharge des fonds pour tous les thèmes"""
        print("🎥 Téléchargement de fonds pour tous les thèmes")
        
        total_downloaded = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📥 Téléchargement...", total=len(self.theme_keywords))

            for theme in self.theme_keywords.keys():
                progress.update(task, description=f"📥 Thème: {theme}")
                
                downloaded = self.download_fonds_for_theme(theme, count_per_theme)
                total_downloaded += downloaded
                
                progress.advance(task)

        print(f"\n✅ Total téléchargé: {total_downloaded} fonds pour tous les thèmes")
        return total_downloaded

    def get_available_fonds(self, theme: str = None) -> List[Dict]:
        """Récupère les fonds disponibles"""
        try:
            with sqlite3.connect(self.fond_db_path) as conn:
                cursor = conn.cursor()
                
                if theme:
                    cursor.execute("""
                        SELECT * FROM fonds WHERE theme = ? ORDER BY usage_count ASC, download_date DESC
                    """, (theme,))
                else:
                    cursor.execute("""
                        SELECT * FROM fonds ORDER BY usage_count ASC, download_date DESC
                    """)
                
                columns = [description[0] for description in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des fonds: {e}")
            return []

    def select_fond_for_video(self, theme: str) -> Optional[str]:
        """Sélectionne un fond pour une vidéo en évitant les répétitions"""
        try:
            fonds = self.get_available_fonds(theme)
            
            if not fonds:
                print(f"⚠️  Aucun fond disponible pour le thème '{theme}'")
                return None

            # Sélectionner le fond le moins utilisé
            selected_fond = min(fonds, key=lambda x: x['usage_count'])
            
            # Mettre à jour le compteur d'utilisation
            with sqlite3.connect(self.fond_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE fonds 
                    SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (selected_fond['id'],))
                conn.commit()

            return str(self.output_dir / theme / selected_fond['filename'])

        except Exception as e:
            print(f"❌ Erreur lors de la sélection du fond: {e}")
            return None

    def display_fond_statistics(self):
        """Affiche les statistiques des fonds"""
        try:
            with sqlite3.connect(self.fond_db_path) as conn:
                cursor = conn.cursor()
                
                # Statistiques par thème
                cursor.execute("""
                    SELECT theme, COUNT(*) as count, AVG(usage_count) as avg_usage
                    FROM fonds 
                    GROUP BY theme 
                    ORDER BY count DESC
                """)
                
                theme_stats = cursor.fetchall()
                
                # Statistiques par source
                cursor.execute("""
                    SELECT source, COUNT(*) as count
                    FROM fonds 
                    GROUP BY source 
                    ORDER BY count DESC
                """)
                
                source_stats = cursor.fetchall()

            # Affichage
            table = Table(title="📊 Statistiques des fonds vidéos")
            table.add_column("Thème", style="cyan")
            table.add_column("Nombre de fonds", style="green")
            table.add_column("Utilisation moyenne", style="yellow")

            for theme, count, avg_usage in theme_stats:
                table.add_row(theme, str(count), f"{avg_usage:.1f}")

            self.console.print(table)

            print(f"\n📡 Sources:")
            for source, count in source_stats:
                print(f"  - {source}: {count} fonds")

        except Exception as e:
            print(f"❌ Erreur lors de l'affichage des statistiques: {e}")

def main():
    """Interface principale du téléchargeur de fonds"""
    console = Console()

    downloader = FondDownloader()

    while True:
        console.print(Panel.fit(
            "🎥 Téléchargeur de Fonds Vidéos",
            style="bold blue"
        ))

        print("\nOptions disponibles:")
        print("1. 🎯 Télécharger des fonds pour un thème spécifique")
        print("2. 🔄 Télécharger des fonds pour tous les thèmes")
        print("3. 📊 Afficher les statistiques des fonds")
        print("4. 🔍 Lister les fonds disponibles")
        print("5. ⚙️  Configurer les clés API")
        print("0. ❌ Retour")

        try:
            choice = input("\n🎯 Votre choix (0-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Retour au menu principal...")
            break

        if choice == "0":
            break
        elif choice == "1":
            print("\n🎨 Thèmes disponibles:")
            for i, theme in enumerate(downloader.theme_keywords.keys(), 1):
                print(f"{i}. {theme}")
            
            theme_choice = input("\n🎯 Choisir un thème (numéro ou nom): ").strip()
            
            if theme_choice.isdigit():
                theme_index = int(theme_choice) - 1
                themes = list(downloader.theme_keywords.keys())
                if 0 <= theme_index < len(themes):
                    theme = themes[theme_index]
                else:
                    print("❌ Choix invalide")
                    continue
            else:
                theme = theme_choice.lower()
                if theme not in downloader.theme_keywords:
                    print("❌ Thème invalide")
                    continue

            count = input("📊 Nombre de fonds par source (défaut: 3): ").strip()
            count = int(count) if count.isdigit() else 3
            
            downloader.download_fonds_for_theme(theme, count)
        elif choice == "2":
            count = input("📊 Nombre de fonds par thème (défaut: 3): ").strip()
            count = int(count) if count.isdigit() else 3
            
            downloader.download_fonds_for_all_themes(count)
        elif choice == "3":
            downloader.display_fond_statistics()
        elif choice == "4":
            theme = input("🎨 Thème (Enter pour tous): ").strip() or None
            fonds = downloader.get_available_fonds(theme)
            
            if fonds:
                table = Table(title="📁 Fonds disponibles")
                table.add_column("Fichier", style="cyan")
                table.add_column("Thème", style="green")
                table.add_column("Source", style="yellow")
                table.add_column("Utilisations", style="red")
                
                for fond in fonds[:20]:  # Limiter à 20 résultats
                    table.add_row(
                        fond['filename'],
                        fond['theme'],
                        fond['source'],
                        str(fond['usage_count'])
                    )
                
                console.print(table)
                
                if len(fonds) > 20:
                    print(f"... et {len(fonds) - 20} autres")
            else:
                print("❌ Aucun fond trouvé")
        elif choice == "5":
            print("\n🔑 Configuration des clés API:")
            print("1. Pexels: https://www.pexels.com/api/")
            print("2. Pixabay: https://pixabay.com/api/docs/")
            print("\n💡 Configurez les variables d'environnement:")
            print("   PEXELS_API_KEY=votre_cle_pexels")
            print("   PIXABAY_API_KEY=votre_cle_pixabay")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 