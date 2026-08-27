from pathlib import Path


def load_profile(path: str) -> str:
    """Read my resume as plain text. Supports .pdf (extract text) or .md/.txt."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        # Pull the text layer out of every page and join it.
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return p.read_text()  # .md / .txt fall through to a plain read


def build_prompt(company_url: str, profile_path: str = "my_profile.pdf") -> str:
    my_profile = load_profile(profile_path)
    return (
        f"You are helping ME prepare for an interview at the company at {company_url}.\n\n"
        f"=== MY PROFILE (resume) ===\n{my_profile}\n=== END PROFILE ===\n\n"
        "Do this:\n"
        "1. Research the company (web search + fetch): what they do, industry, size, "
        "tech stack, and the skills they'd want.\n"
        "2. COMPARE their needs against MY profile to decide: which of my projects to "
        "focus on (and why), which of my skills match, and which skills I should brush up.\n"
        "3. Call save_brief EXACTLY ONCE with everything filled. "
        "Use 'N/A' for anything you can't verify — do not guess."
    )
