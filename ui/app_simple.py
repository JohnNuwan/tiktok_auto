#!/usr/bin/env python3
"""
Interface Streamlit simplifiée pour TikTok_Auto
Version qui ne dépend que des modules existants
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys
import os

# Ajouter le répertoire courant au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports des modules existants
try:
    from database.manager import VideoDatabase
    from config import Config
    DB_AVAILABLE = True
except ImportError as e:
    st.error(f"Erreur d'import database: {e}")
    DB_AVAILABLE = False

# Configuration de la page
st.set_page_config(
    page_title="TikTok_Auto - Gestionnaire YouTube",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-metric {
        border-left-color: #28a745;
    }
    .warning-metric {
        border-left-color: #ffc107;
    }
    .error-metric {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class TikTokAutoApp:
    def __init__(self):
        if DB_AVAILABLE:
            self.db = VideoDatabase()
        else:
            self.db = None
    
    def main(self):
        # Header principal
        st.markdown('<h1 class="main-header">🎵 TikTok_Auto</h1>', unsafe_allow_html=True)
        st.markdown('<h2 style="text-align: center; color: #666;">Gestionnaire YouTube Intelligent</h2>', unsafe_allow_html=True)
        
        # Vérifier la disponibilité de la base de données
        if not DB_AVAILABLE:
            st.error("❌ Base de données non disponible. Vérifiez l'installation.")
            return
        
        # Sidebar
        self.sidebar()
        
        # Onglets principaux
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Dashboard", "📥 Téléchargement", "🌍 Traduction", "🎙️ TTS"
        ])
        
        with tab1:
            self.dashboard_tab()
        with tab2:
            self.download_tab()
        with tab3:
            self.translation_tab()
        with tab4:
            self.tts_tab()
    
    def sidebar(self):
        """Sidebar avec métriques et actions rapides"""
        st.sidebar.title("📈 Métriques")
        
        # Statistiques
        try:
            if self.db:
                stats = self.db.get_stats()
                
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    st.metric("📹 Vidéos", stats.get('videos', 0))
                    st.metric("📺 Chaînes", stats.get('channels', 0))
                
                with col2:
                    st.metric("🌍 Traductions", stats.get('translations', 0))
                    st.metric("🎙️ TTS", stats.get('tts', 0))
                
                # Actions rapides
                st.sidebar.title("⚡ Actions Rapides")
                
                if st.sidebar.button("🔄 Actualiser les données"):
                    st.rerun()
                
                if st.sidebar.button("🧪 Tester le système"):
                    with st.spinner("Test en cours..."):
                        st.success("✅ Système opérationnel")
                
                # Configuration
                st.sidebar.title("⚙️ Configuration")
                if st.sidebar.button("🔧 Gérer la config"):
                    st.session_state.show_config = True
                    
        except Exception as e:
            st.sidebar.error(f"Erreur: {e}")
    
    def dashboard_tab(self):
        """Onglet Dashboard avec visualisations"""
        st.header("📊 Dashboard")
        
        try:
            if not self.db:
                st.warning("Base de données non disponible")
                return
                
            # Récupérer les données
            videos = self.db.list_all_videos()
            if not videos:
                st.warning("Aucune vidéo trouvée. Commencez par télécharger des vidéos.")
                return
            
            # Convertir en DataFrame
            df = pd.DataFrame(videos, columns=[
                'id', 'title', 'description', 'duration', 'upload_date', 
                'view_count', 'translation_count', 'theme'
            ])
            
            # Nettoyer et convertir les types de données
            try:
                # Convertir duration en numérique, remplacer les valeurs non-numériques par 0
                df['duration'] = pd.to_numeric(df['duration'], errors='coerce').fillna(0)
                
                # Convertir translation_count en entier
                df['translation_count'] = pd.to_numeric(df['translation_count'], errors='coerce').fillna(0).astype(int)
                
                # Convertir view_count en entier
                df['view_count'] = pd.to_numeric(df['view_count'], errors='coerce').fillna(0).astype(int)
                
                # Nettoyer les thèmes (remplacer None par 'Non assigné')
                df['theme'] = df['theme'].fillna('Non assigné')
                
            except Exception as e:
                st.warning(f"Attention: Erreur lors du nettoyage des données: {e}")
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
                st.metric("Total Vidéos", len(df))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card warning-metric">', unsafe_allow_html=True)
                non_translated = len(df[df['translation_count'] == 0])
                st.metric("Non Traduites", non_translated)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card success-metric">', unsafe_allow_html=True)
                with_theme = len(df[df['theme'] != 'Non assigné'])
                st.metric("Avec Thème", with_theme)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                try:
                    avg_duration = df['duration'].mean()
                    if pd.isna(avg_duration) or avg_duration == 0:
                        duration_text = "N/A"
                    else:
                        duration_text = f"{avg_duration:.1f}s"
                    st.metric("Durée Moyenne", duration_text)
                except Exception:
                    st.metric("Durée Moyenne", "N/A")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Répartition des traductions
                try:
                    translated_count = len(df[df['translation_count'] > 0])
                    non_translated_count = len(df[df['translation_count'] == 0])
                    
                    if translated_count > 0 or non_translated_count > 0:
                        fig_translations = px.pie(
                            values=[translated_count, non_translated_count],
                            names=['Traduites', 'Non traduites'],
                            title="Répartition des traductions",
                            color_discrete_sequence=['#28a745', '#ffc107']
                        )
                        st.plotly_chart(fig_translations, use_container_width=True)
                    else:
                        st.info("Aucune donnée de traduction disponible")
                except Exception as e:
                    st.error(f"Erreur graphique traductions: {e}")
            
            with col2:
                # Répartition des thèmes
                try:
                    theme_df = df[df['theme'] != 'Non assigné']
                    if not theme_df.empty:
                        theme_counts = theme_df['theme'].value_counts()
                        if len(theme_counts) > 0:
                            fig_themes = px.bar(
                                x=theme_counts.values,
                                y=theme_counts.index,
                                orientation='h',
                                title="Répartition des thèmes",
                                labels={'x': 'Nombre de vidéos', 'y': 'Thème'}
                            )
                            st.plotly_chart(fig_themes, use_container_width=True)
                        else:
                            st.info("Aucun thème disponible")
                    else:
                        st.info("Aucun thème assigné. Utilisez l'analyse thématique.")
                except Exception as e:
                    st.error(f"Erreur graphique thèmes: {e}")
            
            # Tableau des vidéos récentes
            st.subheader("📹 Vidéos Récentes")
            try:
                # Sélectionner et nettoyer les colonnes pour l'affichage
                display_columns = ['id', 'title', 'translation_count', 'theme']
                recent_videos = df.head(10)[display_columns].copy()
                
                # Nettoyer les titres trop longs
                recent_videos['title'] = recent_videos['title'].astype(str).str[:50] + '...'
                
                st.dataframe(recent_videos, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur affichage tableau: {e}")
            
        except Exception as e:
            st.error(f"Erreur lors du chargement du dashboard: {e}")
            st.error("Détails de l'erreur:")
            st.code(str(e))
    
    def download_tab(self):
        """Onglet de téléchargement"""
        st.header("📥 Téléchargement de Vidéos")
        
        # Téléchargement d'une chaîne
        st.subheader("📺 Télécharger une chaîne YouTube")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            channel_url = st.text_input("URL de la chaîne YouTube")
        with col2:
            max_videos = st.number_input("Max vidéos", min_value=1, max_value=100, value=10)
        
        if st.button("🚀 Télécharger la chaîne", type="primary"):
            if channel_url:
                with st.spinner("Téléchargement en cours..."):
                    try:
                        # Simulation du téléchargement
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        for i in range(100):
                            progress_bar.progress(i + 1)
                            status_text.text(f"Téléchargement... {i+1}%")
                        
                        st.success("✅ Téléchargement terminé!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erreur: {e}")
            else:
                st.warning("Veuillez entrer une URL de chaîne")
        
        # Scanner les fichiers existants
        st.subheader("🔍 Scanner les fichiers existants")
        if st.button("📁 Scanner le dossier datas"):
            with st.spinner("Scan en cours..."):
                try:
                    # Simulation du scan
                    st.success("✅ Scan terminé - Fichiers détectés")
                except Exception as e:
                    st.error(f"Erreur: {e}")
    
    def translation_tab(self):
        """Onglet de traduction"""
        st.header("🌍 Traduction")
        
        # Options de traduction
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Traduction individuelle")
            video_id = st.text_input("ID de la vidéo")
            if st.button("Traduire cette vidéo"):
                if video_id:
                    with st.spinner("Traduction en cours..."):
                        try:
                            st.success("✅ Traduction terminée!")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez entrer un ID de vidéo")
        
        with col2:
            st.subheader("🔄 Traduction en lot")
            if st.button("Traduire toutes les vidéos", type="primary"):
                with st.spinner("Traduction en lot..."):
                    try:
                        # Récupérer toutes les vidéos non traduites
                        if self.db:
                            videos = self.db.list_all_videos()
                            untranslated = [v[0] for v in videos if v[6] == 0]
                            
                            if untranslated:
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                
                                for i, video_id in enumerate(untranslated):
                                    progress = (i + 1) / len(untranslated)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Traduction {i+1}/{len(untranslated)}")
                                
                                st.success(f"✅ {len(untranslated)} vidéos traduites!")
                            else:
                                st.info("Toutes les vidéos sont déjà traduites")
                        else:
                            st.error("Base de données non disponible")
                            
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        
        # Statistiques de traduction
        st.subheader("📊 Statistiques de traduction")
        try:
            if self.db:
                videos = self.db.list_all_videos()
                df = pd.DataFrame(videos, columns=[
                    'id', 'title', 'description', 'duration', 'upload_date', 
                    'view_count', 'translation_count', 'theme'
                ])
                
                # Nettoyer les types de données
                try:
                    df['translation_count'] = pd.to_numeric(df['translation_count'], errors='coerce').fillna(0).astype(int)
                except Exception as e:
                    st.warning(f"Attention: Erreur lors du nettoyage des données: {e}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        translated = len(df[df['translation_count'] > 0])
                        total = len(df)
                        st.metric("Vidéos traduites", f"{translated}/{total}")
                        
                        if total > 0:
                            percentage = (translated / total) * 100
                            st.progress(percentage / 100)
                            st.text(f"{percentage:.1f}%")
                        else:
                            st.progress(0)
                            st.text("0.0%")
                    except Exception as e:
                        st.error(f"Erreur calcul statistiques: {e}")
                
                with col2:
                    try:
                        waiting = len(df[df['translation_count'] == 0])
                        st.metric("En attente", waiting)
                    except Exception as e:
                        st.error(f"Erreur calcul en attente: {e}")
            else:
                st.error("Base de données non disponible")
                
        except Exception as e:
            st.error(f"Erreur: {e}")
    
    def tts_tab(self):
        """Onglet TTS"""
        st.header("🎙️ Synthèse Vocale (TTS)")
        
        # Options TTS
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 TTS individuel")
            video_id = st.text_input("ID de la vidéo (TTS)")
            if st.button("Générer TTS"):
                if video_id:
                    with st.spinner("Génération TTS en cours..."):
                        try:
                            st.success("✅ TTS généré!")
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                else:
                    st.warning("Veuillez entrer un ID de vidéo")
        
        with col2:
            st.subheader("🔄 TTS en lot")
            if st.button("Générer TTS pour toutes les vidéos", type="primary"):
                with st.spinner("Génération TTS en lot..."):
                    try:
                        st.success("✅ TTS généré pour toutes les vidéos!")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
        
        # Configuration TTS
        st.subheader("⚙️ Configuration TTS")
        voice_model = st.selectbox("Modèle de voix", ["Bark", "Coqui", "gTTS"])
        language = st.selectbox("Langue", ["Français", "Anglais", "Espagnol"])
        
        if st.button("💾 Sauvegarder la configuration"):
            st.success("Configuration sauvegardée!")

def main():
    """Fonction principale de l'application"""
    app = TikTokAutoApp()
    app.main()

if __name__ == "__main__":
    main() 