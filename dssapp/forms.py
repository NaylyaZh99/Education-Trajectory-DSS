from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField(label="Загрузите файл с данными опроса студентов:", required=True)


class ParamsCriteriaForm(forms.Form):
    ext_params = forms.CharField(label='Перечислите внешние параметры через запятую', max_length=250)
    criteria = forms.CharField(label='Перечислите критерии через запятую', max_length=250)


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