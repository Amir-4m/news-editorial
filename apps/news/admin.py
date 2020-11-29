import difflib

from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.admin.mixins import DynamicArrayMixin

from .models import News, Category, NewsAgency, NewsSiteCategory
from .forms import AssignEditor, AssignCategory, NewsForm
from .tasks import collect_news_task


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    form = NewsForm
    radio_fields = {"status": admin.HORIZONTAL, "priority": admin.HORIZONTAL}

    def get_queryset(self, request):
        chief_group = User.objects.filter(groups__name="editors_chief")
        monitoring_group = User.objects.filter(groups__name="monitoring")

        if request.user.is_superuser or request.user in chief_group:
            return News.objects.all()
        elif request.user in monitoring_group:
            return News.objects.filter(status__in=["void", "junk", "editable"])
        return News.objects.filter(editor__exact=request.user).filter(status__in=["assigned", "rejected"])

    def changelist_view(self, request, extra_context=None):
        user_groups = [g.name for g in request.user.groups.all()]
        if 'editors' in user_groups:
            self.list_display = (
                "news_title", "status", "priority", "created_time", "news_site", "news_category", "chapar_category",
                "news_date",
            )
            self.fields = (
                "news_site", "news_date", "news_title", "news_summary", "news_main_editable", "comment", "status",
                "priority", "news_image"
            )
            self.list_filter = ("news_site", "news_date", "priority")
            self.readonly_fields = ("news_site", "status", "priority")
            self.change_form_template = "edit_form.html"
            self.actions = []

        elif 'monitoring' in user_groups:
            self.list_display = ("news_title", "status", "created_time", "news_site", "news_category",
                                 "chapar_category", "news_date")
            self.fields = ("news_site", "news_date", "news_summary", "news_main")
            self.readonly_fields = ("news_site", "news_date", "news_summary", "news_main", 'wp_post_id')
            self.list_filter = ("news_site", "news_date", "category",)
            self.actions = ["junk_status", "editable_status"]
            self.search_fields = ("news_category",)
            self.change_form_template = 'admin/change_form.html'

        elif request.user.is_superuser or 'chief' in user_groups:
            self.readonly_fields = ("news_site", "news_main", "number_of_changes")
            self.search_fields = ('news_site_id',)
            self.list_display = ("news_title", "status", "priority", "created_time", "news_site", "news_category",
                                 "chapar_category", "news_date", "editor", "news_site_id")
            self.list_filter = ("news_site", "news_date", 'priority', "editor", "status", "category", "news_category")

            self.actions = ["assign_editor", "assign_category"]
            self.change_form_template = 'admin/change_form.html'
        return super().changelist_view(request, extra_context)

    def chapar_category(self, obj):
        return "\n".join([c.title for c in obj.category.all()])

    def response_change(self, request, instance):
        editors = User.objects.filter(groups__name='editors')
        if request.user in editors:
            if "_edited" in request.POST:
                matching_names_except_this = self.get_queryset(request).filter(
                    news_title=instance.news_title
                ).exclude(pk=instance.id)

                matching_names_except_this.delete()
                instance.status = "edited"

                changes = 0
                for s in difflib.ndiff(instance.news_main, instance.news_main_editable):
                    if s[0] == "+" or s[0] == "-":
                        changes += 1

                instance.number_of_changes = changes
                instance.save()
                self.message_user(request, f"News {instance.news_title}has been Edited")
                return HttpResponseRedirect(reverse_lazy('admin:news_news_changelist'))
            return super().response_change(request, instance)
        else:
            return super().response_change(request, instance)

    # Custom Actions
    def assign_category(self, request, queryset):
        form = None
        if '_assign_category' in request.POST:
            form = AssignCategory(request.POST)
            if form.is_valid():
                category = form.cleaned_data["category"]
                for q in queryset:
                    if q.category is None:
                        news_agency = NewsAgency.objects.filter(news_website=q.news_site)
                        news_category_agency = news_agency.get(category=category)
                        news_website_categories = news_category_agency.news_website_categories
                        news_website_cat = q.news_category
                        if news_website_cat not in news_website_categories:
                            news_website_categories.append(news_website_cat)
                        news_category_agency.save()
                    q.category.add(category)
                    q.save()
                count = len(queryset)
                # for news_id in request.POST.getlist(admin.ACTION_CHECKBOX_NAME):
                #     news = News.objects.get(id=news_id)
                #     print(category.agencies.news_website_categories)
                #     if news.news_category not in category.agencies.news_website_categories:
                #         category.agencies.news_website_categories.append(news.news_category)
                #         print(category.agencies.news_website_categories)
                #         category.agencies.save()
                self.message_user(request, f"Successfully Assigned {count} News  to {category}.")
                return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = AssignCategory(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'assign_category_form.html', {'news': queryset, 'assign_category': form})
    assign_category.short_description = _("Assign a Category to News")

    def assign_editor(self, request, queryset):
        e_messages = []
        form = None
        if '_assign_editor' in request.POST:
            form = AssignEditor(request.POST)
            for news in queryset.iterator():
                if news.status != "editable" or news.status == "junk":
                    e_messages.append(_(
                        f"News with id = {news.id} Could not be Assigned to Editors ---> News Status is {news.status.upper()}'."))
                else:
                    if form.is_valid():
                        editor = form.cleaned_data['editor']
                        queryset.update(editor=editor)
                        queryset.update(status="assigned")
                        count = len(queryset)
                        self.message_user(request, f"Successfully Assigned {count} News  to {editor}.")
                        return HttpResponseRedirect(request.get_full_path())
        if not form:
            form = AssignEditor(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
        return render(request, 'assign_editor_form.html',
                      {'news': queryset, 'assign_editor': form, 'e_messages': e_messages})
    assign_editor.short_description = _("Assign News to an Editor")

    # Custom Fields
    def junk_status(self, request, queryset):
        queryset.update(status="junk")
    junk_status.short_description = _("Change the Status to Junk")

    def editable_status(self, request, queryset):
        queryset.update(status="editable")
    editable_status.short_description = _("Change the Status to Editable")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "word_press_id")


@admin.register(NewsAgency)
class NewsAgencyAdmin(admin.ModelAdmin, DynamicArrayMixin):
    change_form_template = "crawl_form.html"
    list_display = ("news_website",)

    def save_model(self, request, obj, form, change):
        if "_crawl" in request.POST:
            collect_news_task.apply_async(args=(obj.slug,))
            self.message_user(request, f"News from {obj.news_website} has been crawled")
            return HttpResponseRedirect(reverse_lazy('admin:news_news_changelist'))
        return super().save_model(request, obj, form, change)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    list_filter = ['user', 'content_type', 'action_flag']
    list_display = ['action_time', 'user', 'content_type', 'action_flag', 'change_message']


@admin.register(NewsSiteCategory)
class NewsSiteCategoryAdmin(admin.ModelAdmin):
    list_display = ('site_category_name', 'category', 'news_agency', 'news_url')
    list_filter = ('category', 'news_agency')
    list_editable = ('news_agency',)
