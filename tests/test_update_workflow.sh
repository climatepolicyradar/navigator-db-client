#!/bin/bash

# Test script for the update-dependencies workflow logic
# This script simulates the workflow steps to verify they work correctly

set -e

echo "🧪 Testing update-dependencies workflow logic..."

# Simulate a release tag
GITHUB_REF="refs/tags/v3.9.14"

# Extract version from release tag (remove 'v' prefix)
NEW_VERSION="${GITHUB_REF#refs/tags/}"
NEW_VERSION="${NEW_VERSION#v}"

echo "🔄 Testing version extraction: ${NEW_VERSION}"

# Validate release tag
if [[ ! ${GITHUB_REF} =~ ^refs/tags/v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
	echo "❌ Invalid release tag format: ${GITHUB_REF}"
	echo "Expected format: refs/tags/vX.Y.Z"
	exit 1
fi
echo "✅ Valid release tag: ${GITHUB_REF}"

# Test the sed command with a sample pyproject.toml
cat >test_pyproject.toml <<'EOF'
[tool.poetry.dependencies]
python = "^3.11"
db-client = { git = "https://github.com/climatepolicyradar/navigator-db-client.git", tag = "v3.9.12" }
EOF

echo "📝 Created test pyproject.toml:"
cat test_pyproject.toml

# Test the update logic (macOS compatible)
if sed -i '' "s/tag = \"v[0-9]*\.[0-9]*\.[0-9]*\"/tag = \"v${NEW_VERSION}\"/" test_pyproject.toml; then
	echo "✅ Successfully updated pyproject.toml"
else
	echo "❌ Failed to update pyproject.toml"
	exit 1
fi

echo "📝 Updated pyproject.toml:"
cat test_pyproject.toml

# Test branch name generation
BRANCH_NAME="bump-db-client-to-v${GITHUB_REF#refs/tags/}"
echo "🌿 Generated branch name: ${BRANCH_NAME}"

# Test PR title generation
PR_TITLE="🔧 Bump db-client to ${GITHUB_REF#refs/tags/}"
echo "📋 Generated PR title: ${PR_TITLE}"

# Cleanup
rm -f test_pyproject.toml

echo "✅ All tests passed!"
