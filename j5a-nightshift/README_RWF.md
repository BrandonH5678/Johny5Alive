
# J5A Nightshift + Robust Web Fetcher Integration Kit

This kit connects your local Ollama-based Nightshift workflow with your existing Robust Web Fetcher (RWF) repository.
It enables automatic discovery and download of podcast media files (MP3/M4A/M3U8) directly from episode webpages.

### Components
- `podcast_fetch_with_rwf.py` — main wrapper integrating RWF, Ollama, and curl/ffmpeg.
- `contracts/find_candidates_rwf.txt` — LLM prompt for ranking candidate media URLs.
- `contracts/download_command_rwf.txt` — LLM prompt for generating safe download commands.
- `nightly_job_runner_rwf.sh` — one-line runner.
- `README_RWF.md` — setup and usage notes.

### Installation
```bash
cd ~/j5a-nightshift/ops/fetchers
git clone https://github.com/BrandonH5678/robust-web-fetcher.git
pip install -e robust-web-fetcher/
```

Then run:
```bash
chmod +x nightly_job_runner_rwf.sh
./nightly_job_runner_rwf.sh "https://example.com/episode/34" "Weaponized – Episode 34"
```

Outputs appear in:
- `ops/outputs/podcast_download/`
- `ops/logs/podcast_fetch.log`
