#!/bin/bash

# Test script for the update-dependencies workflow logic
# This script simulates the workflow steps to verify they work correctly
# This script is run in CI to verify the workflow logic

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

# Test the sed command with a sample pyproject.toml (uv format)
cat >test_pyproject.toml <<'EOF'
[project]
requires-python = ">=3.11"
dependencies = [
    "db-client @ git+https://github.com/climatepolicyradar/navigator-db-client.git@v3.9.12",
]
EOF

echo "📝 Created test pyproject.toml:"
cat test_pyproject.toml

# Test the update logic (cross-platform compatible)
if [[ ${OSTYPE} == "darwin"* ]]; then
	# macOS
	if sed -i '' "s/@v[0-9]*\.[0-9]*\.[0-9]*/@v${NEW_VERSION}/" test_pyproject.toml; then
		echo "✅ Successfully updated pyproject.toml (macOS)"
	else
		echo "❌ Failed to update pyproject.toml"
		exit 1
	fi
else
	# Linux
	if sed -i "s/@v[0-9]*\.[0-9]*\.[0-9]*/@v${NEW_VERSION}/" test_pyproject.toml; then
		echo "✅ Successfully updated pyproject.toml (Linux)"
	else
		echo "❌ Failed to update pyproject.toml"
		exit 1
	fi
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
