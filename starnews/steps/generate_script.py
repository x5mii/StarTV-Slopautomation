from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from google import genai

from starnews.config import Settings


@dataclass
class ScriptPackage:
    title: str
    caption: str
    hashtags: str
    script: str

    @property
    def hashtags_list(self) -> list[str]:
        return [tag.strip() for tag in re.findall(r"#\S+", self.hashtags)]


def _parse_gemini_output(text: str) -> ScriptPackage:
    sections = {
        "TITLE": "",
        "CAPTION": "",
        "HASHTAGS": "",
        "SCRIPT": "",
    }
    current = None
    for line in text.splitlines():
        header = line.strip().upper().rstrip(":")
        if header in sections:
            current = header
            continue
        if current:
            sections[current] += (line + "\n")

    title = sections["TITLE"].strip()
    caption = sections["CAPTION"].strip()
    hashtags = sections["HASHTAGS"].strip()
    script = sections["SCRIPT"].strip()

    if not all([title, caption, hashtags, script]):
        raise ValueError(
            "Gemini response missing required sections (TITLE, CAPTION, HASHTAGS, SCRIPT)"
        )

    return ScriptPackage(title=title, caption=caption, hashtags=hashtags, script=script)


def generate_script(article_text: str, settings: Settings) -> ScriptPackage:
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set. Add it to ~/.starnews/.env")

    prompt_template = settings.gemini_prompt_file.read_text(encoding="utf-8")
    prompt = f"{prompt_template}\n{article_text}"

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
    )
    text = response.text or ""
    return _parse_gemini_output(text)


def write_script_outputs(package: ScriptPackage, day_dir: Path) -> dict[str, Path]:
    day_dir.mkdir(parents=True, exist_ok=True)

    docx_path = day_dir / "skript.docx"
    doc = Document()
    doc.add_paragraph(package.title)
    doc.add_paragraph(f"Caption:{package.caption} {package.hashtags}")
    doc.add_paragraph(package.script)
    doc.save(docx_path)

    metadata = {
        "title": package.title,
        "caption": package.caption,
        "hashtags": package.hashtags,
        "hashtags_list": package.hashtags_list,
        "script": package.script,
    }
    json_path = day_dir / "metadata.json"
    json_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    txt_path = day_dir / "metadata.txt"
    txt_path.write_text(
        "\n".join(
            [
                f"TITLE: {package.title}",
                "",
                f"CAPTION: {package.caption}",
                "",
                f"HASHTAGS: {package.hashtags}",
                "",
                "SCRIPT:",
                package.script,
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return {"docx": docx_path, "json": json_path, "txt": txt_path}
