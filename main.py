import argparse
import asyncio
import logging
import os
import pathlib

import genshin
import jinja2
import requests
import io
import time
import pathlib
from bs4 import BeautifulSoup

logger = logging.getLogger()

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--template", default="template.html", type=pathlib.Path)
parser.add_argument("-o", "--output", default="stats.html", type=pathlib.Path)
parser.add_argument("-c", "--cookies", default=None)
parser.add_argument("-l", "--lang", "--language", choices=genshin.LANGS, default="en-us")


async def main():
    args = parser.parse_args()
    cookies = args.cookies or os.environ["COOKIES"]

    client = genshin.Client(cookies, debug=True, game=genshin.Game.GENSHIN)

    user = await client.get_full_genshin_user(0, lang=args.lang)
    abyss = user.abyss.current if user.abyss.current.floors else user.abyss.previous
    diary = await client.get_diary()

    try:
        await client.claim_daily_reward(lang=args.lang, reward=False)
    except genshin.AlreadyClaimed:
        pass
    finally:
        reward = await client.claimed_rewards(lang=args.lang).next()
        reward_info = await client.get_reward_info()
        
    #=========================================================================
    res = requests.get("https://www.pockettactics.com/genshin-impact/codes")
    soup = BeautifulSoup(res.text, 'html.parser')

    active_codes = [code.text.strip() for code in soup.find(
        "div", {"class": "entry-content"}).find("ul").findAll("strong")]
    
    kode = []
    for tag in soup.select("div ul li strong"):
        #print(tag.text)
        kode.append(tag.text)
    o = 1
    while o <= 5:
        #print(i)
        kode.pop(0)
        o += 1
    i = 1
    while i <= 8:
        #print(i)
        kode.pop(3)
        i += 1

    root = pathlib.Path(__file__).parent.resolve()
    codes_file = root / "codes.txt"
    used_codes = codes_file.open().read().split("\n")
    new_codes = list(filter(lambda x: x not in used_codes, kode))


    # Redeem codes
    print("[Code redeem] ", end="")
    redeemed_codes = []
    for code in kode[:-1]:
        try:
            await client.redeem_code(code)
            redeemed_codes.append(code)
        except Exception:
            pass
        time.sleep(5.2)
    if len(kode) != 0:
        try:
            await client.redeem_code(kode[-1])
            redeemed_codes.append(code)
        except Exception:
            pass

    if len(redeemed_codes) != 0:
        print("Redeemed " + str(len(redeemed_codes)) +
              " new codes: " + ", ".join(redeemed_codes))
    else:
        print("No new codes found")
        
    #%% Add new codes to used codes

    used_codes.extend(new_codes)
    io.open(codes_file, "w", newline="\n").write("\n".join(used_codes))

     #=========================================================================

    template = jinja2.Template(args.template.read_text())
    rendered = template.render(
        user=user,
        lang=args.lang,
        abyss=abyss,
        reward=reward,
        diary=diary,
        reward_info=reward_info,
    )
    args.output.write_text(rendered)


if __name__ == "__main__":
    asyncio.run(main())
