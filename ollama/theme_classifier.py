#!/usr/bin/env python3
"""
Module d'analyse thématique avec Ollama
Classifie automatiquement les vidéos par thème (motivation, succès, etc.)
"""

import os
import sys
import json
import requests
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import List, Dict, Optional, Tuple
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from database.manager import VideoDatabase
from config import Config

class ThemeClassifier:
    """Classifieur thématique utilisant Ollama"""

    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = ollama_url or Config.OLLAMA_HOST
        self.model = model or Config.OLLAMA_MODEL
        self.db = VideoDatabase()
        self.console = Console()

        # Thèmes supportés avec leurs descriptions
        self.themes = {
            "motivation": "Discours motivants, encouragement, inspiration personnelle",
            "success": "Histoires de réussite, accomplissements, victoires",
            "philosophy": "Réflexions profondes, sagesse, pensée philosophique",
            "discipline": "Autodiscipline, habitudes, routines, persévérance",
            "growth": "Développement personnel, apprentissage, amélioration",
            "failure": "Leçons d'échec, résilience, rebond après échec",
            "leadership": "Leadership, management, influence, direction",
            "mindset": "État d'esprit, mentalité, façon de penser",
            "business": "Entrepreneuriat, business, stratégie commerciale",
            "health": "Santé, bien-être, fitness, mode de vie sain"
        }

        # Vérifier la connexion Ollama
        self._check_ollama_connection()

    def _check_ollama_connection(self):
        """Vérifie la connexion à Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model in model_names:
                    print(f"✅ Ollama connecté - Modèle {self.model} disponible")
                else:
                    print(f"⚠️  Modèle {self.model} non trouvé. Modèles disponibles: {', '.join(model_names[:3])}")
                    if model_names:
                        self.model = model_names[0]
                        print(f"🔄 Utilisation du modèle: {self.model}")
            else:
                print(f"❌ Erreur de connexion Ollama: {response.status_code}")
        except Exception as e:
            print(f"❌ Impossible de se connecter à Ollama: {e}")
            print("💡 Assurez-vous qu'Ollama est installé et en cours d'exécution")

    def _generate_prompt(self, title: str, description: str) -> str:
        """Génère le prompt pour la classification"""
        themes_list = "\n".join([f"- {theme}: {desc}" for theme, desc in self.themes.items()])
        
        prompt = f"""Analyse le contenu suivant et classe-le dans UN SEUL thème parmi ceux listés.

Titre: {title}
Description: {description}

Thèmes disponibles:
{themes_list}

Réponds UNIQUEMENT avec le nom du thème (ex: "motivation", "success", etc.) sans ponctuation ni explication."""

        return prompt

    def classify_video(self, video_id: str, title: str, description: str) -> Optional[str]:
        """Classifie une vidéo par thème"""
        try:
            prompt = self._generate_prompt(title, description)
            
            # Appel à l'API Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                theme = result.get("response", "").strip().lower()
                
                # Nettoyer la réponse
                theme = theme.replace(".", "").replace("!", "").replace("?", "").strip()
                
                # Mapping des variations de thèmes
                theme_mapping = {
                    "motivational": "motivation",
                    "motivating": "motivation",
                    "inspiration": "motivation",
                    "inspiring": "motivation",
                    "successful": "success",
                    "achievement": "success",
                    "philosophical": "philosophy",
                    "wise": "philosophy",
                    "disciplined": "discipline",
                    "growth": "growth",
                    "personal growth": "growth",
                    "self improvement": "growth",
                    "failure": "failure",
                    "failures": "failure",
                    "resilience": "failure",
                    "leader": "leadership",
                    "leading": "leadership",
                    "mindset": "mindset",
                    "attitude": "mindset",
                    "business": "business",
                    "entrepreneur": "business",
                    "entrepreneurship": "business",
                    "healthy": "health",
                    "fitness": "health",
                    "wellness": "health"
                }
                
                # Appliquer le mapping si nécessaire
                if theme in theme_mapping:
                    theme = theme_mapping[theme]
                
                # Vérifier que le thème est valide
                if theme in self.themes:
                    return theme
                else:
                    print(f"⚠️  Thème non reconnu: '{theme}' pour la vidéo {video_id}")
                    return "other"
            else:
                print(f"❌ Erreur API Ollama: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Erreur lors de la classification de {video_id}: {e}")
            return None

    def update_video_theme(self, video_id: str, theme: str):
        """Met à jour le thème d'une vidéo dans la base de données"""
        try:
            import sqlite3
            # Vérifier si la colonne theme existe, sinon l'ajouter
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Vérifier si la colonne theme existe
                cursor.execute("PRAGMA table_info(videos)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if "theme" not in columns:
                    print("🔄 Ajout de la colonne 'theme' à la table videos...")
                    cursor.execute("ALTER TABLE videos ADD COLUMN theme TEXT")
                
                # Mettre à jour le thème
                cursor.execute(
                    "UPDATE videos SET theme = ? WHERE video_id = ?",
                    (theme, video_id)
                )
                
                if cursor.rowcount > 0:
                    print(f"✅ Thème mis à jour: {video_id} -> {theme}")
                else:
                    print(f"⚠️  Vidéo {video_id} non trouvée")

        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour du thème: {e}")

    def classify_all_videos(self, force_reclassify: bool = False):
        """Classifie toutes les vidéos de la base de données"""
        try:
            # Récupérer toutes les vidéos
            videos = self.db.list_all_videos()
            
            if not videos:
                print("❌ Aucune vidéo trouvée dans la base de données")
                return

            # Filtrer les vidéos à classifier
            if force_reclassify:
                videos_to_classify = videos
                print(f"🔄 Reclassification forcée de {len(videos)} vidéos")
            else:
                # Vérifier quelles vidéos n'ont pas de thème
                videos_to_classify = []
                for video in videos:
                    video_id = video[0]
                    with sqlite3.connect(self.db.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT theme FROM videos WHERE video_id = ?", (video_id,))
                        result = cursor.fetchone()
                        if not result or not result[0]:
                            videos_to_classify.append(video)

                print(f"🎯 {len(videos_to_classify)} vidéos à classifier sur {len(videos)} total")

            if not videos_to_classify:
                print("✅ Toutes les vidéos sont déjà classifiées")
                return

            # Classifier les vidéos
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("🧠 Classification en cours...", total=len(videos_to_classify))

                for video in videos_to_classify:
                    video_id, title, description = video[0], video[1], video[2]
                    progress.update(task, description=f"🧠 Classification: {title[:30]}...")

                    theme = self.classify_video(video_id, title, description)
                    if theme:
                        self.update_video_theme(video_id, theme)

                    progress.advance(task)

            print("✅ Classification terminée")

        except Exception as e:
            print(f"❌ Erreur lors de la classification en lot: {e}")

    def get_theme_statistics(self) -> Dict[str, int]:
        """Récupère les statistiques par thème"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT theme, COUNT(*) as count 
                    FROM videos 
                    WHERE theme IS NOT NULL 
                    GROUP BY theme 
                    ORDER BY count DESC
                """)
                
                stats = {}
                for theme, count in cursor.fetchall():
                    stats[theme] = count
                
                return stats

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return {}

    def display_theme_statistics(self):
        """Affiche les statistiques thématiques"""
        stats = self.get_theme_statistics()
        
        if not stats:
            print("📊 Aucune statistique disponible")
            return

        table = Table(title="📊 Statistiques par thème")
        table.add_column("Thème", style="cyan")
        table.add_column("Nombre de vidéos", style="green")
        table.add_column("Description", style="yellow")

        total_videos = sum(stats.values())
        
        for theme, count in stats.items():
            description = self.themes.get(theme, "Thème personnalisé")
            percentage = (count / total_videos * 100) if total_videos > 0 else 0
            table.add_row(
                f"{theme} ({percentage:.1f}%)",
                str(count),
                description
            )

        self.console.print(table)
        print(f"📈 Total: {total_videos} vidéos classifiées")

    def list_unclassified_videos(self) -> List[Tuple[str, str]]:
        """Liste les vidéos non classifiées"""
        try:
            with self.db.db_path as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT video_id, title 
                    FROM videos 
                    WHERE theme IS NULL OR theme = ''
                    ORDER BY created_at DESC
                """)
                
                return cursor.fetchall()

        except Exception as e:
            print(f"❌ Erreur lors de la récupération des vidéos non classifiées: {e}")
            return []

def main():
    """Interface principale du classifieur thématique"""
    console = Console()

    classifier = ThemeClassifier()

    while True:
        console.print(Panel.fit(
            "🧠 Classifieur Thématique avec Ollama",
            style="bold blue"
        ))

        print("\nOptions disponibles:")
        print("1. 🎯 Classifier une vidéo spécifique")
        print("2. 🔄 Classifier toutes les vidéos")
        print("3. 📊 Afficher les statistiques thématiques")
        print("4. 🔍 Lister les vidéos non classifiées")
        print("5. 🎨 Lister les thèmes disponibles")
        print("0. ❌ Retour")

        choice = input("\n🎯 Votre choix (0-5): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            video_id = input("📹 ID de la vidéo: ").strip()
            if video_id:
                # Récupérer les infos de la vidéo
                video_info = classifier.db.get_video_info(video_id)
                if video_info:
                    title = video_info.get('title', '')
                    description = video_info.get('description', '')
                    
                    print(f"🎯 Classification de: {title}")
                    theme = classifier.classify_video(video_id, title, description)
                    if theme:
                        classifier.update_video_theme(video_id, theme)
                        print(f"✅ Thème assigné: {theme}")
                else:
                    print("❌ Vidéo non trouvée")
        elif choice == "2":
            force = input("🔄 Forcer la reclassification ? (y/N): ").strip().lower() == 'y'
            classifier.classify_all_videos(force_reclassify=force)
        elif choice == "3":
            classifier.display_theme_statistics()
        elif choice == "4":
            unclassified = classifier.list_unclassified_videos()
            if unclassified:
                print(f"\n🔍 {len(unclassified)} vidéos non classifiées:")
                for i, (video_id, title) in enumerate(unclassified[:10], 1):
                    print(f"{i}. {video_id} - {title[:50]}...")
                if len(unclassified) > 10:
                    print(f"... et {len(unclassified) - 10} autres")
            else:
                print("✅ Toutes les vidéos sont classifiées")
        elif choice == "5":
            table = Table(title="🎨 Thèmes disponibles")
            table.add_column("Thème", style="cyan")
            table.add_column("Description", style="yellow")
            
            for theme, description in classifier.themes.items():
                table.add_row(theme, description)
            
            console.print(table)
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 