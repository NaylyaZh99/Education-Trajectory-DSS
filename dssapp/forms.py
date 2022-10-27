from django import forms
import pandas as pd
from django.core.exceptions import ValidationError
import re

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Загрузите файл с данными опроса студентов:", required=True)

    def clean_file(self):
        try:
            df = pd.read_excel(self.cleaned_data['file'].temporary_file_path(), header=[0,1])
        except:
            raise ValidationError("Требуемый формат файла .xlsx")
        return df


class ParamsCriteriaForm(forms.Form):
    ext_params = forms.CharField(label='Перечислите параметры внешней среды через запятую', max_length=250)
    criteria = forms.CharField(label='Перечислите критерии оценки траекторий через запятую', max_length=250)

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


class ParamAssessmentForm(forms.Form):
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