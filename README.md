## Full‑page Screenshot pentru orice pagină Web (Flask + Playwright)

Aplicație care face capturi full‑page din pagini web și le optimizează pentru publicare (redimensionare, compresie). Oferă:
- interfață web (formular) cu previzualizare inline și link de descărcare
- utilitar CLI flexibil cu opțiuni pentru format, dimensiuni, calitate și momentul capturii

ÎNCERCAȚI DEMO https://screenshoter-site-dsvh.onrender.com/

### Cerințe
- Python 3.7+
- macOS/Linux/Windows

### Instalare
```bash
cd /cale/către/proiect
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

### Rulare – Interfață web
```bash
cd /cale/către/proiect
# macOS/Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\activate
# dacă portul 5000 e ocupat (macOS/Linux)
lsof -ti tcp:5000 | xargs -r kill -9
python webapp.py
```
- Deschide în browser: `http://127.0.0.1:5000`
- Completează URL-ul, apoi „Generează”. Imaginea apare sub formular (previzualizare + butoane „Descarcă”/„Deschide într-un tab nou”).

Opțiuni din UI (secțiunea „Opțiuni avansate”):
- Format: `WEBP` (implicit), `JPEG`, `PNG`
- Lățime finală (px): redimensionare pe lățime
- Înălțime maximă (px): crop vertical din partea de sus dacă imaginea depășește această înălțime
- Lățime captură (viewport): lățimea cu care se randă pagina
- Moment captură: `Rapid (DOM)`, `Complet (load)`, `Rețea liniștită (networkidle)`
- Wait după autoscroll (ms): pauză mică după ce derulăm ca să se încarce conținutul lazy

Note:
- Aplicația derulează pagina pentru a încărca conținutul lazy, apoi revine automat la începutul paginii ca header‑ul să fie corect în captură.

### Rulare – Linie de comandă (CLI)
Exemple:
```bash
# WebP optimizat (lățime 900px), așteaptă încărcare completă
python screenshot.py https://exemplu.ro -o pagina.webp \
  --output-width 900 --wait-until load --wait-ms 1200

# JPEG (lățime 1200px), cu înălțime maximă 1500px
python screenshot.py https://exemplu.ro -f jpeg -o pagina.jpg \
  --output-width 1200 --output-height 1500 --quality 70

# PNG (fără pierderi), doar redimensionare
python screenshot.py https://exemplu.ro -f png -o pagina.png --output-width 1000
```

Parametri principali CLI:
- `-o, --output`: calea fișierului rezultat (extensia stabilește formatul)
- `-f, --format`: `webp` (implicit), `jpeg`, `png`
- `--capture-width`: lățimea viewport‑ului pentru randare (implicit 1280)
- `--output-width`: lățimea finală a imaginii (implicit 800)
- `--output-height`: înălțimea maximă; dacă e depășită, se face crop vertical din partea de sus
- `--quality`: calitate pentru `webp/jpeg` (1–100, implicit 70)
- `--max-bytes`: mărimea maximă a fișierului (în bytes); reduce calitatea iterativ până încape
- `--wait-until`: `domcontentloaded` | `load` (implicit) | `networkidle`
- `--wait-ms`: pauză după auto‑scroll (implicit 800ms)
- `--timeout-ms`: timeout încărcare pagină (implicit 60000ms)
- `--no-autoscroll`: dezactivează auto‑scroll pentru conținut lazy
- `--show-scrollbars`: nu ascunde scrollbars
- `--open`: deschide imaginea salvată în browser

### Sfaturi pentru rezultate stabile
- Dacă pagina face multe cereri după `load`, încearcă `--wait-until networkidle` (poate bloca anumite site‑uri); alternativ crește `--wait-ms`
- Scade `--capture-width` (ex. 1024) dacă pagina e foarte grea
- Folosește `WEBP` pentru fișiere mici, `PNG` doar când ai nevoie de fără pierderi

### Depanare
- „python: command not found” – rulează cu interpreterul din venv:
```bash
# macOS/Linux:
./.venv/bin/python webapp.py
# Windows:
.venv\Scripts\python.exe webapp.py
```
- „Address already in use” pe 5000 – eliberează portul sau pornește pe alt port:
```bash
lsof -ti tcp:5000 | xargs -r kill -9
# sau:
FLASK_APP=webapp:app flask run --port 5001
```

### Structura proiectului
- `screenshot.py` – captură full‑page cu Playwright și optimizare cu Pillow (CLI)
- `webapp.py` – server Flask (formular + previzualizare)
- `templates/index.html` – UI
- `requirements.txt` – dependențe

### Rulare pe GitHub Codespaces
1. Fă push la repo pe GitHub.
2. În pagina repo-ului, apasă „Code” → tab „Codespaces” → „Create codespace on main”.
3. Așteaptă inițializarea. Configurația din `.devcontainer/devcontainer.json` va:
   - crea venv și va instala dependențele
   - instala Playwright cu dependențele de sistem și `chromium`
   - forward‑ui portul `5000`
4. Rulează aplicația din terminalul Codespaces:
   ```bash
   source .venv/bin/activate
   python webapp.py
   ```
5. Codespaces va deschide automat previzualizarea pe portul 5000; poți seta vizibilitatea portului la Public dacă vrei link partajabil.

Notă: GitHub Pages servește doar conținut static, deci nu poate rula direct serverul Flask. Pentru hosting permanent, folosește un PaaS (Render, Railway, Fly.io, Cloud Run, Azure App Service). Dacă dorești, pot adăuga fișiere de deploy pentru una din aceste platforme.

### Deschide direct în GitHub Codespaces
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?hide_repo_select=true&ref=main&repo=alexlescinschi/screenshoter-site)

După deschidere, rularea se face ca mai sus (activare venv și `python webapp.py`). Portul 5000 se va deschide automat în browserul Codespaces.

### Deploy fără bătăi de cap (Render)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

- Blueprint `render.yaml` + `Dockerfile` sunt incluse. Apasă butonul, conectează repo‑ul GitHub și Render va construi imaginea (include Playwright/Chromium) și va porni serviciul web.
- După deploy, accesezi URL‑ul public oferit de Render.

Notă: planul Free poate hiberna după inactivitate; prima accesare după pauză poate dura câteva zeci de secunde.

