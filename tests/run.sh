#!/usr/bin/env bash
# Lance les tests hors ligne, exactement comme la CI GitHub.
#
#   ./tests/run.sh
#
# pillow et numpy ne sont nécessaires que pour quelques tests de vignettes : la CI
# les installe, en local on se contente d'un avertissement.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if ! python3 -c "import PIL, numpy" 2>/dev/null; then
    echo "note : pillow/numpy absents, certains tests peuvent être ignorés (la CI les installe)." >&2
fi

exec python3 -m unittest discover -s tests -v
