from EpisodeType import EpisodeType
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from requests import get
from tqdm import tqdm

import urllib3, os, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__version__ = "0.1.0"
DOWNLOAD_PATH = "./download/"
DOWNLOAD_FILLERS = True
URL = "https://ft.wbijam.pl/ps.html"

def download_episode(driver, e):
    mp4up_url = None
    print(f"Downloading {e['name']}")
    driver.get(e["link"])
    video_providers = driver.find_element_by_class_name("lista").find_elements_by_class_name("lista_hover")
    for provider in video_providers:
        provider_name = provider.find_elements_by_tag_name("td")[2].text
        if provider_name == "mp4up":
            mp4up_url = provider.find_elements_by_tag_name("td")[4].find_element_by_class_name("odtwarzacz_link").get_attribute("rel")
            break

    if mp4up_url is None:
        raise ValueError("mp4up video not found.")

    main_url = urlparse(driver.current_url)
    player_url = f"{main_url.scheme}://{main_url.hostname}/odtwarzacz-{mp4up_url}.html"
    driver.get(player_url)
    frame = driver.find_element_by_xpath("/html/body/div[2]/div/center/iframe")
    driver.switch_to.frame(frame)
    video =  WebDriverWait(driver, 10).until(lambda x: x.find_element_by_xpath("/html/body/div/video"))
    time.sleep(2)
    video_url =  video.get_attribute("src")
    print(f"Found video at: {video_url}")

    file_name = format_file_name(e["name"])
    full_file_name = DOWNLOAD_PATH + file_name
    r = get(video_url, stream=True, verify=False)
    file_size = int(r.headers['Content-Length'])
    chunk_size=1024
    num_bars = int(file_size / chunk_size)

    with open(full_file_name, 'wb') as fp:
        for chunk in tqdm(
                                    r.iter_content(chunk_size=chunk_size)
                                    , total= num_bars
                                    , unit = 'KB'
                                    , desc = file_name
                                    , leave = True # progressbar stays
                                ):
            fp.write(chunk)
    print("Done")


def format_file_name(file_name):
    file_name = file_name \
        .replace('.', '') \
        .replace(":", '') \
        .replace(' ', '_') \
        .replace('"', '')
    file_name += ".mp4"
    return file_name


def get_episodes(driver):
    table = driver.find_element_by_class_name("lista")
    table_position = table.find_element_by_tag_name("tbody").find_elements_by_tag_name("tr")
    episodes = []
    for e in table_position:
        a = e.find_element_by_tag_name("td").find_element_by_tag_name("a")
        if e.find_elements_by_tag_name("td")[1].text == "filler":
            episode_type = EpisodeType.Filler
        else:
            episode_type = EpisodeType.Normal
        episode = {
            "name": a.text,
            "link": a.get_property("href"),
            "type": episode_type
        }
        episodes.append(episode)
    if not DOWNLOAD_FILLERS:
        print("Ignoring fillers.")
        episodes = [e for e in episodes if e["type"] != EpisodeType.Filler]

    episodes.sort(key=lambda x: x["link"])
    print(f"Found episodes: {len(episodes)}")
    return episodes


def filer_episodes(episodes):
    files = os.listdir(DOWNLOAD_PATH)
    episodes = [e for e in episodes if format_file_name(e["name"]) not in files]
    return episodes


def main():
    print("======================")
    print(f"Video downloader {__version__}")
    print("======================")

    if not os.path.exists(DOWNLOAD_PATH):
        print(f"Download directory ({DOWNLOAD_PATH})not found. Creating new one.")
        os.mkdir(DOWNLOAD_PATH)

    # example: https://ft.wbijam.pl/ps.html
    # url = input("Paste your URL here: ")

    driver = webdriver.Chrome()
    driver.get(url=URL)

    episodes = get_episodes(driver)
    episodes = filer_episodes(episodes)
    print(f"Episodes remained to download: {len(episodes)}")
    for e in episodes:
        download_episode(driver, e)


if __name__ == "__main__":
    main()