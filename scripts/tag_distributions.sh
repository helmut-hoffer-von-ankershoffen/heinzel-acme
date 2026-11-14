#!/usr/bin/env bash
# Create the per-distribution lightweight tags `<distribution>/vX.Y.Z` on the release commit, for the root and every
# plugins/<dist> whose pyproject version equals X.Y.Z. Additive: never force, never move a tag. An existing tag on
# the same commit is fine; one on another commit fails. Usage: tag_distributions.sh vX.Y.Z [--dry-run]
set -euo pipefail

tag="${1:?usage: tag_distributions.sh vX.Y.Z [--dry-run]}"
dry="${2:-}"
version="${tag#v}"
sha="$(git rev-parse HEAD)"
status=0
root_tagged=0

field() { # field FILE KEY: first top-level `KEY = "value"` of a pyproject.toml
  sed -n "s/^$2 = \"\\(.*\\)\"\$/\\1/p" "$1" | head -n 1
}

for file in pyproject.toml plugins/*/pyproject.toml; do
  [[ -f "$file" ]] || continue
  [[ "$(field "$file" version)" == "$version" ]] || continue
  name="$(field "$file" name | tr 'A-Z' 'a-z' | sed -E 's/[-_.]+/-/g')" # canonical, as hz looks it up
  [[ -n "$name" ]] || { echo "No name in $file" >&2; status=1; continue; }
  dist_tag="$name/$tag"
  [[ "$file" == pyproject.toml ]] && root_tagged=1
  # ls-remote patterns match trailing path components: compare the exact ref.
  remote="$(git ls-remote --tags origin "refs/tags/$dist_tag" | awk -v r="refs/tags/$dist_tag" '$2 == r {print $1}')"
  if [[ -n "$remote" ]]; then
    # An annotated tag would list its tag object; compare the peeled commit as well.
    peeled="$(git ls-remote --tags origin "refs/tags/$dist_tag^{}" | awk -v r="refs/tags/$dist_tag^{}" '$2 == r {print $1}')"
    if [[ "${peeled:-$remote}" == "$sha" ]]; then
      echo "$dist_tag already on $sha."
      [[ -z "$peeled" ]] || echo "::warning::$dist_tag is annotated; hz reads its tagger date as the release age."
    else
      echo "$dist_tag exists on another commit (${peeled:-$remote}); refusing." >&2
      status=1
    fi
    continue
  fi
  echo "Tagging $dist_tag on $sha."
  if [[ "$dry" != "--dry-run" ]]; then
    git tag "$dist_tag" "$sha"
    git push "https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "refs/tags/$dist_tag"
  fi
done
if [[ "$root_tagged" != 1 ]]; then
  echo "The root pyproject.toml does not have version $version; no root tag." >&2
  status=1
fi
exit "$status"
