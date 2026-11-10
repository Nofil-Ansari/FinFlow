"""
Document loader supporting Markdown frontmatter and structured JSON documents.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
from .models import KnowledgeDocument


def parse_markdown_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """Parse YAML-style frontmatter enclosed in --- at the start of a markdown file."""
    metadata: Dict[str, Any] = {}
    body = content

    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        yaml_text = match.group(1)
        body = match.group(2).strip()

        # Simple robust line-by-line key-value parser (no mandatory PyYAML dep)
        for line in yaml_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()

                # Parse JSON-like arrays: tags: ["a", "b"]
                if val.startswith("[") and val.endswith("]"):
                    try:
                        parsed_val = json.loads(val)
                    except Exception:
                        items = [x.strip().strip("'\"") for x in val[1:-1].split(",") if x.strip()]
                        parsed_val = items
                    metadata[key] = parsed_val
                # Remove surrounding quotes
                elif (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    metadata[key] = val[1:-1]
                else:
                    metadata[key] = val

    return metadata, body


class DocumentLoader:
    """Loads and normalizes raw documents into KnowledgeDocument instances."""

    @classmethod
    def load_markdown_file(cls, filepath: str) -> KnowledgeDocument:
        """Load a single markdown file with optional frontmatter."""
        path = Path(filepath)
        doc_id = path.stem

        with open(path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        meta, body = parse_markdown_frontmatter(raw_text)

        # Fallback to first heading if title missing
        title = meta.get("title")
        if not title:
            h1_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = h1_match.group(1).strip() if h1_match else doc_id.replace("_", " ").title()

        return KnowledgeDocument(
            doc_id=doc_id,
            title=title,
            category=meta.get("category", "General"),
            body=body,
            source_url=meta.get("source_url"),
            jurisdiction=meta.get("jurisdiction", "Pakistan"),
            authority=meta.get("authority"),
            effective_date=meta.get("effective_date"),
            tags=meta.get("tags", []),
            metadata={k: v for k, v in meta.items() if k not in [
                "title", "category", "source_url", "jurisdiction", "authority", "effective_date", "tags"
            ]}
        )

    @classmethod
    def load_substitutions_json(cls, filepath: str) -> List[KnowledgeDocument]:
        """Convert structured substitutions JSON into modular KnowledgeDocuments."""
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        docs: List[KnowledgeDocument] = []
        jurisdiction = data.get("jurisdiction", "Pakistan")
        currency = data.get("currency", "PKR")

        for category_info in data.get("categories", []):
            cat_name = category_info.get("category_name", "Substitutions")
            cat_slug = cat_name.lower().replace(" ", "_").replace("&", "and")

            lines = [
                f"# Pakistani Market Consumer Substitutions: {cat_name}",
                f"**Jurisdiction**: {jurisdiction} | **Currency**: {currency}",
                "",
                "Verified cheaper alternatives and domestic product replacements:",
                ""
            ]

            all_keywords = []

            for item in category_info.get("substitutions", []):
                brand = item.get("original_brand", "Unknown")
                kws = item.get("match_keywords", [])
                all_keywords.extend(kws)

                lines.append(f"## Target Brand: {brand}")
                lines.append(f"**Identified Keywords**: {', '.join(kws)}")
                lines.append("")
                lines.append("| Cheaper Alternative | Type | Pricing Model | Estimated Savings | Rationale |")
                lines.append("|---|---|---|---|---|")

                for alt in item.get("recommended_alternatives", []):
                    name = alt.get("name", "")
                    atype = alt.get("type", "")
                    price = alt.get("price_model", "")
                    pct = f"{alt.get('estimated_saving_pct', 0)}%"
                    rat = alt.get("saving_rationale", "")
                    lines.append(f"| {name} | {atype} | {price} | {pct} | {rat} |")
                lines.append("")

            body = "\n".join(lines)
            doc_id = f"substitutions_{cat_slug}"
            docs.append(
                KnowledgeDocument(
                    doc_id=doc_id,
                    title=f"Consumer Substitutions — {cat_name}",
                    category="Consumer Substitutions",
                    body=body,
                    jurisdiction=jurisdiction,
                    tags=["substitutions", "saving", "pakistan"] + list(set(all_keywords))[:10],
                    metadata={"category_type": cat_name, "currency": currency}
                )
            )

        return docs

    @classmethod
    def load_directory(cls, dirpath: str) -> List[KnowledgeDocument]:
        """Load all markdown and JSON documents from a directory."""
        dir_p = Path(dirpath)
        if not dir_p.exists():
            return []

        documents: List[KnowledgeDocument] = []
        for file in sorted(dir_p.glob("*")):
            if file.suffix.lower() == ".md":
                documents.append(cls.load_markdown_file(str(file)))
            elif file.suffix.lower() == ".json" and "substitution" in file.stem.lower():
                documents.extend(cls.load_substitutions_json(str(file)))

        return documents

