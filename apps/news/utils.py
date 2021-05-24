import json
import random
import os
import difflib
from importlib import import_module
import logging

from django.conf import settings
from django.utils import timezone
from django.core.cache import cache

import requests
from requests.auth import HTTPBasicAuth


logger = logging.getLogger(__file__)


def CrawlerDynamically(class_name):
    """
    Args:
        class_name: 'capitalize of class_name value that equal to web site news name' + 'Crawler class name'
        to get it from "news.crawler"
    Returns: Crawler Class
    """
    module = import_module('apps.news.crawler')
    return getattr(module, f'{class_name.upper()}Crawler')


class WordPressHandler:
    token_cache_key = 'wordpress_auth_token'
    base_url = 'https://www.chapar.news/wp-json/'
    urls = {
        'token': 'jwt-auth/v1/token',
        'validate-token': 'jwt-auth/v1/token/validate',
        'post': f'wp/v2/posts/',
        'media': f'wp/v2/media/'
    }

    def __init__(self, instance):
        """
        Args:
            instance: Instance is News object.
        """
        self.instance = instance
        self.token = cache.get(self.token_cache_key) or self.get_token()
        self.validate_token()

    # def get_headers(self):
    # return dict(Authorization=f"Bearer {settings.WORDPRESS_TOKEN}")
    # return dict(Authorization="Basic %s" % b64encode('m.rezaei:09VqT4X1dxJOwB'))

    def get_token(self):
        logger.debug(f"[getting new token]-[URL: {self.urls['token']}]")
        req = self.post_request(
            self.urls['token'],
            auth=False,
            json=dict(username=settings.WP_USER, password=settings.WP_PASS),
        )

        if req.ok:
            token = req.json()['data']['token']
            logger.debug(f'[new token successfully added]-[token: {token}]')
            cache.set(self.token_cache_key, token, 604800)  # 7 days default expire time
            return token
        else:
            logger.critical(f'[Getting token failed]-[]')

    def validate_token(self):
        logger.debug(f"[validating the JWT Token]-[URL: {self.urls['validate-token']}]")
        req = self.post_request(
            self.urls['validate-token'],
            auth=True,
        )
        if req.ok:
            logger.debug(f'[Token is valid]')
        else:
            logger.debug(f'[JWT Token of WP is not valid or expired]')
            self.token = self.get_token()

    def post_request(self, url, method='post', headers={}, auth=True, **kwargs):
        if auth:
            headers.update({'Authorization': f"Bearer {self.token}"})

        if headers:
            kwargs.update({'headers': headers})
        return requests.request(
            method,
            f"{self.base_url + url}",
            # auth=HTTPBasicAuth(settings.WP_USER, settings.WP_PASS),
            **kwargs
        )

    def create_post(self):
        """
        Create a new Post to Wordpress from News object.
        Returns: None
        """
        media_id = self.create_media()  # Create media for this post
        categories = self.instance.category.all()
        payload_data = dict(
            title=self.instance.news_title,
            content=self.instance.news_main_editable,
            slug=self.instance.news_title,
            excerpt=self.instance.news_summary,
            author=getattr(self.instance, 'editor_id', 9),
            publicize=False,  # True or false if the post be publicized to external services.
            status='draft',  # publish, private, draft, pending, future, auto-draft
            sticky=False,  # False: (default) Post is not marked as sticky.
            password='',
            format='standard',
            categories=[cat.word_press_id for cat in categories],
            featured_media=media_id,
        )
        req = self.post_request(self.urls['post'], json=payload_data, headers={'Content-Type': 'application/json'})
        if req.ok:
            from apps.news.models import News

            self.instance.wp_post_id = req.json()['id']
            self.instance._b_status = News.STATUS_APPROVED
            self.instance.save()

    def create_media(self):
        """
        Create a new Media object in Wordpress site to assign it to Wordpress Post.

        Returns: media's id of uploaded image to wordpress site
        """
        file_name = self.instance.news_image.name.split('/')[-1]
        payload_data = dict(status='draft')
        req = self.post_request(
            self.urls['media'],
            data={'file': file_name, 'data': json.dumps(payload_data)},
            files={'file': (
                file_name,
                open(self.instance.news_image.path, 'rb'),
                f'image/{file_name.split(".")[-1]}',
                {'Expires': '0'}
            )},
        )
        if req.ok:
            return req.json()['id']

    def update_news_from_post(self):
        from .models import News
        req = self.post_request(f"{self.urls['post'] + self.instance.wp_post_id}",
                                headers={'Content-Type': 'application/json'})
        if req.ok:
            changes = 0
            for s in difflib.ndiff(self.instance.news_main, req.json()['content']['raw']):
                if s[0] == "+" or s[0] == "-":
                    changes += 1

            self.instance.number_of_changes = changes
            self.instance.news_main_editable = req.json()['content']['raw']
            if req.json()['status'] == 'publish':
                self.instance.status = News.STATUS_PUBLISHED
            self.instance.save(update_fields=['updated_time', 'number_of_changes', 'news_main_editable', 'status'])


class UploadTo:
    def __init__(self, name):
        self.name = name

    def __call__(self, instance, filename):
        base_filename, file_extension, random_str = self.generate_name(filename)
        return f'images/{instance.__class__.__name__}/{instance.news_site}/{timezone.now().strftime("%y-%m-%d")}/' \
               f'{base_filename}_{random_str}{file_extension}'

    def random_string_generator(self, number, string=True):
        chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        nums = '1234567890'
        return ''.join((random.choice(chars + str(nums) if string else nums)) for x in range(number))

    def generate_name(self, filename):
        base_filename, file_extension = os.path.splitext(filename)
        return base_filename, file_extension, self.random_string_generator(3)

    def deconstruct(self):
        return 'apps.news.utils.UploadTo', [self.name], {}
