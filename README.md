## Full‑page Screenshot pentru Web (Flask + Playwright)

Aplicație care face capturi full‑page din pagini web și le optimizează pentru publicare (redimensionare, compresie). Oferă:
- interfață web (formular) cu previzualizare inline și link de descărcare
- utilitar CLI flexibil cu opțiuni pentru format, dimensiuni, calitate și momentul capturii

### Cerințe
- Python 3.7+
- macOS/Linux/Windows

### Instalare
```bash
cd "/Users/a1707/Desktop/screenshoter site"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

### Rulare – Interfață web
```bash
cd "/Users/a1707/Desktop/screenshoter site"
source .venv/bin/activate
# dacă portul 5000 e ocupat
lsof -ti tcp:5000 | xargs -r kill -9
"/Users/a1707/Desktop/screenshoter site/.venv/bin/python" webapp.py
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
"/Users/a1707/Desktop/screenshoter site/.venv/bin/python" webapp.py
```
- „Address already in use” pe 5000 – eliberează portul sau pornește pe alt port:
```bash
lsof -ti tcp:5000 | xargs -r kill -9
# sau:
FLASK_APP=webapp:app flask run --port 5001
```
- „Eroare la generare (subprocess)” în UI – pagina afișează ultimele linii din stdout/stderr de la subproces. Încearcă:
  - mărește `Timeout încărcare (ms)`
  - mărește `Wait după autoscroll (ms)`
  - schimbă „Moment captură” la `load` sau `domcontentloaded`

### Structura proiectului
- `screenshot.py` – captură full‑page cu Playwright și optimizare cu Pillow (CLI)
- `webapp.py` – server Flask (formular + previzualizare)
- `templates/index.html` – UI
- `requirements.txt` – dependențe

