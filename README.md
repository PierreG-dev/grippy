# 📁 File Manager – Interface Flask Self-Hosted

Une application web légère et auto-hébergeable pour uploader, lister, télécharger et supprimer des fichiers, avec interface d'administration et API sécurisée par token.

---

## 🧩 Fonctionnalités

- Authentification via interface (admin)
- Upload manuel via interface ou via API
- Génération automatique de liens de téléchargement
- Vue tableau avec tri dynamique (nom, taille, type, date)
- Téléchargement global des fichiers (.zip)
- API REST sécurisée par token
- Icônes visuelles par type de fichier
- Interface responsive en **dark mode**, propulsée par **TailwindCSS**

---

## 📁 Structure du projet

.
├── app.py (ou main.py)
├── .env
├── uploads/ ← Dossier de stockage des fichiers
├── static/
│ └── icons/ ← Icônes SVG des fichiers (.pdf, .zip, .py, etc.)
├── templates/
│ └── dashboard.html ← Interface utilisateur
└── backup.zip ← Généré à la demande via API

---

## 🔐 Fichier `.env` attendu

API_TOKEN=your_api_token_here
ADMIN_USER=admin
ADMIN_PASS=strongpassword
SECRET_KEY=flask_secret_key_here

| Clé          | Description                                   |
| ------------ | --------------------------------------------- |
| `API_TOKEN`  | Token Bearer pour sécuriser les requêtes API  |
| `ADMIN_USER` | Nom d'utilisateur pour le login à l’interface |
| `ADMIN_PASS` | Mot de passe associé                          |
| `SECRET_KEY` | Clé secrète Flask pour les sessions           |

---

## 🚀 Lancer l’application

1. Installe les dépendances :

```bash
pip install flask python-dotenv
```

2. Crée un fichier `.env` à la racine
3. Lance l'app :

```bash
python main.py
```

L'interface est accessible sur `http://localhost:5000`

---

## 📡 API Endpoints

> Toutes les requêtes API doivent inclure un header :  
> `Authorization: Bearer <API_TOKEN>`

### 🔸 Upload

```
POST /api/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
Body: file=<FICHIER>
```

**Réponse JSON :**
{
"message": "File uploaded successfully",
"url": "https://domain.com/files/uuid.png",
"id": "uuid",
"filename": "uuid.png"
}

---

### 🔸 Liste des fichiers

```
GET /api/files
Authorization: Bearer <token>
```

**Réponse :**
[
{
"name": "uuid.png",
"size": 123456,
"url": "https://domain.com/files/uuid.png"
}
]

---

### 🔸 Supprimer un fichier

```
DELETE /api/delete/<filename>
Authorization: Bearer <token>
```

---

### 🔸 Télécharger tous les fichiers

```
GET /api/backup
Authorization: Bearer <token>
```

Renvoie un `.zip` contenant tous les fichiers uploadés.

---

## 🔐 Interface admin

Accès via :

```
GET /login
```

Authentification par `ADMIN_USER` et `ADMIN_PASS`.  
L’interface permet :

- Upload manuel (drag & drop)
- Tri par colonnes (Nom, Taille, Type, Date)
- Copier lien de fichier
- Supprimer un fichier
- Télécharger tous les fichiers

---

## 🛡️ Sécurité recommandée

- Ne jamais exposer cette app sans reverse proxy ou HTTPS
- Utiliser un token fort (`API_TOKEN`)
- Changer la `SECRET_KEY`
- Restreindre les droits du dossier `/uploads/` si nécessaire

---

## 📜 Licence

Ce projet est fourni **sans garantie**, sous la licence de ton choix. Tu peux :

- L’utiliser librement
- Le modifier pour usage personnel
- **Mais ne pas le vendre tel quel sans autorisation**

---

## ✨ Auteurs & crédits

Créé avec ❤️ par **Pierre GODINO**  
Icônes issues de :

- Heroicons (MIT)
- VS Code File Icons (si utilisées)
