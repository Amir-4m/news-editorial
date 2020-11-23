import requests
from bs4 import BeautifulSoup

from .models import News
from khayyam import JalaliDate

jalali_months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور", "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


# news_site_id=news_site_id,
#                                        defaults={"news_jalali_date": news_jalali_date,
#                                                  "news_category": news_category,
#                                                  "news_title": news_title,
#                                                  "news_site": "isna.ir",
#                                                  "news_main": "".join(news_main_text),
#                                                  "news_main_editable": "".join(news_main_text),
#                                                  "news_summary": str(news_summary),
#                                                  "news_date": news_date,
#                                                  "news_image": news_image


# @receiver(signals.pre_save, sender=News)
# def raw_news(sender, instance, **kwargs):
#     old_news_main = News.objects.get(id=instance.id).news_main_editable
#
#     number_of_changes = 0
#     for s in difflib.ndiff(old_news_main, instance.news_main_editable):
#         if s[0] == "+" or s[0] == "-":
#             number_of_changes += 1
#
#     if number_of_changes > 0:
#         instance.number_of_changes = number_of_changes


def collect_tasnim_news():
    url = "https://www.tasnimnews.com/fa/news/1399/07/08/2359191/%D9%88%D8%B2%D8%A7%D8%B1%D8%AA-%D8%A7%D9%85%D9%88%D8%B1-%D8%AE%D8%A7%D8%B1%D8%AC%D9%87-%D8%AA%D8%B1%D8%A7%D9%86%D8%B2%DB%8C%D8%AA-%D8%AA%D8%B3%D9%84%DB%8C%D8%AD%D8%A7%D8%AA-%D8%A7%D8%B2-%D8%AE%D8%A7%DA%A9-%D8%A7%DB%8C%D8%B1%D8%A7%D9%86-%D8%A8%D9%87-%D8%A7%D8%B1%D9%85%D9%86%D8%B3%D8%AA%D8%A7%D9%86-%D8%B1%D8%A7-%D8%B1%D8%AF-%DA%A9%D8%B1%D8%AF"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    jalali_date = soup.find("li", class_="time").get_text()
    # print(jalali_date)

    jalali_date_details = jalali_date.split("-")
    jalali_date_details = jalali_date_details[0].strip().split(" ")
    # print(jalali_date_details)
    news_date = JalaliDate(int(jalali_date_details[2]),
                           jalali_months.index(jalali_date_details[1]) + 1,
                           int(jalali_date_details[0])).todate()

    # print(news_date)

    news_category_list = soup.find_all("li", class_="service")
    news_category = ""
    for li in news_category_list:
        news_category += li.get_text()

    # print(news_category)

    news_title = soup.find("h1", class_="title").get_text()
    # print(news_title)

    news_main_list = soup.find("div", class_="story").find_all("p")
    news_main = ""
    for p in news_main_list:
        if "</a>" not in str(p):
            news_main += str(p)

    # print(news_main)

    news_summary = soup.find("h3", class_="lead")
    # print(news_summary)

    news_image = soup.find("img", class_="img-responsive").attrs['src']
    print(news_image)


def collect_sputnik_news():
    url = "https://ir.sputniknews.com/near_east/202009296979453-%D8%A8%D8%A7%D8%B2%D8%AF%D8%A7%D8%B4%D8%AA-%D9%85%D8%B8%D9%86%D9%88%D9%86%DB%8C%D9%86-%D8%B9%D9%85%D9%84%DB%8C%D8%A7%D8%AA-%D8%AA%D8%B1%D9%88%D8%B1%DB%8C%D8%B3%D8%AA%DB%8C-%D8%AF%D8%B1-%D8%B9%D8%B1%D8%A8%D8%B3%D8%AA%D8%A7%D9%86"
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    news_category = soup.find("a", class_="b-article__refs-rubric").get_text()
    # print(news_category)

    news_title = soup.find("div", class_="b-article__header-title").find("h1").get_text()
    # print(news_title)

    news_main_list = soup.find("div", class_="b-article__text").find_all("p")

    news_main = str()
    for p in news_main_list:
        news_main += str(p)
    # print(news_main)

    news_summary = soup.find("div", class_="b-article__lead").find("p")
    # print(news_summary)

    news_image = soup.find("div", class_="b-article__header").find("img").attrs["src"]
    print(news_image)


def collect_yjc_news():
    url = "https://www.yjc.ir/fa/news/7514208/%D8%A2%D8%BA%D8%A7%D8%B2-%D8%AF%D9%88%D8%B1-%D8%AF%D9%88%D9%85-%D8%AB" \
          "%D8%A8%D8%AA-%D9%86%D8%A7%D9%85-%D9%88%D8%A7%D9%85-%D9%88%D8%AF%DB%8C%D8%B9%D9%87-%D9%85%D8%B3%DA%A9%D9%86" \
          "-%D8%AA%D8%A7-%D8%B3%D8%A7%D8%B9%D8%A7%D8%AA%DB%8C-%D8%AF%DB%8C%DA%AF%D8%B1 "
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")

    news_site_id = int(soup.find("div", class_="news_nav news_id_c").get_text().strip().split(' ')[-1])
    # print(news_site_id)

    news_jalali_date = soup.find("div", class_="news_nav news_pdate_c").get_text().split("-")[0].split(":")[1].strip()
    # print(news_jalali_date)

    news_category = soup.find("div", class_="news_path").find("a").get_text().strip()
    # print(news_category)

    news_title = soup.find("div", class_="title").find("a").get_text().strip()
    # print(news_title)

    news_main_list = soup.find("div", class_="body").find_all("p")

    news_main = str()
    for p in news_main_list:
        news_main += str(p)

    # print(news_main)

    news_summary = soup.find("h2", class_="Htags_news_subtitle").get_text().strip()
    # print(news_summary)

    news_date_list = news_jalali_date.split(" ")
    news_date = JalaliDate(int(news_date_list[2]), jalali_months.index(news_date_list[1]) + 1, int(news_date_list[0]))\
        .todate()
    # print(news_date)

    news_image = soup.find("div", class_="body").find("img").attrs["src"]
    # print(news_image)
