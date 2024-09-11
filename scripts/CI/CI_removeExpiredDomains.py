#!/usr/bin/env python3
import re
import os
import sys
import subprocess
import git


pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))

git_repo = git.Repo(script_path, search_parent_directories=True)
# Main_path is where the root of the repository is located
main_path = git_repo.git.rev_parse("--show-toplevel")

filerlist_path = pn(pj(main_path, "..", sys.argv[1]))


config_path = pj(filerlist_path, ".SFLB.config")

def getValuesFromConf(config_path):
    class conf():
        # Read settings from config file
        def __init__(self):
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf8") as cf:
                    for lineConf in cf:
                        cfProperty = lineConf.strip().split()[
                            0].replace("@", "")
                        if matchC := re.search(r'@'+cfProperty+' (.*)$', lineConf):
                            self[cfProperty] = matchC.group(1)

        def __setitem__(self, key, value):
            setattr(self, key, value)

        def __getitem__(self, key):
            return getattr(self, key)
    return conf

sections_path = pn(pj(filerlist_path, "sections"))
conf = getValuesFromConf(config_path)
if hasattr(conf(), 'sectionsPath'):
    sections_path = pn(pj(filerlist_path, conf().sectionsPath))

expiredListFiles = []
for expiredType in ["expired", "parked"]:
    if sys.argv[1] == "PolishAnnoyanceFilters":
        paf_lists = ["PAF_arrows", "PAF_backgrounds_self-advertising","PAF_contact_feedback_widgets", "PAF_e_newspaper", "PAF_newsletters", "PAF_other_widgets", "PAF_pop-ups", "PAF_push", "PAF_scrolling_videos", "PAF_backgrounds_self-adv_supp", "PAF_comeback_titles", "PAF_contact_feedback_widgets_supp", "PAF_newsletters_supp", "PAF_other_elements_supp", "PAF_pop-ups_supp", "PAF_push_supp", "PAF_scrolling_videos_supp", "PAF_tagged_internal_links"]
        for paf_list in paf_lists:
            expiredListFiles.append(f"{paf_list}-{expiredType}.txt")
    elif sys.argv[1] == "KAD":
        expiredListFiles.append(f"KAD-{expiredType}.txt")
    elif sys.argv[1] == "KADhosts":
        expiredListFiles.append(f"KADhosts-{expiredType}.txt")
    elif sys.argv[1] == "PolishAntiAnnoyingSpecialSupplement":
        expiredListFiles.append(f"polish_rss_filters-{expiredType}.txt")
    elif sys.argv[1] == "PolishSocialCookiesFiltersDev":
        psc_lists = ["adblock_cookies", "adblock_social_list", "cookies_uB_AG", "social_filters_uB_AG"]
        for psc_list in psc_lists:
            expiredListFiles.append(f"{psc_list}-{expiredType}.txt")

for expiredListFile in expiredListFiles:
    expiredListFilePath = pj(main_path, "expired-domains", expiredListFile)
    if os.path.exists(expiredListFilePath):
        subprocess.run(["python3", pj(main_path, "scripts", "EDRFF.py"), sections_path, expiredListFilePath])
        if sys.argv[1] == "KAD":
            for tpName in ["CERT", "LWS"]:
                subprocess.run(["python3", pj(filerlist_path, "scripts", "update3pExpired.py"), tpName, expiredListFilePath])

mail = os.environ["CI_EMAIL"]
name = os.environ["CI_USERNAME"]

git_filerlist_repo = git.Repo(filerlist_path, search_parent_directories=True)
with git_filerlist_repo.config_writer() as cw:
    cw.set_value("user", "name", name).release()
    cw.set_value("user", "email", mail).release()

M_S_PAT = re.compile(r"^"+re.escape(os.path.relpath(sections_path, start=filerlist_path) + "/"))
sectionsWereModified = ""
for item in git_filerlist_repo.index.diff(None):
    if M_S_PAT.search(item.a_path):
         sectionsWereModified = "true"

if sectionsWereModified:
    git_filerlist_repo.git.add(sections_path)
    if sys.argv[1] == "KAD":
        exclusions_path = pn(pj(filerlist_path, "exclusions"))
        git_filerlist_repo.git.add(exclusions_path)
    git_filerlist_repo.index.commit("Wygasłe domeny\n[ci skip]")
    GIT_SLUG = git_filerlist_repo.remotes.origin.url.replace(
        'https://', "").replace("git@", "").replace(":", "/")
    git_filerlist_repo.git.push(f"https://{name}:{os.environ['GIT_TOKEN']}@{GIT_SLUG}")
