from EpisodeType import EpisodeType
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from requests import get
from tqdm import tqdm
from tkinter import *

import urllib3, os, time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

__version__ = "0.1.0"

class WbijamDownloader:
    def __init__(self, download_path, should_download_fillers = False):
        self.download_path = download_path
        self.should_download_fillers = should_download_fillers

    def download_episode(self, driver, e):
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
        video =  WebDriverWait(driver, 10).until(lambda x: x.find_element_by_tag_name("video"))
        time.sleep(2)
        video_url =  video.find_element_by_tag_name("source").get_attribute("src")
        print(f"Found video at: {video_url}")

        file_name = self.format_file_name(e["name"])
        full_file_name = self.download_path + file_name
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

    def format_file_name(self, file_name):
        file_name = file_name \
            .replace('.', '') \
            .replace(":", '') \
            .replace(' ', '_') \
            .replace('\'', '') \
            .replace('!', '') \
            .replace('?', '') \
            .replace('"', '')

        file_name += ".mp4"
        return file_name

    def get_episodes(self, driver):
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
        if not self.should_download_fillers:
            print("Ignoring fillers.")
            episodes = [e for e in episodes if e["type"] != EpisodeType.Filler]

        episodes.reverse()
        print(f"Found episodes: {len(episodes)}")
        return episodes

    def filer_episodes(self, episodes):
        files = os.listdir(self.download_path)
        episodes = [e for e in episodes if self.format_file_name(e["name"]) not in files]
        return episodes

    def start_downloading(self, url: str):
        print("======================")
        print(f"Video downloader {__version__}")
        print("======================")

        if not os.path.exists(self.download_path):
            print(f"Download directory ({self.download_path})not found. Creating new one.")
            os.mkdir(self.download_path)

        driver = webdriver.Chrome()
        driver.get(url=url)

        episodes = self.get_episodes(driver)
        episodes = self.filer_episodes(episodes)

        print(f"Episodes remained to download: {len(episodes)}")

        for e in episodes:
            self.download_episode(driver, e)

if __name__ == "__main__":
    downloader = WbijamDownloader("D:/Download/Attack on Titans/", should_download_fillers=False)
    downloader.start_downloading("https://snk.wbijam.pl/pierwsza_seria.html")