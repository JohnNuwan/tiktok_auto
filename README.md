# 🎵 TikTok_Auto - Système d'Automatisation de Création de Vidéos

## 🎯 Vue d'ensemble

TikTok_Auto est un système complet d'automatisation pour créer des vidéos TikTok/YouTube Shorts en français à partir de contenu YouTube anglais. Le système intègre toutes les étapes : téléchargement, classification, transcription, traduction, synthèse vocale et montage avec sous-titres progressifs.

## ✨ Fonctionnalités principales

### 🎬 Montage Vidéo Avancé
- **Sous-titres progressifs** : Affichage phrase par phrase synchronisé avec l'audio
- **Durée fixe** : Exactement 70 secondes (1min10) optimale pour TikTok/Shorts
- **Hook et Call-to-Action** : "🎯 ATTENTION !" et "👍 Likez et abonnez-vous !"
- **Vidéos de fond intelligentes** : Sélection automatique basée sur le thème

### 🧠 Classification Thématique (Ollama)
- **10 thèmes supportés** : motivation, succès, philosophie, discipline, etc.
- **IA locale** : Utilise Ollama pour l'analyse automatique
- **Organisation automatique** : Classifie et organise le contenu

### 🎵 Synthèse Vocale (ElevenLabs)
- **Qualité professionnelle** : Audio français naturel
- **Voix multiples** : Rachel, Domi, Bella, Sam, Adam, Echo
- **Configuration centralisée** : Via variables d'environnement

### 🎥 Gestion des Fonds Vidéos
- **Sources multiples** : Pexels, Pixabay, Mixkit
- **Téléchargement automatique** : Par thème
- **Gestion des doublons** : Évite les téléchargements répétés

### 📝 Recréation de Vidéos
- **Application des nouveautés** : Hook, CTA, sous-titres, durée fixe
- **Recréation sélective** : Une vidéo ou toutes les vidéos
- **Préservation des données** : Garde les traductions et TTS existants

## 🚀 Installation

### Prérequis
- Python 3.8+
- FFmpeg
- Ollama (pour la classification)

### 1. Cloner le repository
```bash
git clone https://github.com/JohnNuwan/tiktok_auto.git
cd tiktok_auto
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration
Créer un fichier `.env` avec vos clés API :
```env
# APIs
PEXELS_API_KEY=votre_cle_pexels
PIXABAY_API_KEY=votre_cle_pixabay
ELEVENLABS_API_KEY=votre_cle_elevenlabs

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2

# TTS
DEFAULT_TTS_ENGINE=elevenlabs
BARK_VOICE=v2/fr_speech_01

# FFmpeg
FFMPEG_PATH=/usr/bin/ffmpeg
```

### 4. Installer Ollama
```bash
# Windows
winget install Ollama.Ollama

# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

### 5. Lancer Ollama
```bash
ollama serve
ollama pull llama3.2
```

## 🎮 Utilisation

### Démarrage rapide
```bash
python main.py
```

### Pipeline complet automatique
```bash
python auto_pipeline_complete.py
```

## 📋 Menu Principal

Le système offre 14 options :

1. **📊 Afficher la base de données** - État du traitement
2. **🎤 Transcription audio (Whisper)** - Audio → Texte anglais
3. **🌍 Traduction texte (EN → FR)** - Traduction automatique
4. **🎵 Génération audio (TTS)** - Texte → Audio français
5. **🎬 Montage vidéo** - Création des vidéos finales
6. **📥 Télécharger des vidéos** - Interface YouTube complète
7. **📺 Télécharger une chaîne YouTube** - Chaîne complète
8. **🧠 Classification thématique (Ollama)** - Organisation par thème
9. **🎥 Télécharger les fonds vidéos** - Fonds thématiques
10. **🚀 Pipeline complet automatique** - Processus complet
11. **🗄️ Gérer la base de données** - Outils de gestion
12. **🧪 Tests système** - Diagnostic
13. **📝 Recréer vidéos avec sous-titres** - Application des nouveautés

## 🎬 Structure de la Vidéo Finale

```
0-5s    : 🎯 ATTENTION ! (Hook)
5-65s   : Contenu principal avec sous-titres progressifs
65-70s  : 👍 Likez et abonnez-vous ! (CTA)
```

## 📁 Structure du Projet

```
TikTok_Auto/
├── main.py                    # Point d'entrée principal
├── auto_pipeline_complete.py  # Pipeline automatique
├── config.py                  # Configuration centralisée
├── requirements.txt           # Dépendances Python
├── .env                      # Variables d'environnement
├── .gitignore               # Fichiers exclus de Git
├── README.md                # Documentation
├── GUIDE_UTILISATION.md     # Guide détaillé
├── GUIDE_SOUS_TITRES.md     # Guide sous-titres
├── GUIDE_DUREE_HOOK_CTA.md  # Guide Hook/CTA
├── core/                    # Modules principaux
│   ├── downloader.py        # Téléchargement YouTube
│   └── fond_downloader.py   # Gestion des fonds
├── translation/             # Modules de traduction
│   ├── whisper_simple.py    # Transcription
│   ├── text_translator.py   # Traduction texte
│   ├── tts.py              # Synthèse vocale
│   └── audio_translator.py  # Traduction audio
├── montage/                # Modules de montage
│   └── video_builder.py    # Création vidéos
├── ollama/                 # Classification IA
│   └── theme_classifier.py # Classification thématique
├── database/               # Base de données
│   └── manager.py          # Gestion BDD
└── datas/                  # Données générées
    ├── audios_En/          # Audio anglais
    ├── whisper_texts/      # Textes transcrits
    ├── whisper_translations/ # Textes traduits
    ├── tts_outputs/        # Audio français
    ├── final_videos/       # Vidéos finales
    └── temp_subtitles/     # Sous-titres temporaires
```

## 🔧 Configuration Avancée

### Obtenir les clés API

#### ElevenLabs (TTS)
1. Allez sur [ElevenLabs](https://elevenlabs.io/)
2. Créez un compte gratuit
3. Générez une clé API dans les paramètres

#### Pexels (Fonds vidéos)
1. Allez sur [Pexels](https://www.pexels.com/api/)
2. Créez un compte
3. Générez une clé API

#### Pixabay (Fonds vidéos)
1. Allez sur [Pixabay](https://pixabay.com/api/docs/)
2. Créez un compte
3. Générez une clé API

## 🚀 Workflow Recommandé

### Pour une nouvelle chaîne YouTube :
1. Lancez le pipeline complet (Option 10)
2. Entrez l'URL de la chaîne
3. Laissez le système faire tout le travail

### Pour des vidéos existantes :
1. Classification (Option 8) : Organisez par thème
2. Téléchargement fonds (Option 9) : Téléchargez les fonds vidéos
3. Transcription (Option 2) : Transcrivez l'audio
4. Traduction (Option 3) : Traduisez en français
5. TTS (Option 4) : Générez l'audio français
6. Montage (Option 5) : Créez les vidéos finales

### Pour améliorer des vidéos existantes :
1. Recréation (Option 13) : Appliquez les nouvelles fonctionnalités
2. Sélection : Une vidéo ou toutes les vidéos

## 🎯 Conseils d'Utilisation

### Performance
- **Traitement en lot** : Utilisez les options de limite
- **Classification** : Faites la classification en premier
- **Fonds vidéos** : Téléchargez les fonds avant le montage
- **TTS** : ElevenLabs offre une qualité supérieure

### Engagement
- **Hook** : Capte l'attention dès les premières secondes
- **Sous-titres** : Encourage la lecture et améliore l'accessibilité
- **CTA** : Guide l'action (like, abonnement)
- **Durée** : 70 secondes optimale pour TikTok/Shorts

## 🎉 Résultat Final

Le système génère des vidéos TikTok/YouTube Shorts optimisées :
- **Format** : Portrait (1080x1920)
- **Durée** : Exactement 70 secondes (1min10)
- **Audio** : Français de qualité professionnelle (ElevenLabs)
- **Vidéo** : Fonds thématiques automatiques avec boucle
- **Sous-titres** : Progressifs, synchronisés, stylisés
- **Hook** : "🎯 ATTENTION !" pour capturer l'attention
- **CTA** : "👍 Likez et abonnez-vous !" pour l'engagement
- **Prêt à publier** : Optimisé pour les algorithmes TikTok/YouTube

## 📚 Documentation

- **Guide d'utilisation** : `GUIDE_UTILISATION.md`
- **Guide sous-titres** : `GUIDE_SOUS_TITRES.md`
- **Guide Hook/CTA** : `GUIDE_DUREE_HOOK_CTA.md`

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Ajouter de nouvelles fonctionnalités

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

**🎵 TikTok_Auto** - Créez du contenu français automatiquement avec sous-titres et engagement optimisé ! 🚀 