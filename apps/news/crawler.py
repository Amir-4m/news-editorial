import logging
import pytz
from datetime import datetime

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup
from khayyam import JalaliDatetime

from .models import News, NewsAgency, NewsSiteCategory

jalali_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
jalali_months_entekhab = ['فروردين', 'ارديبهشت', 'خرداد', 'تير', 'مرداد', 'شهريور', 'مهر', 'آبان', 'آذر', 'دی', 'بهمن',
                          'اسفند']


class Crawler:
    website_name = ''

    def __init__(self):
        try:
            self.news_agency = NewsAgency.objects.get(news_website=self.website_name)
        except NewsAgency.DoesNotExist:
            logging.error(f'NewsAgency object not found with this news_website: {self.website_name}')
            return
        if self.news_agency.crawl_enable:
            logging.info(f'Starting Crawl on {self.website_name}')

            # self.urls = [{ 'news_url': '<url>', 'category_id': 1 }, ...]
            # this value is just use in collect_links() method.
            self.urls = NewsSiteCategory.objects.filter(
                news_agency=self.news_agency
            ).values('news_url', 'category_id')

            logging.debug(f"urls to crawl >>> {self.urls}")
            self.collect_news()
        else:
            logging.error(f'Crawler has stopped working! {self.website_name} crawl is disabled.')

    def collect_links(self):
        """
        :return: A list of urls of news and category id of that news like this [ ("<url>", <category_id>), ... ]  
        """
        raise NotImplementedError()

    def collect_news(self):
        raise NotImplementedError()

    def get_categories_name(self):
        return [
            cat.strip() for cat in NewsSiteCategory.objects.filter(
                news_agency=self.news_agency
            ).values_list('site_category_name', flat=True)
        ]

    def download_image(self, url):
        """
        Args:
            url: url of news image that takes from page
            defaults: data for create a new field

        Returns: Image <django.core.files.File> to save in ImageField <news_image>
        """
        r = requests.get(url, allow_redirects=False)
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(r.content)
        img_temp.flush()  # deleting the file from RAM
        return File(img_temp, name=url.split('/')[-1])


class ILNACrawler(Crawler):
    website_name = 'ilna.news'

    def collect_links(self):
        news_links = []
        for url in self.urls:
            try:
                page = requests.get(url['news_url'], allow_redirects=False)
                soup = BeautifulSoup(page.text, "html.parser")

                first_news = soup.find(class_="defloat firstDIV center").find("a").attrs["href"]
                news_links.append((f"https://www.ilna.news{first_news}", url['category_id']))

                second_news = soup.find(class_="seclevel_news mb8 mt16 clearbox").find_all("h3")

                for news in second_news:
                    news_links.append((f"https://www.ilna.news{news.find('a').attrs['href']}", url['category_id']))

                news_list = soup.find(class_="pb32").find_all("li")
                for news in news_list:
                    news_links.append((f"https://www.ilna.news{news.find('a').attrs['href']}", url['category_id']))
            except Exception as e:
                logging.error(f"collect links >>> {e.args}")

        return news_links

    def collect_news(self):
        urls = self.collect_links()
        defined_categories = self.get_categories_name()
        for url, category_id in urls:
            try:
                page = requests.get(url, allow_redirects=False)
                soup = BeautifulSoup(page.text, "html.parser")

                news_site_id = int(soup.find(class_="inlineblock ml16").find("span").get_text())
                news_str_date = soup.find_all("time")[1].attrs['datetime']
                news_date = news_str_date.split('-')  # ['2020', '11', '17T06:36:55Z']
                news_time = news_str_date.split(':')  # ['2020-11-17T06', '36', '55Z']
                news_date = datetime(
                    int(news_date[0]),  # year
                    int(news_date[1]),  # month
                    int(news_date[2][:2]),  # day -> '15T04:28:25Z'
                    int(news_time[0][-2:]),  # hour '2020-11-01T12'
                    int(news_time[1]),  # minute
                    int(news_time[2][:2]),
                    tzinfo=pytz.timezone(settings.TIME_ZONE)
                )

                news_category = soup.find_all("a", class_="float ml4 mr4")[-1].get_text()

                news_title = soup.find("h1", class_="fb fn22 news_title mt8 mb8").get_text().strip()
                news_summary = soup.find("p", class_="fn14 news_lead pr8 pl8 pt8 pb8").text
                news_main_soup = soup.find("section", class_="article_body mt16 clearbox fn14 content").find_all("p")
                news_main = str()

                for i in range(1, len(news_main_soup)):
                    news_main_soup[i] = str(news_main_soup[i])
                    news_main += news_main_soup[i]

                # final data to save
                defaults = {
                    'direct_link': url,
                    "news_category": news_category,
                    "news_title": news_title,
                    "news_site": "ilna.news",
                    "news_main": news_main,
                    "news_main_editable": news_main,
                    "news_summary": news_summary,
                    "news_date": news_date,
                    # download news image
                    "news_image": self.download_image(
                        # image URL
                        soup.find(
                            "section", class_="article_body mt16 clearbox fn14 content"
                        ).find("img").attrs["src"])
                }

                # creating news ...
                news, _created = News.objects.get_or_create(news_site_id=news_site_id, defaults=defaults)
                # adding the categories of news
                if news_category in defined_categories:
                    news.category.add(category_id)
                # success log
                if _created:
                    logging.info(f"New news created!, id = {news_site_id}, website = ilna.news")
                else:
                    logging.info(f"Duplicate news!, id = {news_site_id}, website = ilna.news")
            except Exception as e:
                logging.error(f"collect news error >>> {e.args}, url: {url}, news site: {self.website_name}")


class ISNACrawler(Crawler):
    website_name = 'isna.ir'

    def collect_links(self):
        all_a = ''
        news_links = []
        for url in self.urls:
            page = requests.get(url['news_url'], allow_redirects=False)
            soup = BeautifulSoup(page.text, 'html.parser')
            news_list_1 = soup.find('section', attrs={'id': 'box9',
                                                      'class': "box card no-header horizontal full-card _cyan has-more has-more-bottom has-more-default has-more-centered"})
            try:
                all_a = news_list_1.find_all("a")
            except Exception as e:
                logging.error(f"-- 1 collect links error >>> {e.args}, url: {url.get('news_url')}, {self.website_name}")
            try:
                for a in all_a:
                    if a.find("img"):
                        news_links.append((f"https://www.isna.ir{a.attrs['href']}", url['category_id']))
            except Exception as e:
                logging.error(f"2 collect links error >>> {e.args}, url: {url}")
            try:
                news_list_2 = soup.find(
                    class_="box card no-header horizontal full-card _cyan has-more has-more-bottom has-more-default has-more-centered")
                links = news_list_2.find_all("li")

                for link in links:
                    anchor = link.find("a").attrs['href']
                    news_links.append((f"https://www.isna.ir{anchor}", url['category_id']))
            except Exception as e:
                logging.error(f"3 collect links error >>> {e.args}, url: {url}")
        result = list(set(news_links))
        logging.debug(f"urls found {result}")
        return result

    def collect_news(self):
        urls = self.collect_links()
        defined_categories = self.get_categories_name()
        for url, category_id in urls:
            page = requests.get(url, allow_redirects=False)
            soup = BeautifulSoup(page.text, 'html.parser')

            try:
                news_jalali_date = soup.find(class_="title-meta").get_text().strip() + soup.find(
                    class_="text-meta").get_text().strip()
                jalali_date_list = news_jalali_date.strip().split("/")
                jalali_date_details = jalali_date_list[1].split(" ")  # date
                jalali_time_details = jalali_date_list[2].split(':')  # time

                news_date = JalaliDatetime(
                    int(jalali_date_details[2]),
                    jalali_months.index(jalali_date_details[1]) + 1,
                    int(jalali_date_details[0]),
                    int(jalali_time_details[0]),
                    int(jalali_time_details[1]),
                    tzinfo=pytz.timezone(settings.TIME_ZONE)
                ).todatetime()

                news_category = soup.find_all(class_="text-meta")[1].get_text().strip()
                news_site_id = url.split("/")[4]
                news_title = soup.find('h1', class_="first-title").get_text()

                news_main_text = (soup.find(class_="item-text"))
                news_main_text = news_main_text.find_all_next("p")
                news_main_text = list(news_main_text)
                for i in range(len(news_main_text)):
                    news_main_text[i] = str(news_main_text[i])

                news_summary = soup.find(class_="summary").text

                # downloading news image
                news_image = self.download_image(soup.find(class_="item-img img-md").find("img").attrs["src"])

                news, _created = News.objects.get_or_create(
                    news_site_id=news_site_id,
                    defaults={
                        'direct_link': url,
                        "news_category": news_category,
                        "news_title": news_title,
                        "news_site": "isna.ir",
                        "news_main": "".join(news_main_text),
                        "news_main_editable": "".join(news_main_text),
                        "news_summary": news_summary,
                        "news_date": news_date,
                        "news_image": news_image
                    }
                )
                if news_category in defined_categories:
                    news.category.add(category_id)

                if _created:
                    logging.info(f"News created!, id = {news_site_id}, website = isna.ir")
                else:
                    logging.info(f"Duplicate news!, id = {news_site_id}, website = isna.ir")
            except Exception as e:
                logging.error(f"collect news error >>> {e.args}, url: {url}")


class ENTEKHABCrawler(Crawler):
    website_name = 'entekhab.ir'

    def collect_links(self):
        entekhab_news_links = []
        for url in self.urls:
            try:
                page = requests.get(url['news_url'], allow_redirects=False)
                soup = BeautifulSoup(page.text, 'html.parser')

                article_link = soup.find('h2', class_='Htags')
                entekhab_news_links.append(
                    (f"https://www.entekhab.ir{article_link.find('a').attrs['href']}", url['category_id']))

                news_list = soup.find(
                    'div', class_="im-news col-xs-36 section_paged_main_content_div").find_all("a", class_="title6")

                for news in news_list:
                    entekhab_news_links.append((f"https://www.entekhab.ir{news.attrs['href']}", url['category_id']))
            except Exception as e:
                logging.error(f"collect links error >>> {e.args}, url: {url}")

        return entekhab_news_links

    def collect_news(self):
        urls = self.collect_links()
        defined_categories = self.get_categories_name()
        for url, category_id in urls:
            try:
                page = requests.get(url, allow_redirects=False)
                soup = BeautifulSoup(page.text, "html.parser")

                news_site_id = soup.find("div", class_="news_id_c").get_text().split(" ")[-1]

                news_jalali_date = soup.find("div", class_="news_pdate_c").get_text().split('ر:')[-1].strip()

                news_category_a = soup.find(class_="news_path").find_all("a")
                news_category = []
                for a in news_category_a:
                    news_category.append(a.get_text().strip())

                news_category = news_category[0]
                news_title = soup.find("h1", class_="title col-xs-36").get_text().strip()
                news_summary = soup.find('div', class_="subtitle").text
                news_main = soup.find(class_="body col-xs-36").find_all(['a', 'p'])

                for i in range(len(news_main)):
                    news_main[i] = str(news_main[i])

                news_main = "".join(news_main)

                # date
                news_date = news_jalali_date.split("-")[1].strip().split(" ")
                news_date_day = int(news_date[0])
                news_date_month = jalali_months_entekhab.index(news_date[1]) + 1
                news_date_year = int(news_date[-1])

                # time
                news_time = news_jalali_date.split("-")[0].strip().split(' : ')
                news_date = datetime(
                    news_date_year,
                    news_date_month,
                    news_date_day,
                    int(news_time[1]),
                    int(news_time[0]),
                    tzinfo=pytz.timezone(settings.TIME_ZONE)
                )

                news_image = soup.find("img", class_="image_btn")

                if news_image:
                    news_image = news_image.attrs["src"]
                else:
                    news_image = soup.find("img", class_="news_corner_image").attrs["src"]
                news_image = self.download_image(f"https://www.entekhab.ir{news_image}")

                news, _created = News.objects.get_or_create(
                    news_site_id=news_site_id,
                    defaults={
                        'direct_link': url,
                        "news_category": news_category,
                        "news_title": news_title,
                        "news_site": "entekhab.ir",
                        "news_main": news_main,
                        "news_main_editable": news_main,
                        "news_summary": news_summary,
                        "news_date": news_date,
                        "news_image": news_image,
                    }
                )
                if news_category in defined_categories:
                    news.category.add(category_id)
                logging.info(f"news created!, id = {news_site_id}, website = entekhab.ir")
            except Exception as e:
                logging.error(f"collect links error >>> {e.args}, url: {url}")


def add_category():
    news = News.objects.get(id=6252)
    nn = news.news_category
    n_cat = news.category.first()
    n_agen = NewsAgency.objects.filter(news_website=news.news_site)
    n_cat_agen = n_agen.filter(category=n_cat).first()
    print(n_cat_agen.news_website_categories)
    print(nn)
