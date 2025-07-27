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
- Alternative Bark disponible
- Interface dédiée avec options de traitement en lot

### 5. 🎬 Montage vidéo
- Combine l'audio français avec des vidéos de fond
- **NOUVEAU** : Sous-titres progressifs français
- **NOUVEAU** : Durée fixe de 1min10 (70 secondes)
- **NOUVEAU** : Hook et Call-to-Action intégrés
- Génère des vidéos TikTok/Shorts au format portrait
- Interface dédiée avec options de traitement en lot

### 6. 📥 Télécharger des vidéos
- Interface complète de téléchargement YouTube
- Options : nouvelle chaîne, scan fichiers existants, recherche
- Télécharge audio + sous-titres automatiques

### 7. 📺 Télécharger une chaîne YouTube
- Téléchargement direct d'une chaîne complète
- Entrée simple de l'URL de la chaîne
- Télécharge toutes les vidéos de la chaîne

### 8. 🧠 Classification thématique (Ollama)
- Classification automatique des vidéos par thème
- Utilise Ollama (IA locale) pour analyser le contenu
- Thèmes : motivation, succès, philosophie, discipline, etc.
- Organise automatiquement les vidéos dans les assets

### 9. 🎥 Télécharger les fonds vidéos
- **NOUVEAU** : Télécharge des vidéos de fond depuis Pexels, Pixabay, Mixkit
- Classifie automatiquement par thème
- Interface de gestion des fonds existants
- Options de téléchargement par thème ou recherche

### 10. 🚀 Pipeline complet automatique
- Automatise tout le processus
- Téléchargement → Classification → Transcription → Traduction → TTS → Montage
- Interface dédiée avec options étape par étape

### 11. 🗄️ Gérer la base de données
- Outils de gestion de la base de données
- Nettoyage, export, import

### 12. 🧪 Tests système
- Vérification de tous les composants
- Diagnostic des problèmes

### 13. 📝 Recréer vidéos avec sous-titres
- **NOUVEAU** : Recrée des vidéos existantes avec sous-titres
- Sélection d'une vidéo spécifique ou toutes les vidéos
- Application des nouvelles fonctionnalités (Hook, CTA, durée fixe)

## 🎬 Montage Vidéo Avancé

### Nouvelles fonctionnalités

#### 📝 Sous-titres progressifs
- **Affichage progressif** : Le texte apparaît phrase par phrase
- **Synchronisation audio** : Synchronisé avec l'audio TTS
- **Style professionnel** : Police Arial, couleurs contrastées
- **Format ASS** : Sous-titres avancés avec effets visuels

#### ⏱️ Durée fixe de 1min10
- **Durée exacte** : 70 secondes (1 minute 10 secondes)
- **Structure fixe** :
  - Hook : 0-5 secondes
  - Contenu principal : 5-65 secondes
  - Call-to-Action : 65-70 secondes

#### 🎯 Hook et Call-to-Action
- **Hook** : "🎯 ATTENTION !" (0-5s, jaune, 64px)
- **CTA** : "👍 Likez et abonnez-vous !" (65-70s, vert, 56px)
- **Engagement** : Encourage l'interaction et l'abonnement

#### 🎥 Vidéos de fond intelligentes
- **Sélection automatique** : Basée sur le thème de la vidéo
- **Sources multiples** : Pexels, Pixabay, Mixkit
- **Boucle automatique** : Si la vidéo de fond est plus courte que 70s
- **Fallback** : Thème par défaut si aucun fond spécifique

### Structure de la vidéo finale
```
0-5s    : 🎯 ATTENTION ! (Hook)
5-65s   : Contenu principal avec sous-titres progressifs
65-70s  : 👍 Likez et abonnez-vous ! (CTA)
```

## 🎥 Gestion des Fonds Vidéos

### Fonctionnalités
- **Téléchargement automatique** : Depuis Pexels, Pixabay, Mixkit
- **Classification par thème** : Organisation automatique
- **Gestion des doublons** : Évite les téléchargements répétés
- **Interface complète** : Téléchargement, consultation, nettoyage

### Thèmes supportés
- `motivation` : Discours motivants, encouragement
- `success` : Histoires de réussite, accomplissements
- `philosophy` : Réflexions profondes, sagesse
- `discipline` : Autodiscipline, habitudes, routines
- `growth` : Développement personnel, apprentissage
- `failure` : Leçons d'échec, résilience
- `leadership` : Leadership, management, influence
- `mindset` : État d'esprit, mentalité
- `business` : Entrepreneuriat, business
- `health` : Santé, bien-être, fitness

### Utilisation
1. **Lancez le téléchargement** : Option 9 du menu principal
2. **Choisissez l'action** :
   - Télécharger de nouveaux fonds
   - Consulter les fonds existants
   - Nettoyer les doublons
   - Rechercher par thème

## 📝 Recréation de Vidéos avec Sous-titres

### Fonctionnalités
- **Recréation sélective** : Une vidéo ou toutes les vidéos
- **Application des nouveautés** : Hook, CTA, durée fixe, sous-titres
- **Préservation des données** : Garde les traductions et TTS existants
- **Interface simple** : Sélection par ID ou traitement en lot

### Utilisation
1. **Lancez la recréation** : Option 13 du menu principal
2. **Choisissez le mode** :
   - Recréer une vidéo spécifique (entrez l'ID)
   - Recréer toutes les vidéos avec TTS
3. **Le système applique automatiquement** :
   - Sous-titres progressifs
   - Hook et CTA
   - Durée fixe de 70 secondes
   - Vidéos de fond thématiques

## 🧠 Classification Thématique avec Ollama

### Fonctionnalités
- **Classification automatique** : Analyse le titre et la description
- **10 thèmes supportés** :
  - `motivation` : Discours motivants, encouragement
  - `success` : Histoires de réussite, accomplissements
  - `philosophy` : Réflexions profondes, sagesse
  - `discipline` : Autodiscipline, habitudes, routines
  - `growth` : Développement personnel, apprentissage
  - `failure` : Leçons d'échec, résilience
  - `leadership` : Leadership, management, influence
  - `mindset` : État d'esprit, mentalité
  - `business` : Entrepreneuriat, business
  - `health` : Santé, bien-être, fitness

### Utilisation
1. **Lancez la classification** : Option 8 du menu principal
2. **Choisissez l'option** :
   - Classifier une vidéo spécifique
   - Classifier toutes les vidéos
   - Afficher les statistiques
   - Lister les vidéos non classifiées

### Configuration Ollama
- **Modèle par défaut** : `llama3.2`
- **Hôte par défaut** : `http://localhost:11434`
- **Configuration** : Dans le fichier `.env`

## 🎵 Configuration TTS (ElevenLabs)

### Configuration requise
```env
# Dans le fichier .env
ELEVENLABS_API_KEY=votre_cle_api_elevenlabs
DEFAULT_TTS_ENGINE=elevenlabs
```

### Obtenir une clé API ElevenLabs
1. Allez sur [ElevenLabs](https://elevenlabs.io/)
2. Créez un compte gratuit
3. Générez une clé API dans les paramètres
4. Ajoutez-la dans votre fichier `.env`

### Voix disponibles
- **Rachel** : Voix féminine anglaise (par défaut)
- **Domi** : Voix féminine anglaise
- **Bella** : Voix féminine anglaise
- **Sam** : Voix masculine anglaise
- **Adam** : Voix masculine anglaise
- **Echo** : Voix masculine anglaise

## 📁 Structure des dossiers

```
TikTok_Auto/
├── datas/
│   ├── audios_En/          # Fichiers audio anglais
│   ├── whisper_texts/      # Textes transcrits
│   ├── whisper_translations/ # Textes traduits
│   ├── tts_outputs/        # Audio français généré
│   ├── final_videos/       # Vidéos finales
│   └── temp_subtitles/     # Fichiers sous-titres temporaires
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
3. **Laissez le système faire tout le travail** :
   - Téléchargement automatique
   - Classification thématique
   - Transcription Whisper
   - Traduction Google Translate
   - Génération TTS ElevenLabs
   - Montage vidéo final avec sous-titres

### Pour des vidéos existantes :

1. **Classification** (Option 8) : Organisez par thème
2. **Téléchargement fonds** (Option 9) : Téléchargez les fonds vidéos
3. **Transcription** (Option 2) : Transcrivez l'audio
4. **Traduction** (Option 3) : Traduisez en français
5. **TTS** (Option 4) : Générez l'audio français
6. **Montage** (Option 5) : Créez les vidéos finales avec sous-titres

### Pour améliorer des vidéos existantes :

1. **Recréation** (Option 13) : Appliquez les nouvelles fonctionnalités
2. **Sélection** : Une vidéo ou toutes les vidéos
3. **Automatique** : Le système applique Hook, CTA, sous-titres

## 🎯 Conseils d'utilisation

### Performance
- **Traitement en lot** : Utilisez les options de limite pour traiter par petits groupes
- **Classification** : Faites la classification en premier pour organiser le contenu
- **Fonds vidéos** : Téléchargez les fonds avant le montage
- **TTS** : ElevenLabs offre une qualité supérieure à Bark

### Organisation
- **Thèmes** : La classification automatique aide à organiser le contenu
- **Fonds** : Téléchargez régulièrement de nouveaux fonds par thème
- **Base de données** : Vérifiez régulièrement l'état avec l'option 1
- **Statistiques** : Utilisez les statistiques pour suivre le progrès

### Engagement
- **Hook** : Capte l'attention dès les premières secondes
- **Sous-titres** : Encourage la lecture et améliore l'accessibilité
- **CTA** : Guide l'action (like, abonnement)
- **Durée** : 70 secondes optimale pour TikTok/Shorts

### Dépannage
- **Tests système** (Option 12) : Vérifiez que tout fonctionne
- **Configuration** : Vérifiez vos clés API dans `.env`
- **FFmpeg** : Assurez-vous qu'il est installé pour le montage
- **Fonds manquants** : Utilisez l'option 9 pour télécharger des fonds

## 🎉 Résultat final

Le système génère des vidéos TikTok/YouTube Shorts optimisées :
- **Format** : Portrait (1080x1920)
- **Durée** : Exactement 70 secondes (1min10)
- **Audio** : Français de qualité professionnelle (ElevenLabs)
- **Vidéo** : Fonds thématiques automatiques avec boucle
- **Sous-titres** : Progressifs, synchronisés, stylisés
- **Hook** : "🎯 ATTENTION !" pour capturer l'attention
- **CTA** : "👍 Likez et abonnez-vous !" pour l'engagement
- **Prêt à publier** : Optimisé pour les algorithmes TikTok/YouTube

## 📚 Guides détaillés

Pour plus d'informations sur les fonctionnalités spécifiques :
- **Sous-titres** : Voir `GUIDE_SOUS_TITRES.md`
- **Durée, Hook, CTA** : Voir `GUIDE_DUREE_HOOK_CTA.md`

---

**🎵 TikTok_Auto** - Créez du contenu français automatiquement avec sous-titres et engagement optimisé ! 🚀 