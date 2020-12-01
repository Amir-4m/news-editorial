from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from .utils import UploadTo


class News(models.Model):
    STATUS_VOID = "void"
    STATUS_JUNK = "junk"
    STATUS_EDITABLE = "editable"
    STATUS_ASSIGNED = "assigned"
    STATUS_EDITED = "edited"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_WORTHLESS = "worthless"
    STATUS_PUBLISHED = "published"

    STATUS = ((STATUS_VOID, _("Void")),
              (STATUS_JUNK, _("Junk")),
              (STATUS_EDITABLE, _("Editable")),
              (STATUS_ASSIGNED, _("Assigned")),
              (STATUS_EDITED, _("Edited")),
              (STATUS_APPROVED, _("Approved")),
              (STATUS_REJECTED, _("Rejected")),
              (STATUS_WORTHLESS, _("Worthless")),
              (STATUS_PUBLISHED, _("Published")))

    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"

    PRIORITY = (
        (PRIORITY_LOW, _("Low")),
        (PRIORITY_MEDIUM, _("Medium")),
        (PRIORITY_HIGH, _("High"))
    )

    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    news_title = models.CharField(_("title"), max_length=1500)
    news_site = models.CharField(_("news site"), max_length=50)
    news_category = models.CharField(_("category"), max_length=50)
    news_site_id = models.BigIntegerField(_("site id"))
    news_summary = models.TextField(_("news summary"))
    news_main = models.TextField(_("news main content"), editable=False)
    news_main_editable = models.TextField(_("news main editable"))
    comment = models.TextField(_("Editorial Chief Comment"), null=True, blank=True)

    news_date = models.DateTimeField(_("news Date"))

    news_image = models.ImageField(_("news image"), upload_to=UploadTo('news_image'), blank=True)

    priority = models.CharField(_("priority"), choices=PRIORITY, default=PRIORITY_MEDIUM, max_length=100)
    status = models.CharField(_("status"), choices=STATUS, default=STATUS_VOID, max_length=100)
    number_of_changes = models.PositiveIntegerField(_("number of changes after editing"), null=True, blank=True)

    editor = models.ForeignKey(User, verbose_name=_("editor"), on_delete=models.CASCADE, related_name="news_editor",
                               blank=True, null=True, limit_choices_to={'groups__name': "editors"})

    category = models.ManyToManyField("Category", verbose_name=_("chapar category"), related_name="news", blank=True)

    wp_post_id = models.CharField(_('wordpress post id'), max_length=30, blank=True)
    direct_link = models.CharField(_('direct link'), max_length=1000, blank=True)

    class Meta:
        verbose_name = _('news')
        verbose_name_plural = _("news")

    def __str__(self):
        return self.news_title

    def get_image_url(self):
        if self.news_image:
            return settings.BASE_URL + self.news_image.url


class Category(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    title = models.CharField(_("title"), max_length=100)
    word_press_id = models.CharField(_('wordpress id '), max_length=5)

    class Meta:
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.title


class NewsSiteCategory(models.Model):
    site_category_name = models.CharField(_('category name'), max_length=50)
    news_url = models.CharField(_('news url'), max_length=300)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, verbose_name=_('category'))
    news_agency = models.ForeignKey('NewsAgency', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category} - {self.site_category_name}"


class NewsAgency(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    title = models.CharField(_('title'), max_length=50)
    slug = models.SlugField(_('slug'), unique=True)

    news_website = models.CharField(_("news website"), max_length=150)
    crawl_enable = models.BooleanField(_("crawl enable"), default=True)

    class Meta:
        verbose_name = _('news agency')
        verbose_name_plural = _("news agencies")

    def __str__(self):
        return self.news_website

