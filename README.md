# PDFLibre 🗂️

Outils PDF gratuits & illimités — clone open-source d'iLovePDF.

## Stack

| Couche | Techno |
|--------|--------|
| Frontend | HTML/CSS/JS vanilla (zéro dépendance) |
| Backend | Python 3.12 + FastAPI |
| PDF | pypdf, pdf2image (poppler), Pillow, reportlab |
| Déploiement | Docker · Railway · Render |

## Outils disponibles

- ✅ Fusionner PDF
- ✅ Diviser PDF (toutes pages / plages)
- ✅ Rotation (90°/180°, toutes/paires/impaires)
- ✅ Compresser PDF (3 niveaux)
- ✅ Filigrane texte (opacité, position)
- ✅ PDF → JPG/PNG/WebP (DPI configurable)
- ✅ JPG/PNG → PDF (A4, Lettre, ajusté)
- ✅ Protéger PDF (mot de passe AES-128)
- 🔜 Déverrouiller PDF
- 🔜 PDF → Word

---

## 🚀 Lancer en local (2 minutes)

### Prérequis
- Docker + Docker Compose installés

### Démarrage
```bash
git clone <votre-repo>
cd pdflibre
docker-compose up --build
```

- **Frontend** → http://localhost:3000
- **API docs** → http://localhost:8000/docs
- **Health**   → http://localhost:8000/health

### Sans Docker (dev Python)
```bash
cd backend
pip install -r requirements.txt
# macOS/Linux: installer poppler
# Ubuntu: sudo apt install poppler-utils
# macOS: brew install poppler
uvicorn app.main:app --reload --port 8000
```
Puis ouvrez `frontend/index.html` dans le navigateur.

---

## ☁️ Déployer sur Railway (gratuit)

1. Créez un compte sur [railway.app](https://railway.app)
2. **New Project → Deploy from GitHub repo**
3. Sélectionnez le dossier `backend/` comme **Root Directory**
4. Railway détecte automatiquement le `Dockerfile`
5. Récupérez l'URL publique (ex: `https://pdflibre-api.railway.app`)
6. Dans `frontend/index.html`, ligne `API_BASE`, remplacez `''` par votre URL :
   ```js
   const API_BASE = 'https://pdflibre-api.railway.app';
   ```
7. Déployez le frontend sur [Vercel](https://vercel.com) ou Netlify (drag & drop du dossier `frontend/`)

---

## ☁️ Déployer sur Render (gratuit)

1. Créez un compte sur [render.com](https://render.com)
2. **New → Web Service → Connect GitHub**
3. Root directory : `backend/`
4. Render détecte le `render.yaml` automatiquement
5. Deploy → récupérez l'URL publique
6. Même étape frontend que ci-dessus

---

## Structure du projet

```
pdflibre/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + routes
│   │   ├── routers/
│   │   │   ├── merge.py
│   │   │   ├── split.py
│   │   │   ├── compress.py
│   │   │   ├── rotate.py
│   │   │   ├── pdf2jpg.py
│   │   │   ├── jpg2pdf.py
│   │   │   ├── watermark.py
│   │   │   └── protect.py
│   │   └── utils/
│   │       └── files.py         # tmp files + cleanup
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── railway.json
│   └── render.yaml
├── frontend/
│   └── index.html               # App complète (single file)
├── docker-compose.yml
└── README.md
```

---

## Variables d'environnement (optionnelles)

| Variable | Défaut | Description |
|----------|--------|-------------|
| `PORT` | `8000` | Port d'écoute |
| `MAX_FILE_SIZE_MB` | illimité | Limite taille fichier |
| `ALLOWED_ORIGINS` | `*` | CORS origins |

---

## Prochaines étapes

- [ ] Auth JWT (historique des fichiers)
- [ ] Unlock PDF (pikepdf)
- [ ] PDF → Word (python-docx + pdfminer)
- [ ] OCR (pytesseract)
- [ ] Suppression automatique des fichiers temp (cron)
- [ ] Rate limiting par IP
- [ ] Analytics (Plausible ou Umami — sans cookies)
