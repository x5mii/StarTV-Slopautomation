from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura


@dataclass
class ArticleContent:
    url: str
    title: str
    text: str
    image_urls: list[str]


def _normalize_date(date_str: str) -> str:
    cleaned = date_str.strip()
    if not re.fullmatch(r"\d{2}\.\d{2}", cleaned):
        raise ValueError("Date must be DD.MM, e.g. 01.07")
    return cleaned


def _extract_image_urls(html: str, base_url: str) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<img[^>]+src=["\']([^"\']+)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, html, flags=re.IGNORECASE):
            url = urljoin(base_url, match.group(1))
            if url.startswith("data:"):
                continue
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls


def scrape_gala(url: str) -> ArticleContent:
    parsed = urlparse(url)
    if "gala.de" not in parsed.netloc:
        raise ValueError("URL must be a gala.de article")

    with httpx.Client(follow_redirects=True, timeout=60) as client:
        response = client.get(
            url,
            headers={"User-Agent": "StarNewsPipeline/0.1 (+local automation)"},
        )
        response.raise_for_status()
        html = response.text

    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(
        downloaded or html,
        include_comments=False,
        include_tables=False,
        favor_recall=True,
    )
    if not text or len(text.strip()) < 200:
        raise ValueError("Could not extract enough article text from URL")

    metadata = trafilatura.extract_metadata(downloaded or html)
    title = metadata.title if metadata and metadata.title else "Gala Artikel"

    image_urls = _extract_image_urls(html, url)
    return ArticleContent(url=url, title=title, text=text.strip(), image_urls=image_urls[:12])


def download_images(image_urls: list[str], assets_dir: Path) -> list[Path]:
    assets_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        for idx, image_url in enumerate(image_urls, start=1):
            try:
                response = client.get(image_url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            ext = _guess_extension(image_url, response.headers.get("content-type", ""))
            filename = _safe_filename(image_url, idx, ext)
            path = assets_dir / filename
            path.write_bytes(response.content)
            saved.append(path)
    return saved


def _guess_extension(url: str, content_type: str) -> str:
    lowered = content_type.lower()
    if "jpeg" in lowered or "jpg" in lowered:
        return ".jpg"
    if "png" in lowered:
        return ".png"
    if "webp" in lowered:
        return ".webp"
    if "avif" in lowered:
        return ".avif"
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".avif"):
        if path.endswith(ext):
            return ext if ext != ".jpeg" else ".jpg"
    return ".jpg"


def _safe_filename(url: str, index: int, ext: str) -> str:
    base = Path(urlparse(url).path).name
    base = re.sub(r"[^\w.\-]", "_", base)[:80] or f"article_image_{index}"
    if not base.lower().endswith(ext):
        base = f"{base}{ext}"
    return base


def save_article_text(article: ArticleContent, assets_dir: Path) -> Path:
    assets_dir.mkdir(parents=True, exist_ok=True)
    path = assets_dir / "article.txt"
    content = f"URL: {article.url}\nTitle: {article.title}\n\n{article.text}\n"
    path.write_text(content, encoding="utf-8")
    return path
