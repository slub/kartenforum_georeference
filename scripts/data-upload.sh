#!/bin/bash
######################################################################
# @author      : nicolas (nicolas.looschen@pikobytes.de)
# @file        : data-upload
# @created     : Mittwoch Mai 04, 2022 09:08:33 CEST
#
# @description : This utility allows to easily access the functionality of the
#                import api from the command line
#
#
# @example-usage: ./data-upload.sh (create|delete|update) [-f path/to/image/file]
#                               [-m path/to/metadata/file] [-b username:password]
#                 https://geo.test.kartenforum.slub-dresden.de/maps/?user_id=example_user
######################################################################

verb="$1"

if [ -z verb ]; then
	echo "The script requires to be called with some parameters."
	exit 1
fi

if [[ "$verb" != "create" ]] && [[ "$verb" != "update" ]] && [[ "$verb" != "delete" ]]; then
	echo "The script only supports the functions create, delete and update."
	exit 1
fi

shift 1

# Handle Create
if [[ "$verb" == "create" ]]; then
	# check for force flag
	while getopts "f:b:m:" o; do
		case "${o}" in
		b)
			echo "Use basic auth."
			b=${OPTARG}
			;;
		f)
			file=${OPTARG}
			;;
		m)
			metadata=${OPTARG}
			;;
		*)
			echo "Usage: $0 create [-b username:password] -f path/to/file -m path/to/metadata import-api.de/maps/?user_id=test_user"
			exit 1
			;;
		esac
	done
	shift "$((OPTIND - 1))"

	upload_url="$1"
	curl_args+=(
		-X POST
		"$upload_url"
		-F "metadata=<$metadata"
		-F "file=@$file"
		-s
		-w "%{http_code}"
		--max-time 1800
	)
elif [[ "$verb" == "update" ]]; then
	while getopts "f:b:m:" o; do
		case "${o}" in
		b)
			echo "Use basic auth."
			b=${OPTARG}
			;;
		f)
			file=${OPTARG}
			;;
		m)
			metadata=${OPTARG}
			;;
		*)
			echo "Usage: $0 update [-b username:password] [-f path/to/file] [-m path/to/metadata] import-api.de/maps/{map_id}?user_id=test_user"
			exit 1
			;;
		esac
	done
	shift "$((OPTIND - 1))"

	upload_url="$1"

	curl_args+=(
		-X POST
		"$upload_url"
		-s
		-w "%{http_code}"
		--max-time 1800
	)

	if [[ (! -f "$file") && (! -f "$metdata") ]]; then
		echo "Either a file or a metadata file is required for an update."
	fi

	if [ -f "$file" ]; then
		curl_args+=(
			-F "file=@$file"
		)
	fi

	if [ -f "$metadata" ]; then
		curl_args+=(
			-F "metadata=<$metadata"
		)
	fi

elif

	[[ "$verb" == "delete" ]]
then
	# check for force flag
	while getopts "b:" o; do
		case "${o}" in
		b)
			echo "Use basic auth."
			b=${OPTARG}
			;;
		*)
			echo "Usage: $0 delete [-b username:password] import-api.de/maps/{map_id}?user_id=test_user"
			exit 1
			;;
		esac
	done
	shift "$((OPTIND - 1))"

	upload_url="$1"

	curl_args+=(
		-X DELETE
		"$upload_url"
		-w "%{http_code}"
	)
fi

# Add basic auth data
if [[ -n $b ]]; then
	curl_args+=(-u $b)
fi

# Make request
res=$(curl "${curl_args[@]}")

# Write response to stdout
echo "$res"
