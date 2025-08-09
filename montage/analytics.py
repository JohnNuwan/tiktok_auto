#!/usr/bin/env python3
"""
Module d'Analytics pour le Suivi des Performances des Shorts
Analyse et suit les performances des shorts générés
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.manager import VideoDatabase
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

class ShortsAnalytics:
    """Système d'analytics pour les shorts"""
    
    def __init__(self):
        self.db = VideoDatabase()
        self.console = Console()
    
    def track_short_creation(self, video_id: str, platform: str, short_path: str, 
                           duration: float, file_size: int) -> bool:
        """Enregistre la création d'un short"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO shorts_analytics (
                        video_id, platform, short_path, duration, file_size,
                        created_at, status
                    ) VALUES (?, ?, ?, ?, ?, datetime('now'), 'created')
                ''', (video_id, platform, short_path, duration, file_size))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Erreur lors du tracking: {e}")
            return False
    
    def update_short_performance(self, short_path: str, views: int = 0, 
                               likes: int = 0, shares: int = 0, comments: int = 0):
        """Met à jour les performances d'un short"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE shorts_analytics 
                    SET views = ?, likes = ?, shares = ?, comments = ?,
                        last_updated = datetime('now')
                    WHERE short_path = ?
                ''', (views, likes, shares, comments, short_path))
                conn.commit()
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
    
    def get_platform_stats(self, platform: str = None, days: int = 30) -> Dict:
        """Récupère les statistiques par plateforme"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_shorts,
                            AVG(duration) as avg_duration,
                            AVG(file_size) as avg_size,
                            SUM(views) as total_views,
                            SUM(likes) as total_likes,
                            SUM(shares) as total_shares,
                            SUM(comments) as total_comments
                        FROM shorts_analytics 
                        WHERE platform = ? AND created_at >= datetime('now', '-{} days')
                    '''.format(days), (platform,))
                else:
                    cursor.execute('''
                        SELECT 
                            platform,
                            COUNT(*) as total_shorts,
                            AVG(duration) as avg_duration,
                            AVG(file_size) as avg_size,
                            SUM(views) as total_views,
                            SUM(likes) as total_likes,
                            SUM(shares) as total_shares,
                            SUM(comments) as total_comments
                        FROM shorts_analytics 
                        WHERE created_at >= datetime('now', '-{} days')
                        GROUP BY platform
                    '''.format(days))
                
                results = cursor.fetchall()
                return self._format_stats(results, platform)
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des stats: {e}")
            return {}
    
    def get_viral_shorts(self, limit: int = 10) -> List[Dict]:
        """Récupère les shorts les plus viraux"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        video_id, platform, short_path, duration,
                        views, likes, shares, comments,
                        (views + likes * 2 + shares * 5 + comments * 3) as viral_score
                    FROM shorts_analytics 
                    WHERE views > 0 OR likes > 0 OR shares > 0 OR comments > 0
                    ORDER BY viral_score DESC
                    LIMIT ?
                ''', (limit,))
                
                results = cursor.fetchall()
                return [
                    {
                        'video_id': row[0],
                        'platform': row[1],
                        'short_path': row[2],
                        'duration': row[3],
                        'views': row[4],
                        'likes': row[5],
                        'shares': row[6],
                        'comments': row[7],
                        'viral_score': row[8]
                    }
                    for row in results
                ]
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des shorts viraux: {e}")
            return []
    
    def generate_report(self, days: int = 30) -> str:
        """Génère un rapport complet d'analytics"""
        try:
            report = []
            report.append("📊 RAPPORT D'ANALYTICS DES SHORTS")
            report.append("=" * 50)
            report.append(f"Période: {days} derniers jours")
            report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append("")
            
            # Statistiques générales
            stats = self.get_platform_stats(days=days)
            report.append("📈 STATISTIQUES GÉNÉRALES")
            report.append("-" * 30)
            
            for platform, data in stats.items():
                report.append(f"\n🎬 {platform.upper()}:")
                report.append(f"  • Shorts créés: {data.get('total_shorts', 0)}")
                report.append(f"  • Durée moyenne: {data.get('avg_duration', 0):.1f}s")
                report.append(f"  • Taille moyenne: {data.get('avg_size', 0)/1024/1024:.1f}MB")
                report.append(f"  • Vues totales: {data.get('total_views', 0)}")
                report.append(f"  • Likes totaux: {data.get('total_likes', 0)}")
                report.append(f"  • Partages totaux: {data.get('total_shares', 0)}")
                report.append(f"  • Commentaires totaux: {data.get('total_comments', 0)}")
            
            # Shorts viraux
            viral_shorts = self.get_viral_shorts(5)
            if viral_shorts:
                report.append("\n🔥 SHORTS LES PLUS VIRAUX")
                report.append("-" * 30)
                for i, short in enumerate(viral_shorts, 1):
                    report.append(f"\n{i}. {short['video_id']} ({short['platform']})")
                    report.append(f"   Score viral: {short['viral_score']:.0f}")
                    report.append(f"   Vues: {short['views']}, Likes: {short['likes']}, Partages: {short['shares']}")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"❌ Erreur lors de la génération du rapport: {e}"
    
    def _format_stats(self, results: List, platform: str = None) -> Dict:
        """Formate les résultats des statistiques"""
        if platform:
            if results:
                row = results[0]
                return {
                    'total_shorts': row[0] or 0,
                    'avg_duration': row[1] or 0,
                    'avg_size': row[2] or 0,
                    'total_views': row[3] or 0,
                    'total_likes': row[4] or 0,
                    'total_shares': row[5] or 0,
                    'total_comments': row[6] or 0
                }
        else:
            stats = {}
            for row in results:
                platform_name = row[0]
                stats[platform_name] = {
                    'total_shorts': row[1] or 0,
                    'avg_duration': row[2] or 0,
                    'avg_size': row[3] or 0,
                    'total_views': row[4] or 0,
                    'total_likes': row[5] or 0,
                    'total_shares': row[6] or 0,
                    'total_comments': row[7] or 0
                }
            return stats
        return {}

def create_analytics_table():
    """Crée la table analytics dans la base de données"""
    try:
        db = VideoDatabase()
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS shorts_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    short_path TEXT NOT NULL,
                    duration REAL,
                    file_size INTEGER,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES videos (video_id)
                )
            ''')
            conn.commit()
            print("✅ Table analytics créée")
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table: {e}")

def main():
    """Interface CLI pour l'analytics"""
    console = Console()
    title = Panel.fit("📊 Analytics des Shorts", style="bold blue")
    console.print(title)
    
    analytics = ShortsAnalytics()
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "📊 Statistiques par plateforme")
        table.add_row("2", "🔥 Shorts viraux")
        table.add_row("3", "📈 Rapport complet")
        table.add_row("4", "🔄 Mettre à jour performances")
        table.add_row("0", "❌ Quitter")
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-4): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            platform = input("🎬 Plateforme (Enter pour toutes): ").strip() or None
            stats = analytics.get_platform_stats(platform)
            console.print(stats)
        elif choice == "2":
            limit = int(input("🔥 Nombre de shorts (défaut: 10): ").strip() or "10")
            viral_shorts = analytics.get_viral_shorts(limit)
            if viral_shorts:
                table = Table(title="🔥 Shorts Viraux")
                table.add_column("Rang", style="cyan")
                table.add_column("ID", style="green")
                table.add_column("Plateforme", style="yellow")
                table.add_column("Score Viral", style="red")
                table.add_column("Vues", style="blue")
                
                for i, short in enumerate(viral_shorts, 1):
                    table.add_row(
                        str(i),
                        short['video_id'],
                        short['platform'],
                        f"{short['viral_score']:.0f}",
                        str(short['views'])
                    )
                console.print(table)
            else:
                console.print("❌ Aucun short viral trouvé")
        elif choice == "3":
            days = int(input("📈 Nombre de jours (défaut: 30): ").strip() or "30")
            report = analytics.generate_report(days)
            console.print(report)
        elif choice == "4":
            short_path = input("🔄 Chemin du short: ").strip()
            views = int(input("👁️ Vues: ").strip() or "0")
            likes = int(input("❤️ Likes: ").strip() or "0")
            shares = int(input("📤 Partages: ").strip() or "0")
            comments = int(input("💬 Commentaires: ").strip() or "0")
            analytics.update_short_performance(short_path, views, likes, shares, comments)
            console.print("✅ Performances mises à jour")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    create_analytics_table()
    main() 