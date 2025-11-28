# Matrix Studio - Générateur EEPROM pour Matrice LED (Logique Câblée)

**Matrix Studio** est une application de bureau Python permettant de dessiner des animations pixel-art sur une grille 16x16 et de générer les fichiers binaires (`.bin`) nécessaires pour piloter un écran à LED basé sur une architecture **"Hard Logic" (Logique Câblée)**, sans aucun microcontrôleur.

Ce projet a été conçu spécifiquement pour une simulation **Proteus ISIS** utilisant des compteurs, des décodeurs et des mémoires EEPROM (type 27C64).

## Fonctionnalités

  * **Éditeur Graphique :** Dessin à la souris (clic gauche : allumer, clic droit : éteindre) sur une matrice 16x16.
  * **Timeline d'Animation :** Création, duplication, suppression et réorganisation des frames.
  * **Prévisualisation :** Lecture de l'animation en temps réel avec vitesse réglable.
  * **Gestion de Projet :** Sauvegarde et chargement des dessins au format JSON.
  * **Moteur d'Exportation Avancé :**
      * Découpage automatique de la grille 16x16 en 4 sous-blocs 8x8 (TL, TR, BL, BR).
      * **Correction Hardware :** Gestion de l'inversion de polarité, miroir horizontal/vertical et ordre des bits.
      * **Correction de Décalage (Offset) :** Algorithme de rotation circulaire pour compenser le déphasage entre le compteur et le balayage des lignes.
      * **Remplissage Mémoire (Looping) :** Répétition automatique de l'animation pour remplir l'espace d'adressage (évite les écrans noirs si le compteur dépasse le nombre de frames dessinées).

## Architecture Matérielle Cible

Ce logiciel génère des données pour une architecture matérielle spécifique :

1.  **Affichage :** 4 matrices LED 8x8 assemblées pour former un écran 16x16.
2.  **Mémoire :** 4 EEPROMs (ex: 27C64), une par quadrant.
3.  **Adressage :**
      * **A0-A2 :** Balayage des lignes (Scan).
      * **A3-Axx :** Sélection de la Frame (Animation).
4.  **Logique :** Active Low (Anode commune) ou Active High, configurable dans le logiciel.

## Installation et Lancement

Aucune installation complexe n'est requise. L'application utilise les librairies standard de Python.

### Prérequis

  * Python 3.x installé sur votre machine.

### Lancement

1.  Clonez ce dépôt :
    ```bash
    git clone https://github.com/Tiger-Foxx/led-matrix-tkinter.git
    cd matrix-studio
    ```
2.  Lancez le script :
    ```bash
    python main.py
    ```

## Guide de Configuration (Export)

Le panneau de droite contient des réglages cruciaux pour adapter le fichier binaire à votre câblage Proteus/Réel.

### Configuration Recommandée (Setup Validé)

Si vous utilisez le schéma standard développé pour ce projet, voici les réglages par défaut :

  * [x] **Inverser Bits (D0↔D7)** : `Activé`. Corrige l'ordre des bits souvent inversé sur les matrices Proteus.
  * [x] **Inverser Polarité (Low)** : `Activé`. Pour les matrices à Anode Commune (0 = Allumé, 1 = Éteint).
  * [x] **Flip Horizontal (X)** : `Activé`. Corrige l'effet miroir gauche/droite.
  * [ ] **Flip Vertical (Y)** : `Désactivé`.
  * **Offset Y** : `-1`. Corrige le décalage circulaire d'une ligne vers le bas induit par le compteur.
  * **Taille Boucle** : `64`. Remplit les 64 premières "cases" d'animation de la mémoire (Frames A3..A8).

### Détails des Options

| Option | Description |
| :--- | :--- |
| **Inverser Bits** | Inverse l'ordre des bits d'un octet (MSB devient LSB). Utile si D0 est câblé sur la colonne 7. |
| **Inverser Polarité** | Inverse les 0 et les 1. Cochez cette case si votre matrice s'allume en "négatif". |
| **Offset Y** | Applique une rotation verticale des lignes. Si votre image est décalée d'une ligne vers le bas, mettez `-1`. |
| **Taille Boucle** | Définit combien de slots mémoire remplir. Le logiciel copiera vos frames en boucle pour atteindre ce nombre. |

## Utilisation des fichiers BIN

Une fois l'export terminé, vous obtiendrez 4 fichiers :

1.  `nom_TL.bin` (Top-Left) -\> Charger dans l'EEPROM U4 (par ex.)
2.  `nom_TR.bin` (Top-Right) -\> Charger dans l'EEPROM U5
3.  `nom_BL.bin` (Bottom-Left) -\> Charger dans l'EEPROM U6
4.  `nom_BR.bin` (Bottom-Right) -\> Charger dans l'EEPROM U7

Dans Proteus : Double-cliquez sur chaque EEPROM et chargez le fichier correspondant dans le champ "Image File".


