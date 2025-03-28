#! /usr/bin/env bash
set -e

# Get the name of the expected venv for this repo from the pyproject.toml file.
venv_name=$(grep -m 1 venv pyproject.toml | tr -s ' ' | tr -d '"' | tr -d "'" | cut -d' ' -f3) || true

# Check if pyrightconfig already exists.
if [[ ! -f pyrightconfig.json ]]; then

	# Capture poetry environment path and check if it's empty.
	poetry_env_info=$(poetry env info --path 2>/dev/null || true)
	if [[ -z ${poetry_env_info} ]]; then
		# Check if pyenv is installed
		if ! command -v pyenv &>/dev/null; then
			echo "pyenv not installed. Please install pyenv..."
			exit 1
		fi

		pyenv_root=$(pyenv root)
		dir_path="${pyenv_root}"/plugins/pyenv-pyright
		if [[ ! -d ${dir_path} ]]; then
			# trunk-ignore(shellcheck/SC2312)
			if [[ -z $(ls -A "${dir_path}") ]]; then
				git clone https://github.com/alefpereira/pyenv-pyright.git "${dir_path}"
			fi
		fi

		# Generate the pyrightconfig.json file.
		pyenv pyright "${venv_name}"
		pyenv local "${venv_name}"
	else
		poetry_env_info=$(poetry env info --path 2>/dev/null || true)
		venv_path=$(dirname "${poetry_env_info}")  # Get directory path
		venv_name=$(basename "${poetry_env_info}") # Get base name

		# Generate the pyrightconfig.json file.
		json_string=$(jq -n \
			--arg v "${venv_name}" \
			--arg vp "${venv_path}" \
			'{venv: $v, venvPath: $vp} ')

		echo "${json_string}" >pyrightconfig.json
	fi
fi

# Check whether required keys are present in pyrightconfig.json.
if ! jq -r --arg venv_name "${venv_name}" '. | select((.venv != $venv_name or .venv == "") and (.venvPath == null or .venvPath == ""))' pyrightconfig.json >/dev/null 2>&1; then
	echo "Failed to configure pyright to use environment '${venv_name}' as interpreter. Please check pyrightconfig.json..."
	exit 1
fi
exit 0
