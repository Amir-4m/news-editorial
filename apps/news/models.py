from django.db import models
# from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

# from django_better_admin_arrayfield.models.fields import ArrayField
from django.contrib.postgres.fields import ArrayField


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
    news_title = models.CharField(_("News Title"), max_length=1500)
    news_site = models.CharField(_("News Website"), max_length=50)
    news_jalali_date = models.CharField(_("news Site Jalali Date"), max_length=50)
    news_category = models.CharField(_("News Website Category"), max_length=50)
    news_site_id = models.BigIntegerField(_("News Site Id"))
    news_summary = models.TextField(_("News Head"))
    news_main = models.TextField(_("News Main Content"), editable=False)
    news_main_editable = models.TextField(_("News Main Content"))
    comment = models.TextField(_("Editorial Chief Comment"), null=True, blank=True)
    news_date = models.DateField(_("News Date"))
    news_image = models.URLField(_("News Image"), max_length=1000)
    priority = models.CharField(_("Priority"), choices=PRIORITY, default=PRIORITY_MEDIUM, max_length=100)
    status = models.CharField(_("Status"), choices=STATUS, default=STATUS_VOID, max_length=100)
    number_of_changes = models.PositiveIntegerField(_("Number of Changes After Editing"), null=True, blank=True)

    editor = models.ForeignKey(User, verbose_name=_("Editor"), on_delete=models.CASCADE, related_name="news_editor",
                               blank=True, null=True, limit_choices_to={'groups__name': "editors"})

    category = models.ManyToManyField("Category", verbose_name=_("Chapar Category"), related_name="news", blank=True)

    class Meta:
        verbose_name_plural = _("News")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._b_status = self.status

    def __str__(self):
        return self.news_title


class Category(models.Model):
    created_time = models.DateTimeField(_('created time'), auto_now_add=True)
    updated_time = models.DateTimeField(_('updated time'), auto_now=True)

    title = models.CharField(_("title"), max_length=100)

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

    news_website = models.CharField(_("news Website"), max_length=150)
    crawl_enable = models.BooleanField(_("crawl enable"), default=True)

    class Meta:
        verbose_name = _('news agency')
        verbose_name_plural = _("news agencies")

    def __str__(self):
        return self.news_website

