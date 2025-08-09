#!/usr/bin/env python3
"""
Module de Détection de Moments Viraux
Utilise l'IA pour identifier automatiquement les segments les plus viraux
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import ollama
from config import Config

class ViralDetector:
    """Détecteur de moments viraux avec IA"""
    
    def __init__(self):
        self.db_path = "videos.db"
    
    def analyze_viral_potential(self, video_id: str) -> List[Dict]:
        """Analyse le potentiel viral d'une vidéo"""
        try:
            # Récupérer la transcription
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT french_text FROM whisper_translations 
                    WHERE video_id = ?
                ''', (video_id,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"❌ Transcription non trouvée pour {video_id}")
                    return []
                
                text = result[0]
                
                # Analyser avec l'IA
                viral_segments = self._ai_analysis(text)
                return viral_segments
                
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse: {e}")
            return []
    
    def _ai_analysis(self, text: str) -> List[Dict]:
        """Analyse le texte avec l'IA pour trouver les moments viraux"""
        try:
            # Diviser le texte en segments
            segments = self._split_text_into_segments(text)
            
            # Analyser chaque segment
            viral_segments = []
            for i, segment in enumerate(segments):
                score = self._calculate_viral_score(segment)
                if score > 0.6:  # Seuil élevé pour les moments viraux
                    viral_segments.append({
                        'title': self._generate_title(segment),
                        'start_time': i * 30,
                        'end_time': min((i + 1) * 30, 90),
                        'text': segment,
                        'viral_score': score,
                        'justification': self._generate_justification(segment, score)
                    })
            
            # Trier par score viral
            viral_segments.sort(key=lambda x: x['viral_score'], reverse=True)
            return viral_segments[:5]  # Top 5
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse IA: {e}")
            return []
    
    def _split_text_into_segments(self, text: str, max_duration: int = 90) -> List[str]:
        """Divise le texte en segments optimisés"""
        words = text.split()
        segments = []
        current_segment = []
        current_length = 0
        
        for word in words:
            current_segment.append(word)
            current_length += len(word) + 1
            
            # Estimer la durée (environ 150 mots par minute)
            estimated_duration = (current_length / 150) * 60
            
            if estimated_duration >= max_duration:
                segments.append(' '.join(current_segment))
                current_segment = []
                current_length = 0
        
        if current_segment:
            segments.append(' '.join(current_segment))
        
        return segments
    
    def _calculate_viral_score(self, text: str) -> float:
        """Calcule un score viral pour un segment"""
        # Mots-clés viraux avec poids (étendus)
        viral_keywords = {
            # Mots-clés de révélation et secrets
            'secret': 0.9, 'révélation': 0.95, 'choc': 0.8, 'incroyable': 0.7,
            'jamais': 0.6, 'toujours': 0.5, 'erreur': 0.7, 'succès': 0.6,
            'échec': 0.7, 'transformation': 0.8, 'méthode': 0.6, 'technique': 0.5,
            'astuce': 0.7, 'conseil': 0.6, 'truc': 0.5, 'hack': 0.8,
            'lifehack': 0.9, 'productivité': 0.6, 'argent': 0.9, 'richesse': 0.9,
            'bonheur': 0.7, 'amour': 0.6, 'relation': 0.5, 'succès': 0.6,
            'échec': 0.7, 'transformation': 0.8, 'méthode': 0.6, 'technique': 0.5,
            
            # Nouveaux mots-clés viraux
            'découverte': 0.8, 'révolutionnaire': 0.9, 'innovant': 0.7,
            'exclusif': 0.8, 'unique': 0.7, 'spécial': 0.6, 'rare': 0.7,
            'puissant': 0.8, 'efficace': 0.7, 'rapide': 0.6, 'facile': 0.6,
            'gratuit': 0.8, 'gratuitement': 0.8, 'économiser': 0.7,
            'gagner': 0.8, 'perdre': 0.7, 'changer': 0.6, 'améliorer': 0.7,
            'développer': 0.6, 'créer': 0.6, 'construire': 0.5, 'réaliser': 0.6,
            'accomplir': 0.7, 'atteindre': 0.6, 'obtenir': 0.6, 'acquérir': 0.6,
            'maîtriser': 0.7, 'dominer': 0.8, 'conquérir': 0.8, 'surmonter': 0.7,
            'résoudre': 0.7, 'trouver': 0.5, 'découvrir': 0.7, 'apprendre': 0.6,
            'comprendre': 0.5, 'savoir': 0.5, 'connaître': 0.5, 'expérimenter': 0.6,
            'tester': 0.5, 'essayer': 0.5, 'proposer': 0.5, 'suggérer': 0.5,
            'recommander': 0.6, 'conseiller': 0.6, 'guider': 0.5, 'aider': 0.5,
            'soutenir': 0.5, 'encourager': 0.6, 'motiver': 0.7, 'inspirer': 0.7,
            'influencer': 0.7, 'impacter': 0.7, 'changer': 0.6, 'transformer': 0.8,
            'révolutionner': 0.9, 'innover': 0.8, 'créer': 0.6, 'inventer': 0.8,
            'développer': 0.6, 'construire': 0.5, 'réaliser': 0.6, 'accomplir': 0.7,
            'atteindre': 0.6, 'obtenir': 0.6, 'acquérir': 0.6, 'maîtriser': 0.7,
            'dominer': 0.8, 'conquérir': 0.8, 'surmonter': 0.7, 'résoudre': 0.7,
            'trouver': 0.5, 'découvrir': 0.7, 'apprendre': 0.6, 'comprendre': 0.5,
            'savoir': 0.5, 'connaître': 0.5, 'expérimenter': 0.6, 'tester': 0.5,
            'essayer': 0.5, 'proposer': 0.5, 'suggérer': 0.5, 'recommander': 0.6,
            'conseiller': 0.6, 'guider': 0.5, 'aider': 0.5, 'soutenir': 0.5,
            'encourager': 0.6, 'motiver': 0.7, 'inspirer': 0.7, 'influencer': 0.7,
            'impacter': 0.7, 'changer': 0.6, 'transformer': 0.8, 'révolutionner': 0.9,
            'innover': 0.8, 'créer': 0.6, 'inventer': 0.8, 'développer': 0.6,
            'construire': 0.5, 'réaliser': 0.6, 'accomplir': 0.7, 'atteindre': 0.6,
            'obtenir': 0.6, 'acquérir': 0.6, 'maîtriser': 0.7, 'dominer': 0.8,
            'conquérir': 0.8, 'surmonter': 0.7, 'résoudre': 0.7, 'trouver': 0.5,
            'découvrir': 0.7, 'apprendre': 0.6, 'comprendre': 0.5, 'savoir': 0.5,
            'connaître': 0.5, 'expérimenter': 0.6, 'tester': 0.5, 'essayer': 0.5,
            'proposer': 0.5, 'suggérer': 0.5, 'recommander': 0.6, 'conseiller': 0.6,
            'guider': 0.5, 'aider': 0.5, 'soutenir': 0.5, 'encourager': 0.6,
            'motiver': 0.7, 'inspirer': 0.7, 'influencer': 0.7, 'impacter': 0.7
        }
        
        text_lower = text.lower()
        total_score = 0
        keyword_count = 0
        
        # Calculer le score basé sur les mots-clés
        for keyword, weight in viral_keywords.items():
            if keyword in text_lower:
                total_score += weight
                keyword_count += 1
        
        # Score basé sur la longueur (optimal: 50-150 mots)
        word_count = len(text.split())
        length_score = 0
        if 50 <= word_count <= 150:
            length_score = 1.0
        elif 30 <= word_count <= 200:
            length_score = 0.8
        elif 20 <= word_count <= 300:
            length_score = 0.6
        else:
            length_score = 0.3
        
        # Score basé sur la structure (questions, exclamations, émotions)
        structure_score = 0
        if '?' in text:
            structure_score += 0.3
        if '!' in text:
            structure_score += 0.2
        if text.startswith(('Le', 'La', 'Les', 'Un', 'Une', 'Ce', 'Cette')):
            structure_score += 0.1
        if any(word in text_lower for word in ['pourquoi', 'comment', 'quand', 'où', 'qui', 'quoi']):
            structure_score += 0.2
        
        # Score basé sur les émotions
        emotion_words = ['amour', 'haine', 'joie', 'tristesse', 'colère', 'peur', 'surprise', 'dégoût']
        emotion_score = sum(0.1 for word in emotion_words if word in text_lower)
        structure_score += min(emotion_score, 0.3)
        
        # Score basé sur les chiffres et statistiques
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            structure_score += 0.1
        
        # Score basé sur les listes
        if any(word in text_lower for word in ['première', 'deuxième', 'troisième', '1.', '2.', '3.']):
            structure_score += 0.2
        
        # Score final pondéré
        keyword_weight = 0.4
        length_weight = 0.25
        structure_weight = 0.35
        
        final_score = (
            (total_score * keyword_weight) + 
            (length_score * length_weight) + 
            (structure_score * structure_weight)
        )
        
        return min(final_score, 1.0)
    
    def _generate_title(self, text: str) -> str:
        """Génère un titre viral pour un segment"""
        try:
            # Utiliser l'IA pour générer un titre
            prompt = f"""
            Génère un titre viral et accrocheur (max 10 mots) pour ce segment de texte.
            Le titre doit être percutant, intriguant et optimisé pour les réseaux sociaux.
            
            Texte: {text[:200]}...
            
            Titre:
            """
            
            response = ollama.chat(
                model=Config.OLLAMA_MODEL,
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            title = response['message']['content'].strip()
            # Nettoyer le titre
            title = title.replace('"', '').replace("'", "").strip()
            return title[:50]  # Limiter la longueur
            
        except Exception as e:
            # Fallback: titre basé sur les mots-clés
            words = text.split()[:5]
            return ' '.join(words) + "..."
    
    def _generate_justification(self, text: str, score: float) -> str:
        """Génère une justification pour le score viral"""
        if score > 0.8:
            return "Segment très viral avec mots-clés puissants et structure optimale"
        elif score > 0.6:
            return "Segment viral avec bon potentiel d'engagement"
        elif score > 0.4:
            return "Segment avec potentiel viral modéré"
        else:
            return "Segment avec potentiel viral limité"
    
    def get_top_viral_moments(self, video_id: str, limit: int = 3) -> List[Dict]:
        """Récupère les moments les plus viraux d'une vidéo"""
        moments = self.analyze_viral_potential(video_id)
        return moments[:limit]
    
    def batch_analyze_videos(self, limit: int = 10) -> Dict[str, List[Dict]]:
        """Analyse en lot plusieurs vidéos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT DISTINCT v.video_id, v.title
                    FROM videos v
                    INNER JOIN whisper_texts w ON v.video_id = w.video_id
                    ORDER BY v.created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                videos = cursor.fetchall()
            
            results = {}
            for video_id, title in videos:
                print(f"🧠 Analyse de {title[:50]}...")
                moments = self.analyze_viral_potential(video_id)
                if moments:
                    results[video_id] = moments
            
            return results
            
        except Exception as e:
            print(f"❌ Erreur lors de l'analyse en lot: {e}")
            return {}

def main():
    """Interface CLI pour le détecteur viral"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    title = Panel.fit("🧠 Détecteur de Moments Viraux", style="bold blue")
    console.print(title)
    
    detector = ViralDetector()
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "🧠 Analyser une vidéo")
        table.add_row("2", "🔄 Analyse en lot")
        table.add_row("3", "📊 Top moments viraux")
        table.add_row("0", "❌ Quitter")
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-3): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            video_id = input("🎬 ID de la vidéo: ").strip()
            moments = detector.analyze_viral_potential(video_id)
            if moments:
                console.print(f"✅ {len(moments)} moments viraux trouvés")
                for i, moment in enumerate(moments, 1):
                    console.print(f"{i}. {moment['title']} (Score: {moment['viral_score']:.2f})")
            else:
                console.print("❌ Aucun moment viral trouvé")
        elif choice == "2":
            limit = int(input("🎬 Nombre de vidéos (défaut: 5): ").strip() or "5")
            results = detector.batch_analyze_videos(limit)
            console.print(f"✅ Analyse terminée: {len(results)} vidéos traitées")
        elif choice == "3":
            video_id = input("🎬 ID de la vidéo: ").strip()
            moments = detector.get_top_viral_moments(video_id)
            if moments:
                console.print("🏆 Top moments viraux:")
                for i, moment in enumerate(moments, 1):
                    console.print(f"{i}. {moment['title']} (Score: {moment['viral_score']:.2f})")
            else:
                console.print("❌ Aucun moment viral trouvé")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 