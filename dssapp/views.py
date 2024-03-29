from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .forms import UploadFileFormRu, UploadFileFormEn, ParamAssessmentFormRu, ParamAssessmentFormEn
from django.forms import formset_factory
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import copy
from itertools import combinations
from sklearn.metrics import calinski_harabasz_score, silhouette_score
from django.utils import translation
# Create your views here.

# clusters_number = 3 # or 'auto'
questions_ru = ['Вид источников для самостоятельного изучения', 'Способ организации учебного процесса', \
             'Численность учебной группы', 'Технология преподнесения материалов', 'Способ проверки знаний', \
             'Темп подачи материала', 'Форма обучения']

questions_en = ['Course materials reception method', 'Types of classes', \
             'Number of students in the study group', 'The way the learner perceives the learning material', 'Arranging knowledge control', \
             'Training speed', 'The sequence of subjects and the number of simultaneously studied subjects']

def upload_file(request):
    lang = translation.get_language()
    if request.method == 'POST':
        if lang == "ru":
            form = UploadFileFormRu(request.POST, request.FILES)
        elif lang == "en":
            form = UploadFileFormEn(request.POST, request.FILES)
        if form.is_valid():
            # df = pd.read_excel(request.FILES['file'].temporary_file_path(), header=[0,1])
            ext_param_fields = [value for key, value in request.POST.items() if key.startswith('ext_param_field')]
            probs_fields = [float(value) for key, value in request.POST.items() if key.startswith('prob_field')]
            disable_probabilities = 'disable_probabilities' in request.POST
            criteria_fields = [value for key, value in request.POST.items() if key.startswith('criterion_field')]
            request.session['ext_params'] = ext_param_fields
            request.session['ext_params_probs'] = probs_fields
            request.session['ext_params_probs_flag'] = not disable_probabilities
            request.session['criteria'] = criteria_fields
            # print(ext_param_fields)
            # print(probs_fields)
            # print(disable_probabilities)
            # print(criteria_fields)
            df = form.cleaned_data['file']
            if form.cleaned_data['auto_clusters_num']:
                request.session['clusters_num'] = 'auto'
            else:
                request.session['clusters_num'] = form.cleaned_data['clusters_num']
            trajectories, clusters_num = clusterization(request, df)
            request.session['clusters_num'] = str(clusters_num)
            new_trajectories = {}
            trajectories_for_table = {}
            for key, trajectory in trajectories.items():
                new_trajectory = {}
                new_trajectory_for_table = {}
                for questiond_idx, answers in trajectory.items():
                    # trajectory[int(questiond_idx)] = f'- {questions[int(questiond_idx)-1]}: {answer}'
                    if lang == "ru":
                        answer = ' И/ИЛИ '.join([x[2:] for x in answers])
                        new_trajectory[questiond_idx] = f'- {questions_ru[int(questiond_idx)-1]}: {answer}'
                        new_trajectory_for_table[questions_ru[int(questiond_idx)-1]] = answer
                    elif lang == "en":
                        answer = ' AND/OR '.join([x[2:] for x in answers])
                        new_trajectory[questiond_idx] = f'- {questions_en[int(questiond_idx)-1]}: {answer}'
                        new_trajectory_for_table[questions_en[int(questiond_idx)-1]] = answer
                new_trajectories[key] = copy.deepcopy(new_trajectory)
                trajectories_for_table[key] = copy.deepcopy(new_trajectory_for_table)
            request.session['trajectories'] = new_trajectories
            request.session['trajectories_for_table'] = trajectories_for_table
            return redirect('assessment')
            # return redirect('fill_params')
    else:
        if lang == "ru":
            form = UploadFileFormRu()
        elif lang == "en":
            form = UploadFileFormEn()
    if lang == "ru":
        return render(request, 'ru/upload.html', {'form': form})
    elif lang == "en":
        return render(request, 'en/upload.html', {'form': form})


# def fill_params(request):
#     trajectories = request.session['trajectories']
#     trajectories_for_table = request.session['trajectories_for_table']
#     if request.method == 'POST':
#         form = ParamsCriteriaForm(request.POST)
#         if form.is_valid():
#             ext_params = form.cleaned_data['ext_params']
#             ext_params = ext_params.split(', ')
#             # print(ext_params_num, ext_params)
#             request.session['ext_params'] = ext_params
#             criteria = form.cleaned_data['criteria']
#             criteria = criteria.split(', ')
#             # print(criteria_num, criteria)
#             request.session['criteria'] = criteria
#             return redirect('assessment')
#     else:
#         form = ParamsCriteriaForm()
#     print(trajectories)
#     print(trajectories_for_table)
#     if lang == "ru":
#         new_trajectory[questiond_idx] = f'- {questions_ru[int(questiond_idx)-1]}: {answer}'
#         new_trajectory_for_table[questions_ru[int(questiond_idx)-1]] = answer
#     elif lang == "en":
#         new_trajectory[questiond_idx] = f'- {questions_en[int(questiond_idx)-1]}: {answer}'
#         new_trajectory_for_table[questions_en[int(questiond_idx)-1]] = answer
#     return render(request, 'fill_params.html', {'trajectories': trajectories, 'trajectories_for_table': trajectories_for_table, 'questions': questions, 'form': form})


def assessment(request):
    lang = translation.get_language()
    trajectories = request.session['trajectories']
    trajectories_for_table = request.session['trajectories_for_table']
    ext_params = request.session['ext_params']
    criteria = request.session['criteria']
    # print(criteria)
    clusters_number = int(request.session['clusters_num'])
    ext_params_num = len(ext_params)
    criteria_num = len(criteria)
    clusters_forms_num = int(clusters_number * (clusters_number - 1) / 2)
    criteria_forms_num = int(criteria_num * (criteria_num - 1) / 2)
    param_forms_num = ext_params_num * criteria_num * clusters_forms_num
    forms_num = criteria_forms_num + param_forms_num
    if lang == "ru":
        ParamAssessmentSet = formset_factory(ParamAssessmentFormRu, extra=forms_num)
    elif lang == "en":
        ParamAssessmentSet = formset_factory(ParamAssessmentFormEn, extra=forms_num)
    if request.method == 'POST':
        formset = ParamAssessmentSet(request.POST, request.FILES)
        if formset.is_valid():
            form_counter = 0
            criteria_matrix = np.ones((criteria_num, criteria_num))
            params_dict = {}
            for i in range(criteria_num):
                for j in range(i + 1, criteria_num):
                    tmp_val = formset.cleaned_data[form_counter]['assessment_field']
                    # print(formset.cleaned_data[form_counter])
                    # print(tmp_val)
                    if tmp_val[0] == '1' and len(tmp_val) > 1:
                        tmp_val = int(tmp_val[-1])
                        criteria_matrix[i][j] = 1 / tmp_val
                        criteria_matrix[j][i] = tmp_val
                    else:
                        tmp_val = int(tmp_val)
                        criteria_matrix[i][j] = tmp_val
                        criteria_matrix[j][i] = 1 / tmp_val
                    form_counter += 1
            for ext_param in ext_params:
                params_dict[ext_param] = {}
                for criterion in criteria:
                    tmp_matrix = np.ones((clusters_number, clusters_number))
                    for i in range(clusters_number):
                        for j in range(i + 1, clusters_number):
                            tmp_val = formset.cleaned_data[form_counter]['assessment_field']
                            if tmp_val[0] == '1' and len(tmp_val) > 1:
                                tmp_val = int(tmp_val[-1])
                                tmp_matrix[i][j] = 1 / tmp_val
                                tmp_matrix[j][i] = tmp_val
                            else:
                                tmp_val = int(tmp_val)
                                tmp_matrix[i][j] = tmp_val
                                tmp_matrix[j][i] = 1 / tmp_val
                            form_counter += 1
                    params_dict[ext_param][criterion] = tmp_matrix
            # print(criteria_matrix)
            # print()
            # for param, criteries in params_dict.items():
            #     for criterion, criterion_matrix in criteries.items():
            #         print(criterion_matrix)
            criteria_weights = get_weights(criteria_matrix)
            params_weights_dict = {}
            for param, criteries in params_dict.items():
                tmp_list = []
                for criterion, criterion_matrix in criteries.items():
                    tmp_list.append(get_weights(criterion_matrix))
                alt_weights = np.array(tmp_list).T
                params_weights_dict[param] = alt_weights

            payoff_matrix = compute_payoff_matrix(params_weights_dict, criteria_weights)
            request.session['payoff_matrix'] = payoff_matrix.tolist()

            return redirect('result_trajectory')
    else:
        formset = ParamAssessmentSet()
        forms_context = []
        for combs in combinations(list(range(1, criteria_num+1)), 2):
            forms_context.append({'combs': {'0': combs[0], '1': combs[1]}})
        form_counter = 0
        prev_ext_param = ''
        prev_criterion = ''
        for ext_param in ext_params:
            for criterion in criteria:
                for combs in combinations(list(range(1, clusters_number+1)), 2):
                    tmp = {}
                    if prev_ext_param != ext_param:
                        tmp['print_ext_param'] = True
                        prev_ext_param = ext_param
                    else:
                        tmp['print_ext_param'] = False
                    if prev_criterion != criterion:
                        tmp['print_criterion'] = True
                        prev_criterion = criterion
                    else:
                        tmp['print_criterion'] = False
                    tmp['ext_param'] = ext_param
                    tmp['criterion'] = criterion
                    tmp['combs'] = {'0': combs[0], '1': combs[1]}
                    forms_context.append(tmp)
                    form_counter += 1
    # print(trajectories_for_table)
    if lang == "ru":
        return render(request, 'ru/assessment.html', {
            'trajectories': trajectories,
            'trajectories_for_table': trajectories_for_table,
            'questions': questions_ru, 
            'criteria_forms_num': criteria_forms_num,
            'forms_context': forms_context,
            'formset': formset,
            'criteria': criteria,
        })
    elif lang == "en":
        return render(request, 'en/assessment.html', {
            'trajectories': trajectories,
            'trajectories_for_table': trajectories_for_table,
            'questions': questions_en, 
            'criteria_forms_num': criteria_forms_num,
            'forms_context': forms_context,
            'formset': formset,
            'criteria': criteria,
        })


# def final_trajectory(request):
#     trajectories = request.session['trajectories']
#     payoff_matrix = np.array(request.session['payoff_matrix'])
#     payoff_criteria = {
#         'Лаплас': laplace,
#         'Вальд': wald,
#     }
#     best_trajectories = {}
#     for key, value in payoff_criteria:
#         best_trajectories[key] = value(payoff_matrix)
#     return render(request, 'final_trajectory.html', {
#         'trajectories': trajectories,
#         'best_trajectories': best_trajectories,
#         'criteria_forms_num': criteria_forms_num,
#         'forms_context': forms_context,
#         'formset': formset,
#     })

def result_trajectory(request):
    lang = translation.get_language()
    trajectories = request.session['trajectories']
    trajectories_for_table = request.session['trajectories_for_table']
    probs_flag = request.session['ext_params_probs_flag']
    if probs_flag:
        probs = request.session['ext_params_probs']
        probs = np.array(probs)
    payoff_matrix = np.array(request.session['payoff_matrix'])
    if lang == "ru":
        payoff_criteria = {
            'Лапласа': laplace,
            'Вальда': wald,
            'крайнего оптимизма': optimist,
            'крайнего пессимизма': pessimist,
            'Гурвица': hurwitz,
            'Сэвиджа': savage,
            'произведений': multiplication,
            'Байеса': bayes,
            'Гермейера': germeier,
            'Ходжа-Лемана': hodge_lehmann,
            'Гермейера-Гурвица': germeier_hurwitz,
        }
        methods_with_probs = set(['Байеса', 'Гермейера', 'Ходжа-Лемана', 'Гермейера-Гурвица'])
    elif lang == "en":
        payoff_criteria = {
            'Laplace': laplace,
            'Wald': wald,
            'extreme optimism': optimist,
            'extreme pessimism': pessimist,
            'Hurwitz': hurwitz,
            'Savage': savage,
            'multiplication': multiplication,
            'Bayes': bayes,
            'Germeier': germeier,
            'Hodge-Lehman': hodge_lehmann,
            'Germeier-Hurwitz': germeier_hurwitz,
        }
        methods_with_probs = set(['Bayes', 'Germeier', 'Hodge-Lehman', 'Germeier-Hurwitz'])
    best_trajectories = {}
    # for key, value in payoff_criteria.items():
    #     best_trajectories[key] = {'idx': value(payoff_matrix), 'data': trajectories[str(value(payoff_matrix))]}
    # print(probs_flag)
    for key, value in payoff_criteria.items():
        if key in methods_with_probs and probs_flag:
            best_trajectories[key] = {'idx': value(payoff_matrix, probs), 'data': trajectories_for_table[str(value(payoff_matrix, probs))]}
        elif key not in methods_with_probs:
            best_trajectories[key] = {'idx': value(payoff_matrix), 'data': trajectories_for_table[str(value(payoff_matrix))]}
    if lang == "ru":
        return render(request, 'ru/final_trajectory.html', {
            'trajectories': trajectories,
            'best_trajectories': best_trajectories,
        })
    elif lang == "en":
        return render(request, 'en/final_trajectory.html', {
            'trajectories': trajectories,
            'best_trajectories': best_trajectories,
        })


def clusterization(request, df):
    new_columns = ['No', 'ID', 'User', 'IP', 'Date', 'Course', 'Group']
    question_num_set = set()
    for column_tuple in list(df.columns):
        if 'Вопрос' in column_tuple[0]:
            question_num_set.add(column_tuple[0][-1])
            new_columns.append(f'{column_tuple[0][-1]}_{column_tuple[1]}')
    df.set_axis(new_columns, axis=1, inplace=True)
    df.drop(['No', 'ID', 'User', 'IP', 'Date', 'Course', 'Group'], axis=1, inplace=True)
    question_number = len(question_num_set)
    clusters_number = request.session['clusters_num']

    if clusters_number == 'auto':
        search_range = range(2, 11)
        report = {}
        for k in search_range:
            temp_dict = {}
            kmeans = KMeans(init='k-means++',
                            algorithm='auto',
                            n_clusters=k,
                            max_iter=1000,
                        random_state=1).fit(df)
            inertia = kmeans.inertia_
            temp_dict['Sum of squared error'] = inertia
            try:
                cluster = kmeans.predict(df)
                chs = calinski_harabasz_score(df, cluster)
                ss = silhouette_score(df, cluster)
                temp_dict['Calinski Harabasz Score'] = chs
                temp_dict['Silhouette Score'] = ss
                report[k] = temp_dict
            except:
                report[k] = temp_dict
        
        chs = [-10, -10]
        ss = [-10, -10]
        for i in range(2, len(report)):
            chs.append(report[i]['Calinski Harabasz Score'])
            ss.append(report[i]['Silhouette Score'])
        chs = np.array(chs)
        ss = np.array(ss)
        clusters_number = (np.argmax(chs) + np.argmax(ss)) // 2

    kmeans = KMeans(init='k-means++',
                    algorithm='auto',
                    n_clusters=clusters_number,
                    max_iter=1000,
                   random_state=1).fit(df)

    cluster = kmeans.predict(df)

    centroids = pd.DataFrame(kmeans.cluster_centers_, columns=list(df.columns))
    centroids_dict = centroids.to_dict(orient='records')

    trajectories = {}
    threshold = 0.2
    for i in range(centroids.shape[0]):
        prev_question_index = 1
        trajectories[i+1] = {}
        for j in range(1, question_number+1):
            sub_dict = {}
            for key, value in centroids_dict[i].items():
                if f'{j}_' in key:
                    sub_dict[key] = value
            best_names = [max(sub_dict, key=sub_dict.get)]
            best_val = max(sub_dict.values())
            for key, value in sub_dict.items():
                if (best_val - value) <= threshold and key not in best_names:
                    best_names.append(key)
            trajectories[i+1][j] = best_names

    return trajectories, clusters_number


def get_weights(matrix):
    return (matrix / matrix.sum(axis=0)).mean(axis=1)


def compute_payoff_matrix(params_weights_dict, criteria_weights):
    payoff_matrix = []
    for param, weight_matrix in params_weights_dict.items():
        payoff_matrix.append(weight_matrix @ criteria_weights.T)
    payoff_matrix = np.array(payoff_matrix).T
    return payoff_matrix


def laplace(matrix):
    '''
    Критерий Лапласа. Находит максимум средних по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс строки, в которой максимальное среднее
    '''
    best_path = np.argmax(matrix.mean(axis=1))
    return best_path + 1


def wald(matrix):
    '''
    Критерий Вальда. Находит максимум минимумов по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс строки, в которой максимальный минимум
    '''
    best_path = np.argmax(matrix.min(axis=1))
    return best_path + 1


def optimist(matrix):
    '''
    Критерий максимакса или оптимизма. Находит максимум максимумов по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс строки, в которой максимальный минимум
    '''
    best_path = np.argmax(matrix.max(axis=1))
    return best_path + 1


def pessimist(matrix):
    '''
    Критерий пессимизма. Находит минимум минимумов по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс выбранной строки
    '''
    best_path = np.argmin(matrix.min(axis=1))
    return best_path + 1



def hurwitz(matrix, alpha=0.5):
    '''
    Критерий Вальда. Находит максимум минимумов по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами
                    alpha: Коэффициент α принимает значения от 0 до 1. Если α стремится к 1, то критерий Гурвица приближается к критерию Вальда,
                                а при α стремящемуся к 0, то критерий Гурвица приближается к критерию максимакса. По умолчанию равен 0.5

            Returns:
                    best_path: индекс строки, в которой максимальный минимум
    '''
    maxs = matrix.max(axis=1)
    mins = matrix.min(axis=1)
    best_path = np.argmax(alpha*maxs + (1-alpha)*mins)
    return best_path + 1


def savage(matrix):
    '''
    Критерий Сэвиджа или минимакса (критерий потерь). Строит матрицу потерь, в матрице потерь находит минимум максимумов по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс строки, в которой максимальный минимум
    '''
    loss_matrix = matrix.max(axis=0) - matrix
    best_path = np.argmin(loss_matrix.max(axis=1))
    return best_path + 1


def multiplication(matrix):
    '''
    Критерий произведений. Находит максимум произведений по строкам и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами

            Returns:
                    best_path: индекс выбранной строки
    '''
    best_path = np.argmax(np.prod(matrix, axis=1))
    return best_path + 1

def bayes(matrix, probs): ### Можно использовать, если есть веса внешних состояний
    '''
    Критерий Байеса или среднего выигрыша. Находит максимум взвешенных сумм коэффициентов и возвращает индекс соответствующей строки.

            Parameters:
                    matrix: платежная матрица с коэффициентами
                    probs: массив с весами внешних состояний

            Returns:
                    best_path: индекс выбранной строки
    '''
    best_path = np.argmax((matrix * probs).sum(axis=1))
    return best_path + 1

def germeier(matrix, probs): ### Можно использовать, если есть веса внешних состояний
    '''
    Критерий Гермейера.

            Parameters:
                    matrix: платежная матрица с коэффициентами
                    probs: массив с весами внешних состояний

            Returns:
                    best_path: индекс выбранной строки
    '''
    best_path = np.argmax((matrix * probs).min(axis=1))
    return best_path + 1

def hodge_lehmann(matrix, probs, alpha=0.5): ### Можно использовать, если есть веса внешних состояний
    '''
    Критерий Ходжа-Лемана.

            Parameters:
                    matrix: платежная матрица с коэффициентами
                    probs: массив с весами внешних состояний
                    alpha: Коэффициент α принимает значения от 0 до 1. Если α стремится к 1, то критерий Ходжа-Лемана приближается к критерию Байеса,
                                а при α стремящемуся к 0, то критерий Ходжа-Лемана приближается к критерию Вальда. По умолчанию равен 0.5

            Returns:
                    best_path: индекс выбранной строки
    '''

    best_path = np.argmax(alpha * (matrix * probs).sum(axis=1) + (1-alpha) * matrix.min(axis=1))
    return best_path + 1

def germeier_hurwitz(matrix, probs, alpha=0.5): ### Можно использовать, если есть веса внешних состояний
    '''
    Критерий Гермейера-Гурвица.

            Parameters:
                    matrix: платежная матрица с коэффициентами
                    probs: массив с весами внешних состояний
                    alpha: Коэффициент α принимает значения от 0 до 1. По умолчанию равен 0.5

            Returns:
                    best_path: индекс выбранной строки
    '''

    matrix_with_probs = matrix * probs
    best_path = np.argmax(alpha * matrix_with_probs.max(axis=1) + (1-alpha) * matrix_with_probs.min(axis=1))
    return best_path + 1
