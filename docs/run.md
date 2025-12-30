# Running AffiliatePrograms.wiki (Local)

## 1) API

```bash
bash ~/affiliateprograms-wiki/api/bootstrap_venv.sh
export DATABASE_URL="$(/home/skynet/google-cloud-sdk/bin/gcloud secrets versions access latest --secret=database_url_affiliate_wiki --project superapp-466313)"
~/affiliateprograms-wiki/api/.venv/bin/python ~/affiliateprograms-wiki/api/server.py
```

API runs at `http://127.0.0.1:8120` (docs: `http://127.0.0.1:8120/docs`).

## 2) UI (Affiliate Compass design)

```bash
cd ~/affiliateprograms-wiki/web/affiliate-compass-ui
npm i
echo 'VITE_API_BASE_URL=http://127.0.0.1:8120' > .env.local
npm run dev
```

