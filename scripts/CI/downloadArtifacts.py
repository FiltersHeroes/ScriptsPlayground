#!/usr/bin/env python3
# coding=utf-8
# pylint: disable=C0103
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
import os
import sys
import shutil
import asyncio
import aiohttp


pj = os.path.join
pn = os.path.normpath

script_path = os.path.dirname(os.path.realpath(__file__))
main_path = os.getenv("GITHUB_WORKSPACE")

expired_dir = pj(main_path, "expired-d")
if not os.path.isdir(expired_dir):
    os.mkdir(expired_dir)

async def download_artifact(session, limit, name):
    async with limit:
        try:
            repo = os.getenv("GITHUB_REPOSITORY")
            artifacts_url = f"https://api.github.com/repos/{repo}/actions/artifacts"
            token = os.getenv("GIT_TOKEN")
            headers = { "Authorization": f"Bearer {token}", "User-Agent": "Python"}
            params = {'name': name}
            resp = await session.get(artifacts_url, headers=headers, params=params)
            if resp.status == 200:
                data = await resp.json()
                print(data)
                if data["artifacts"]:
                    artifact = data["artifacts"][0]
                    try:
                        print(f"Downloading artifact {name} ...")
                        resp_adl = await session.get(artifact["archive_download_url"], headers=headers)
                        if resp_adl.status == 200:
                            file_path = pj(expired_dir, name + ".zip")
                            zip_file = await resp_adl.read()
                            with open(file_path, "wb") as f:
                                f.write(zip_file)
                            if os.path.isfile(file_path):
                                shutil.unpack_archive(file_path, expired_dir)
                                os.remove(file_path)
                    except Exception as e_adl:
                        print(e_adl)
        except Exception as e:
            print(e)

async def download_artifacts(limit_value, names):
    limit = asyncio.Semaphore(limit_value)
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[download_artifact(session, limit, name) for name in names])

artifact_names = []
if sys.argv[1]:
    artifact_names = os.getenv(str(sys.argv[1])).split(" ")
asyncio.run(download_artifacts(5, artifact_names))
