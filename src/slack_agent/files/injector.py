from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedDocument:
    """Holds parsed text and metadata of a user-uploaded file."""

    file_id: str
    file_name: str
    file_type: str
    text_content: str
    char_count: int


def synthesize_prompt_with_files(
    user_prompt: str,
    documents: list[ExtractedDocument],
    max_chars_per_doc: int = 40000,
) -> str:
    """Prepend extracted document texts to user prompt with clear boundary markers."""
    if not documents:
        return user_prompt

    sections: list[str] = []
    for doc in documents:
        content = doc.text_content
        if doc.char_count > max_chars_per_doc:
            content = (
                f"{content[:max_chars_per_doc]}\n\n"
                f"... [Content truncated due to context limits: "
                f"{max_chars_per_doc} of {doc.char_count} characters shown]"
            )

        header = (
            f"[ATTACHED DOCUMENT: {doc.file_name} "
            f"(Type: {doc.file_type}, Characters: {doc.char_count})]"
        )
        section = (
            f"{header}\n--- START DOCUMENT CONTENT ---\n{content}\n--- END DOCUMENT CONTENT ---"
        )
        sections.append(section)

    documents_block = "\n\n".join(sections)
    return f"{documents_block}\n\nUser Request: {user_prompt}"
