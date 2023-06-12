from django import forms
import pandas as pd
from django.core.exceptions import ValidationError
import re

class UploadFileFormRu(forms.Form):
    file = forms.FileField(label="Загрузите файл с данными опроса студентов:", required=True)
    auto_clusters_num = forms.BooleanField(required=False, label='Автоматический выбор количества траекторий')
    clusters_num = forms.IntegerField(required=False, label='Желаемое количество образовательных траекторий')

    def order_fields(self, field_order):
        # Set the order of fields so that my_checkbox_field is validated first
        return ['file', 'auto_clusters_num', 'clusters_num']

    def clean_file(self):
        try:
            df = pd.read_excel(self.cleaned_data['file'].temporary_file_path(), header=[0,1])
        except:
            raise ValidationError("Требуемый формат файла .xlsx")
        return df

    def clean_clusters_num(self):
        if not self.cleaned_data['auto_clusters_num'] and not self.cleaned_data.get('clusters_num'):
            raise forms.ValidationError("Пожалуйста либо введите количество траекторий, либо отметьте автоматический выбор")
        return self.cleaned_data['clusters_num']
    

class UploadFileFormEn(forms.Form):
    file = forms.FileField(label="Upload the student survey data file:", required=True)
    auto_clusters_num = forms.BooleanField(required=False, label='Automatic selection of the number of trajectories')
    clusters_num = forms.IntegerField(required=False, label='Desired number of educational trajectories')

    def order_fields(self, field_order):
        # Set the order of fields so that my_checkbox_field is validated first
        return ['file', 'auto_clusters_num', 'clusters_num']

    def clean_file(self):
        try:
            df = pd.read_excel(self.cleaned_data['file'].temporary_file_path(), header=[0,1])
        except:
            raise ValidationError("Required file format .xlsx")
        return df

    def clean_clusters_num(self):
        if not self.cleaned_data['auto_clusters_num'] and not self.cleaned_data.get('clusters_num'):
            raise forms.ValidationError("Please either enter the number of trajectories or check the automatic selection")
        return self.cleaned_data['clusters_num']


class ParamsCriteriaFormRu(forms.Form):
    ext_params = forms.CharField(label='Перечислите состояния внешней среды', max_length=250)
    criteria = forms.CharField(label='Перечислите критерии оценки траекторий', max_length=250)

    def clean_ext_params(self):
        text = self.cleaned_data['ext_params']
        text = text.replace(',', ', ')
        text = re.sub(' +', ' ', text)
        return text

    def clean_criteria(self):
        text = self.cleaned_data['criteria']
        text = text.replace(',', ', ')
        text = re.sub(' +', ' ', text)
        return text
    

class ParamsCriteriaFormEn(forms.Form):
    ext_params = forms.CharField(label='List the states of the external environment', max_length=250)
    criteria = forms.CharField(label='List the criteria for evaluating trajectories', max_length=250)

    def clean_ext_params(self):
        text = self.cleaned_data['ext_params']
        text = text.replace(',', ', ')
        text = re.sub(' +', ' ', text)
        return text

    def clean_criteria(self):
        text = self.cleaned_data['criteria']
        text = text.replace(',', ', ')
        text = re.sub(' +', ' ', text)
        return text


class ParamAssessmentFormRu(forms.Form):
    assessment_choices = [
        # ('9', 'принципиально хуже'),
        # ('7', 'значительно хуже'),
        # ('5', 'хуже'),
        # ('3', 'немного хуже'),
        # ('1', 'равна'),
        # ('1/3', 'немного лучше'),
        # ('1/5', 'лучше'),
        # ('1/7', 'значительно лучше'),
        # ('1/9', 'принципиально лучше')
        ('9', 'принципиально лучше'),
        ('7', 'значительно лучше'),
        ('5', 'лучше'),
        ('3', 'немного лучше'),
        ('1', 'равна'),
        ('1/3', 'немного хуже'),
        ('1/5', 'хуже'),
        ('1/7', 'значительно хуже'),
        ('1/9', 'принципиально хуже')
    ]
    assessment_field = forms.ChoiceField(choices=assessment_choices)


class ParamAssessmentFormEn(forms.Form):
    assessment_choices = [
        # ('9', 'принципиально хуже'),
        # ('7', 'значительно хуже'),
        # ('5', 'хуже'),
        # ('3', 'немного хуже'),
        # ('1', 'равна'),
        # ('1/3', 'немного лучше'),
        # ('1/5', 'лучше'),
        # ('1/7', 'значительно лучше'),
        # ('1/9', 'принципиально лучше')
        ('9', 'fundamentally better'),
        ('7', 'much better'),
        ('5', 'better'),
        ('3', 'a little better'),
        ('1', 'equals'),
        ('1/3', 'a little worse'),
        ('1/5', 'worse'),
        ('1/7', 'much worse'),
        ('1/9', 'fundamentally worse')
    ]
    assessment_field = forms.ChoiceField(choices=assessment_choices)