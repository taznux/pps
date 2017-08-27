import logging
import os
import re

import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed

from pyplanscoring.competition.utils import get_dicom_data
from pyplanscoring.complexity.PyComplexityMetric import PyComplexityMetric, MeanAreaMetricEstimator
from pyplanscoring.complexity.dicomrt import RTPlan

logger = logging.getLogger('script.py')

logging.basicConfig(filename='complexity_reports.log', level=logging.DEBUG)


def get_score(s):
    p = re.compile(r'\d+\.\d+')
    # p = re.compile(r'\d+(?:\.\d+)?')
    floats = [float(i) for i in p.findall(s)]  # Convert strings to float
    return floats


def calc_complexity(plan_file):
    plan_info = RTPlan(filename=plan_file)
    plan_dict = plan_info.get_plan()
    complexity_metric = PyComplexityMetric().CalculateForPlan(None, plan_dict)
    area_metric = MeanAreaMetricEstimator().CalculateForPlan(None, plan_dict)
    return complexity_metric, plan_dict['Plan_MU'] / 200.0, area_metric


def aggregate_score_complexity(f):
    folder, plan_file = os.path.split(f)
    score = get_score(folder)
    if score:
        try:
            complexity, muf, area_metric = calc_complexity(f)
            scores = score[0]
            return scores, complexity, muf, area_metric
        except:
            txt = 'error in file %s' % f
            logger.debug(txt)
            print(txt)


def get_score_complexity(participant_folder):
    files_data = get_dicom_data(participant_folder)
    rp = files_data.reset_index().set_index(1).loc['rtplan']['index']
    res = Parallel(n_jobs=-1, verbose=50)(delayed(aggregate_score_complexity)(f) for f in rp.values)
    return res


def get_score_complexity_debug(participant_folder):
    files_data = get_dicom_data(participant_folder)
    rp = files_data.reset_index().set_index(1).loc['rtplan']['index']
    res = []
    for f in rp.values:
        print('processing: ', f)
        v = aggregate_score_complexity(f)
        res.append(v)
    return res


if __name__ == '__main__':
    plt.style.use('ggplot')

    participant_folder = r'/media/victor/TOURO Mobile/COMPETITION 2017/final_plans/ECLIPSE/ECPLIPSE_VMAT'
    res = get_score_complexity(participant_folder)
    score_complexity = np.array(list(filter(lambda x: x is not None, res)))

    plt.figure()
    plt.plot(score_complexity[:, 0], score_complexity[:, 1], '.')
    plt.xlabel('Score')
    plt.ylabel('complexity factor mm-1')
    plt.xlim([0, 105])
    plt.ylim([0, 0.3])
    plt.axhline(0.18, color='b')
    plt.title('Eclipse - VMAT')

    plt.figure()
    plt.plot(score_complexity[:, 0], score_complexity[:, 3], '.')
    plt.xlabel('Score')
    plt.ylabel('Weighted aperture area [mm2]')
    # plt.xlim([0, 105])
    # plt.ylim([0, 0.3])
    # plt.axhline(0.18, color='b')
    plt.title('Eclipse - VMAT')

    plt.figure()
    plt.plot(score_complexity[:, 3], score_complexity[:, 1], '.')
    plt.xlabel('Weighted aperture area [mm2]')
    plt.ylabel('complexity factor mm-1')
    # plt.xlim([0, 105])
    # plt.ylim([0, 0.3])
    plt.axhline(0.18, color='b')
    plt.title('Eclipse - VMAT')

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(score_complexity[:, 3], score_complexity[:, 1], score_complexity[:, 0])
    ax.set_xlabel('Weighted aperture area [mm2]')
    ax.set_ylabel('Complexity factor mm-1')
    ax.set_zlabel('Score')






    # plt.figure()
    # plt.plot(score_complexity[:, 0], score_complexity[:, 2], '.')
    # plt.xlabel('Score')
    # plt.ylabel('MU/cGy')
    # plt.xlim([0, 105])
    # plt.ylim([0, 13])
    # plt.title('RayStation - VMAT')
    #
    # plt.figure()
    # plt.plot(score_complexity[:, 2], score_complexity[:, 1], '.')
    # plt.xlabel('MU/cGy')
    # plt.ylabel('complexity factor mm-1')
    # plt.xlim([0, 13])
    # plt.ylim([0, 0.3])
    # plt.title('RayStation - VMAT')
    # plt.show()
