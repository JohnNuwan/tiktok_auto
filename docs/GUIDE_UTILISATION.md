# 🎵 Guide d'Utilisation TikTok_Auto

## 🎯 Vue d'ensemble

TikTok_Auto est un système complet d'automatisation pour créer des vidéos TikTok/YouTube Shorts en français à partir de contenu YouTube anglais. Le système intègre toutes les étapes : téléchargement, classification, transcription, traduction, synthèse vocale et montage avec sous-titres progressifs.

## 🚀 Démarrage rapide

### 1. Lancement du système
```bash
python main.py
```

### 2. Pipeline complet automatique
```bash
python auto_pipeline_complete.py
```

### 3. Générateur de Shorts
```bash
python montage/shorts_generator.py
```

## 📋 Menu Principal

Le menu principal offre 14 options :

### 1. 📊 Afficher la base de données
- Affiche toutes les vidéos enregistrées avec leurs statuts
- Utile pour vérifier l'état du traitement

### 2. 🎤 Transcription audio (Whisper)
- Transcrit les fichiers audio anglais en texte anglais
- Utilise OpenAI Whisper pour une transcription précise
- Interface dédiée avec options de traitement en lot

### 3. 🌍 Traduction texte (EN → FR)
- Traduit les textes anglais en français
- Utilise Google Translate
- Interface dédiée avec options de traitement en lot

### 4. 🎵 Génération audio (TTS)
- Génère de l'audio français à partir des textes traduits
- **Utilise ElevenLabs par défaut** (qualité professionnelle)
- **CTA audio** : Génération automatique avec Bark (gratuit)
- Alternative Bark disponible
- Interface dédiée avec options de traitement en lot

### 5. 🎬 Montage vidéo
- Combine l'audio français avec des vidéos de fond
- **NOUVEAU** : Sous-titres progressifs français
- **NOUVEAU** : Durée fixe de 1min10 (70 secondes)
- **NOUVEAU** : Hook et Call-to-Action audio intégrés
- Génère des vidéos TikTok/Shorts au format portrait
- Interface dédiée avec options de traitement en lot

### 6. 📥 Télécharger des vidéos
- Interface complète de téléchargement YouTube
- Options : nouvelle chaîne, scan fichiers existants, recherche
- Télécharge audio + sous-titres automatiques

### 7. 📺 Télécharger une chaîne YouTube
- Télécharge toutes les vidéos d'une chaîne
- Interface simplifiée pour les chaînes complètes
- Gestion automatique des doublons

### 8. 🧠 Classification thématique (Ollama)
- **NOUVEAU** : Classification automatique par thème
- Utilise Ollama (IA locale) pour l'analyse
- 10 thèmes supportés : motivation, succès, philosophie, etc.
- Interface dédiée avec options de traitement en lot

### 9. 🎥 Télécharger les fonds vidéos
- **NOUVEAU** : Téléchargement automatique de fonds vidéos
- Sources : Pexels, Pixabay, Mixkit
- Téléchargement par thème
- Gestion automatique des doublons

### 10. 🚀 Pipeline complet automatique
- **NOUVEAU** : Processus complet automatisé
- Téléchargement → Classification → Transcription → Traduction → TTS → Montage
- Interface simplifiée pour un traitement en lot complet

### 11. 🗄️ Gérer la base de données
- Outils de gestion avancés
- Recherche, statistiques, nettoyage
- Interface dédiée

### 12. 🧪 Tests système
- Diagnostic complet du système
- Vérification des dépendances
- Tests de connectivité

### 13. 📝 Recréer vidéos avec sous-titres
- **NOUVEAU** : Application des nouveautés aux vidéos existantes
- Hook, CTA audio, sous-titres, durée fixe
- Recréation sélective (une vidéo ou toutes)

## 🎬 Générateur de Shorts Automatiques

### ✨ Nouvelles Fonctionnalités (v2.2.0)

Le générateur de shorts offre des fonctionnalités avancées pour créer des contenus optimisés pour les réseaux sociaux :

- **CTA audio intégrés** : Messages vocaux d'incitation à s'abonner à la fin de la vidéo
- **Organisation structurée** : Dossiers organisés par plateforme et type
- **Durée minimale garantie** : 70 secondes (1min10) pour tous les shorts
- **Format TikTok corrigé** : Format 9:16 (vertical) pour tous les shorts
- **Détection virale améliorée** : +50 mots-clés viraux et algorithme sophistiqué
- **Effets visuels avancés** : Zoom progressif, transitions fade, filtres de couleur
- **Système d'analytics** : Suivi complet des performances (vues, likes, partages)
- **Interface analytics** : CLI pour consulter les statistiques et rapports

### 🎯 Formats Supportés

| Plateforme | Format | Durée | Effets | CTA Audio |
|------------|--------|-------|--------|-----------|
| **TikTok** | 9:16 | 70s+ | Zoom, transitions, filtres | ✅ |
| **YouTube Shorts** | 9:16 | 70s+ | Zoom, transitions | ✅ |
| **Instagram Reels** | 9:16 | 70s+ | Zoom, transitions, filtres | ✅ |

### 📁 Organisation des Shorts

Les shorts sont automatiquement organisés dans une structure claire :

```
datas/shorts/
├── final/              # Shorts finaux prêts à publier
├── temp/               # Fichiers temporaires de traitement
├── thumbnails/         # Miniatures générées
└── platforms/          # Shorts organisés par plateforme
    ├── tiktok/         # Shorts TikTok
    ├── youtube/        # Shorts YouTube
    └── instagram/      # Reels Instagram
```

### 🎤 CTA Audio

Les Call-to-Action sont maintenant générés en audio et ajoutés à la fin de la vidéo :

- **TikTok** : "Abonne-toi pour plus de contenu comme ça !", "Suis-moi pour du contenu exclusif !"
- **YouTube** : "Abonne-toi et active la cloche !", "Like et abonne-toi pour plus de contenu !"
- **Instagram** : "Suis-moi pour plus de contenu !", "Abonne-toi et active les notifications !"

### 🎮 Utilisation du Générateur de Shorts

#### Lancement
```bash
python montage/shorts_generator.py
```

#### Options disponibles

1. **🎬 Créer un short TikTok**
   - Entrez l'ID de la vidéo source
   - Le système génère automatiquement un short optimisé pour TikTok
   - Durée minimale : 70 secondes
   - CTA audio intégré

2. **📺 Créer un short YouTube**
   - Entrez l'ID de la vidéo source
   - Le système génère automatiquement un short optimisé pour YouTube Shorts
   - Durée minimale : 70 secondes
   - CTA audio intégré

3. **📱 Créer un Reel Instagram**
   - Entrez l'ID de la vidéo source
   - Le système génère automatiquement un Reel optimisé pour Instagram
   - Durée minimale : 70 secondes
   - CTA audio intégré

4. **🔄 Création en lot**
   - Choisissez la plateforme
   - Entrez le nombre de shorts à créer
   - Le système traite automatiquement plusieurs vidéos

5. **📊 Afficher les shorts créés**
   - Affiche tous les shorts créés de manière organisée
   - Statistiques par plateforme
   - Informations détaillées (taille, date, etc.)

6. **🧹 Nettoyer les fichiers temporaires**
   - Supprime les fichiers temporaires de traitement
   - Libère de l'espace disque
   - Nettoie les dossiers temp

7. **📈 Statistiques des shorts**
   - Affiche les statistiques complètes des shorts
   - Nombre total de shorts par plateforme
   - Taille totale des fichiers
   - Dernier short créé

## 🎬 Structure de la Vidéo Finale

```
0-5s    : 🎯 ATTENTION ! (Hook)
5-65s   : Contenu principal avec sous-titres progressifs
65-70s  : CTA audio "Abonne-toi pour plus de contenu !" (parole)
```

## 📁 Structure des dossiers

```
TikTok_Auto/
├── datas/
│   ├── audios_En/          # Fichiers audio anglais
│   ├── whisper_texts/      # Textes transcrits
│   ├── whisper_translations/ # Textes traduits
│   ├── tts_outputs/        # Audio français généré
│   ├── final_videos/       # Vidéos finales
│   ├── temp_subtitles/     # Fichiers sous-titres temporaires
│   └── shorts/             # Shorts générés automatiquement
│       ├── final/          # Shorts finaux prêts à publier
│       ├── temp/           # Fichiers temporaires de traitement
│       ├── thumbnails/     # Miniatures générées
│       └── platforms/      # Shorts organisés par plateforme
│           ├── tiktok/     # Shorts TikTok
│           ├── youtube/    # Shorts YouTube
│           └── instagram/  # Reels Instagram
├── assets/
│   └── videos/             # Vidéos de fond par thème
│       ├── motivation/     # Fonds motivation
│       ├── success/        # Fonds succès
│       ├── philosophy/     # Fonds philosophie
│       └── ...             # Autres thèmes
├── database/
│   ├── videos.db           # Base de données SQLite
│   └── fond_usage.db       # Base de données des fonds
└── config.py               # Configuration centralisée
```

## 🔧 Configuration

### Fichier .env
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

## 🚀 Workflow recommandé

### Pour une nouvelle chaîne YouTube :

1. **Lancez le pipeline complet** (Option 10)
2. **Entrez l'URL de la chaîne**
3. **Laissez le système faire tout le travail**

### Pour des vidéos existantes :

1. **Classification** (Option 8) : Organisez par thème
2. **Téléchargement fonds** (Option 9) : Téléchargez les fonds vidéos
3. **Transcription** (Option 2) : Transcrivez l'audio
4. **Traduction** (Option 3) : Traduisez en français
5. **TTS** (Option 4) : Générez l'audio français
6. **Montage** (Option 5) : Créez les vidéos finales

### Pour améliorer des vidéos existantes :

1. **Recréation** (Option 13) : Appliquez les nouvelles fonctionnalités
2. **Sélection** : Une vidéo ou toutes les vidéos

### Pour générer des shorts :

1. **Lancez le générateur de shorts** : `python montage/shorts_generator.py`
2. **Choisissez la plateforme** (TikTok, YouTube, Instagram)
3. **Sélectionnez une vidéo ou créez en lot**
4. **Les shorts seront organisés automatiquement** dans les dossiers appropriés

## 🎯 Conseils d'Utilisation

### Performance
- **Traitement en lot** : Utilisez les options de limite
- **Classification** : Faites la classification en premier
- **Fonds vidéos** : Téléchargez les fonds avant le montage
- **TTS** : ElevenLabs offre une qualité supérieure
- **CTA audio** : Bark est utilisé automatiquement pour éviter les quotas

### Engagement
- **Hook** : Capte l'attention dès les premières secondes
- **Sous-titres** : Encourage la lecture et améliore l'accessibilité
- **CTA audio** : Messages vocaux naturels pour l'engagement
- **Durée** : 70 secondes optimale pour TikTok/Shorts

### Organisation
- **Dossiers structurés** : Les shorts sont automatiquement organisés
- **Nettoyage régulier** : Utilisez l'option de nettoyage des fichiers temporaires
- **Statistiques** : Consultez régulièrement les statistiques des shorts

## 🎉 Résultat Final

Le système génère des vidéos TikTok/YouTube Shorts optimisées :
- **Format** : Portrait (1080x1920)
- **Durée** : Exactement 70 secondes (1min10)
- **Audio** : Français de qualité professionnelle (ElevenLabs)
- **Vidéo** : Fonds thématiques automatiques avec boucle
- **Sous-titres** : Progressifs, synchronisés, stylisés
- **Hook** : "🎯 ATTENTION !" pour capturer l'attention
- **CTA audio** : Messages vocaux d'incitation à s'abonner
- **Organisation** : Dossiers structurés par plateforme
- **Prêt à publier** : Optimisé pour les algorithmes TikTok/YouTube

## 🔍 Dépannage

### Erreurs courantes

#### Erreur FFmpeg
```bash
# Windows
# Téléchargez FFmpeg depuis https://ffmpeg.org/download.html

# Linux
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

#### Erreur Ollama
```bash
# Vérifiez qu'Ollama est installé et en cours d'exécution
ollama serve

# Vérifiez que le modèle est téléchargé
ollama pull llama3.2
```

#### Erreur CTA audio
- Les CTA audio utilisent Bark (gratuit) par défaut
- Si vous avez des problèmes, vérifiez que Bark est installé
- Les quotas ElevenLabs ne sont pas utilisés pour les CTA

#### Fichiers temporaires
- Utilisez l'option de nettoyage pour supprimer les fichiers temporaires
- Les fichiers temporaires sont stockés dans `datas/shorts/temp/`

## 📚 Documentation

- **Guide sous-titres** : `GUIDE_SOUS_TITRES.md`
- **Guide Hook/CTA** : `GUIDE_DUREE_HOOK_CTA.md`
- **Documentation complète** : `docs/README.md` 