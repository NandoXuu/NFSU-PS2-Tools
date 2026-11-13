from pathlib import Path
import subprocess
import shutil

HOME = Path.home()
DEST = HOME / "NFSU-PS2-Tools"

SOURCES = {
    "NFS.BIN.Tool": HOME / "NFS.BIN.Tool",
    "EA-Compression": HOME / "EAC-NFS",
}

ALLOWED = {
    ".cs", ".csproj", ".sln", ".md", ".json", ".config",
    ".list", ".py", ".sh", ".txt", ".xml", ".props",
    ".targets", ".gitattributes", ".gitignore", ".c",
    ".h", ".cpp", ".hpp", ".java", ".bat"
}

EXCLUDED_DIRS = {
    ".git", "bin", "obj", ".vs", "__pycache__",
    "build", "Debug", "Release", "termux"
}

def tracked_and_untracked(repo):
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-co",
         "--exclude-standard", "-z"],
        capture_output=True, check=True
    )
    return [
        x.decode() for x in result.stdout.split(b"\0") if x
    ]

if DEST.exists():
    raise SystemExit(
        f"A pasta {DEST} já existe. Não vou sobrescrevê-la."
    )

DEST.mkdir(parents=True)

for project, repo in SOURCES.items():
    if not repo.is_dir():
        print(f"[AVISO] Não encontrado: {repo}")
        continue

    output = DEST / project
    copied = 0

    for rel in tracked_and_untracked(repo):
        src = repo / rel
        parts = Path(rel).parts

        if not src.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in parts):
            continue

        name = src.name.lower()
        if any(tag in name for tag in (
            ".bak", ".backup", ".before_", ".pretermux",
            ".arm64.bak", ".~1~", ".~2~"
        )):
            continue

        if src.suffix.lower() not in ALLOWED and name not in (
            "license", "license.txt", "copying"
        ):
            continue

        target = output / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        copied += 1

    print(f"[OK] {project}: {copied} arquivos copiados")

# Scripts próprios usados nas pesquisas
scripts = [
    "scan_nfs.py",
    "scan_tpk.py",
    "test_eac_tpk.py",
    "test_eac_all.py",
]

script_dir = DEST / "Scripts"
script_dir.mkdir(exist_ok=True)

for name in scripts:
    src = HOME / name
    if src.is_file():
        shutil.copy2(src, script_dir / name)
        print(f"[OK] Script: {name}")

(DEST / "UPSTREAMS.md").write_text(
"""# Projetos de origem

Este repositório reúne modificações e ferramentas auxiliares
para pesquisa dos formatos de Need for Speed Underground (PS2).

## Projetos originais

- NFS.BIN.Tool: https://github.com/Ekey/NFS.BIN.Tool
- EAC: https://github.com/RayneDuarte/EAC

Os códigos originais permanecem atribuídos aos seus respectivos
autores. Consulte as licenças originais em cada projeto.
""",
encoding="utf-8"
)

(DEST / ".gitignore").write_text(
"""bin/
obj/
.vs/
__pycache__/
*.pyc
*.so
*.dll
*.exe
*.o
*.obj
*.a
*.pdb
*.cache
""",
encoding="utf-8"
)

(DEST / "README.md").write_text(
"""# NFSU-PS2-Tools

Ferramentas e pesquisas para extração e análise dos formatos
de Need for Speed Underground para PlayStation 2.

## Componentes

- NFS.BIN.Tool: versão adaptada para Termux/.NET 8,
  com suporte a extração TPK.
- EA-Compression: código-fonte e adaptações para ARM64/Termux.
- Scripts: ferramentas Python de inspeção e testes.

## Plataformas

- Android / Termux / ARM64
- .NET 8
- Python 3
- Clang

## Créditos e licenças

Consulte UPSTREAMS.md e as licenças dos projetos originais.
""",
encoding="utf-8"
)

print("\nProjeto preparado em:", DEST)
