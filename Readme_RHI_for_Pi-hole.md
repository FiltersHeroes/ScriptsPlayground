# Regex Hosts Installer for Pi-hole

This script is based on https://github.com/mmotti/pihole-regex/blob/master/install.sh.
All commands will need to be entered via Terminal (PuTTY or your SSH client of choice) after logging in.

## Why use this installer?

As @mmoti told:
> The installer will determine whether you are using the Pi-hole database or the older style regex.list, then evaluate your current regular expressions and act accordingly. It has been created to make life easier.

Additionaly we add that you can add this script to cron and have automatic updates of regex lists.

## How to use this installer?

Before doing any steps, we recommend backuping your existing regex list.

If you are using the new **Pi-hole DB**
```
sudo cp /etc/pihole/gravity.db /etc/pihole/gravity.db.bak
```

If you are using the older style **regex.list**:
```
sudo cp /etc/pihole/regex.list /etc/pihole/regex.list.bak
```

### Installation
First download it:
```bash
wget https://raw.githubusercontent.com/PolishFiltersTeam/ScriptsPlayground/master/scripts/RHI_for_Pi-hole.sh | bash
```

Then just run it with url to list as its parameter:
```bash
path_to_script/RHI_for_Pi-hole.sh https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhole.txt
```

You can also install multiple list at once:
```bash
path_to_script/RHI_for_Pi-hole.sh https://raw.githubusercontent.com/PolishFiltersTeam/KADhosts/master/KADhole.txt https://raw.githubusercontent.com/mmotti/pihole-regex/master/regex.list
```

### Removal
**Uninstallation script coming soon!**