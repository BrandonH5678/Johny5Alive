import argparse, json, pathlib
from urllib.parse import urlparse
from .rwf import RobustWebFetcher
from .discovery import discover_audio_from_homepage

def _safe_name(url: str) -> str:
    p = urlparse(url)
    return (p.netloc + p.path).replace("/", "_")

def cmd_discover(args):
    fetcher = RobustWebFetcher()
    url, meta = discover_audio_from_homepage(args.home, args.title, args.ep, fetcher=fetcher)
    print(json.dumps({"media_url": url, "meta": meta}, indent=2))

def cmd_download(args):
    fetcher = RobustWebFetcher()
    url, meta = discover_audio_from_homepage(args.home, args.title, args.ep, fetcher=fetcher)
    outdir = pathlib.Path(args.out or "./output"); outdir.mkdir(parents=True, exist_ok=True)
    filename = args.name or _safe_name(url)
    if not any(filename.endswith(ext) for ext in (".mp3",".m4a",".aac",".ogg",".opus",".wav")):
        filename += ".bin"
    outpath = outdir / filename
    with fetcher.s.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(outpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*512):
                if chunk: f.write(chunk)
    print(json.dumps({"media_url": url, "meta": meta, "downloaded_to": str(outpath)}, indent=2))

def main(argv=None):
    p = argparse.ArgumentParser(prog="retriever", description="Retriever CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Discover media URL from homepage")
    d.add_argument("--home", required=True, help="Homepage URL")
    d.add_argument("--title", help="Prefer title substring")
    d.add_argument("--ep", type=int, help="Prefer episode number in title")
    d.set_defaults(func=cmd_discover)

    dl = sub.add_parser("download", help="Discover and download media")
    dl.add_argument("--home", required=True, help="Homepage URL")
    dl.add_argument("--title", help="Prefer title substring")
    dl.add_argument("--ep", type=int, help="Prefer episode number in title")
    dl.add_argument("--out", help="Output directory")
    dl.add_argument("--name", help="Output filename (without extension)")
    dl.set_defaults(func=cmd_download)

    args = p.parse_args(argv)
    args.func(args)

if __name__ == "__main__":
    main()
