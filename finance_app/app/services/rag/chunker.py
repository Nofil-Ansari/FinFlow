"""
Semantic chunker preserving Markdown headers, subsection hierarchy, and tables.
"""

import re
from typing import List, Dict, Any, Optional
from .models import KnowledgeDocument, KnowledgeChunk, estimate_token_count


class MarkdownHeaderChunker:
    """Chunks documents along logical markdown headers (## / ###),
    ensuring Markdown tables and key lists are never split mid-block.
    """

    def __init__(self, target_chunk_tokens: int = 450, max_chunk_tokens: int = 750):
        self.target_chunk_tokens = target_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens

    def chunk_document(self, doc: KnowledgeDocument) -> List[KnowledgeChunk]:
        """Split a KnowledgeDocument into granular KnowledgeChunks with contextual titles."""
        chunks: List[KnowledgeChunk] = []

        # Split text into sections based on level-2 headings (## )
        # Keep the delimiter using lookahead
        raw_sections = re.split(r"(?=(?:\r?\n|^)##\s+)", doc.body)

        section_idx = 0
        for sec in raw_sections:
            sec_text = sec.strip()
            if not sec_text:
                continue

            # Extract heading title if present
            header_match = re.match(r"^##\s+(.+)$", sec_text, re.MULTILINE)
            if header_match:
                section_title = header_match.group(1).strip()
            else:
                # Section before any ## (e.g. # Document title and overview)
                h1_match = re.search(r"^#\s+(.+)$", sec_text, re.MULTILINE)
                section_title = h1_match.group(1).strip() if h1_match else doc.title

            combined_title = (
                f"{doc.title} — {section_title}"
                if section_title != doc.title
                else doc.title
            )

            tokens = estimate_token_count(sec_text)

            # If section fits within max chunk limits or is a contiguous table, keep intact
            if tokens <= self.max_chunk_tokens or "|" in sec_text:
                chunk_id = f"{doc.doc_id}_s{section_idx:02d}"
                chunks.append(
                    KnowledgeChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        title=combined_title,
                        content=sec_text,
                        category=doc.category,
                        tags=doc.tags,
                        jurisdiction=doc.jurisdiction,
                        effective_date=doc.effective_date,
                        metadata={
                            **doc.metadata,
                            "section_title": section_title,
                            "source_doc_title": doc.title,
                            "source_url": doc.source_url,
                            "authority": doc.authority,
                        },
                    )
                )
                section_idx += 1
            else:
                # Sub-split on level-3 headings (### )
                sub_sections = re.split(r"(?=(?:\r?\n|^)###\s+)", sec_text)
                sub_idx = 0
                for sub in sub_sections:
                    sub_text = sub.strip()
                    if not sub_text:
                        continue

                    h3_match = re.match(r"^###\s+(.+)$", sub_text, re.MULTILINE)
                    sub_title = (
                        h3_match.group(1).strip() if h3_match else f"Part {sub_idx + 1}"
                    )
                    sub_combined_title = f"{combined_title} ({sub_title})"

                    chunk_id = f"{doc.doc_id}_s{section_idx:02d}_{sub_idx:02d}"
                    chunks.append(
                        KnowledgeChunk(
                            chunk_id=chunk_id,
                            doc_id=doc.doc_id,
                            title=sub_combined_title,
                            content=sub_text,
                            category=doc.category,
                            tags=doc.tags,
                            jurisdiction=doc.jurisdiction,
                            effective_date=doc.effective_date,
                            metadata={
                                **doc.metadata,
                                "section_title": section_title,
                                "subsection_title": sub_title,
                                "source_doc_title": doc.title,
                                "source_url": doc.source_url,
                                "authority": doc.authority,
                            },
                        )
                    )
                    sub_idx += 1
                section_idx += 1

        return chunks
