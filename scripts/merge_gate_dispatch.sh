#!/usr/bin/env bash
# What a dispatched merge gate may judge (.github/workflows/merge-gate.yml). Its check runs land on the dispatched
# branch's head, so: on main without a pull request it judges the project only; on any other branch it needs PR, the
# open pull request into main whose head is exactly this commit, and this branch's gate must be main's, so a branch
# can't bring its own judge. Anything else fails, rather than leaving a skipped (that is, passed) required check.
#
# Environment: PR (may be empty), REF (github.ref), SHA (github.sha), GH_TOKEN, GITHUB_REPOSITORY.
set -euo pipefail

die() { echo "::error::$*" >&2; exit 1; }

if [[ -z "${PR:-}" ]]; then
  [[ "$REF" == refs/heads/main ]] || die "dispatched on $REF without a pull request: name it with -f pr=<number>"
  echo "main without a pull request: the project only."
  exit 0
fi
[[ "$PR" =~ ^[1-9][0-9]*$ ]] || die "pr must be a pull request number, not '$PR'"
[[ "$REF" != refs/heads/main ]] || die "dispatch on the pull request's branch, not main: the checks land on its head"

read -r state base head < <(gh api "repos/$GITHUB_REPOSITORY/pulls/$PR" --jq '"\(.state) \(.base.ref) \(.head.sha)"')
[[ "$state" == open ]] || die "#$PR is $state"
[[ "$base" == main ]] || die "#$PR goes into $base, not main"
[[ "$head" == "$SHA" ]] || die "#$PR's head is ${head:0:8}, but this run is at ${SHA:0:8}: dispatch on its branch"

git fetch --quiet --no-tags origin main
git diff --quiet FETCH_HEAD "$SHA" -- .github/workflows/merge-gate.yml scripts/merge_gate.py scripts/merge_gate.py.lock \
  scripts/merge_gate_dispatch.sh || die "this branch changes the merge gate; only main's gate may judge"
echo "#$PR at ${SHA:0:8}, judged with main's gate."
