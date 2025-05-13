
import datetime
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

from src.server import CrawlerMetadata

def extract_section_info(chunk: str) -> Dict[str, Any]:
    """
    Extracts headers and stats from a chunk.
    
    Args:
        chunk: Markdown chunk
        
    Returns:
        Dictionary with headers and stats
    """
    headers = re.findall(r'^(#+)\s+(.+)$', chunk, re.MULTILINE)
    header_str = '; '.join([f'{h[0]} {h[1]}' for h in headers]) if headers else ''

    return {
        "headers": header_str,
        "char_count": len(chunk),
        "word_count": len(chunk.split())
    }


def smart_chunk_markdown(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = end

    return chunks

def enrich_chunks_with_metadata(
    chunks: List[str],
    source_url: str,
    tool_name: str,
    local_file_path: str = None,
    file_name_from_url: str = None
) -> List[Dict[str, Any]]:
    """
    Enriches chunks with metadata for storage.
    """

    urls_db, chunk_numbers, contents, metadatas = [], [], [], []
    for i, chunk in enumerate(chunks):
        urls_db.append(source_url)
        chunk_numbers.append(i)
        contents.append(chunk)
        section_info = extract_section_info(chunk)
        meta = CrawlerMetadata(
            chunk_index=i,
            url=source_url,
            source_domain=urlparse(source_url).netloc,
            crawled_at=datetime.datetime.now(datetime.timezone.utc),
            crawler_tool=tool_name,
            document_title=section_info.get("title") or file_name_from_url,
            document_description=section_info.get("description"),
            document_keywords=section_info.get("keywords"),
            content_headings=section_info.get("headings"),
            file_name=file_name_from_url,
            file_path_in_source=urlparse(source_url).path,
            additional_info=(
                {"local_file_path": local_file_path} if local_file_path else None
            ),
        )
        metadatas.append(meta.to_dict())
    return urls_db, chunk_numbers, contents, metadatas