import argparse
import re
import sys
from pathlib import Path

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "so", "of", "to",
    "in", "on", "at", "for", "with", "as", "by", "from", "is", "are", "was",
    "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    "will", "would", "should", "could", "can", "may", "might", "must",
    "this", "that", "these", "those", "it", "its", "we", "you", "your",
    "our", "their", "they", "he", "she", "his", "her", "not", "no", "yes",
    "about", "into", "than", "which", "who", "whom", "what", "when",
    "where", "how", "all", "any", "each", "other", "such", "only", "own",
    "same", "so", "too", "very", "just", "up", "down", "out", "over",
    "under", "again", "further", "once", "here", "there", "both", "few",
    "more", "most", "some", "s", "t",
}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return path.read_text(errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            sys.exit(
                f"Cannot read {path}: PDF support requires 'pypdf'. "
                "Install it with: pip install pypdf"
            )
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    sys.exit(f"Unsupported file type: {path} (expected .txt or .pdf)")


def extract_keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#]*", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOPWORDS}


def score_resume(jd_keywords: set[str], resume_text: str) -> tuple[float, set[str], set[str]]:
    resume_words = extract_keywords(resume_text)
    matched = jd_keywords & resume_words
    missing = jd_keywords - resume_words
    score = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 0.0
    return score, matched, missing


def collect_resume_files(paths: list[str]) -> list[Path]:
    files = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.glob("*.txt")) + sorted(path.glob("*.pdf")))
        else:
            files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(
        description="Score resumes against a job description by keyword overlap."
    )
    parser.add_argument("jd", help="Path to the job description (.txt or .pdf)")
    parser.add_argument(
        "resumes",
        nargs="+",
        help="Resume file(s) and/or director(y/ies) containing resumes",
    )
    args = parser.parse_args()

    jd_text = extract_text(Path(args.jd))
    jd_keywords = extract_keywords(jd_text)
    if not jd_keywords:
        sys.exit("No keywords could be extracted from the job description.")

    resume_files = collect_resume_files(args.resumes)
    if not resume_files:
        sys.exit("No resume files found.")

    results = []
    for path in resume_files:
        text = extract_text(path)
        score, matched, missing = score_resume(jd_keywords, text)
        results.append((path.name, score, matched, missing))

    results.sort(key=lambda r: r[1], reverse=True)

    print(f"\nJD keywords ({len(jd_keywords)}): {', '.join(sorted(jd_keywords))}\n")
    print(f"{'Rank':<5}{'Resume':<40}{'Score':>8}")
    print("-" * 55)
    for rank, (name, score, _, _) in enumerate(results, start=1):
        print(f"{rank:<5}{name:<40}{score:>7.1f}%")

    print("\nDetails:\n")
    for name, score, matched, missing in results:
        print(f"{name} — {score:.1f}%")
        print(f"  Matched ({len(matched)}): {', '.join(sorted(matched))}")
        print(f"  Missing ({len(missing)}): {', '.join(sorted(missing))}\n")


if __name__ == "__main__":
    main()
