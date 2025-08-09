#!/usr/bin/env python3
"""
Module de Génération de Sous-titres Stylisés
Génère des sous-titres optimisés pour les shorts avec différents styles
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

class SubtitleGenerator:
    """Générateur de sous-titres stylisés pour les shorts"""
    
    def __init__(self, output_dir: str = "datas/subtitles"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Styles de sous-titres pour différentes plateformes
        self.styles = {
            'tiktok': {
                'font_size': 32,
                'font_color': '&Hffffff&',  # Blanc
                'outline_color': '&H000000&',  # Noir
                'border_style': 3,
                'alignment': 2,  # Centré
                'margin_v': 50
            },
            'youtube_shorts': {
                'font_size': 28,
                'font_color': '&Hffffff&',
                'outline_color': '&H000000&',
                'border_style': 3,
                'alignment': 2,
                'margin_v': 40
            },
            'instagram_reels': {
                'font_size': 30,
                'font_color': '&Hffffff&',
                'outline_color': '&H000000&',
                'border_style': 3,
                'alignment': 2,
                'margin_v': 45
            }
        }
    
    def generate_subtitles(self, text: str, style: str = 'tiktok', duration: Optional[float] = None) -> str:
        """Génère des sous-titres stylisés"""
        try:
            # Diviser le texte en phrases
            sentences = self._split_into_sentences(text)
            
            # Créer le fichier SRT
            subtitle_path = self.output_dir / f"subtitles_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.srt"
            
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                for i, sentence in enumerate(sentences, 1):
                    if sentence.strip():
                        # Calculer le timing
                        if duration:
                            # Répartir uniformément sur la durée
                            start_time = (i - 1) * (duration / len(sentences))
                            end_time = i * (duration / len(sentences))
                        else:
                            # Timing par défaut (2-3 secondes par phrase)
                            start_time = (i - 1) * 2.5
                            end_time = start_time + 3.0
                        
                        f.write(f"{i}\n")
                        f.write(f"{self._format_time(start_time)} --> {self._format_time(end_time)}\n")
                        f.write(f"{sentence.strip()}\n\n")
            
            return str(subtitle_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des sous-titres: {e}")
            return ""
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Divise le texte en phrases optimisées pour les sous-titres"""
        # Diviser par points, points d'exclamation et points d'interrogation
        import re
        sentences = re.split(r'[.!?]+', text)
        
        # Nettoyer et filtrer les phrases vides
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Ignorer les phrases trop courtes
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def _format_time(self, seconds: float) -> str:
        """Formate le temps au format SRT"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def generate_ass_subtitles(self, text: str, style: str = 'tiktok') -> str:
        """Génère des sous-titres au format ASS (Advanced SubStation Alpha) pour plus de contrôle"""
        try:
            style_config = self.styles.get(style, self.styles['tiktok'])
            
            # Créer le fichier ASS
            ass_path = self.output_dir / f"subtitles_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ass"
            
            with open(ass_path, 'w', encoding='utf-8') as f:
                # En-tête ASS
                f.write("[Script Info]\n")
                f.write("Title: Generated Subtitles\n")
                f.write("ScriptType: v4.00+\n")
                f.write("WrapStyle: 1\n")
                f.write("ScaledBorderAndShadow: yes\n")
                f.write("YCbCr Matrix: TV.601\n\n")
                
                # Styles
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write(f"Style: Default,Arial,{style_config['font_size']},{style_config['font_color']},&H00000000,{style_config['outline_color']},&H00000000,0,0,0,0,100,100,0,0,{style_config['border_style']},2,2,{style_config['alignment']},10,10,{style_config['margin_v']},1\n\n")
                
                # Événements (sous-titres)
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                # Diviser le texte en phrases
                sentences = self._split_into_sentences(text)
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        # Timing (2-3 secondes par phrase)
                        start_time = i * 2.5
                        end_time = start_time + 3.0
                        
                        # Formater les temps pour ASS
                        start_ass = self._format_time_ass(start_time)
                        end_ass = self._format_time_ass(end_time)
                        
                        # Écrire l'événement
                        f.write(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{sentence.strip()}\n")
            
            return str(ass_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des sous-titres ASS: {e}")
            return ""
    
    def _format_time_ass(self, seconds: float) -> str:
        """Formate le temps au format ASS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def apply_subtitles_to_video(self, video_path: str, subtitle_path: str, output_path: str, style: str = 'tiktok') -> bool:
        """Applique les sous-titres à une vidéo"""
        try:
            if not self._check_ffmpeg():
                print("❌ FFmpeg non disponible")
                return False
            
            style_config = self.styles.get(style, self.styles['tiktok'])
            
            # Construire la commande FFmpeg
            if subtitle_path.endswith('.ass'):
                # Utiliser les sous-titres ASS
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'ass={subtitle_path}',
                    '-c:v', 'libx264', '-c:a', 'copy',
                    '-y', output_path
                ]
            else:
                # Utiliser les sous-titres SRT
                subtitle_style = f"FontSize={style_config['font_size']},PrimaryColour={style_config['font_color']},OutlineColour={style_config['outline_color']},BorderStyle={style_config['border_style']},Alignment={style_config['alignment']},MarginV={style_config['margin_v']}"
                cmd = [
                    'ffmpeg', '-i', video_path,
                    '-vf', f'subtitles={subtitle_path}:force_style=\'{subtitle_style}\'',
                    '-c:v', 'libx264', '-c:a', 'copy',
                    '-y', output_path
                ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Erreur lors de l'application des sous-titres: {e}")
            return False
    
    def _check_ffmpeg(self) -> bool:
        """Vérifie si FFmpeg est disponible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def generate_animated_subtitles(self, text: str, style: str = 'tiktok') -> str:
        """Génère des sous-titres avec animations (fade in/out)"""
        try:
            style_config = self.styles.get(style, self.styles['tiktok'])
            
            # Créer le fichier ASS avec animations
            ass_path = self.output_dir / f"animated_subtitles_{style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ass"
            
            with open(ass_path, 'w', encoding='utf-8') as f:
                # En-tête ASS
                f.write("[Script Info]\n")
                f.write("Title: Animated Subtitles\n")
                f.write("ScriptType: v4.00+\n")
                f.write("WrapStyle: 1\n")
                f.write("ScaledBorderAndShadow: yes\n")
                f.write("YCbCr Matrix: TV.601\n\n")
                
                # Styles avec animations
                f.write("[V4+ Styles]\n")
                f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
                f.write(f"Style: Default,Arial,{style_config['font_size']},{style_config['font_color']},&H00000000,{style_config['outline_color']},&H00000000,0,0,0,0,100,100,0,0,{style_config['border_style']},2,2,{style_config['alignment']},10,10,{style_config['margin_v']},1\n\n")
                
                # Événements avec animations
                f.write("[Events]\n")
                f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
                sentences = self._split_into_sentences(text)
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        start_time = i * 3.0
                        end_time = start_time + 3.0
                        
                        start_ass = self._format_time_ass(start_time)
                        end_ass = self._format_time_ass(end_time)
                        
                        # Ajouter des animations (fade in/out)
                        animated_text = f"{{\\fad(200,200)}}{sentence.strip()}"
                        f.write(f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{animated_text}\n")
            
            return str(ass_path)
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des sous-titres animés: {e}")
            return ""

def main():
    """Interface CLI pour le générateur de sous-titres"""
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    
    console = Console()
    title = Panel.fit("📝 Générateur de Sous-titres Stylisés", style="bold blue")
    console.print(title)
    
    generator = SubtitleGenerator()
    
    while True:
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("1", "📝 Générer sous-titres SRT")
        table.add_row("2", "🎨 Générer sous-titres ASS")
        table.add_row("3", "✨ Générer sous-titres animés")
        table.add_row("4", "🎬 Appliquer à une vidéo")
        table.add_row("0", "❌ Quitter")
        console.print(table)
        
        choice = input("\n🎯 Votre choix (0-4): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            text = input("📝 Texte: ").strip()
            style = input("🎨 Style (tiktok/youtube_shorts/instagram_reels): ").strip() or "tiktok"
            subtitle_path = generator.generate_subtitles(text, style)
            if subtitle_path:
                console.print(f"✅ Sous-titres générés: {subtitle_path}")
        elif choice == "2":
            text = input("📝 Texte: ").strip()
            style = input("🎨 Style (tiktok/youtube_shorts/instagram_reels): ").strip() or "tiktok"
            subtitle_path = generator.generate_ass_subtitles(text, style)
            if subtitle_path:
                console.print(f"✅ Sous-titres ASS générés: {subtitle_path}")
        elif choice == "3":
            text = input("📝 Texte: ").strip()
            style = input("🎨 Style (tiktok/youtube_shorts/instagram_reels): ").strip() or "tiktok"
            subtitle_path = generator.generate_animated_subtitles(text, style)
            if subtitle_path:
                console.print(f"✅ Sous-titres animés générés: {subtitle_path}")
        elif choice == "4":
            video_path = input("🎬 Chemin de la vidéo: ").strip()
            subtitle_path = input("📝 Chemin des sous-titres: ").strip()
            output_path = input("🎬 Chemin de sortie: ").strip()
            style = input("🎨 Style (tiktok/youtube_shorts/instagram_reels): ").strip() or "tiktok"
            if generator.apply_subtitles_to_video(video_path, subtitle_path, output_path, style):
                console.print(f"✅ Sous-titres appliqués: {output_path}")
            else:
                console.print("❌ Erreur lors de l'application")
        else:
            print("❌ Choix invalide")

if __name__ == "__main__":
    main() 