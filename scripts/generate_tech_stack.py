#!/usr/bin/env python3
"""Update the README tech stack from public GitHub repositories."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import PurePosixPath


README = "README.md"
START = "<!-- tech-stack:start -->"
END = "<!-- tech-stack:end -->"
API = "https://api.github.com"
EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    "target", "coverage", "site-packages",
}

# Shields.io uses Simple Icons slugs. This catalog keeps package names mapped to
# stable, known logo slugs; unknown dependencies are omitted instead of guessed.
PACKAGE_LOGOS = {
    "react": ("React", "react", "61DAFB"),
    "react-dom": ("React", "react", "61DAFB"),
    "next": ("Next.js", "nextdotjs", "000000"),
    "nextjs": ("Next.js", "nextdotjs", "000000"),
    "vue": ("Vue", "vuedotjs", "4FC08D"),
    "vuejs": ("Vue", "vuedotjs", "4FC08D"),
    "angular": ("Angular", "angular", "0F0F11"),
    "svelte": ("Svelte", "svelte", "FF3E00"),
    "express": ("Express", "express", "000000"),
    "fastapi": ("FastAPI", "fastapi", "009688"),
    "django": ("Django", "django", "092E20"),
    "flask": ("Flask", "flask", "000000"),
    "numpy": ("NumPy", "numpy", "013243"),
    "pandas": ("pandas", "pandas", "150458"),
    "scikit-learn": ("scikit-learn", "scikitlearn", "F7931E"),
    "sklearn": ("scikit-learn", "scikitlearn", "F7931E"),
    "tensorflow": ("TensorFlow", "tensorflow", "FF6F00"),
    "torch": ("PyTorch", "pytorch", "EE4C2C"),
    "pytorch": ("PyTorch", "pytorch", "EE4C2C"),
    "keras": ("Keras", "keras", "D00000"),
    "opencv-python": ("OpenCV", "opencv", "5C3EE8"),
    "opencv-python-headless": ("OpenCV", "opencv", "5C3EE8"),
    "tailwindcss": ("Tailwind CSS", "tailwindcss", "06B6D4"),
    "bootstrap": ("Bootstrap", "bootstrap", "7952B3"),
    "vite": ("Vite", "vite", "646CFF"),
    "webpack": ("Webpack", "webpack", "8DD6F9"),
    "prisma": ("Prisma", "prisma", "2D3748"),
    "mongoose": ("Mongoose", "mongoose", "880000"),
    "sqlalchemy": ("SQLAlchemy", "sqlalchemy", "D71F00"),
    "pytest": ("pytest", "pytest", "0A9EDC"),
    "pydantic": ("Pydantic", "pydantic", "E92063"),
    "@aws-sdk/client-bedrock-runtime": ("AWS", "amazonaws", "232F3E"),
    "@aws-sdk/client-s3": ("AWS", "amazonaws", "232F3E"),
    "boto3": ("AWS", "amazonaws", "232F3E"),
    "@google/generative-ai": ("Google AI", "google", "4285F4"),
    "@clerk/nextjs": ("Clerk", "clerk", "6C47FF"),
    "@radix-ui/react-alert-dialog": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-avatar": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-checkbox": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-dialog": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-dropdown-menu": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-label": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-progress": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-radio-group": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-scroll-area": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-select": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-separator": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-slot": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-switch": ("Radix UI", "radixui", "161618"),
    "@radix-ui/react-tabs": ("Radix UI", "radixui", "161618"),
    "@heroicons/react": ("Heroicons", "heroicons", "8B5CF6"),
    "@tailwindcss/forms": ("Tailwind CSS", "tailwindcss", "06B6D4"),
    "@vercel/postgres": ("Vercel", "vercel", "000000"),
    "next-auth": ("Auth.js", "auth0", "000000"),
    "lucide-react": ("Lucide", "lucide", "F56565"),
    "recharts": ("Recharts", "", "22B5BF"),
    "class-variance-authority": ("Class Variance Authority", "", "3B82F6"),
    "clsx": ("clsx", "", "64748B"),
    "zod": ("Zod", "", "3E67B1"),
    "axios": ("Axios", "", "5A29E4"),
    "python-telegram-bot": ("Telegram Bot API", "telegram", "26A5E4"),
    "pyyaml": ("PyYAML", "", "CB171E"),
    "langchain": ("LangChain", "", "1C3C3C"),
    "langchain-community": ("LangChain", "", "1C3C3C"),
    "langchain-qdrant": ("LangChain", "", "1C3C3C"),
    "langchain-openai": ("LangChain", "", "1C3C3C"),
    "langchain-text-splitters": ("LangChain", "", "1C3C3C"),
    "qdrant-client": ("Qdrant", "", "DC244C"),
    "openai": ("OpenAI", "openai", "412991"),
    "pypdf": ("PyPDF", "", "B30B00"),
    "pymupdf4llm": ("PyMuPDF", "", "4B5563"),
    "sentence-transformers": ("Sentence Transformers", "huggingface", "FFD21E"),
    "easyocr": ("EasyOCR", "", "2563EB"),
    "flask-cors": ("Flask", "flask", "000000"),
    "pdf2image": ("PDF2Image", "", "B30B00"),
    "pillow": ("Pillow", "python", "3776AB"),
    "redis": ("Redis", "redis", "FF4438"),
    "lancedb": ("LanceDB", "", "6D28D9"),
    "hdbscan": ("HDBSCAN", "", "2563EB"),
    "pyarrow": ("Apache Arrow", "apachearrow", "CB333B"),
    "python-dotenv": ("python-dotenv", "python", "3776AB"),
    "pydantic-settings": ("Pydantic", "pydantic", "E92063"),
    "requests": ("Requests", "", "2563EB"),
    "dotenv": ("dotenv", "", "64748B"),
    "json5": ("JSON5", "", "F7DF1E"),
    "jszip": ("JSZip", "", "D97706"),
    "tailwind-merge": ("Tailwind Merge", "tailwindcss", "06B6D4"),
    "pdf-lib": ("PDF-lib", "", "B30B00"),
    "zod-mongoose": ("Zod", "", "3E67B1"),
}

LANGUAGE_LOGOS = {
    "python": ("Python", "python", "3776AB"),
    "javascript": ("JavaScript", "javascript", "F7DF1E"),
    "typescript": ("TypeScript", "typescript", "3178C6"),
    "html": ("HTML", "html5", "E34F26"),
    "css": ("CSS", "css3", "1572B6"),
    "java": ("Java", "openjdk", "437291"),
    "c++": ("C++", "cplusplus", "00599C"),
    "c#": ("C#", "csharp", "512BD4"),
    "c": ("C", "c", "A8B9CC"),
    "go": ("Go", "go", "00ADD8"),
    "rust": ("Rust", "rust", "000000"),
    "ruby": ("Ruby", "ruby", "CC342D"),
    "php": ("PHP", "php", "777BB4"),
    "kotlin": ("Kotlin", "kotlin", "7F52FF"),
    "swift": ("Swift", "swift", "F05138"),
    "shell": ("Shell", "gnubash", "4EAA25"),
    "r": ("R", "r", "276DC3"),
}

MANIFEST_NAMES = {
    "package.json", "requirements.txt", "requirements-dev.txt",
    "pyproject.toml", "Pipfile", "Cargo.toml", "go.mod",
    "Gemfile", "composer.json",
}


def request_json(url: str, token: str | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-tech-stack-generator",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def read_raw(url: str) -> str | None:
    request = urllib.request.Request(url, headers={"User-Agent": "profile-tech-stack-generator"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read(512_000).decode("utf-8", errors="replace")
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def normalize_package(name: str) -> str:
    name = re.sub(r"\[.*?\]$", "", name.strip().lower())
    return re.sub(r"[-_.]+", "-", name)


def packages_from_manifest(filename: str, content: str) -> set[str]:
    name = PurePosixPath(filename).name
    packages: set[str] = set()
    try:
        if name == "package.json":
            data = json.loads(content)
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                packages.update(data.get(section, {}).keys())
        elif name.startswith("requirements"):
            for line in content.splitlines():
                line = line.split("#", 1)[0].strip()
                match = re.match(r"([A-Za-z0-9_.-]+)", line)
                if match and not line.startswith(("-", ".", "/")):
                    packages.add(match.group(1))
        elif name == "pyproject.toml":
            data = tomllib.loads(content)
            project = data.get("project", {})
            dependencies = project.get("dependencies", [])
            for entry in dependencies:
                match = re.match(r"([A-Za-z0-9_.-]+)", str(entry))
                if match:
                    packages.add(match.group(1))
            for group in project.get("optional-dependencies", {}).values():
                for entry in group:
                    match = re.match(r"([A-Za-z0-9_.-]+)", str(entry))
                    if match:
                        packages.add(match.group(1))
            for section in (data.get("tool", {}).get("poetry", {}).get("dependencies", {}),):
                packages.update(k for k in section if k.lower() != "python")
        elif name == "Pipfile":
            data = tomllib.loads(content)
            for section in ("packages", "dev-packages"):
                packages.update(data.get(section, {}).keys())
        elif name == "Cargo.toml":
            data = tomllib.loads(content)
            for section in ("dependencies", "dev-dependencies", "build-dependencies"):
                packages.update(data.get(section, {}).keys())
        elif name == "go.mod":
            packages.update(re.findall(r"(?m)^\s*([\w./-]+/[\w./-]+)\s+v[\w.+-]+", content))
        elif name == "Gemfile":
            packages.update(re.findall(r"(?m)^\s*gem\s+['\"]([^'\"]+)", content))
        elif name == "composer.json":
            data = json.loads(content)
            for section in ("require", "require-dev"):
                packages.update(data.get(section, {}).keys())
    except (json.JSONDecodeError, tomllib.TOMLDecodeError, AttributeError, TypeError):
        return set()
    return {normalize_package(p) for p in packages}


def get_repositories(username: str, token: str | None) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        url = f"{API}/users/{urllib.parse.quote(username)}/repos?type=owner&sort=updated&per_page=100&page={page}"
        batch = request_json(url, token)
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def collect(username: str, token: str | None) -> tuple[Counter, Counter]:
    languages: Counter = Counter()
    package_repos: Counter = Counter()
    for repo in get_repositories(username, token):
        if repo.get("fork") or repo.get("archived") or repo.get("name", "").lower() == username.lower():
            continue
        owner = repo["owner"]["login"]
        name = repo["name"]
        branch = urllib.parse.quote(repo.get("default_branch") or "main", safe="")
        api_root = f"{API}/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}"
        try:
            lang_data = request_json(f"{api_root}/languages", token)
            if isinstance(lang_data, dict):
                languages.update({k: int(v) for k, v in lang_data.items()})
            tree = request_json(f"{api_root}/git/trees/{branch}?recursive=1", token)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError):
            continue
        paths = []
        for entry in tree.get("tree", []) if isinstance(tree, dict) else []:
            path = entry.get("path", "")
            filename = PurePosixPath(path).name
            is_requirements = filename.startswith("requirements") and filename.endswith(".txt")
            if entry.get("type") != "blob" or (filename not in MANIFEST_NAMES and not is_requirements):
                continue
            if any(part in EXCLUDED_DIRS for part in PurePosixPath(path).parts):
                continue
            paths.append(path)
        for path in paths[:15]:
            raw_url = (
                f"https://raw.githubusercontent.com/{urllib.parse.quote(owner)}/"
                f"{urllib.parse.quote(name)}/{branch}/{urllib.parse.quote(path, safe='/')}"
            )
            content = read_raw(raw_url)
            if content is not None:
                package_repos.update(packages_from_manifest(path, content))
        time.sleep(0.15)
    languages["Python"] = max(languages["Python"], 1)
    return languages, package_repos


def badge(label: str, logo: str, color: str) -> str:
    label = urllib.parse.quote(label, safe="")
    logo_suffix = f"&logo={urllib.parse.quote(logo)}&logoColor=white" if logo else ""
    url = f"https://img.shields.io/badge/{label}-{color}?style=for-the-badge{logo_suffix}"
    return f"![{label}]({url})"


def render(languages: Counter, package_repos: Counter) -> str:
    # Ignore tiny language fragments, then show up to 12 languages by code volume.
    total = sum(languages.values()) or 1
    selected_languages = [
        name for name, count in languages.most_common()
        if name.casefold() in LANGUAGE_LOGOS
        and (count / total >= 0.01 or name.casefold() == "python")
    ][:12]
    if not any(name.casefold() == "python" for name in selected_languages):
        selected_languages.append("Python")

    badges: list[str] = []
    seen = set()
    for name in selected_languages:
        key = name.casefold()
        label, logo, color = LANGUAGE_LOGOS[key]
        if label.casefold() not in seen:
            badges.append(badge(label, logo, color))
            seen.add(label.casefold())

    selected_packages = [
        key for key, count in package_repos.most_common()
        if key in PACKAGE_LOGOS and count >= 1
    ]
    for key in selected_packages:
        label, logo, color = PACKAGE_LOGOS[key]
        if label.casefold() not in seen:
            badges.append(badge(label, logo, color))
            seen.add(label.casefold())

    # Include other recurring direct dependencies as readable badges too. This
    # avoids silently dropping useful packages just because we lack a logo slug.
    excluded = {"typescript", "eslint", "prettier", "globals", "postcss", "autoprefixer"}
    generic = [
        (key, count) for key, count in package_repos.most_common()
        if key not in PACKAGE_LOGOS and count >= 2
        and not key.startswith("@types/") and key not in excluded
    ][:20]
    for key, _count in generic:
        label = key.rsplit("/", 1)[-1].replace("-", " ").replace("_", " ").title()
        if label.casefold() not in seen:
            badges.append(badge(label, "", "64748B"))
            seen.add(label.casefold())
    return "\n".join(badges)


def update_readme(content: str, generated: str) -> str:
    start_at = content.find(START)
    end_at = content.find(END)
    if start_at < 0 or end_at < 0 or end_at < start_at:
        raise ValueError(f"README must include {START} and {END} markers")
    before = content[: start_at + len(START)]
    after = content[end_at:]
    return f"{before}\n{generated}\n{after}"


def main() -> int:
    username = os.environ.get("GITHUB_USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not username:
        print("Set GITHUB_USERNAME to the GitHub account to scan.", file=sys.stderr)
        return 2
    with open(README, encoding="utf-8") as file:
        original = file.read()
    languages, packages = collect(username, os.environ.get("GITHUB_TOKEN"))
    updated = update_readme(original, render(languages, packages))
    if updated != original:
        with open(README, "w", encoding="utf-8") as file:
            file.write(updated)
    print(f"Updated tech stack from public repositories for {username} (Python is always included).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
