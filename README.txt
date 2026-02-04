# FOSA – Plateforme Santé 

Ce projet a été réalisé pendant mon stage à l’Agence Numérique de l’État en Mauritanie.  
L’objectif était de développer un module (FOSA) pour rassembler les données des structures de santé et de les rendre accessibles via une application web (backend Django + frontend React).

---

## Comment lancer le projet

### Backend (Django)
Dans le dossier `backend` :
```bash
python -m venv .venv
source .venv/bin/activate   # sous Linux/Mac
# .venv\Scripts\Activate.ps1 # sous Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Le backend est dispo sur : http://127.0.0.1:8000
Frontend (React)

Dans le dossier frontend :

npm install
npm start

Le site démarre sur : http://localhost:3000
Répertoires principaux

.
├── backend/                # Code Django (API + logique métier)
│   ├── manage.py
│   ├── requirements.txt
│   ├── project/            # configuration Django (settings, urls…)
│   ├── fosa/               # app Django pour la gestion des structures de santé
│   └── data/
│       └── structures-sante.xlsx   # fichier Excel importé
└── frontend/               # Code React (interface utilisateur)
    ├── package.json
    ├── src/
    │   ├── App.js
    │   ├── components/     # composants réutilisables
    │   ├── pages/          # pages principales
    │   └── services/       # appels API
    └── public/

Données déjà présentes

Un fichier structures-sante.xlsx est inclus et contient les structures de santé déjà importées.
Ça permet de tester directement le module FOSA sans recréer toutes les données.
Compte admin

Interface d’administration : http://127.0.0.1:8000/admin/

    utilisateur : cheikh

    code : 37797933AW-

Ce que fait le projet

    Module FOSA : gestion des structures de santé (CH, CS, PS, etc.), avec codification par wilaya/moughataa/commune et géolocalisation.

    API REST : accès aux données en JSON. Exemple :

        /api/fosa/ → liste des structures de santé

Outils utilisés

    Backend : Django + Django REST Framework

    Frontend : React (Axios, Leaflet pour la carte)

    Base de données : SQLite (en développement)

    Import de données : fichier Excel structures-sante.xlsx

Remarques

    En développement, j’utilise python manage.py runserver et npm start. Ça marche directement sur Linux, Mac ou Windows si Python et Node sont installés.

    Pour tester rapidement, il suffit de lancer les deux serveurs et d’ouvrir le frontend.

    Le projet est pensé pour évoluer (PostgreSQL, Nginx, ajout du module Éducation…), mais ce n’était pas inclus dans mon stage.
