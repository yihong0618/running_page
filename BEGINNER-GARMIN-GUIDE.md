# Beginner Guide: Run Your Garmin Running Page on Your Own Machine

This guide is for non-coders. Follow it exactly from top to bottom.

## 1) Install required apps

Install these first:

1. **Git**: https://git-scm.com/downloads
2. **Python 3.11+**: https://www.python.org/downloads/
3. **Node.js 20+**: https://nodejs.org/
4. **pnpm** (after Node is installed):

```bash
npm install -g pnpm
```

## 2) Download this project

Open Terminal (macOS) or PowerShell (Windows) and run:

```bash
git clone https://github.com/yihong0618/running_page.git
cd running_page
```

## 3) Install project dependencies

```bash
pip install -r requirements.txt
pnpm install
```

## 4) Pull your Garmin data (easy way)

Run this command and replace your email:

```bash
./scripts_garmin_quickstart.sh --email "your_garmin_email@example.com"
```

- It will ask your Garmin password securely.
- It will automatically:
  1. get your Garmin secret,
  2. sync your activities,
  3. generate running SVG,
  4. start the local website.

## 4.1) Data-only mode (no webpage)

Yes, this is possible. If you only want workout data for analysis, run:

```bash
./scripts_garmin_quickstart.sh --email "your_garmin_email@example.com" --no-web
```

This will sync your Garmin data and prepare files/database, but **will not** start the website server.

## 5) Open your running page

When the command finishes setup, open:

- http://localhost:5173

## 6) If you use Garmin China

Use:

```bash
./scripts_garmin_quickstart.sh --email "your_garmin_email@example.com" --is-cn
```

## 7) Common problems (copy these fixes)

### "command not found: pnpm"

```bash
npm install -g pnpm
```

### "Permission denied" for script

```bash
chmod +x scripts_garmin_quickstart.sh
./scripts_garmin_quickstart.sh --email "your_garmin_email@example.com"
```

### Python package install error

Try:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

If you want, after this is working locally, you can deploy it online with Vercel in the next step.
