# Version Include Checksum Hosts Sort (VICHS)

That script can:
* include sections of filterlists into one file
* create whitelists from direct blocking rules from local and external filterlist using standard method or **badfilter** modifier
* include external filterlists or its sections into the local filterlist
* combine local and external sections and include it into the local filterlist
* convert direct blocking rules of local or external filterlists to hosts rules and include it into one file
* convert regex blocking rules (all or only this with star multipler) of local or external filterlists to Pi-hole regex rules and include it into one file
* update version and modified date of list
* add checksum
* sort lines alphabetically
* add, commit and send filterlist into the git repository (it will ask you about password or you can use machine user with CircleCI and personal access token to send filterlist to git repository)
* integrate with **FOP.py** script

## Required dependencies
You will need following dependencies: `git, openssh-client, ca-certificates, wget, tzdata` and `gettext-base`.

## How to start?
For first, you will need to create some folder in root of your repository. Let's call it **scripts**. Then you should [download script](https://raw.githubusercontent.com/PolishFiltersTeam/ScriptsPlayground/master/scripts/VICHS.sh) and put in into that newly created folder. Then create **VICHS.config** file in **scripts** folder. Here you can set format of date and version, username, e-mail for CI, language for script, timezone and path to sections of filterlist. For first you can set format of date and version like this:
```
@dateFormat %a, %d %b %Y, %H:%M UTC%:::z
@versionFormat Year.Month.Day.TodayNumberOfCommits
```

Date's format should be in format of date command ([a complete list of FORMAT control characters](https://www.cyberciti.biz/faq/linux-unix-formatting-dates-for-display/)). There are 2 version formats to choose: `Year.Month.NumberOfCommitsInMonth` and `Year.Month.Day.TodayNumberOfCommits`, but you can also write your own using format control characters supported by date command, but instead of `@dateFormat`, you should write `@versionDateFormat`. If you didn't provide any version format, then default is `YearMonthDayHourMinute`.

You can also set timezone, for example: `@tz Poland`, instead of `Poland`, you should write [TZ database name](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

You can also set language of script: `@lang pl`, but currently there is only Polish and English language, if you didn't set it, then default is English. If you want to use Polish language, then you should download [VICHS.mo file](https://github.com/PolishFiltersTeam/ScriptsPlayground/raw/master/scripts/locales/pl/LC_MESSAGES/VICHS.mo) and put it into **scripts/locales/pl/LC_MESSAGES/** directory.

If you want to use CI for updating your lists, then you can also set username and e-mail of machine user like this:
```
@CIusername PolishJarvis
@CIemail PolishJarvis@int.pl
```
The next step is creating **templates** folder in root of your repository. In that folder, should create **name_of_final_filterlist_file.template** file and put into it something like this:
```
! Checksum: @
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

`@include section_file_name` - includes local section (section should be without comments) into the final filterlist file, that should be written without path and extension of file. Default path to section is **root/sections/FILTERLIST_final_filename**, you can override this in **.templates** or **VICHS.config** file writing something like this: `@path Test` (path always begins from root directory of repository, we assume that the script is in the 1 lower directory than the main repository directory)

`@URLinclude https://example.com/mylist.txt` - includes external filterlist/section into the final filterlist file, adds comments about source of external filterlist

`@URLUinclude https://example.com/mylist.txt` - includes external filterlist/section with only unique rules into the final filterlist file, adds comments about source of external filterlist

`@NWLinclude section_file_name` - make whitelist from direct blocking rules from section using standard method

`@URLNWLinclude https://example.com/mylist.txt` - make whitelist from direct blocking rules from external section using standard method

`@BNWLinclude section_file_name` - make whitelist from direct blocking rules from section using **badfilter** modifier

`@URLBNWLinclude https://example.com/mylist.txt` - make whitelist from direct blocking rules from external section using **badfilter** modifier

`@COMBINEinclude section_file_name https://example.com/mysection.txt` - combines local and external section into one section (combining is always done on temporary files)

`@HOSTSinclude section_file_name` - converts direct blocking rules of section/filterlist into the hosts format and include it into the final filterlist file (converting is always done on temporary files)

`@URLHOSTSinclude https://example.com/mylist.txt` - converts direct blocking rules of external section/filterlist into the hosts format and include it into the final filterlist file

`@COMBINEHOSTSinclude section_file_name https://example.com/mylist.txt` - converts direct blocking rules of local and external section/filterlist into the hosts format and combines them into one section (combining is always done on temporary files)

`@DOMAINSinclude section_file_name` - converts direct blocking rules of section/filterlist into the domains format and include it into the final filterlist file (converting is always done on temporary files)

`@URLDOMAINSinclude https://example.com/mylist.txt` - converts direct blocking rules of external section/filterlist into the domains format and include it into the final filterlist file

`@COMBINEDOMAINSinclude section_file_name https://example.com/mylist.txt` - converts direct blocking rules of local and external section/filterlist into the domains format and combines them into one section (combining is always done on temporary files)

`@PHinclude section_file_name` - converts network blocking regex rules **with star multipler** of section/filterlist into the Pi-hole regex rules (converting is always done on temporary files)

`@URLPHinclude https://example.com/mylist.txt` - converts network blocking regex rules **with star multipler** of external section/filterlist into the Pi-hole regex rules

`@COMBINEPHinclude section_file_name https://example.com/mysection.txt` - converts network blocking regex rules **with star multipler** of external section/filterlist into the Pi-hole regex rules (converting is always done on temporary files) and combines it with local section into one section (combining is always done on temporary files)

Script should sort lines of sections of filterlists, but it's only basic sort, it can't sort domains or filter options in one line and remove some duplicates (only removes duplicates if lines are identical). Anyway for more advanced sorting and deduplication, you can use [FOP.py script](https://raw.githubusercontent.com/PolishFiltersTeam/ScriptsPlayground/master/scripts/FOP.py), just download it and place it on the same folder as **VICHS** script and it should be launched automatically by **VICHS** (**FOP** requires min. **python 3.2**).

If you want to use CI for updating filterlists, then you should also create personal access token with **public_repo scope** and add it to CircleCI as environment variable named **GIT_TOKEN**. Default commit message for CI is **Update filterlist_filename to version VERSION**, but you can override **filterlist_filename**, by adding comment like this to filterlist template `! Codename: Test`, of course you should replace **Test** with your chosen codename. You can also set extended commit message/description for CI in `VICHS.config` file, like this:
```
@commitDesc This is test commit description
```

The final step is launching `VICHS.sh`, to do that you just need to put final_filename.extension with path to it as argument (script always begins job from root directory of repository, so you can skip that directory), for example: `./scripts/VICHS.sh list/mylist.txt list/mylist2.txt` (you can put multiple lists at once as arguments).

Script should always update lists only if new rules are added. However sometimes maybe you want to update it despite the lack of new content (for example you have supplemental list for uBO, then version should be bumped on main filterlist), you can do it by setting **FORCED** variable, like this: `FORCED="true" ./scripts/VICHS.sh list/mylist.txt`, of course recommended is also adding condition for checking if supplemental list was updated and main list wasn't updated.
That condtion you can add in `VICHS.config` file, like this:
```
@updateListIfAnotherListUpdated ListForUpdate.txt AnotherList.txt
@updateListIfAnotherListUpdated ListForUpdate2.txt AnotherList2.txt
@updateListIfAnotherListUpdated ListForUpdate2.txt AnotherList.txt
```
Then you will need to launch [HelperForVICHS.sh script](https://raw.githubusercontent.com/PolishFiltersTeam/ScriptsPlayground/master/scripts/HelperForVICHS.sh). In that case you also don't need to run both scripts (VICHS and HelperForVichs), you can launch HelperForVichs script with arguments same as for VICHS and it will forward arguments to VICHS.

The last thing worth mentioning is that VICHS script has **RTM mode**. That allows to remove **DEV** name from filterlist and also send only filterlists without sections to another git repository (you can for example have DEV filterlist in one repository and RTM filterlist in another). To launch script in **RTM mode**, just run it like this: `RTM="true" ./scripts/VICHS.sh list/mylist.txt`.

## Translating script
If you want to translate this script to your language, then you will need Poedit installed. If you already have that program, then fork that repository, clone it and open [VICHS.pot file](https://github.com/PolishFiltersTeam/ScriptsPlayground/blob/master/scripts/locales/VICHS.pot) in Poedit and click on button `Create translation`, choose your language from list and start translation. After ending of translation, click on **Edit** menu and choose **Settings**, here you can set your e-mail and name (can be nickname). Then click on **File=>Save as** and create folder in **locales** folder with name **your_language_code** and then in that folder create also **LC_MESSAGES** folder and then save file in **locales/your_language_code/LC_MESSAGES** directory. The final step is of course pushing that to GitHub and making Pull Request.