#!/bin/bash

# Test script for the update-dependencies workflow using act

set -e

echo "🧪 Testing update-dependencies workflow with act..."

# Check if act is installed
if ! command -v act &>/dev/null; then
	echo "❌ act is not installed. Please install it first:"
	echo "   brew install act"
	exit 1
fi

# Check if test events directory exists
if [[ ! -d "tests/test-deps-update" ]]; then
	echo "❌ tests/test-deps-update directory not found"
	exit 1
fi

echo ""
echo "📋 Available test events:"
echo "1. push-tag.json - Simulates a push tag event"
echo "2. release-published.json - Simulates a release published event"
echo ""

# Function to test workflow with event
test_workflow() {
	local event_file=$1
	local event_name=$2

	echo "🚀 Testing workflow with ${event_name} event..."
	echo "   Event file: ${event_file}"
	echo ""

	# Run act with the event file
	act push \
		--eventpath "tests/test-deps-update/${event_file}" \
		--workflows ".github/workflows/update-dependencies.yml" \
		--dryrun

	echo ""
	echo "✅ Test completed for ${event_name}"
	echo "----------------------------------------"
}

# Test with push tag event
if [[ -f "tests/test-deps-update/push-tag.json" ]]; then
	test_workflow "push-tag.json" "push tag"
else
	echo "❌ push-tag.json not found"
fi

# Test with release published event
if [[ -f "tests/test-deps-update/release-published.json" ]]; then
	test_workflow "release-published.json" "release published"
else
	echo "❌ release-published.json not found"
fi

echo ""
echo "🎉 All tests completed!"
echo ""
echo "💡 To run without --dryrun (actual execution), remove the --dryrun flag"
echo "💡 Note: The workflow will fail when trying to access external repositories"
echo "   as it needs proper GitHub tokens and permissions"
