from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from .forms import UploadFileForm, ParamsCriteriaForm, ParamAssessmentForm
from django.forms import formset_factory
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
import copy
from itertools import combinations
# Create your views here.

clusters_number = 3 # or 'auto'
questions = ['Вид источников для самостоятельного изучения', 'Способ организации учебного процесса', \
             'Численность учебной группы', 'Технология преподнесения материалов', 'Способ проверки знаний', \
             'Темп подачи материала', 'Форма обучения']

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            df = pd.read_excel(request.FILES['file'].temporary_file_path(), header=[0,1])
            trajectories = clusterization(df)
            new_trajectories = {}
            for key, trajectory in trajectories.items():
                new_trajectory = {}
                for questiond_idx, answers in trajectory.items():
                    answer = ' И/ИЛИ '.join([x[2:] for x in answers])
                    # trajectory[int(questiond_idx)] = f'- {questions[int(questiond_idx)-1]}: {answer}'
                    new_trajectory[questiond_idx] = f'- {questions[int(questiond_idx)-1]}: {answer}'
                new_trajectories[key] = copy.deepcopy(new_trajectory)
            request.session['trajectories'] = new_trajectories
            return redirect('fill_params')
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})


def fill_params(request):
    trajectories = request.session['trajectories']
    if request.method == 'POST':
        form = ParamsCriteriaForm(request.POST)
        if form.is_valid():
            ext_params = form.cleaned_data['ext_params']
            ext_params = ext_params.split(', ')
            # print(ext_params_num, ext_params)
            request.session['ext_params'] = ext_params
            criteria = form.cleaned_data['criteria']
            criteria = criteria.split(', ')
            # print(criteria_num, criteria)
            request.session['criteria'] = criteria
            return redirect('assessment')
    else:
        form = ParamsCriteriaForm()
    return render(request, 'fill_params.html', {'trajectories': trajectories, 'questions': questions, 'form': form})


def assessment(request):
    trajectories = request.session['trajectories']
    ext_params = request.session['ext_params']
    criteria = request.session['criteria']
    # print(criteria)
    ext_params_num = len(ext_params)
    criteria_num = len(criteria)
    clusters_forms_num = int(clusters_number * (clusters_number - 1) / 2)
    criteria_forms_num = int(criteria_num * (criteria_num - 1) / 2)
    param_forms_num = ext_params_num * criteria_num * clusters_forms_num
    forms_num = criteria_forms_num + param_forms_num
    ParamAssessmentSet = formset_factory(ParamAssessmentForm, extra=forms_num)
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
    return render(request, 'assessment.html', {
        'trajectories': trajectories,
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
    trajectories = request.session['trajectories']
    payoff_matrix = np.array(request.session['payoff_matrix'])
    payoff_criteria = {
        'Лапласа': laplace,
        'Вальда': wald,
        'оптимизма': optimist,
        'устойчивости Гурвица': hurwitz,
        'Сэвиджа': savage,
    }
    best_trajectories = {}
    for key, value in payoff_criteria.items():
        best_trajectories[key] = {'idx': value(payoff_matrix), 'data': trajectories[str(value(payoff_matrix))]}
    return render(request, 'final_trajectory.html', {
        'trajectories': trajectories,
        'best_trajectories': best_trajectories,
    })


def clusterization(df):
    new_columns = ['No', 'ID', 'User', 'IP', 'Date', 'Course', 'Group']
    question_num_set = set()
    for column_tuple in list(df.columns):
        if 'Вопрос' in column_tuple[0]:
            question_num_set.add(column_tuple[0][-1])
            new_columns.append(f'{column_tuple[0][-1]}_{column_tuple[1]}')
    df.set_axis(new_columns, axis=1, inplace=True)
    df.drop(['No', 'ID', 'User', 'IP', 'Date', 'Course', 'Group'], axis=1, inplace=True)
    question_number = len(question_num_set)

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

    return trajectories


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
    best_path = np.argmax(alpha*maxs + (1-alpha))
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