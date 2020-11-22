from ckeditor.widgets import CKEditorWidget
from django import forms
from django.contrib.auth.models import Group

from .models import Category, News


class AssignEditor(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    editor = forms.ModelChoiceField(Group.objects.get(name="editors").user_set.all())


class AssignCategory(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    category = forms.ModelChoiceField(Category.objects.all())


class NewsForm(forms.ModelForm):
    news_main_editable = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = News
        fields = '__all__'


