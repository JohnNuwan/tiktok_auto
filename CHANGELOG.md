# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

## [2.2.0] - 2024-12-19

### ✅ Ajouté
- **CTA audio intégrés** : Messages vocaux d'incitation à s'abonner à la fin des shorts
- **Organisation structurée des shorts** : Dossiers organisés par plateforme et type
- **Durée minimale garantie** : 70 secondes (1min10) pour tous les shorts
- **Générateur de shorts automatiques** : Interface CLI complète pour la génération de shorts
- **Détection virale améliorée** : Algorithmes sophistiqués pour identifier les moments viraux
- **Effets visuels avancés** : Zoom progressif, transitions fade, filtres de couleur
- **Système d'analytics** : Suivi complet des performances (vues, likes, partages)
- **Interface analytics** : CLI pour consulter les statistiques et rapports
- **Nettoyage automatique** : Suppression des fichiers temporaires
- **Miniatures automatiques** : Génération de thumbnails pour les shorts

### 🔧 Modifié
- **Structure des dossiers shorts** : Organisation en `final/`, `temp/`, `thumbnails/`, `platforms/`
- **CTA implementation** : Passage des sous-titres aux messages audio
- **Durée des shorts** : Minimum 70 secondes garanti pour tous les formats
- **Gestion des erreurs** : Meilleure gestion des erreurs FFmpeg et TTS
- **Documentation** : Mise à jour complète avec les nouvelles fonctionnalités

### 🗑️ Supprimé
- **CTA sous-titres** : Remplacés par des messages audio
- **Ancienne organisation** : Structure de dossiers non organisée

## [2.1.0] - 2024-12-18

### ✅ Ajouté
- **Format TikTok corrigé** : Format 9:16 (vertical) pour tous les shorts
- **Durées optimisées** : Shorts de 15-60 secondes (vrais shorts)
- **Découpage automatique** : Les vidéos longues sont automatiquement découpées
- **Détection virale améliorée** : +50 mots-clés viraux et algorithme sophistiqué
- **Effets visuels avancés** : Zoom progressif, transitions fade, filtres de couleur
- **Système d'analytics** : Suivi complet des performances (vues, likes, partages)
- **Interface analytics** : CLI pour consulter les statistiques et rapports

### 🔧 Modifié
- **Architecture** : Refactorisation complète en modules spécialisés
- **Base de données** : Nouvelles tables pour Whisper, traductions, TTS, shorts
- **Workflow** : Pipeline simplifié et optimisé
- **Interface** : Menu principal mis à jour

### 🗑️ Supprimé
- **Modules obsolètes** : Anciens modules de traduction et TTS
- **Fichiers temporaires** : Scripts de migration et de test

## [1.5.0] - 2024-08-06

### ✅ Ajouté
- **Support ElevenLabs** : Intégration TTS haute qualité
- **Interface graphique** : GUI avec CustomTkinter
- **Gestion des erreurs** : Meilleure gestion des exceptions
- **Documentation** : Guides d'utilisation

### 🔧 Modifié
- **TTS** : Support multi-moteurs (Bark + ElevenLabs)
- **Interface** : Amélioration de l'UX

## [1.0.0] - 2024-08-05

### ✅ Ajouté
- **Transcription audio** : Support Whisper
- **Traduction** : Google Translate API
- **TTS** : Support Bark
- **Base de données** : Stockage SQLite
- **Interface CLI** : Menu interactif
- **Gestion des fichiers** : Organisation automatique 