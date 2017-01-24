import os
import re
import time
from collections import OrderedDict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.interpolate as itp
from copy import deepcopy

from dev.dvhcalculation import Structure, prepare_dvh_data
from dicomparser import ScoringDicomParser
from dosimetric import read_scoring_criteria
from dvhcalc import get_dvh
from dvhcalc import load
from dvhdoses import get_dvh_max
from scoring import DVHMetrics


def test_real_dvh():
    # rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/FantomaPQRT/RS.PQRT END TO END.dcm'
    # rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/FantomaPQRT/RD.PQRT END TO END.Dose_PLAN.dcm'
    up = (0.5, 0.5, 0.5)
    # rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/Eclipse Plans/Venessa IMRT Eclipse/RD-Eclipse-Venessa-IMRTDose.dcm'
    # rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/Competition Package/DICOM Sets/RS.1.2.246.352.71.4.584747638204.208628.20160204185543.dcm'

    rs_file = r'/media/victor/TOURO Mobile/COMPETITION 2017/Send to Victor - Jan10 2017/Norm Res with CT Images/RS.1.2.246.352.71.4.584747638204.248648.20170110152358.dcm'
    rd_file = r'/media/victor/TOURO Mobile/COMPETITION 2017/Send to Victor - Jan10 2017/Norm Res with CT Images/RD.1.2.246.352.71.7.584747638204.1746016.20170110164605.dcm'
    rp = r'/media/victor/TOURO Mobile/COMPETITION 2017/Send to Victor - Jan10 2017/Norm Res with CT Images/RP.1.2.246.352.71.5.584747638204.950069.20170110164605.dcm'
    dvh_file = r'/media/victor/TOURO Mobile/COMPETITION 2017/Send to Victor - Jan10 2017/Norm Res with CT Images/RD.1.2.246.352.71.7.584747638204.1746016.20170110164605.dvh'

    dose = ScoringDicomParser(filename=rd_file)
    struc = ScoringDicomParser(filename=rs_file)
    structures = struc.GetStructures()

    ecl_DVH = dose.GetDVHs()

    st = time.time()
    for structure in structures.values():
        if structure['id'] in ecl_DVH:
            if not structure['name'] == 'BODY':
                dicompyler_dvh = get_dvh(structure, dose)
                struc_teste = Structure(structure)

                ecl_dvh = ecl_DVH[structure['id']]['data']
                dhist, chist = struc_teste.calculate_dvh(dose, upsample=True, delta_cm=up)
                plt.figure()
                plt.plot(chist, label='Up Sampled Structure')
                plt.hold(True)
                plt.plot(ecl_dvh, label='Eclipse DVH')
                plt.title(structure['name'] + ' volume (cc): %1.3f' % ecl_dvh[0])
                plt.plot(dicompyler_dvh['data'], label='Not up sampled')
                plt.legend(loc='best')
    end = time.time()

    print('Total elapsed Time (min):  ', (end - st) / 60)
    plt.show()


class CurveCompare(object):
    """
        Statistical analysis of the DVH volume (%) error histograms. volume (cm 3 ) differences (numerical–analytical)
        were calculated for points on the DVH curve sampled at every 10 cGy then normalized to
        the structure's total volume (cm 3 ) to give the error in volume (%)
    """

    def __init__(self, a_dose, a_dvh, calc_dose, calc_dvh):
        self.calc_data = ''
        self.ref_data = ''
        self.a_dose = a_dose
        self.a_dvh = a_dvh
        self.cal_dose = calc_dose
        self.calc_dvh = calc_dvh
        self.dose_samples = np.arange(0, len(calc_dvh) + 10, 10)  # The DVH curve sampled at every 10 cGy
        self.ref_dvh = itp.interp1d(a_dose, a_dvh, fill_value='extrapolate')
        self.calc_dvh = itp.interp1d(calc_dose, calc_dvh, fill_value='extrapolate')
        self.delta_dvh = self.calc_dvh(self.dose_samples) - self.ref_dvh(self.dose_samples)
        self.delta_dvh_pp = (self.delta_dvh / a_dvh[0]) * 100

    def stats(self):
        df = pd.DataFrame(self.delta_dvh_pp, columns=['delta_pp'])
        print(df.describe())

    @property
    def stats_paper(self):
        stats = {}
        stats['min'] = self.delta_dvh_pp.min()
        stats['max'] = self.delta_dvh_pp.max()
        stats['mean'] = self.delta_dvh_pp.mean()
        stats['std'] = self.delta_dvh_pp.std(ddof=1)
        return stats

    def eval_range(self, lim=0.2):
        t1 = self.delta_dvh < -lim
        t2 = self.delta_dvh > lim
        ok = np.sum(np.logical_or(t1, t2))

        pp = ok / len(self.delta_dvh) * 100
        print('pp %1.2f - %i of %i ' % (pp, ok, self.delta_dvh.size))

    def plot_results(self):
        # PLOT HISTOGRAM AND DELTA
        pass


def test1():
    """
    In Test 1, the axial contour spacing was kept constant at
    0.2 mm to essentially eliminate the variation and/or errors
    associated with rendering axial contours into volumes, and to
    focus solely on the effect of altering the dose grid resolution
    in various stages from fine (0.4 × 0.2 × 0.4 mm 3 ) to coarse (3
    × 3 × 3 mm 3 ).
    Analytical results for the following parameters
    per structure were compared to both PlanIQ (with supersam-
    pling turned on: Ref. 20) and PINCACLE: total volume (V );
    mean, maximum, and minimum dose (D mean , D max , D min );
    near-maximum (D1, dose covering 1% of the volume) and
    near-minimum (D99) doses; D95 and D5; and maximum dose
    to a small absolute (0.03 cm 3 ) volume (D0.03 cm 3 ). We were
    primarily interested in the high and low dose regions because
    with the linear dose gradient, they correspond to the structure
    boundary and this is where the deviations are expected to occur.

    Results of Test 1. Dose grid resolution is varied while axial contour
    spacing is kept at 0.2 mm. Numbers of points (n) exceeding 3% difference
    (∆) from analytical are presented along with the range of % ∆. Total number
    of structure/dose combinations is N = 40 (20 for V )."""

    # TEST DICOM DATA
    structure_files = ['/home/victor/Downloads/DVH-Analysis-Data-Etc/STRUCTURES/Spheres/Sphere_02_0.dcm',
                       '/home/victor/Downloads/DVH-Analysis-Data-Etc/STRUCTURES/Cylinders/Cylinder_02_0.dcm',
                       '/home/victor/Downloads/DVH-Analysis-Data-Etc/STRUCTURES/Cylinders/RtCylinder_02_0.dcm',
                       '/home/victor/Downloads/DVH-Analysis-Data-Etc/STRUCTURES/Cones/Cone_02_0.dcm',
                       '/home/victor/Downloads/DVH-Analysis-Data-Etc/STRUCTURES/Cones/RtCone_02_0.dcm']

    structure_name = ['Sphere_02_0', 'Cylinder_02_0', 'RtCylinder_02_0', 'Cone__02_0', 'RtCone_02_0']

    dose_files = [
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_AntPost_0-4_0-2_0-4_mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_AntPost_1mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_AntPost_2mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_AntPost_3mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_SupInf_0-4_0-2_0-4_mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_SupInf_1mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_SupInf_2mm_Aligned.dcm',
        r'/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS/Linear_SupInf_3mm_Aligned.dcm']

    # Structure Dict

    structure_dict = dict(zip(structure_name, structure_files))

    # dose dict
    dose_files_dict = {
        'Z(AP)': {'0.4x0.2x0.4': dose_files[0], '1': dose_files[1], '2': dose_files[2], '3': dose_files[3]},
        'Y(SI)': {'0.4x0.2x0.4': dose_files[4], '1': dose_files[5], '2': dose_files[6], '3': dose_files[7]}}

    # grab analytical data
    sheet = 'Analytical'
    df = pd.read_excel('/home/victor/Dropbox/Plan_Competition_Project/testdata/dvh_sphere.xlsx', sheetname=sheet)
    mask = df['CT slice spacing (mm)'] == '0.2mm'
    df = df.loc[mask]

    # Constrains to get data

    # Constrains

    constrains = OrderedDict()
    constrains['Total_Volume'] = True
    constrains['min'] = 'min'
    constrains['max'] = 'max'
    constrains['mean'] = 'mean'
    constrains['D99'] = 99
    constrains['D95'] = 95
    constrains['D5'] = 5
    constrains['D1'] = 1
    constrains['Dcc'] = 0.03

    st = 2
    up = (0.4, 0.4, 0.1)
    df_concat = []
    sname = []
    # GET CALCULATED DATA
    for row in df.iterrows():
        idx, values = row[0], row[1]
        s_name = values['Structure name']
        voxel = str(values['Dose Voxel (mm)'])
        gradient = values['Gradient direction']

        dose_file = dose_files_dict[gradient][voxel]
        struc_file = structure_dict[s_name]

        # get structure and dose
        dicom_dose = ScoringDicomParser(filename=dose_file)
        struc = ScoringDicomParser(filename=struc_file)
        structures = struc.GetStructures()
        structure = structures[st]

        # set up sampled structure
        struc_teste = Structure(structure, end_cap=True)
        dhist, chist = struc_teste.calculate_dvh(dicom_dose, upsample=True, delta_cm=up)
        dvh_data = prepare_dvh_data(dhist, chist)

        # Setup DVH metrics class and get DVH DATA
        metrics = DVHMetrics(dvh_data)
        values_constrains = OrderedDict()
        for k in constrains.keys():
            ct = metrics.eval_constrain(k, constrains[k])
            values_constrains[k] = ct
        values_constrains['Gradient direction'] = gradient

        # Get data
        df_concat.append(pd.Series(values_constrains, name=voxel))
        sname.append(s_name)

    result = pd.concat(df_concat, axis=1).T.reset_index()
    result['Structure name'] = sname

    res_col = ['Structure name', 'Dose Voxel (mm)', 'Gradient direction', 'Total Volume (cc)', 'Dmin', 'Dmax', 'Dmean',
               'D99', 'D95', 'D5', 'D1', 'D0.03cc']

    num_col = ['Total Volume (cc)', 'Dmin', 'Dmax', 'Dmean', 'D99', 'D95', 'D5', 'D1', 'D0.03cc']

    df_num = df[num_col]

    result_num = result[result.columns[1:-2]]
    result_num.columns = df_num.columns

    delta = ((result_num - df_num) / df_num) * 100

    res = OrderedDict()
    lim = 3.0
    for col in delta:
        t0 = delta[col] > lim
        t1 = delta[col] < -lim
        count = np.logical_or(t0, t1).sum()
        rg = np.array([round(delta[col].min(), 2), round(delta[col].max(), 2)])
        res[col] = {'count': count, 'range': rg}

    test_table = pd.DataFrame(res).T
    print(test_table)

    return test_table


def test2():
    """


    """
    ref_data = '/home/victor/Dropbox/Plan_Competition_Project/testdata/dvh_sphere.xlsx'

    struc_dir = '/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/STRUCTURES'
    dose_grid_dir = '/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS'
    #
    # ref_data = r'D:\Dropbox\Plan_Competition_Project\testdata\dvh_sphere.xlsx'

    # struc_dir = r'D:\Dropbox\Plan_Competition_Project\testdata\DVH-Analysis-Data-Etc\STRUCTURES'
    # dose_grid_dir = r'D:\Dropbox\Plan_Competition_Project\testdata\DVH-Analysis-Data-Etc\DOSE GRIDS'

    st = 2
    up = (0.1, 0.1, 0.1)

    snames = ['Sphere_10_0', 'Sphere_20_0', 'Sphere_30_0',
              'Cylinder_10_0', 'Cylinder_20_0', 'Cylinder_30_0',
              'RtCylinder_10_0', 'RtCylinder_20_0', 'RtCylinder_30_0',
              'Cone_10_0', 'Cone_20_0', 'Cone_30_0',
              'RtCone_10_0', 'RtCone_20_0', 'RtCone_30_0']

    structure_path = [os.path.join(struc_dir, f + '.dcm') for f in snames]

    structure_dict = dict(zip(snames, structure_path))

    dose_files = [os.path.join(dose_grid_dir, f) for f in [
        'Linear_AntPost_1mm_Aligned.dcm',
        'Linear_AntPost_2mm_Aligned.dcm',
        'Linear_AntPost_3mm_Aligned.dcm',
        'Linear_SupInf_1mm_Aligned.dcm',
        'Linear_SupInf_2mm_Aligned.dcm',
        'Linear_SupInf_3mm_Aligned.dcm']]

    # dose dict
    dose_files_dict = {
        'Z(AP)': {'1': dose_files[0], '2': dose_files[1], '3': dose_files[2]},
        'Y(SI)': {'1': dose_files[3], '2': dose_files[4], '3': dose_files[5]}}

    test_files = {}
    for s_name in structure_dict:
        grad_files = {}
        for grad in dose_files_dict:
            tick = str(int(int(re.findall(r'\d+', s_name)[0]) / 10))
            grad_files[grad] = dose_files_dict[grad][tick]

        test_files[s_name] = grad_files

    # grab analytical data

    df = pd.read_excel(ref_data, sheetname='Analytical')

    dfi = df.ix[40:]
    mask0 = dfi['Structure Shift'] == 0
    dfi = dfi.loc[mask0]

    # Constrains to get data
    # Constrains

    constrains = OrderedDict()
    constrains['Total_Volume'] = True
    constrains['min'] = 'min'
    constrains['max'] = 'max'
    constrains['mean'] = 'mean'
    constrains['D99'] = 99
    constrains['D95'] = 95
    constrains['D5'] = 5
    constrains['D1'] = 1
    constrains['Dcc'] = 0.03

    df_concat = []
    sname = []
    # GET CALCULATED DATA
    for row in dfi.iterrows():
        idx, values = row[0], row[1]
        s_name = values['Structure name']
        voxel = str(values['Dose Voxel (mm)'])
        gradient = values['Gradient direction']

        dose_file = dose_files_dict[gradient][voxel]
        struc_file = structure_dict[s_name]

        # get structure and dose
        dicom_dose = ScoringDicomParser(filename=dose_file)
        struc = ScoringDicomParser(filename=struc_file)
        structures = struc.GetStructures()
        structure = structures[st]

        # set up sampled structure
        struc_teste = Structure(structure, end_cap=True)
        dhist, chist = struc_teste.calculate_dvh(dicom_dose, upsample=True, delta_cm=up)
        dvh_data = prepare_dvh_data(dhist, chist)
        # dvh_data['Dmin'] = dmin
        # Setup DVH metrics class and get DVH DATA
        metrics = DVHMetrics(dvh_data)
        values_constrains = OrderedDict()
        for k in constrains.keys():
            ct = metrics.eval_constrain(k, constrains[k])
            values_constrains[k] = ct
        values_constrains['Gradient direction'] = gradient

        # Get data
        df_concat.append(pd.Series(values_constrains, name=voxel))
        sname.append(s_name)

    result = pd.concat(df_concat, axis=1).T.reset_index()
    result['Structure name'] = sname

    res_col = ['Structure name', 'Dose Voxel (mm)', 'Gradient direction', 'Total Volume (cc)', 'Dmin', 'Dmax', 'Dmean',
               'D99', 'D95', 'D5', 'D1', 'D0.03cc']

    num_col = ['Total Volume (cc)', 'Dmin', 'Dmax', 'Dmean', 'D99', 'D95', 'D5', 'D1', 'D0.03cc']

    df_num = dfi[num_col]

    result_num = result[result.columns[1:-2]]
    result_num.columns = df_num.columns
    result_num.index = df_num.index

    delta = ((result_num - df_num) / df_num) * 100

    pcol = ['Total Volume (cc)', 'Dmax', 'Dmean', 'D99', 'D95', 'D5', 'D1']

    res = OrderedDict()
    lim = 3.0
    for col in delta:
        t0 = delta[col] > lim
        t1 = delta[col] < -lim
        count = np.logical_or(t0, t1).sum()
        rg = np.array([delta[col].min(), delta[col].max()])
        res[col] = {'count': count, 'range': rg}

    test_table = pd.DataFrame(res).T
    print(test_table)

    mask = np.logical_or(delta > lim, delta < -lim)
    result.index = mask.index
    print(result.loc[mask['D0.03cc']])
    print(result.loc[mask['D95']])


def test3(plot_curves=True):
    ref_data = '/home/victor/Dropbox/Plan_Competition_Project/testdata/dvh_sphere.xlsx'

    struc_dir = '/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/STRUCTURES'
    dose_grid_dir = '/home/victor/Dropbox/Plan_Competition_Project/testdata/DVH-Analysis-Data-Etc/DOSE GRIDS'
    st = 2
    up = (0.5, 0.5, 0.5)

    snames = ['Sphere_10_0', 'Sphere_30_0',
              'Cylinder_10_0', 'Cylinder_30_0',
              'RtCylinder_10_0', 'RtCylinder_30_0',
              'Cone_10_0', 'Cone_30_0',
              'RtCone_10_0', 'RtCone_30_0']

    structure_path = [os.path.join(struc_dir, f + '.dcm') for f in snames]

    structure_dict = dict(zip(snames, structure_path))

    dose_files = [os.path.join(dose_grid_dir, f) for f in [
        'Linear_AntPost_1mm_Aligned.dcm',
        'Linear_AntPost_2mm_Aligned.dcm',
        'Linear_AntPost_3mm_Aligned.dcm',
        'Linear_SupInf_1mm_Aligned.dcm',
        'Linear_SupInf_2mm_Aligned.dcm',
        'Linear_SupInf_3mm_Aligned.dcm']]

    # dose dict
    dose_files_dict = {
        'Z(AP)': {'1': dose_files[0], '2': dose_files[1], '3': dose_files[2]},
        'Y(SI)': {'1': dose_files[3], '2': dose_files[4], '3': dose_files[5]}}

    test_files = {}
    for s_name in structure_dict:
        grad_files = {}
        for grad in dose_files_dict:
            tick = str(int(int(re.findall(r'\d+', s_name)[0]) / 10))
            grad_files[grad] = dose_files_dict[grad][tick]

        test_files[s_name] = grad_files

    result = OrderedDict()
    for sname in snames:
        struc_path = structure_dict[sname]
        # set structure's object
        struc = ScoringDicomParser(filename=struc_path)
        structures = struc.GetStructures()
        structure = structures[st]
        # set up sampled structure
        struc_teste = Structure(structure, end_cap=True)
        str_result = {}
        test_data = test_files[sname]
        for k in test_data:
            # get dose
            dose_file = test_data[k]
            dicom_dose = ScoringDicomParser(filename=dose_file)
            dhist, chist = struc_teste.calculate_dvh(dicom_dose, upsample=True, delta_cm=up)
            dvh_data = prepare_dvh_data(dhist, chist)
            str_result[k] = dvh_data

        result[sname] = str_result

    dest = '/home/victor/Dropbox/Plan_Competition_Project/testdata/test3_ref_dvh.obj'
    # save(an_data, dest)
    an_data = load(dest)
    adata = an_data['Cone_30_0']['Z(AP)']
    calc_data = result['Cone_30_0']['Z(AP)']

    cmp = CurveCompare(adata['dose_axis'], adata['data'], calc_data['dose_axis'], calc_data['data'])

    stats = OrderedDict()
    stats['min'] = cmp.delta_dvh_pp.min()
    stats['max'] = cmp.delta_dvh_pp.max()
    stats['mean'] = cmp.delta_dvh_pp.mean()
    stats['std'] = cmp.delta_dvh_pp.std(ddof=1)

    teste = []
    for s in result:
        for g in result[s]:
            adata = an_data[s][g]
            calc_data = result[s][g]
            cmp = CurveCompare(adata['dose_axis'], adata['data'], calc_data['dose_axis'], calc_data['data'])
            curve_stats = cmp.stats_paper
            curve_stats['Resolution (mm)'] = str(int(int(re.findall(r'\d+', s)[0]) / 10))
            curve_stats['Gradient'] = g

            tmp = pd.DataFrame(curve_stats, index=[s])
            teste.append(tmp)

    df_final = pd.concat(teste)
    print(df_final)

    if plot_curves:
        for grad in ['Z(AP)', 'Y(SI)']:
            for s_key in result:
                adata = an_data[s_key][grad]
                calc_data = result[s_key][grad]
                plt.figure()
                plt.plot(adata['dose_axis'], adata['data'], '.', label='Analytical DVH')
                plt.plot(calc_data['dose_axis'], calc_data['data'], '.', label='Software DVH')
                plt.legend(loc='best')
                plt.xlabel('Dose (cGy)')
                plt.ylabel('Volume (cc)')
                plt.title(s_key + ' Dose Gradient ' + grad)

        plt.show()


if __name__ == '__main__':
    # rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/FantomaPQRT/RS.PQRT END TO END.dcm'
    # rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/FantomaPQRT/RD.PQRT END TO END.Dose_PLAN.dcm'
    up = (0.83, 0.83, 1)
    # up = (2.5, 2.5, 1)
    # rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/Eclipse Plans/Venessa IMRT Eclipse/RD-Eclipse-Venessa-IMRTDose.dcm'
    # rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/Competition Package/DICOM Sets/RS.1.2.246.352.71.4.584747638204.208628.20160204185543.dcm'

    rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RS.1.2.246.352.71.4.584747638204.248648.20170123083029.dcm'
    rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RD.1.2.246.352.71.7.584747638204.1750110.20170123082607.dcm'
    rp = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RP.1.2.246.352.71.5.584747638204.952069.20170122155706.dcm'
    # dvh_file = r'/media/victor/TOURO Mobile/COMPETITION 2017/Send to Victor - Jan10 2017/Norm Res with CT Images/RD.1.2.246.352.71.7.584747638204.1746016.20170110164605.dvh'

    f = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/PlanIQ Criteria TPS PlanIQ matched str names - TXT Fromat - Last mod Jan23.txt'
    constrains_all, scores_all = read_scoring_criteria(f)

    dose = ScoringDicomParser(filename=rd_file)
    struc = ScoringDicomParser(filename=rs_file)
    structures = struc.GetStructures()

    ecl_DVH = dose.GetDVHs()
    plt.style.use('ggplot')
    st = time.time()
    dvhs = {}

    for structure in structures.values():
        for end_cap in [False]:
            if structure['id'] in ecl_DVH:
                # if structure['id'] in [37, 38]:
                if structure['name'] in list(scores_all.keys()):
                    ecl_dvh = ecl_DVH[structure['id']]['data']
                    ecl_dmax = ecl_DVH[structure['id']]['max'] * 100  # to cGy
                    # if ecl_dvh[0] < 50.0:
                    # struc = deepcopy(structure)
                    struc_teste = Structure(structure, end_cap=end_cap)
                    # struc['planes'] = struc_teste.planes
                    # dicompyler_dvh = get_dvh(structure, dose)

                    dhist, chist = struc_teste.calculate_dvh(dose, upsample=True, delta_cm=up)
                    max_dose = get_dvh_max(chist)
                    plt.figure()
                    plt.plot(dhist, chist, label='Up sampled - Dmax: %1.1f cGy' % max_dose)
                    plt.hold(True)
                    plt.plot(ecl_dvh, label='Eclipse - Dmax: %1.1f cGy' % ecl_dmax)
                    dvh_data = prepare_dvh_data(dhist, chist)

                    txt = structure['name'] + ' volume (cc): %1.1f - end_cap: %s ' % (
                        ecl_dvh[0], str(end_cap))
                    plt.title(txt)
                    # nup = get_dvh_max(dicompyler_dvh['data'])
                    # plt.plot(dicompyler_dvh['data'], label='Software DVH - Dmax: %1.1f cGy' % nup)
                    plt.legend(loc='best')
                    plt.xlabel('Dose (cGy)')
                    plt.ylabel('Volume (cc)')

                    dvhs[structure['name']] = dvh_data

        plt.show()

    end = time.time()

    print('Total elapsed Time (min):  ', (end - st) / 60)

    # print(dvhs)



    # for structure in structures.values():
    #     print(structure['id'], structure['name'])
