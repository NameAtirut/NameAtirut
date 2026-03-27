"""
Fetches publications for Atirut Boribalburephan from Semantic Scholar
and updates the Publications section in README.md between marker comments.
"""

import json
import re
import urllib.request
import urllib.parse
from datetime import datetime

AUTHOR_NAME = "Atirut Boribalburephan"
SEMANTIC_SCHOLAR_AUTHOR_ID = None  # resolved at runtime
README_PATH = "README.md"
START_MARKER = "<!-- PUBLICATIONS:START -->"
END_MARKER = "<!-- PUBLICATIONS:END -->"


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "readme-bot/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def find_author_id(name: str) -> str | None:
    query = urllib.parse.quote(name)
    url = (
        f"https://api.semanticscholar.org/graph/v1/author/search"
        f"?query={query}&fields=name,paperCount"
    )
    data = fetch_json(url)
    for author in data.get("data", []):
        if author.get("name", "").lower() == name.lower():
            return author["authorId"]
    # fallback: first result
    results = data.get("data", [])
    return results[0]["authorId"] if results else None


def fetch_papers(author_id: str) -> list[dict]:
    url = (
        f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
        f"?fields=title,year,venue,externalIds,openAccessPdf,publicationDate"
        f"&limit=10&sort=publicationDate:desc"
    )
    data = fetch_json(url)
    return data.get("data", [])


def paper_to_markdown(paper: dict) -> str:
    title = paper.get("title", "Untitled")
    year = paper.get("year", "")
    venue = paper.get("venue", "")
    ext_ids = paper.get("externalIds", {})
    oa_pdf = paper.get("openAccessPdf") or {}

    # Build links
    links = []
    paper_id = paper.get("paperId", "")
    if paper_id:
        links.append(f"[Semantic Scholar](https://www.semanticscholar.org/paper/{paper_id})")
    if oa_pdf.get("url"):
        links.append(f"[PDF]({oa_pdf['url']})")
    if ext_ids.get("DOI"):
        links.append(f"[DOI](https://doi.org/{ext_ids['DOI']})")
    if ext_ids.get("PubMed"):
        links.append(f"[PubMed](https://pubmed.ncbi.nlm.nih.gov/{ext_ids['PubMed']}/)")

    venue_str = f" · *{venue}*" if venue else ""
    year_str = f", {year}" if year else ""
    link_str = " · " + " · ".join(links) if links else ""

    return f"- **{title}**{venue_str}{year_str}{link_str}"


def build_section(papers: list[dict]) -> str:
    lines = [
        START_MARKER,
        f"<!-- Updated: {datetime.utcnow().strftime('%Y-%m-%d')} via Semantic Scholar -->",
    ]
    if papers:
        for paper in papers:
            lines.append(paper_to_markdown(paper))
    else:
        lines.append("*No papers found — check back later.*")
    lines.append(END_MARKER)
    return "\n".join(lines)


def update_readme(new_section: str) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    if pattern.search(content):
        updated = pattern.sub(new_section, content)
    else:
        raise RuntimeError(
            f"Could not find markers {START_MARKER!r} / {END_MARKER!r} in README.md"
        )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)
    print("README.md updated successfully.")


def main() -> None:
    print(f"Looking up author: {AUTHOR_NAME}")
    author_id = find_author_id(AUTHOR_NAME)
    if not author_id:
        raise RuntimeError("Could not find author on Semantic Scholar.")
    print(f"Author ID: {author_id}")

    papers = fetch_papers(author_id)
    print(f"Found {len(papers)} paper(s).")
    for p in papers:
        print(f"  - {p.get('title')} ({p.get('year')})")

    section = build_section(papers)
    update_readme(section)


if __name__ == "__main__":
    main()
