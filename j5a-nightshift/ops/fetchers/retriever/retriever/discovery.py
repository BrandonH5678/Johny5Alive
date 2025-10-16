from __future__ import annotations
import re, json, time, logging
from typing import List, Tuple, Dict, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import feedparser

AUDIO_EXT = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav")

# Configure logging
logger = logging.getLogger(__name__)

class DiscoveryRetryConfig:
    """Configuration for cascade-level retry behavior"""
    def __init__(
        self,
        max_cascade_retries: int = 2,
        max_stage_retries: int = 2,
        retry_delay: float = 2.0,
        exponential_backoff: bool = True
    ):
        self.max_cascade_retries = max_cascade_retries
        self.max_stage_retries = max_stage_retries
        self.retry_delay = retry_delay
        self.exponential_backoff = exponential_backoff

class DiscoveryError(Exception):
    """Base exception for discovery failures"""
    def __init__(self, message: str, stage: str, errors: List[str] = None):
        super().__init__(message)
        self.stage = stage
        self.errors = errors or []

def _find_rss_links(html: str, base: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    links = [urljoin(base, l.get("href")) for l in soup.select('link[type="application/rss+xml"]') if l.get("href")]
    candidates = ["/feed", "/podcast", "/podcast/feed", "/category/podcast/feed", "/rss.xml", "/index.xml", "/podcast.xml"]
    links += [urljoin(base, c) for c in candidates]
    seen, uniq = set(), []
    for u in links:
        if u not in seen:
            seen.add(u); uniq.append(u)
    return uniq

def _parse_rss_enclosures(rss_text: str, rss_url: str):
    feed = feedparser.parse(rss_text)
    out = []
    for e in feed.entries:
        title = e.get("title")
        pub = e.get("published") or e.get("updated")
        if e.get("enclosures"):
            for enc in e["enclosures"]:
                href = enc.get("href")
                if isinstance(href, str) and href.lower().endswith(AUDIO_EXT):
                    out.append({"title": title, "pubDate": pub, "url": href, "rss": rss_url})
        for link in e.get("links", []):
            if link.get("rel") == "enclosure":
                href = link.get("href")
                if isinstance(href, str) and href.lower().endswith(AUDIO_EXT):
                    out.append({"title": title, "pubDate": pub, "url": href, "rss": rss_url})
    return out

def _extract_jsonld_audio(html: str):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string or "")
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            if not isinstance(obj, dict): continue
            t = obj.get("@type") or obj.get("@type".lower())
            if t in ("PodcastEpisode","PodcastSeries","AudioObject"):
                for key in ("contentUrl","url"):
                    v = obj.get(key)
                    if isinstance(v,str) and v.lower().endswith(AUDIO_EXT):
                        out.append(v)
                for k in ("associatedMedia","audio"):
                    v = obj.get(k)
                    if isinstance(v,dict):
                        cu = v.get("contentUrl") or v.get("url")
                        if isinstance(cu,str) and cu.lower().endswith(AUDIO_EXT):
                            out.append(cu)
    seen, uniq = set(), []
    for u in out:
        if u not in seen:
            seen.add(u); uniq.append(u)
    return uniq

def _extract_page_audio(html: str, base: str, fetcher) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    urls = []
    for t in soup.select("audio, audio source"):
        src = t.get("src"); 
        if src: urls.append(urljoin(base, src))
    for a in soup.select("a[href]"):
        href = a.get("href","").strip()
        if href.lower().endswith(AUDIO_EXT):
            urls.append(urljoin(base, href))
    for meta in soup.select('meta[property^="og:audio"]'):
        c = meta.get("content"); 
        if c: urls.append(urljoin(base, c))
    HOST_HINTS = ("simplecast","buzzsprout","libsyn","transistor","captivate","acast","omny","megaphone","art19","soundcloud")
    for frame in soup.select("iframe[src]"):
        src = urljoin(base, frame["src"])
        if any(h in src for h in HOST_HINTS):
            try:
                iframe = fetcher.get(src)
                if iframe.status_code < 400:
                    urls.extend(_extract_page_audio(iframe.text, iframe.url, fetcher))
            except Exception:
                pass
    urls.extend(_extract_jsonld_audio(html))
    canon, seen = [], set()
    for u in urls:
        if isinstance(u,str) and u.lower().endswith(AUDIO_EXT) and u not in seen:
            seen.add(u); canon.append(u)
    return canon

def _retry_with_backoff(func, config: DiscoveryRetryConfig, stage_name: str, *args, **kwargs):
    """Retry a function with exponential backoff"""
    errors = []
    delay = config.retry_delay

    for attempt in range(config.max_stage_retries):
        try:
            result = func(*args, **kwargs)
            if result:  # If we got a valid result, return it
                if attempt > 0:
                    logger.info(f"{stage_name} succeeded on retry {attempt + 1}")
                return result
        except Exception as e:
            error_msg = f"{stage_name} attempt {attempt + 1} failed: {str(e)}"
            logger.warning(error_msg)
            errors.append(error_msg)

            if attempt < config.max_stage_retries - 1:
                logger.info(f"Retrying {stage_name} after {delay:.1f}s delay...")
                time.sleep(delay)
                if config.exponential_backoff:
                    delay *= 2

    return None  # All retries exhausted

def _try_rss_discovery(html: str, base_url: str, prefer_title: Optional[str], prefer_epnum: Optional[int], fetcher) -> Optional[Tuple[str, Dict]]:
    """RSS discovery stage with retry logic"""
    logger.info("Starting RSS discovery stage")

    rss_links = _find_rss_links(html, base_url)
    logger.info(f"Found {len(rss_links)} potential RSS feeds")

    for i, rss in enumerate(rss_links, 1):
        logger.debug(f"Trying RSS feed {i}/{len(rss_links)}: {rss}")

        # Check if RSS feed is valid
        ok = True
        if hasattr(fetcher, "head_ok"):
            ok = fetcher.head_ok(rss, content_types=("application/rss+xml","text/xml","application/xml"))

        if not ok:
            logger.debug(f"RSS feed validation failed: {rss}")
            continue

        try:
            rss_resp = fetcher.get(rss)
            if rss_resp.status_code >= 400:
                logger.debug(f"RSS feed returned {rss_resp.status_code}: {rss}")
                continue

            candidates = _parse_rss_enclosures(rss_resp.text, rss)
            logger.info(f"Found {len(candidates)} audio candidates in RSS feed")

            if candidates:
                # Try to match preferences
                if prefer_title:
                    for c in candidates:
                        if c["title"] and prefer_title.lower() in c["title"].lower():
                            logger.info(f"Found title match: {c['title']}")
                            return c["url"], {"method":"rss", **{k:v for k,v in c.items() if k!='url'}}

                if prefer_epnum is not None:
                    pat = re.compile(rf'\b({prefer_epnum})\b')
                    for c in candidates:
                        if c["title"] and pat.search(c["title"]):
                            logger.info(f"Found episode number match: {c['title']}")
                            return c["url"], {"method":"rss", **{k:v for k,v in c.items() if k!='url'}}

                # Return first candidate if no preference match
                logger.info(f"Using first candidate: {candidates[0]['title']}")
                return candidates[0]["url"], {"method":"rss", **{k:v for k,v in candidates[0].items() if k!='url'}}

        except Exception as e:
            logger.warning(f"RSS feed processing error: {str(e)}")
            continue

    logger.info("RSS discovery stage found no results")
    return None

def _try_page_scan(html: str, base_url: str, fetcher) -> Optional[Tuple[str, Dict]]:
    """Page-scan discovery stage with retry logic"""
    logger.info("Starting page-scan discovery stage")

    urls = _extract_page_audio(html, base_url, fetcher)
    logger.info(f"Found {len(urls)} potential audio URLs in page")

    for i, u in enumerate(urls, 1):
        logger.debug(f"Validating audio URL {i}/{len(urls)}: {u}")

        ok = True
        if hasattr(fetcher, "head_ok"):
            ok = fetcher.head_ok(u, content_types=("audio/",), min_bytes=1_000_000)

        if ok:
            logger.info(f"Valid audio URL found: {u}")
            return u, {"method":"page-scan", "page": base_url}

    logger.info("Page-scan discovery stage found no valid results")
    return None

def _try_sitemap_discovery(base_url: str, fetcher) -> Optional[Tuple[str, Dict]]:
    """Sitemap discovery stage with retry logic"""
    logger.info("Starting sitemap discovery stage")

    for sm in ("/sitemap.xml", "/sitemap_index.xml"):
        smu = urljoin(base_url, sm)
        logger.debug(f"Trying sitemap: {smu}")

        try:
            sm_xml = fetcher.get(smu)
            if sm_xml.status_code >= 400:
                logger.debug(f"Sitemap returned {sm_xml.status_code}: {smu}")
                continue

            pages = re.findall(r"<loc>(.*?)</loc>", sm_xml.text, flags=re.I)
            logger.info(f"Found {len(pages)} pages in sitemap")

            episode_pages = [p for p in pages if any(seg in p.lower() for seg in ("/episode", "/episodes", "/podcast/"))]
            logger.info(f"Found {len(episode_pages)} episode pages")

            for ep_url in episode_pages:
                logger.debug(f"Checking episode page: {ep_url}")

                try:
                    page = fetcher.get(ep_url)
                    urls = _extract_page_audio(page.text, page.url, fetcher)

                    for u in urls:
                        ok = True
                        if hasattr(fetcher, "head_ok"):
                            ok = fetcher.head_ok(u, content_types=("audio/",), min_bytes=1_000_000)

                        if ok:
                            logger.info(f"Valid audio URL found in sitemap: {u}")
                            return u, {"method":"sitemap", "page": page.url, "sitemap": smu}

                except Exception as e:
                    logger.debug(f"Episode page error: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"Sitemap processing error: {str(e)}")
            continue

    logger.info("Sitemap discovery stage found no results")
    return None

def discover_audio_from_homepage(
    home_url: str,
    prefer_title: Optional[str] = None,
    prefer_epnum: Optional[int] = None,
    fetcher = None,
    retry_config: Optional[DiscoveryRetryConfig] = None
) -> Tuple[str, Dict]:
    """
    Discover audio from homepage with multi-stage cascade and retry logic.

    Args:
        home_url: Homepage URL to start discovery
        prefer_title: Preferred episode title to match
        prefer_epnum: Preferred episode number to match
        fetcher: HTTP fetcher instance (defaults to RobustWebFetcher)
        retry_config: Retry configuration (defaults to DiscoveryRetryConfig())

    Returns:
        Tuple of (audio_url, metadata_dict)

    Raises:
        DiscoveryError: If all discovery stages fail after retries
    """
    if fetcher is None:
        from .rwf import RobustWebFetcher
        fetcher = RobustWebFetcher()

    if retry_config is None:
        retry_config = DiscoveryRetryConfig()

    logger.info(f"Starting discovery cascade for: {home_url}")
    logger.info(f"Retry config: cascade={retry_config.max_cascade_retries}, stage={retry_config.max_stage_retries}")

    all_errors = []

    # Cascade-level retry loop
    for cascade_attempt in range(retry_config.max_cascade_retries):
        if cascade_attempt > 0:
            logger.info(f"=== Cascade retry {cascade_attempt + 1}/{retry_config.max_cascade_retries} ===")
            delay = retry_config.retry_delay * (2 ** cascade_attempt if retry_config.exponential_backoff else 1)
            time.sleep(delay)

        try:
            # Fetch homepage
            logger.info("Fetching homepage")
            home = fetcher.get(home_url)
            html = home.text

            # Stage 1: RSS-first with retries
            result = _retry_with_backoff(
                _try_rss_discovery,
                retry_config,
                "RSS discovery",
                html, home.url, prefer_title, prefer_epnum, fetcher
            )
            if result:
                logger.info("✅ Discovery successful via RSS")
                return result

            # Stage 2: Page-scan with retries
            result = _retry_with_backoff(
                _try_page_scan,
                retry_config,
                "Page-scan discovery",
                html, home.url, fetcher
            )
            if result:
                logger.info("✅ Discovery successful via page-scan")
                return result

            # Stage 3: Sitemap with retries
            result = _retry_with_backoff(
                _try_sitemap_discovery,
                retry_config,
                "Sitemap discovery",
                home.url, fetcher
            )
            if result:
                logger.info("✅ Discovery successful via sitemap")
                return result

        except Exception as e:
            error_msg = f"Cascade attempt {cascade_attempt + 1} failed: {str(e)}"
            logger.error(error_msg)
            all_errors.append(error_msg)

    # All retries exhausted
    error_summary = f"Discovery failed after {retry_config.max_cascade_retries} cascade attempts"
    logger.error(error_summary)
    raise DiscoveryError(error_summary, "cascade", all_errors)
