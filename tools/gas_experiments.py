"""Mesures comparatives de gas pour les questions Q2, Q3, Q4 et Q5 du TP1."""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "contracts" / "MyToken.sol"
FOUNDRY = ROOT / "foundry.toml"
SNAP = ROOT / ".gas-tmp"

# Bloc arithmetique non verifie present dans _transfer
UNCHECKED_BLOCK = """        unchecked {
            balanceOf[from] = bal - amount;
            balanceOf[to] += amount;
        }"""

# Equivalent arithmetique verifie utilise pour la question Q2
CHECKED_BLOCK = """        balanceOf[from] = bal - amount;
        balanceOf[to] += amount;"""

# Controle de solde par erreur custom present dans _transfer et _burn
CUSTOM_ERROR = "        if (bal < amount) revert InsufficientBalance(bal, amount);"

# Equivalent par require et chaine de caracteres utilise pour la question Q3
REQUIRE_STRING = "        require(bal >= amount, 'MyToken: insufficient balance');"


def run_snapshot(label):
    """Execution du test test_Transfer et extraction du gas consomme."""
    result = subprocess.run(
        [
            "forge", "snapshot",
            "--snap", str(SNAP),
            "--match-contract", "MyTokenTest",
            "--match-test", "test_Transfer",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Echec de la mesure pour la variante", label, file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    match = re.search(r"test_Transfer\(\)\s*\(gas:\s*(\d+)\)", SNAP.read_text())

    if match is None:
        print("Aucune valeur de gas trouvee pour la variante", label, file=sys.stderr)
        sys.exit(1)

    return int(match.group(1))

def run_revert_snapshot(label):
    """Mesure du cout sur le chemin de revert pour la question Q3."""
    result = subprocess.run(
        [
            "forge", "snapshot",
            "--snap", str(SNAP),
            "--match-contract", "MyTokenTest",
            "--match-test", "test_RevertIf_InsufficientBalance",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    match = re.search(
        r"test_RevertIf_InsufficientBalance\(\)\s*\(gas:\s*(\d+)\)", SNAP.read_text()
    )

    return int(match.group(1)) if match else None

def run_contract_size():
    """Mesure de la taille du bytecode deploye."""
    result = subprocess.run(
        ["forge", "build", "--sizes"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    match = re.search(r"MyToken\s*\|\s*([\d,]+)", result.stdout)

    return int(match.group(1).replace(",", "")) if match else None

def run_deployment_gas():
    """Extraction du cout de deploiement depuis le rapport de gas Foundry."""
    result = subprocess.run(
        ["forge", "test", "--gas-report", "--match-contract", "MyTokenTest"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    section = result.stdout.split("MyToken Contract", 1)[-1]
    match = re.search(r"Deployment Cost.*\n.*\n\|\s*(\d+)", section)

    return int(match.group(1)) if match else None


def measure_variant(label, replacements):
    """Application temporaire de modifications du contrat puis mesure du gas."""
    original = CONTRACT.read_text()
    patched = original

    for old, new in replacements:
        if old not in patched:
            print("Motif introuvable dans MyToken.sol pour", label, file=sys.stderr)
            sys.exit(1)
        patched = patched.replace(old, new)

    CONTRACT.write_text(patched)
    try:
        return run_snapshot(label)
    finally:
        CONTRACT.write_text(original)


def measure_optimizer(runs):
    """Modification temporaire du nombre de passes de l'optimiseur puis mesure."""
    original = FOUNDRY.read_text()
    patched = re.sub(r"optimizer_runs = \d+", "optimizer_runs = " + str(runs), original)

    FOUNDRY.write_text(patched)
    try:
        return run_snapshot("optimizer_runs=" + str(runs))
    finally:
        FOUNDRY.write_text(original)


def main():
    lines = []

    baseline = run_snapshot("baseline")
    lines.append("Q1 — gas de transfer() (implementation de reference) : " + str(baseline))

    checked = measure_variant("sans unchecked", [(UNCHECKED_BLOCK, CHECKED_BLOCK)])
    lines.append(
        "Q2 — gas de transfer() sans bloc unchecked : "
        + str(checked)
        + "  (ecart : "
        + str(checked - baseline)
        + ")"
    )

    size_baseline = run_contract_size()

    with_require = measure_variant(
        "require avec chaine", [(CUSTOM_ERROR, REQUIRE_STRING)]
    )
    lines.append(
        "Q3 — gas de transfer() (chemin nominal) avec require et chaine : "
        + str(with_require)
        + "  (ecart : "
        + str(with_require - baseline)
        + ")"
    )

    original = CONTRACT.read_text()
    CONTRACT.write_text(original.replace(CUSTOM_ERROR, REQUIRE_STRING))
    try:
        size_require = run_contract_size()
        revert_require = run_revert_snapshot("require avec chaine")
    finally:
        CONTRACT.write_text(original)

    revert_baseline = run_revert_snapshot("baseline")

    lines.append(
        "Q3 — taille du bytecode : erreur custom "
        + str(size_baseline)
        + " octets, require avec chaine "
        + str(size_require)
        + " octets"
    )
    lines.append(
        "Q3 — cout du chemin de revert : erreur custom "
        + str(revert_baseline)
        + ", require avec chaine "
        + str(revert_require)
        + " (test incompatible, erreur attendue differente)"
    )

    deployment = run_deployment_gas()
    lines.append("Q4 — gas du constructeur : " + str(deployment))

    for runs in (1, 200, 1000):
        value = measure_optimizer(runs)
        lines.append(
            "Q5 — gas de transfer() avec optimizer_runs=" + str(runs) + " : " + str(value)
        )

    if SNAP.exists():
        SNAP.unlink()

    report = "\n".join(lines)
    print(report)
    (ROOT / "gas-analysis.txt").write_text(report + "\n")


if __name__ == "__main__":
    main()
