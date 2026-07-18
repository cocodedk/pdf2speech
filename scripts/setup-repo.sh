#!/bin/sh
# Configure branch protection and merge settings for this repository on
# GitHub. Requires the `gh` CLI to be authenticated with sufficient scope.
#
# NOTE: this script is not run automatically - it is intended to be run
# once the first CI run (the "verify" status check) has completed, so that
# the required status check name exists on the repository.
set -eu

REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"
OWNER="$(gh repo view --json owner --jq .owner.login)"
VISIBILITY="$(gh repo view --json visibility --jq .visibility)"

echo "Repository:       $REPO"
echo "Default branch:   $DEFAULT_BRANCH"
echo "Owner:            $OWNER"
echo "Visibility:       $VISIBILITY"
echo

echo "Applying merge settings..."
gh repo edit "$REPO" \
    --delete-branch-on-merge \
    --enable-squash-merge \
    --enable-rebase-merge \
    --enable-merge-commit=false

echo "Applying branch protection to '$DEFAULT_BRANCH'..."

PROTECTION_PAYLOAD=$(cat <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["verify"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "block_creations": false
}
JSON
)

set +e
PROTECTION_OUTPUT=$(printf '%s' "$PROTECTION_PAYLOAD" | gh api \
    --method PUT \
    -H "Accept: application/vnd.github+json" \
    "repos/$REPO/branches/$DEFAULT_BRANCH/protection" \
    --input - 2>&1)
PROTECTION_STATUS=$?
set -e

if [ "$PROTECTION_STATUS" -ne 0 ]; then
    if printf '%s' "$PROTECTION_OUTPUT" | grep -qi "Upgrade to GitHub Pro"; then
        echo
        echo "Skipping branch protection: this repository is private on a" >&2
        echo "GitHub Free plan, which does not support branch protection" >&2
        echo "rules on private repos (\"Upgrade to GitHub Pro\")." >&2
        echo "Falling back to the local .githooks/pre-push hook to enforce" >&2
        echo "owner lock, protected-branch, and verification rules instead." >&2
        exit 0
    fi

    echo "Failed to apply branch protection:" >&2
    echo "$PROTECTION_OUTPUT" >&2
    exit 1
fi

echo "Writing .github/CODEOWNERS..."
mkdir -p .github
printf '* @%s\n' "$OWNER" > .github/CODEOWNERS

echo
echo "Summary of active rules on '$DEFAULT_BRANCH':"
echo "  - Required status checks: verify (strict: must be up to date)"
echo "  - Enforce for admins:      false"
echo "  - Required PR approvals:   0 (dismiss_stale_reviews: false, code owner reviews not required)"
echo "  - Force pushes:            blocked"
echo "  - Branch deletion:         blocked"
echo "  - Linear history required: false"
echo "  - Conversation resolution required: false"
echo "  - Delete branch on merge:  enabled"
echo "  - Squash merge:            enabled"
echo "  - Rebase merge:            enabled"
echo "  - Merge commit:            disabled"
echo "  - CODEOWNERS:              * @$OWNER"
