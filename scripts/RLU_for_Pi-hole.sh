#!/usr/bin/env bash

# Regex Lists Uninstaller for Pi-hole
# Based on https://github.com/mmotti/pihole-regex/blob/master/uninstall.sh

# Variables
db_gravity='/etc/pihole/gravity.db'
installer_comment='github.com/PolishFiltersTeam/ScriptsPlayground'
mapfile -t regexlist < <(find /etc/pihole/ -type f -name '*.list' ! -iname 'adlists.list' ! -iname 'black.list' ! -iname 'gravity.list' ! -iname 'local.list' ! -iname 'regex.list' -exec basename {} \; | cut -f 1 -d '.')

if [[ $LANG == *"pl"* ]];
then
	select_text="Wybierz listę, którą chcesz odinstalować:"
else
	select_text="Select list, which you want to uninstall:"
fi

if [[ $LANG == *"pl"* ]];
then
	exit="Wyjście"
else
	exit="Exit"
fi

if [[ "$regexlist" ]]; then
	echo "$select_text"

	select opt in "${regexlist[@]}" "$exit"
	do
		case $opt in
			"$exit")
					break
					;;
			""
			*)
					break
				;;
		esac
	done
else
	if [[ $LANG == *"pl"* ]];
	then
		no_lists="Nie wykryto żadnych zainstalowanych list."
	else
		no_lists="No installed lists detected."
	fi
	echo "$no_lists"
	exit
fi

if [ "${opt}" != "$exit" ]; then
# Set regex outputs
file_pihole_regex="/etc/pihole/regex.list"
file_list_regex="/etc/pihole/$opt.list"

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

if [[ $LANG == *"pl"* ]];
then
	download_regexp_from_list="Pobieranie wyrażeń regularnych z listy $opt"
else
	download_regexp_from_list="Fetching $opt's regexps"
fi
echo "[i] $download_regexp_from_list"

if [[ $LANG == *"pl"* ]];
then
	fetching_existing="Pobieranie istniejących wyrażeń regularnych"
else
	fetching_existing="Fetching existing regexps"
fi
echo "[i] $fetching_existing"

# Conditional (db / old) variables
if [[ "${usingDB}" == true ]]; then
	str_regex=$(fetchResults "domain")
else
	str_regex=$(grep '^[^#]' < "${file_pihole_regex}")
fi

# If we are uninstalling from the Pi-hole DB, we need to accommodate for
# pi-hole migrated and installer migrated

# Start the uninstall process
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
			# As we have already migrated the user, we can easily
			# remove by the comment filed
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
			# If we have a local mmotti-regex.list, read from that as it was used on the last install (pre-db)
			if [[ -s "${file_list_regex}" ]]; then
				# Only return regexps in both the regex table and regex file
				mapfile -t result <<< "$(comm -12 <(sort <<< "${str_regex}") <(sort < "${file_list_regex}"))"
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
		exit 0
	fi

	# Refresh Pi-hole
	if [[ $LANG == *"pl"* ]];
	then
		refreshing="Odświeżanie"
	else
		refreshing="Refreshing"
	fi
	echo "[i] $refreshing Pi-hole"
	pihole restartdns reload > /dev/null

	# Remove the old list-regex file
	[[ -e "${file_list_regex}" ]] && sudo rm -f "${file_list_regex}"

else
	# Removal for standard regex.list (non-db)
	# If the pihole regex.list is not empty
	if [[ -n "${str_regex}" ]]; then
		# Restore config prior to previous install
		# Keep entries only unique to pihole regex
		if [[ -s "${file_list_regex}" ]]; then
			if [[ $LANG == *"pl"* ]];
			then
				remove_from_prev="Usuwanie $opt.list z poprzedniej instalacji"
			else
				remove_from_prev="Removing $opt.list from a previous install"
			fi
			echo "[i] $remove_from_prev"
			comm -23 <(sort <<< "${str_regex}") <(sort "${file_list_regex}") | sudo tee $file_pihole_regex > /dev/null
		fi
	else
		if [[ $LANG == *"pl"* ]];
		then
			empty="Plik regex.list jest pusty. Nie ma potrzeby przetwarzania."
		else
			empty="Regex.list is empty. No need to process."
		fi
		echo "[i] $empty"
		exit 0
	fi

	# Refresh Pi-hole
	if [[ $LANG == *"pl"* ]];
	then
		refreshing="Odświeżanie"
	else
		refreshing="Refreshing"
	fi
	echo "[i] $refreshing Pi-hole"
	pihole restartdns reload > /dev/null

	# Remove the old list-regex file
	[[ -e "${file_list_regex}" ]] && sudo rm -f "${file_list_regex}"

	if [[ $LANG == *"pl"* ]];
	then
		done="Gotowe"
	else
		done="Done"
	fi
	echo "[i] $done"
fi
fi