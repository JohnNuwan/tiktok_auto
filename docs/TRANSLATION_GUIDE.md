# Guide de Traduction Audio - TikTok Auto

## 🎯 Vue d'ensemble

Ce guide détaille l'utilisation des modules de traduction audio du système TikTok Auto. Le système permet de convertir des fichiers audio anglais en textes français via un processus en deux étapes.

## 🔄 Workflow de Traduction

```
📁 Audio anglais (.mp3)
    ↓
🎙️ Whisper (transcription)
    ↓
📝 Texte anglais (Base de données)
    ↓
🌐 Google Translate
    ↓
🇫🇷 Texte français (Base de données)
    ↓
🎵 TTS (optionnel)
    ↓
🔊 Audio français (.wav/.mp3)
```

## 📋 Prérequis

### 1. Installation des dépendances
```bash
# Transcription audio
pip install openai-whisper

# Traduction
pip install requests

# Interface CLI
pip install rich

# TTS (optionnel)
pip install bark
pip install elevenlabs
```

### 2. Structure des dossiers
```
datas/
├── audios_En/          # Fichiers audio anglais (.mp3)
├── whisper_texts/      # Ancien système (fichiers .txt)
└── tts_outputs/        # Fichiers audio générés
```

### 3. Base de données
Les tables nécessaires sont créées automatiquement :
- `whisper_texts` : Textes transcrits en anglais
- `whisper_translations` : Textes traduits en français

## 🎙️ Module 1 : Whisper Simple

### Description
Transcrit les fichiers audio anglais en texte anglais avec Whisper.

### Utilisation
```bash
python translation/whisper_simple.py
```

### Options disponibles

#### 1. Traiter un fichier audio spécifique
- **Option** : 1
- **Entrée** : ID du fichier audio (nom sans extension)
- **Exemple** : `video_123` pour `video_123.mp3`

#### 2. Traitement en lot
- **Option** : 2
- **Limite par défaut** : 20 fichiers
- **Personnalisable** : Entrer un nombre différent

#### 3. Statistiques
- **Option** : 3
- **Affiche** : Nombre total de transcriptions Whisper

#### 4. Lister les fichiers sans transcription
- **Option** : 4
- **Affiche** : Fichiers audio sans traduction Whisper

#### 5. Lire une transcription existante
- **Option** : 5
- **Entrée** : ID du fichier audio
- **Affiche** : Texte transcrit complet

### Exemple d'utilisation
```bash
$ python translation/whisper_simple.py

🎙️ Traducteur Whisper Simple
===============================

Options disponibles:
1. 🎙️ Traiter un fichier audio spécifique avec Whisper
2. 🔄 Traitement en lot (limité à 20 fichiers)
3. 📊 Afficher les statistiques
4. 🔍 Lister les fichiers audio sans traduction Whisper
5. 📖 Lire une traduction Whisper existante
0. ❌ Retour

🎯 Votre choix (0-5): 2
📊 Nombre max de fichiers (Enter pour 20): 10

🎯 10 fichiers audio à traiter avec Whisper
🔄 Chargement du modèle Whisper...
✅ Whisper initialisé avec succès
🎙️ Traitement Whisper...: 100%|██████████| 10/10 [02:30<00:00]
✅ Traitement Whisper terminé
```

## 🌐 Module 2 : Text Translator

### Description
Traduit les textes anglais transcrits par Whisper en français avec Google Translate.

### Utilisation
```bash
python translation/text_translator.py
```

### Options disponibles

#### 1. Traduire un texte spécifique
- **Option** : 1
- **Entrée** : ID du fichier audio
- **Prérequis** : Doit avoir une transcription Whisper

#### 2. Traduction en lot
- **Option** : 2
- **Limite par défaut** : 20 textes
- **Personnalisable** : Entrer un nombre différent

#### 3. Statistiques
- **Option** : 3
- **Affiche** : Nombre total de traductions françaises

#### 4. Lister les textes sans traduction française
- **Option** : 4
- **Affiche** : Textes Whisper sans traduction française

#### 5. Lire une traduction française existante
- **Option** : 5
- **Entrée** : ID du fichier audio
- **Affiche** : Texte français traduit

### Exemple d'utilisation
```bash
$ python translation/text_translator.py

🌐 Traducteur de Textes Whisper
===============================

Options disponibles:
1. 🌐 Traduire un texte spécifique
2. 🔄 Traduction en lot (limité à 20 textes)
3. 📊 Afficher les statistiques
4. 🔍 Lister les textes sans traduction française
5. 📖 Lire une traduction française existante
0. ❌ Retour

🎯 Votre choix (0-5): 2
📊 Nombre max de textes (Enter pour 20): 15

🎯 15 textes à traduire en français
🌐 Traduction française...: 100%|██████████| 15/15 [01:45<00:00]
✅ Traduction française terminée
```

## 🎵 Module 3 : TTS (Text-to-Speech)

### Description
Génère de l'audio français à partir des textes traduits.

### Utilisation
```bash
python translation/tts.py
```

### Moteurs TTS supportés

#### Bark
- **Qualité** : Très élevée
- **Voix** : Naturelles
- **Installation** : `pip install bark`
- **Avantages** : Gratuit, voix réalistes
- **Inconvénients** : Plus lent

#### ElevenLabs
- **Qualité** : Exceptionnelle
- **Voix** : Ultra-réalistes
- **Installation** : `pip install elevenlabs`
- **Avantages** : Qualité professionnelle
- **Inconvénients** : Nécessite une clé API

## 📊 Monitoring et Statistiques

### Vérifier l'état du système

#### Statistiques Whisper
```bash
python translation/whisper_simple.py
# Option 3
```

#### Statistiques Traduction
```bash
python translation/text_translator.py
# Option 3
```

### Requêtes SQL utiles

#### Nombre de transcriptions
```sql
SELECT COUNT(*) FROM whisper_texts;
```

#### Nombre de traductions
```sql
SELECT COUNT(*) FROM whisper_translations;
```

#### Textes sans traduction française
```sql
SELECT w.video_id, w.translated_text 
FROM whisper_texts w
LEFT JOIN whisper_translations wt ON w.video_id = wt.video_id
WHERE wt.video_id IS NULL;
```

#### Progression complète
```sql
SELECT 
    COUNT(DISTINCT w.video_id) as total_whisper,
    COUNT(DISTINCT wt.video_id) as total_translations,
    ROUND(COUNT(DISTINCT wt.video_id) * 100.0 / COUNT(DISTINCT w.video_id), 2) as completion_percent
FROM whisper_texts w
LEFT JOIN whisper_translations wt ON w.video_id = wt.video_id;
```

## ⚙️ Configuration

### Variables d'environnement
```bash
# ElevenLabs (optionnel)
export ELEVENLABS_API_KEY="your_api_key_here"

# Configuration Whisper
export WHISPER_MODEL="base"  # base, small, medium, large
```

### Limites configurables
- **Traitement Whisper** : 20 fichiers par défaut
- **Traduction** : 20 textes par défaut
- **TTS** : Selon le moteur choisi

## 🐛 Dépannage

### Problèmes courants

#### 1. Erreur Whisper
```bash
# Vérifier l'installation
pip install openai-whisper

# Vérifier FFmpeg
ffmpeg -version

# Redémarrer le module
python translation/whisper_simple.py
```

#### 2. Erreur de traduction
```bash
# Vérifier la connexion internet
ping google.com

# Vérifier requests
pip install requests

# Tester avec un texte court
```

#### 3. Erreur de base de données
```bash
# Recréer les tables
python fix_whisper_table.py
python fix_translations_table.py

# Vérifier les permissions
ls -la database.db
```

### Logs et débogage

#### Vérifier les données
```bash
# Lire une transcription
python translation/whisper_simple.py
# Option 5, entrer un ID

# Lire une traduction
python translation/text_translator.py
# Option 5, entrer un ID
```

#### Vérifier les fichiers
```bash
# Lister les audios disponibles
ls datas/audios_En/*.mp3

# Vérifier la taille des fichiers
du -h datas/audios_En/*.mp3
```

## 🔄 Workflow Complet Recommandé

### Étape 1 : Préparation
```bash
# Vérifier les fichiers audio
ls datas/audios_En/*.mp3 | wc -l

# Vérifier l'espace disque
df -h
```

### Étape 2 : Transcription Whisper
```bash
python translation/whisper_simple.py
# Option 2 - Traitement en lot
# Entrer le nombre de fichiers (ex: 50)
```

### Étape 3 : Traduction en Français
```bash
python translation/text_translator.py
# Option 2 - Traduction en lot
# Entrer le nombre de textes (ex: 50)
```

### Étape 4 : Vérification
```bash
# Statistiques Whisper
python translation/whisper_simple.py
# Option 3

# Statistiques Traduction
python translation/text_translator.py
# Option 3
```

### Étape 5 : TTS (Optionnel)
```bash
python translation/tts.py
# Choisir le moteur et les textes
```

## 📈 Optimisations

### Performance
- **Whisper** : Utiliser le modèle "base" pour la vitesse
- **Traduction** : Traiter par lots pour éviter les limites d'API
- **TTS** : Utiliser Bark pour la gratuité, ElevenLabs pour la qualité

### Stockage
- Les textes sont stockés en base de données (pas de fichiers .txt)
- Les audios générés peuvent être compressés
- Sauvegarder régulièrement la base de données

### Monitoring
- Vérifier les statistiques régulièrement
- Surveiller l'espace disque
- Tester les APIs de traduction

## 🎯 Bonnes Pratiques

### Organisation
1. **Nommage** : Utiliser des IDs cohérents pour les fichiers
2. **Sauvegarde** : Sauvegarder la base de données régulièrement
3. **Monitoring** : Vérifier les statistiques après chaque lot

### Traitement
1. **Whisper** : Traiter par petits lots (10-20 fichiers)
2. **Traduction** : Attendre entre les lots pour éviter les limites
3. **TTS** : Choisir le moteur selon les besoins

### Maintenance
1. **Nettoyage** : Supprimer les anciens fichiers .txt
2. **Mise à jour** : Maintenir les dépendances à jour
3. **Documentation** : Noter les changements de configuration

---

**Version** : 2.0  
**Dernière mise à jour** : 2024  
**Statut** : ✅ Fonctionnel et documenté 