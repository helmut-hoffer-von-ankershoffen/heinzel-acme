#!/usr/bin/env bash
# Start the required checks (CI OK from CI, merge-gate and coverage-floor from Merge gate) on a release pull request
# the workflow token opened, so it can merge like any other (release.yml runs this).
#
# GitHub holds the pull_request runs of such a pull request for approval and starts no pull_request_target run, so
# nothing would report. Dispatched runs report on the branch's head. The pull request shows only the newest run of each
# workflow, so this waits until the held CI run exists before dispatching CI; otherwise the held run, created a moment
# later, hides the dispatched one (release PR #30, 11-02). Run it again by hand after pushing to the release branch.
#
# Usage: bash scripts/release_checks.sh release/vX.Y.Z   (GH_TOKEN, GITHUB_REPOSITORY; WAIT seconds, default 180)
set -euo pipefail

branch="${1:?usage: release_checks.sh release/vX.Y.Z}"
repo="${GITHUB_REPOSITORY:?}"
wait="${WAIT:-180}"

read -r number head < <(gh pr view "$branch" --repo "$repo" --json number,headRefOid --jq '"\(.number) \(.headRefOid)"')
echo "#$number at ${head:0:8}"

held() {
  gh api "repos/$repo/actions/workflows/ci.yml/runs?head_sha=$head&event=pull_request" --jq .total_count
}
waited=0
until [[ "$(held)" != 0 ]]; do
  if ((waited >= wait)); then
    echo "::warning::no pull_request CI run appeared for ${head:0:8} in ${wait}s; dispatching anyway"
    break
  fi
  sleep 10
  waited=$((waited + 10))
done

gh workflow run ci.yml --repo "$repo" --ref "$branch"
gh workflow run merge-gate.yml --repo "$repo" --ref "$branch" -f pr="$number"
echo "Dispatched CI and Merge gate on $branch for #$number."
