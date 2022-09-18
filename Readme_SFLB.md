# Super Filter Lists Builder (SFLB)

That script can:
* include sections of filterlists into one file
* create whitelists from direct blocking rules from local and external filterlist using standard method or **badfilter** modifier
* include external filterlists or its sections into the local filterlist
* combine local and external sections and include it into the local filterlist
* convert direct blocking rules of local or external filterlists to hosts rules and include it into one file
* convert regex blocking rules (all or only this with star multipler) of local or external filterlists to Pi-hole regex rules and include it into one file
* use exclusions list to skip adding lines containing words or regex patterns to final list
* update version and modified date of list
* sort lines "naturally"
* add, commit and send filterlist into the git repository (it will ask you about password or you can use machine user with CircleCI and personal access token to send filterlist to git repository)
* integrate with **FOP_FH.py** script

## Required dependencies
You will need `git, tzdata, gettext-base, python (3.8+)` and following python modules: `gitpython, requests, natsort`.

## How to start?
For first, you will need to create some folder in root of your repository. Let's call it **scripts**. Then you should [download script](https://raw.githubusercontent.com/FiltersHeroes/ScriptsPlayground/master/scripts/SFLB.py) and put in into that newly created folder. Then create **SFLB.config** file in main path of your repository or another place referenced in `SFLB_CONFIG_PATH` environment variable. Here you can set format of date and version, username, e-mail for CI, language for script, timezone and path to sections of filterlist. For first you can set format of date and version like this:
```
@dateFormat %a, %d %b %Y, %H:%M UTC%z
@versionFormat Year.Month.Day.TodayNumberOfCommits
```

For date's format you can use [few format codes](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). If you didn't provide any date format, then default is `{Weekday as locale’s abbreviated name},{Day} {Month as locale’s abbreviated name} {Year},{Hour}:{Minute} {UTC}{UTC offset with colon sign}`
There are 2 version formats to choose: `Year.Month.NumberOfCommitsInMonth` and `Year.Month.Day.TodayNumberOfCommits`, but you can also write your own using similar format codes as for date's format. If you didn't provide any version format, then default is `YearMonthDayHourMinute`.

You can also set timezone, for example: `@tz Poland`, instead of `Poland`, you should write [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

You can also set language of messages in script: `@messagesLang pl_PL`, but currently there is only Polish and English language, if you didn't set it, then default is your OS's locale. If you want to use Polish language, then you should download [SFLB.mo file](https://github.com/FiltersHeroes/ScriptsPlayground/raw/master/scripts/locales/pl/LC_MESSAGES/SFLB.mo) and put it into **scripts/locales/pl/LC_MESSAGES/** directory or another place referenced in `SFLB_LOCALES_PATH` environment variable.

You can also set language for date and time if you want them to be displayed in your chosen language (by default it's in English) like for example: `@timesLang pl_PL`, but in templates file you need to write `@localizedDT` in place where you want to be.

If you want to use CI for updating your lists, then you can also set username and e-mail of machine user like this:
```
@CIusername github-actions[bot]
@CIemail 41898282+github-actions[bot]@users.noreply.github.com
```
The next step is creating folder for templates. By default you need to create **templates** folder in root of your repository, but you can override this in **SFLB.config** file writing something like this: `@templatesPath scripts/templates` (path always begins from root directory of repository). In that folder, you should create **name_of_final_filterlist_file.template** file and put into it something like this:
```
! Title: I don't care about ads
! Description: Ads are the bane of the Internet...
! Last modified: @modified
! Version: @version
! Expires: 2 days
!
!
```
You can skip `Last modified` comment, but version is required.
Then you should add some instructions into it, currently following instructions are available:

`@include section_file_name` - includes local section (section should be without comments) into the final filterlist file, that should be written without path and extension of file. Default path to section is **root/sections/FILTERLIST_final_filename**, you can override this in **.templates** or **SFLB.config** file writing something like this: `@sectionsPath Test` (path always begins from root directory of repository). By default script expects that sections has **txt** extension, but you can override this in **.templates** or **SFLB.config** file writing something like this: `@sectionsExt text`.

`@include https://example.com/mylist.txt path/to/cloned/mylist.txt` - includes external filterlist/section into the final filterlist file, adds comments about source of external filterlist. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@include section_file_name + https://example.com/mysection.txt path/to/cloned/mylist.txt` - combines local and external section into one section (combining is always done on temporary files). Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it. Default path to exclusions is **root/exclusions/FILTERLIST_final_filename**, you can override this in **.templates** or **SFLB.config** file writing something like this: `@exclusionsPath Test` (path always begins from root directory of repository). By default script expects also that files with exclusions has **txt** extension, but you can override this in **.templates** or **SFLB.config** file writing something like this: `@exclusionsExt text`.

`@include https://example.com/mylist.txt - exclusions` - includes external filterlist/section into the final filterlist file, adds comments about source of external filterlist and removes lines matching entries and regex patterns in exclusions file.

`@NWLinclude section_file_name` - make whitelist from direct blocking rules from section using standard method.

`@NWLinclude https://example.com/mylist.txt path/to/cloned/mylist.txt` - make whitelist from direct blocking rules from external section using standard method. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@BNWLinclude section_file_name` - make whitelist from direct blocking rules from section using **badfilter** modifier.

`@BNWLinclude https://example.com/mylist.txt path/to/cloned/mylist.txt` - make whitelist from direct blocking rules from external section using **badfilter** modifier. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@HOSTSinclude section_file_name` - converts direct blocking rules of section/filterlist into the hosts format and include it into the final filterlist file (converting is always done on temporary files).

`@HOSTSinclude https://example.com/mylist.txt path/to/cloned/mylist.txt` - converts direct blocking rules of external section/filterlist into the hosts format and include it into the final filterlist file, adds comments about source. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@HOSTSinclude section_file_name + https://example.com/mylist.txt path/to/cloned/mylist.txt` - converts direct blocking rules of local and external section/filterlist into the hosts format and combines them into one section (combining is always done on temporary files). . Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@DOMAINSinclude section_file_name` - converts direct blocking rules of section/filterlist into the domains format and include it into the final filterlist file (converting is always done on temporary files).

`@DOMAINSinclude https://example.com/mylist.txt path/to/cloned/mylist.txt` - converts direct blocking rules of external section/filterlist into the domains format and include it into the final filterlist file, adds comments about source. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@DOMAINSinclude section_file_name + https://example.com/mylist.txt path/to/cloned/mylist.txt` - converts direct blocking rules of local and external section/filterlist into the domains format and combines them into one section (combining is always done on temporary files). Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@PHinclude section_file_name` - converts network blocking regex rules **with star multipler** of section/filterlist into the Pi-hole regex rules (converting is always done on temporary files).

`@PHinclude https://example.com/mylist.txt path/to/cloned/mylist.txt` - converts network blocking regex rules **with star multipler** of external section/filterlist into the Pi-hole regex rules, adds comments about source. Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

`@PHinclude section_file_name + https://example.com/mysection.txt path/to/cloned/mylist.txt` - converts network blocking regex rules **with star multipler** of external section/filterlist into the Pi-hole regex rules (converting is always done on temporary files) and combines it with local section into one section (combining is always done on temporary files). Optionally as a second argument you can write path to cloned filterlist (path begins from parent directory of repository root directory). Thanks to that if filterlist repo is cloned, then script will use cloned filterlist instead of downloading it, but if it's not available, then it downloads it.

Script should sort lines of sections of filterlists, but it's only basic sort, it can't sort domains or filter options in one line and remove some duplicates (only removes duplicates if lines are identical). Anyway for more advanced sorting and deduplication, you can use [FOP_FH.py script](https://raw.githubusercontent.com/FiltersHeroes/ScriptsPlayground/master/scripts/FOP_FH.py), just download it and place it on the same folder as **SFLB** script and it should be launched automatically by **SFLB** (**FOP_FH** requires min. **python 3.6**).

If you want to use CI for updating filterlists, then you should also create personal access token with **public_repo scope** and add it to CircleCI as environment variable named **GIT_TOKEN**. Default commit message for CI is **Update filterlist_filename to version VERSION**, but you can override **filterlist_filename**, by adding comment like this to filterlist template `! Codename: Test`, of course you should replace **Test** with your chosen codename. You can also set extended commit message/description for CI in `SFLB.config` file, like this:
```
@commitDesc This is test commit description
```

The final step is launching `SFLB.py`, to do that you just need to put final_filename.extension with path to it as argument (script always begins job from root directory of repository, so you can skip that directory), for example: `./scripts/SFLB.py list/mylist.txt list/mylist2.txt` (you can put multiple lists at once as arguments).

Script should always update lists only if new rules are added. However sometimes maybe you want to update it despite the lack of new content (for example you have supplemental list for uBO, then version should be bumped on main filterlist), you can do it by setting **FORCED** variable, like this: `FORCED="true" ./scripts/SFLB.py list/mylist.txt`. However if only purpose is updating list if another one is updatedm then you can just add few conditions to `SFLB.config` file, like this:
```
@updateListIfAnotherListUpdated ListForUpdate.txt AnotherList.txt
@updateListIfAnotherListUpdated ListForUpdate2.txt AnotherList2.txt
@updateListIfAnotherListUpdated ListForUpdate2.txt AnotherList.txt
```
The last thing worth mentioning is that SFLB script has **RTM mode**. That allows to remove **DEV** name from filterlist and also send only filterlists without sections to another git repository (you can for example have DEV filterlist in one repository and RTM filterlist in another). To launch script in **RTM mode**, just run it like this: `RTM="true" ./scripts/SFLB.py list/mylist.txt`.

## Translating script
If you want to translate this script to your language, then you will need Poedit installed. If you already have that program, then fork that repository, clone it and open [SFLB.pot file](https://github.com/FiltersHeroes/ScriptsPlayground/blob/master/scripts/locales/SFLB.pot) in Poedit and click on button `Create translation`, choose your language from list and start translation. After ending of translation, click on **Edit** menu and choose **Settings**, here you can set your e-mail and name (can be nickname). Then click on **File=>Save as** and create folder in **locales** folder with name **your_language_code** and then in that folder create also **LC_MESSAGES** folder and then save file in **locales/your_language_code/LC_MESSAGES** directory. The final step is of course pushing that to GitHub and making Pull Request.
