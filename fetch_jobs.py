"""
AI Viddya Jobs Fetcher - runs on GitHub Actions, writes jobs.json
Secrets: JSEARCH_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY (missing = skipped)
"""
import json, os, re, time, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

KEYWORDS = ["machine learning engineer","data scientist","python developer",
    "generative ai engineer","data analyst","mlops engineer","data engineer"]
MAX_PER_KEYWORD = 10
MAX_AGE_DAYS = 45
MAX_JOBS = 120
OUT_FILE = "jobs.json"
JSEARCH_KEY = os.environ.get("JSEARCH_API_KEY","").strip()
ADZUNA_ID = os.environ.get("ADZUNA_APP_ID","").strip()
ADZUNA_KEY = os.environ.get("ADZUNA_APP_KEY","").strip()
KEEP_RE = re.compile(r"(machine learning|ml engineer|data scien|data analy|python|generative ai|genai|llm|deep learning|nlp|data engineer|mlops|llmops|ai engineer|artificial intelligence)", re.I)
DROP_RE = re.compile(r"(sales|marketing|human resource|accountant|teacher|nurse|driver|delivery|cook|waiter|security guard|telecaller)", re.I)

def http_get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent":"aividdya-jobs-bot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8","ignore"))

def clean_text(t, limit=600):
    t = re.sub(r"<[^>]+>"," ",t or ""); t = re.sub(r"\s+"," ",t).strip()
    return t[:limit]

def relevant(title, desc=""):
    blob = f"{title} {desc}"
    return bool(KEEP_RE.search(blob)) and not bool(DROP_RE.search(blob))

def fetch_jsearch(keywords):
    jobs = []
    headers = {"X-RapidAPI-Key":JSEARCH_KEY,"X-RapidAPI-Host":"jsearch.p.rapidapi.com","User-Agent":"aividdya-jobs-bot/1.0"}
    for kw in keywords:
        try:
            q = urllib.parse.urlencode({"query":f"{kw} in India","page":"1","num_pages":"1","country":"in"})
            data = http_get(f"https://jsearch.p.rapidapi.com/search?{q}", headers)
            for j in data.get("data",[])[:MAX_PER_KEYWORD]:
                title=j.get("job_title",""); desc=j.get("job_description","")
                if not relevant(title,desc): continue
                jobs.append({"id":"js_"+str(j.get("job_id","")),"title":title.strip(),
                    "company":(j.get("employer_name") or "").strip(),
                    "location":", ".join(filter(None,[j.get("job_city"),j.get("job_state"),j.get("job_country")])),
                    "type":(j.get("job_employment_type") or "").strip(),
                    "posted":(j.get("job_posted_at_datetime_utc") or "")[:10],
                    "description":clean_text(desc),
                    "apply_url":j.get("job_apply_link") or j.get("job_google_link") or "",
                    "source":j.get("job_publisher") or "JSearch","category":kw})
            time.sleep(1)
        except Exception as e:
            print(f"[jsearch] '{kw}' failed: {e}")
    print(f"[jsearch] {len(jobs)} jobs"); return jobs

def fetch_adzuna(keywords):
    jobs = []
    for kw in keywords:
        try:
            q = urllib.parse.urlencode({"app_id":ADZUNA_ID,"app_key":ADZUNA_KEY,"what":kw,
                "where":"India","results_per_page":MAX_PER_KEYWORD,"content-type":"application/json"})
            data = http_get(f"https://api.adzuna.com/v1/api/jobs/in/search/1?{q}")
            for j in data.get("results",[])[:MAX_PER_KEYWORD]:
                title=j.get("title",""); desc=j.get("description","")
                if not relevant(title,desc): continue
                loc=j.get("location") or {}
                jobs.append({"id":"az_"+str(j.get("id","")),"title":title.strip(),
                    "company":((j.get("company") or {}).get("display_name") or "").strip(),
                    "location":", ".join(filter(None,[loc.get("display_name"),"India"])),
                    "type":(j.get("contract_type") or "").strip(),
                    "posted":(j.get("created") or "")[:10],
                    "description":clean_text(desc),
                    "apply_url":j.get("redirect_url") or "",
                    "source":"Adzuna","category":kw})
            time.sleep(1)
        except Exception as e:
            print(f"[adzuna] '{kw}' failed: {e}")
    print(f"[adzuna] {len(jobs)} jobs"); return jobs

def load_existing():
    try:
        with open(OUT_FILE,encoding="utf-8") as f:
            d=json.load(f); return d.get("jobs",[]) if isinstance(d,dict) else []
def main():
    day_index=datetime.now(timezone.utc).timetuple().tm_yday
    rot=KEYWORDS[day_index%len(KEYWORDS):]+KEYWORDS[:day_index%len(KEYWORDS)]
    batch=rot[:3]
    print("batch:",batch)
    fresh=[]
    fresh+=fetch_jsearch(batch) if JSEARCH_KEY else print("[jsearch] skipped (no key)") or []
    fresh+=fetch_adzuna(batch) if (ADZUNA_ID and ADZUNA_KEY) else print("[adzuna] skipped (no key)") or []
    def dkey(j):
        t=re.sub(r'\+',',(j.get('title') or '').lower())
                 c=re.sub(r'\+',',(j.get('company') or '').lower())
                 return t+'|'+c    
    merged={dkey(j):j for j in load_existing()}
    for j in fresh: merged[dkey(j)]=j
    cutoff=(datetime.now(timezone.utc)-timedelta(days=MAX_AGE_DAYS)).date().isoformat()
    jobs=[j for j in merged.values() if (j.get("posted") or "9999")>=cutoff]
    jobs.sort(key=lambda j:j.get("posted") or "",reverse=True); jobs=jobs[:MAX_JOBS]
    out={"updated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"count":len(jobs),"jobs":jobs}
    open(OUT_FILE,"w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    print(f"wrote {OUT_FILE}: {len(jobs)} jobs")

if __name__=="__main__": main()
