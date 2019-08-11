#!/usr/bin/env bash

# Regex Hosts Installer for Pi-hole
# Based on https://github.com/mmotti/pihole-regex/blob/master/install.sh

for i in "$@"; do
# Set variables
remote_list_name=$(basename "$i" | cut -f 1 -d '.')
db_gravity='/etc/pihole/gravity.db'
file_pihole_regex='/etc/pihole/regex.list'
file_list_regex=/etc/pihole/$remote_list_name.list
file_list_remote_regex=$i
installer_comment='github.com/PolishFiltersTeam/ScriptsPlayground'

# Determine whether we are using Pi-hole DB
if [[ -s "${db_gravity}" ]]; then
	usingDB=true
fi

# Functions
function fetchResults {

	local selection="${1}" action="${2}" queryStr

	# Select * if not set
	[[ -z "${selection}" ]] && selection='*'

	# Determine course of action
	case "${action}" in
		migrated_regexps ) queryStr="Select ${selection} FROM regex WHERE comment='${installer_comment}'";;
		user_created     ) queryStr="Select ${selection} FROM regex WHERE comment IS NULL OR comment!='${installer_comment}'";;
		current_id       ) queryStr="Select ${selection} FROM regex ORDER BY id DESC LIMIT 1";;
		*                ) queryStr="Select ${selection} FROM regex";;
	esac

	# Execute SQL query
	sqlite3 ${db_gravity} "${queryStr}" 2>&1

	# Check exit status
	status="$?"
	if [[ $LANG == *"pl"* ]];
	then
		error_fetching="Wystąpił błąd podczas pobierania wyników"
	else
		error_fetching="An error occured whilst fetching results"
	fi
	[[ "${status}" -ne 0 ]]  && { (>&2 echo "[i] $error_fetching"); return 1; }

	return 0
}

function updateDB() {

	local inputData="${1}" action="${2}" queryStr

	# Determine course of action
	case "${action}" in
		remove_pre_migrated ) queryStr="DELETE FROM regex WHERE domain in (${inputData})";;
		remove_migrated     ) queryStr="DELETE FROM regex WHERE comment = '${installer_comment}'";;
		*                   ) return ;;
	esac

	# Execute SQL query
	sudo sqlite3 ${db_gravity} "${queryStr}"

	# Check exit status
	status="$?"
	if [[ $LANG == *"pl"* ]];
	then
		error_updating="Wystąpił błąd podczas aktualizowania bazy danych"
	else
		error_updating="An error occured whilst updating database"
	fi
	[[ "${status}" -ne 0 ]]  && { (>&2 echo "[i] $error_updating"); return 1; }

	return 0
}

function generateCSV() {

	# Exit if there is a problem with the remoteRegex string
	[[ -z "${1}" ]] && exit 1

	local remoteRegex timestamp queryArr file_csv_tmp

	# Set local variables
	remoteRegex="${1}"
	timestamp="$(date --utc +'%s')"
	file_csv_tmp="$(mktemp -p "/tmp" --suffix=".csv")"
	iteration="$(fetchResults "id" "current_id")"

	# At this point we need to double check that there wasn't an error (rather than no result) when trying to
	# retrieve the current iteration.
	status="$?"
	[[ "${status}" -ne 0 ]] && return 1

	# Create array to hold import string
	declare -a queryArr

	# Start of processing
	# If we got the id of the last item in the regex table, iterate once
	# Otherwise set the iterator to 1
	[[ -n "${iteration}" ]] && ((iteration++)) || iteration=1

	# Iterate through the remote regexps
	# So long as the line is not empty, generate the CSV values
	while read -r regexp; do
		if [[ -n "${regexp}" ]]; then
			queryArr+=("${iteration},\"${regexp}\",1,${timestamp},${timestamp},\"${installer_comment}\"")
			((iteration++))
		fi
	done <<< "${remoteRegex}"

	# If our array is populated then output the results to a temporary file
	if [[ "${#queryArr[@]}" -gt 0 ]]; then
		printf '%s\n' "${queryArr[@]}" > "${file_csv_tmp}"
	else
		return 1
	fi

	# Output the CSV path
	echo "${file_csv_tmp}"

	return 0
}

if [[ $LANG == *"pl"* ]];
then
	download_regexp_from_remote="Pobieranie wyrażeń regularnych z listy $remote_list_name"
else
	download_regexp_from_remote="Fetching $remote_list_name's regexps"
fi
echo "[i] $download_regexp_from_remote"

# Fetch the remote regex file and remove comment lines
list_remote_regex=$(wget -qO - "${file_list_remote_regex}" | grep '^[^#]')

# Conditional exit if empty
if [[ $LANG == *"pl"* ]];
then
	download_fail="Nie udało się pobrać listy wyrażeń regularnych $remote_list_name"
else
	download_fail="Failed to download $remote_list_name regex list"
fi

[[ -z "${list_remote_regex}" ]] && { echo "[i] $download_fail"; exit 1; }
if [[ $LANG == *"pl"* ]];
then
	fetching_existing="Pobieranie istniejących wyrażeń regularnych"
else
	fetching_existing="Fetching existing regexps"
fi
echo "[i] $fetching_existing"

# Conditionally fetch existing regexps depending on
# whether the user has migrated to the Pi-hole DB or not
if [[ "${usingDB}" == true ]]; then
	str_regex=$(fetchResults "domain")
else
	str_regex=$(grep '^[^#]' < "${file_pihole_regex}")
fi

# Starting the install process
# If we're using the Pi-hole DB
if [[ "${usingDB}" == true ]]; then
	# If we found regexps in the database
	if [[ -n "${str_regex}" ]] ; then
		if [[ $LANG == *"pl"* ]];
		then
			prev_m_check="Sprawdzanie poprzedniej migracji"
		else
			prev_m_check="Checking for previous migration"
		fi
		echo "[i] $prev_m_check"
		# Check whether this script has previously migrated our regexps
		db_migrated_regexps=$(fetchResults "domain" "migrated_regexps")
		# If migration is detected
		if [[ -n "${db_migrated_regexps}" ]]; then
			if [[ $LANG == *"pl"* ]];
			then
				prev_m_detect="Wykryto poprzednią migrację"
			else
				prev_m_detect="Previous migration detected"
			fi
			echo "[i] $prev_m_detect"
			# As we have already migrated the user, we need to check
			# whether the regexps in the database are up-to-date
			if [[ $LANG == *"pl"* ]];
			then
				if_updates_required="Sprawdzanie, czy aktualizacje są wymagane"
			else
				if_updates_required="Checking whether updates are required"
			fi
			echo "[i] $if_updates_required"
			# Use comm -3 to suppress lines that appear in both files
			# If there are any results returned, this will quickly tell us
			# that there are discrepancies
			updatesRequired=$(comm -3 <(sort <<< "${db_migrated_regexps}") <(sort <<< "${list_remote_regex}"))
			# Conditional exit if no updates are required
			if [[ $LANG == *"pl"* ]];
			then
				local_uptodate="Lokalna lista wyrażeń aktualna jest już aktualna"
			else
				local_uptodate="Local regex filter is already up-to-date"
			fi
			[[ -z "${updatesRequired}" ]] && { echo "[i] $local_uptodate"; exit 0; }
			# Now we know that updates are required, it's easiest to start a fresh
			if [[ $LANG == *"pl"* ]];
			then
				run_removal_query="Uruchamianie kwerendy usuwającej"
			else
				run_removal_query="Running removal query"
			fi
			echo "[i] $run_removal_query"
			# Clear our previously migrated domains from the regex table
			updateDB "" "remove_migrated"
		else
			if [[ $LANG == *"pl"* ]];
			then
				no_prev_m="Nie wykryto poprzedniej migracji"
			else
				no_prev_m="No previous migration detected"
			fi
			echo "[i] $no_prev_m"
			# As we haven't yet migrated, we need to manually remove matches
			# If we have a local list-regex.list, read from that as it was used on the last install (pre-db)
			# Otherwise, default to the latest remote copy
			if [[ -s "${file_list_regex}" ]]; then
				# Only return regexps in both the regex table and regex file
				mapfile -t result <<< "$(comm -12 <(sort <<< "${str_regex}") <(sort < "${file_list_regex}"))"

			else
				# Only return regexps in both the regex table and regex file
				mapfile -t result <<< "$(comm -12 <(sort <<< "${str_regex}") <(sort <<< "${list_remote_regex}"))"
			fi
			# If we have matches in both the regex table and regex file
			if [[ -n "${result[*]}" ]]; then
				if [[ $LANG == *"pl"* ]];
				then
					forming_rm="Tworzenie ciągu usuwającego"
				else
					forming_rm="Forming removal string"
				fi
				echo "[i] $forming_rm"
				# regexstring --> 'regexstring1','regexstring2',
				# Then remove the trailing comma
				removalStr=$(printf "'%s'," "${result[@]}" | sed 's/,$//')
				# If our removal string is not empty (sanity check)
				if [[ -n "${removalStr}" ]]; then
					if [[ $LANG == *"pl"* ]];
					then
						run_removal_query="Uruchamianie kwerendy usuwającej"
					else
						run_removal_query="Running removal query"
					fi
					echo "[i] $run_removal_query"
					# Remove regexps from the regex table if there are in the
					# removal string
					updateDB "${removalStr}" "remove_pre_migrated"
				fi
			fi
		fi
	else
		if [[ $LANG == *"pl"* ]];
		then
			no_regex_in_db="W bazie danych nie ma obecnie wyrażeń regularnych"
		else
			no_regex_in_db="No regexps currently exist in the database"
		fi
		echo "[i] $no_regex_in_db"
	fi

	# Create our CSV
	if [[ $LANG == *"pl"* ]];
	then
		gen_csv="Generowanie pliku CSV"
	else
		gen_csv="Generating CSV file"
	fi
	echo "[i] $gen_csv"
	csv_file=$(generateCSV "${list_remote_regex}")

	# Conditional exit
	if [[ $LANG == *"pl"* ]];
	then
		csv_empty="Błąd: Wygenerowany plik CSV jest pusty"
	else
		csv_empty="Error: Generated CSV is empty"
	fi

	if [[ -z "${csv_file}" ]] || [[ ! -s "${csv_file}" ]]; then
		echo "[i] $csv_empty"; exit 1;
	fi

	# Construct correct input format for import
	if [[ $LANG == *"pl"* ]];
	then
		import_csv="Importowanie pliku CSV do bazy danych"
	else
		import_csv="Importing CSV to DB"
	fi
	echo "[i] $import_csv"
	printf ".mode csv\\n.import \"%s\" %s\\n" "${csv_file}" "regex" | sudo sqlite3 "${db_gravity}" 2>&1

	# Check exit status
	status="$?"
	if [[ $LANG == *"pl"* ]];
	then
		error_import_csv="Wystąpił błąd poczas importowania pliku CSV do bazy danych"
	else
		error_import_csv="An error occured whilst importing the CSV into the database"
	fi
	[[ "${status}" -ne 0 ]]  && { echo "[i] $error_import_csv"; exit 1; }

	# Status update
	if [[ $LANG == *"pl"* ]];
	then
		import_complete="Zakończono importowanie wyrażeń regularnych"
	else
		import_complete="Regex import complete"
	fi
	echo "[i] $import_complete"

	# Remove the old list-regex file
	[[ -e "${file_list_regex}" ]] && sudo rm -f "${file_list_regex}"

else
	if [[ $LANG == *"pl"* ]];
	then
		remove_from_prev="Usuwanie $remote_list_name.list z poprzedniej instalacji"
	else
		remove_from_prev="Removing $remote_list_name.list from a previous install"
	fi

	if [[ -n "${str_regex}" ]]; then
		# Restore config prior to previous install
		# Keep entries only unique to pihole regex
		if [[ -s "${file_list_regex}" ]]; then
			echo "[i] $remove_from_prev"
			comm -23 <(sort <<< "${str_regex}") <(sort "${file_list_regex}") | sudo tee $file_pihole_regex > /dev/null
			sudo rm -f "${file_list_regex}"
		else
			# In the event that file_list_regex is not available
			# Match against the latest remote list instead
			echo "[i] $remove_from_prev"
			comm -23 <(sort <<< "${str_regex}") <(sort <<< "${list_remote_regex}") | sudo tee $file_pihole_regex > /dev/null
		fi
	fi

	# Copy latest regex list to file_list_regex dir
	if [[ $LANG == *"pl"* ]];
	then
		copying_remote="Kopiowanie zdalnej listy $remote_list_name do ${file_list_regex}"
	else
		copying_remote="Copying remote $remote_list_name list to ${file_list_regex}"
	fi
	echo "[i] $copying_remote"
	echo "${list_remote_regex}" | sudo tee "${file_list_regex}" > /dev/null

	# Status update
	number_of_remote_regexps=$(wc -l <<< "${list_remote_regex}")

	if [[ $LANG == *"pl"* ]];
	then
		if [ "$number_of_remote_regexps" -eq 1 ];
		then
			remote_regexp="wyrażenie regularne"
		elif [ "$number_of_remote_regexps" -le 4 ];
		then
			remote_regexp="wyrażenia regularne"
		else
			remote_regexp="wyrażeń regularnych"
		fi
	else
		if [ "$number_of_remote_regexps" -eq 1 ];
		then
			remote_regexp="regexp"
		else
			remote_regexp="regexps"
		fi
	fi

	if [[ $LANG == *"pl"* ]];
	then
		found_remote_regex="Znaleziono $number_of_remote_regexps $remote_regexp na liście $remote_list_name"
	else
		found_remote_regex="$number_of_remote_regexps $remote_regexp found in $remote_list_name list"
	fi

	echo "[i] $found_remote_regex"

	# If pihole regex is not empty after changes
	if [[ -s "${file_pihole_regex}" ]]; then
		# Extract local regex entries
		existing_regex_list="$(grep '^[^#]' < "${file_pihole_regex}")"
		# Form output (preserving existing config)
		number_of_local_regexps=$(wc -l <<< "$existing_regex_list")

		if [[ $LANG == *"pl"* ]];
		then
			if [ "$number_of_local_regexps" -eq 1 ];
			then
				local_regexp="wyrażenie regularne"
			elif [ "$number_of_local_regexps" -le 4 ];
			then
				local_regexp="wyrażenia regularne"
			else
				local_regexp="wyrażeń regularnych"
			fi
		else
			if [ "$number_of_local_regexps" -eq 1 ];
			then
				local_regexp="regexp"
			else
				local_regexp="regexps"
			fi
		fi

		if [[ $LANG == *"pl"* ]];
		then
			found_local_regex="Znaleziono $number_of_local_regexps $local_regexp spoza listy $remote_list_name"
		else
			found_local_regex="$number_of_local_regexps $local_regexp exist outside of $remote_list_name list"
		fi
		echo "[i] $found_local_regex"
		final_regex=$(printf "%s\n" "${list_remote_regex}" "${existing_regex_list}")
	else
		if [[ $LANG == *"pl"* ]];
		then
			no_diff="Brak różnic pomiędzy regex.list a $remote_list_name.list"
		else
			no_diff="No regex.list differences to $remote_list_name.list"
		fi
		echo "[i] $no_diff"
		final_regex=$(printf "%s\n" "$list_remote_regex")
	fi

	# Output to regex.list
	if [[ $LANG == *"pl"* ]];
	then
		save="Zapisywanie do"
	else
		save="Saving to"
	fi
	echo "[i] $save ${file_pihole_regex}"
	LC_COLLATE=C sort -u <<< "${final_regex}" | sudo tee $file_pihole_regex > /dev/null
fi
done

# Refresh Pi-hole
if [[ $LANG == *"pl"* ]];
then
	refreshing="Odświeżanie"
else
	refreshing="Refreshing"
fi
echo "[i] $refreshing Pi-hole"
pihole restartdns reload > /dev/null

if [[ $LANG == *"pl"* ]];
then
	done="Gotowe"
else
	done="Done"
fi
echo "[i] $done"

exit 0
