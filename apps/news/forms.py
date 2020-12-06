from django import forms
from django.contrib.auth import get_user_model

from ckeditor.widgets import CKEditorWidget


from .models import Category, News


class AssignEditor(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    editor = forms.ModelChoiceField(queryset=get_user_model().objects.filter(groups__name='editors'))


class AssignCategory(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    category = forms.ModelChoiceField(Category.objects.all())


class NewsForm(forms.ModelForm):
    news_title = forms.CharField(widget=forms.TextInput(attrs={'dir': 'rtl', 'size': 120}))
    news_summary = forms.CharField(widget=forms.Textarea(attrs={'dir': 'rtl'}))
    news_main_editable = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = News
        fields = '__all__'


