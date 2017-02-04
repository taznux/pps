import time
from copy import deepcopy

import numpy as np
import numpy.ma as ma
from joblib import Parallel
from joblib import delayed

from dev.geometry import get_contour_mask_wn, get_dose_grid_3d, \
    get_axis_grid, get_dose_grid, \
    get_interpolated_structure_planes, point_in_contour
from dicomparser import ScoringDicomParser, lazyproperty
from dvhcalc import get_cdvh_numba, calculate_contour_areas_numba, save
from dvhdoses import get_dvh_min, get_dvh_max, get_dvh_mean

float_formatter = lambda x: "%.2f" % x
np.set_printoptions(formatter={'float_kind': float_formatter})
# np.set_printoptions(formatter={'str_kind': str_formatter})


'''

http://dicom.nema.org/medical/Dicom/2016b/output/chtml/part03/sect_C.8.8.html
http://dicom.nema.org/medical/Dicom/2016b/output/chtml/part03/sect_C.7.6.2.html#sect_C.7.6.2.1.1
'''


def prepare_dvh_data(dhist, dvh):
    dvhdata = {}
    dvhdata['dose_axis'] = dhist
    dvhdata['data'] = dvh
    dvhdata['bins'] = len(dvh)
    dvhdata['type'] = 'CUMULATIVE'
    dvhdata['doseunits'] = 'cGY'
    dvhdata['volumeunits'] = 'CM3'
    dvhdata['scaling'] = np.diff(dhist)[0]
    dvhdata['min'] = get_dvh_min(dvh)
    dvhdata['max'] = get_dvh_max(dvh)
    dvhdata['mean'] = get_dvh_mean(dvh)
    return dvhdata


def calculate_contour_dvh(mask, doseplane, bins, maxdose, grid_delta):
    """Calculate the differential DVH for the given contour and dose plane."""

    # Multiply the structure mask by the dose plane to get the dose mask
    mask1 = ma.array(doseplane, mask=~mask)

    # Calculate the differential dvh
    hist, edges = np.histogram(mask1.compressed(),
                               bins=bins,
                               range=(0, maxdose))

    # Calculate the volume for the contour for the given dose plane
    vol = np.sum(hist) * grid_delta[0] * grid_delta[1] * grid_delta[2]

    return hist, vol


# def get_contour_opencv(doseplane, contour, dose_lut):
#     r_contour = contour['data']
#     # fill the ROI so it doesn't get wiped out when the mask is applied
#     mask_teste = np.zeros(doseplane.shape, dtype=np.uint8)
#     ignore_mask_color = (1,)
#     roi_corners = contour2index(r_contour, dose_lut)
#     cv2.fillPoly(mask_teste, roi_corners, ignore_mask_color)
#
#     return mask_teste.astype(bool)


def contour2index(r_contour, dose_lut):
    xgrid = dose_lut[0]
    x = r_contour[:, 0]

    delta_x = np.abs(xgrid[0] - xgrid[1])
    ix = (x - xgrid[0]) / delta_x + 1

    ygrid = dose_lut[1]
    y = r_contour[:, 1]

    delta_y = np.abs(ygrid[0] - ygrid[1])
    iy = (y - ygrid[0]) / delta_y + 1

    roi_corners = np.dstack((ix, iy)).astype(dtype=np.int32)

    return roi_corners


def get_planes_thickness(planesDict):
    ordered_keys = [z for z, sPlane in planesDict.items()]
    ordered_keys.sort(key=float)
    planes = np.array(ordered_keys, dtype=float)

    delta = np.diff(planes)
    delta = np.append(delta, delta[0])
    planes_thickness = dict(zip(ordered_keys, delta))

    return planes_thickness


def get_capped_structure(structure):
    planesDict = structure['planes']

    out_Dict = deepcopy(planesDict)
    ordered_keys = [z for z, sPlane in planesDict.items()]
    ordered_keys.sort(key=float)
    planes = np.array(ordered_keys, dtype=float)
    start_cap = (planes[0] - structure['thickness'] / 2.0)
    start_cap_key = '%.2f' % start_cap
    start_cap_values = planesDict[ordered_keys[0]]

    end_cap = (planes[-1] + structure['thickness'] / 2.0)
    end_cap_key = '%.2f' % end_cap
    end_cap_values = planesDict[ordered_keys[-1]]

    out_Dict.pop(ordered_keys[0])
    out_Dict.pop(ordered_keys[-1])
    # adding structure caps
    out_Dict[start_cap_key] = start_cap_values
    out_Dict[end_cap_key] = end_cap_values

    return out_Dict


class Structure(object):
    def __init__(self, dicom_structure, end_cap=False):
        self.structure = dicom_structure
        self.end_cap = end_cap
        self.contour_spacing = dicom_structure['thickness']
        self.grid_spacing = np.zeros(3)
        self.dose_lut = None
        self.dose_grid_points = None
        self.hi_res_structure = None
        self.dvh = np.array([])
        self.delta_mm = np.asarray([0.5, 0.5, 0.5])

    def set_delta(self, delta_mm):
        self.delta_mm = delta_mm

    @property
    def name(self):
        return self.structure['name']

    @lazyproperty
    def planes(self):
        if self.end_cap and self.volume_original < 25:
            return get_capped_structure(self.structure)
        else:
            return self.structure['planes']

    @lazyproperty
    def volume_original(self):
        grid = [self.structure['thickness'], self.structure['thickness'], self.structure['thickness']]
        vol_cc = self.calculate_volume(self.structure['planes'], grid)

        return vol_cc

    @lazyproperty
    def volume_cc(self):
        grid = [self.structure['thickness'], self.structure['thickness'], self.structure['thickness']]
        vol_cc = self.calculate_volume(self.planes, grid)

        return vol_cc

    @lazyproperty
    def ordered_planes(self):
        ordered_keys = [z for z, sPlane in self.planes.items()]
        ordered_keys.sort(key=float)
        return np.array(ordered_keys, dtype=float)

    def up_sampling(self, lut_grid_3d, delta_mm):

        # ROI UP SAMPLING IN X, Y, Z
        self.dose_grid_points, self.dose_lut, self.grid_spacing = get_dose_grid_3d(lut_grid_3d, delta_mm)
        zi, dz = get_axis_grid(self.grid_spacing[2], self.ordered_planes)
        self.grid_spacing[2] = dz
        print('Upsampling ON')

        self.hi_res_structure = get_interpolated_structure_planes(self.planes, zi)

        return self.hi_res_structure, self.dose_grid_points, self.grid_spacing, self.dose_lut

    def _prepare_data(self, grid_3d, upsample):

        if upsample:
            if self.volume_cc < 25:
                x_delta = abs(grid_3d[0][0] - grid_3d[0][1])
                y_delta = abs(grid_3d[1][0] - grid_3d[1][1])
                # get structure slice position
                ordered_z = self.ordered_planes
                z_delta = abs(ordered_z[0] - ordered_z[1])

                ds, grid_ds, grid_delta, dose_lut = self.up_sampling(grid_3d, self.delta_mm)
                dosegrid_points = grid_ds[:, :2]

                return ds, dose_lut, dosegrid_points, grid_delta
            else:
                ds = self.planes
                dose_lut = [grid_3d[0], grid_3d[1]]
                dosegrid_points = get_dose_grid(dose_lut)
                x_delta = abs(grid_3d[0][0] - grid_3d[0][1])
                y_delta = abs(grid_3d[1][0] - grid_3d[1][1])
                # get structure slice position
                ordered_z = self.ordered_planes
                z_delta = abs(ordered_z[0] - ordered_z[1])
                grid_delta = [x_delta, y_delta, z_delta]
                return ds, dose_lut, dosegrid_points, grid_delta

        else:
            dose_lut = [grid_3d[0], grid_3d[1]]
            dosegrid_points = get_dose_grid(dose_lut)
            x_delta = abs(grid_3d[0][0] - grid_3d[0][1])
            y_delta = abs(grid_3d[1][0] - grid_3d[1][1])
            # get structure slice position
            ordered_z = self.ordered_planes
            z_delta = abs(ordered_z[0] - ordered_z[1])
            grid_delta = [x_delta, y_delta, z_delta]
            return self.planes, dose_lut, dosegrid_points, grid_delta

    def calculate_dvh(self, dicom_dose, bin_size=1.0, upsample=False):

        print(' ----- DVH Calculation -----')
        print('Structure Name: %s - volume (cc) %1.3f' % (self.name, self.volume_cc))
        grid_3d = dicom_dose.get_grid_3d()
        sPlanes, dose_lut, dosegrid_points, grid_delta = self._prepare_data(grid_3d, upsample)
        print('End caping:  ' + str(self.end_cap))
        print('Grid delta (mm): ', grid_delta)

        # 3D DOSE TRI-LINEAR INTERPOLATION
        dose_interp, values = dicom_dose.DoseRegularGridInterpolator()
        xx, yy = np.meshgrid(dose_lut[0], dose_lut[1], indexing='xy', sparse=True)

        # Create an empty array of bins to store the histogram in cGy
        # only if the structure has contour data or the dose grid exists
        dd = dicom_dose.GetDoseData()
        maxdose = int(dd['dosemax'] * dd['dosegridscaling'] * 100)

        # Remove values above the limit (cGy) if specified
        nbins = int(maxdose / bin_size)
        hist = np.zeros(nbins)

        n_voxels = []
        st = time.time()
        volume = 0
        # Iterate over each plane in the structure
        # planes_dz = get_planes_thickness(sPlanes)
        # ordered keys
        ordered_keys = [z for z, sPlane in sPlanes.items()]
        ordered_keys.sort(key=float)

        for z in ordered_keys:
            # for z, sPlane in sPlanes.items():
            sPlane = sPlanes[z]
            print('calculating slice z: %.1f' % float(z))
            # grid_delta[2] = planes_dz[z]
            # Get the contours with calculated areas and the largest contour index
            contours, largestIndex = calculate_contour_areas_numba(sPlane)

            # Get the dose plane for the current structure plane
            doseplane = dose_interp((z, yy, xx))
            # If there is no dose for the current plane, go to the next plane

            if not len(doseplane):
                break

            # Calculate the histogram for each contour
            for i, contour in enumerate(contours):
                m = get_contour_mask_wn(dose_lut, dosegrid_points, contour['data'])
                h, vol = calculate_contour_dvh(m, doseplane, nbins, maxdose, grid_delta)

                mask = ma.array(doseplane, mask=~m)
                n_voxels.append(len(mask.compressed()))

                # If this is the largest contour, just add to the total histogram
                if i == largestIndex:
                    hist += h
                    volume += vol
                # Otherwise, determine whether to add or subtract histogram
                # depending if the contour is within the largest contour or not
                else:
                    inside = False
                    for point in contour['data']:
                        poly = contours[largestIndex]['data']
                        if point_in_contour(point, poly):
                            inside = True
                            # Assume if one point is inside, all will be inside
                            break
                    # If the contour is inside, subtract it from the total histogram
                    if inside:
                        hist -= h
                        volume -= vol
                    # Otherwise it is outside, so add it to the total histogram
                    else:
                        hist += h
                        volume += vol

        # Volume units are given in cm^3
        volume /= 1000
        # volume = self.volume_cc
        # Rescale the histogram to reflect the total volume
        hist = hist * volume / sum(hist)

        # Remove the bins above the max dose for the structure
        # hist = np.trim_zeros(hist, trim='b')
        chist = get_cdvh_numba(hist)
        # dhist = np.arange(len(chist))
        dhist = (np.arange(0, nbins) / nbins) * maxdose
        idx = np.nonzero(chist)  # remove 0 volumes from DVH

        # dose_range, cdvh = dhist, chist
        dose_range, cdvh = dhist[idx], chist[idx]
        end = time.time()

        print('elapsed (s):', end - st)
        print('number of structure voxels: %i' % np.sum(n_voxels))
        print(' ----- END DVH Calculation -----')

        return dose_range, cdvh

    def calc_conformation_index(self, rtdose, lowerlimit, upsample=False):
        """From a selected structure and isodose line, return conformality index.
            Up sample structures calculation by Victor Alves
        Read "A simple scoring ratio to index the conformity of radiosurgical
        treatment plans" by Ian Paddick.
        J Neurosurg (Suppl 3) 93:219-222, 2000"""

        print(' ----- Conformality index calculation -----')
        print('Structure Name: %s - volume (cc) %1.3f - lower_limit (cGy):  %1.2f' % (
            self.name, self.volume_cc, lowerlimit))

        grid_3d = rtdose.get_grid_3d()

        sPlanes, dose_lut, dosegrid_points, grid_delta = self._prepare_data(grid_3d, upsample)

        # 3D trilinear DOSE INTERPOLATION
        dose_interp, values = rtdose.DoseRegularGridInterpolator()
        xx, yy = np.meshgrid(dose_lut[0], dose_lut[1], indexing='xy', sparse=True)

        PITV = 0  # Rx isodose volume in cc
        CV = 0  # coverage volume

        ordered_keys = [z for z, sPlane in sPlanes.items()]
        ordered_keys.sort(key=float)

        # Iterate over each plane in the structure
        # for z, sPlane in sPlanes.items():
        for z in ordered_keys:
            sPlane = sPlanes[z]
            # print('calculating plane:', z)
            # Get the contours with calculated areas and the largest contour index
            contours, largestIndex = calculate_contour_areas_numba(sPlane)
            # Get the dose plane for the current structure plane
            doseplane = dose_interp((z, yy, xx))

            # If there is no dose for the current plane, go to the next plane
            if not len(doseplane):
                break

            for i, contour in enumerate(contours):
                m = get_contour_mask_wn(dose_lut, dosegrid_points, contour['data'])
                PITV_vol, CV_vol = self.calc_ci_vol(m, doseplane, lowerlimit, grid_delta)

                # If this is the largest contour, just add to the total volume
                if i == largestIndex:
                    PITV += PITV_vol
                    CV += CV_vol
                # Otherwise, determine whether to add or subtract
                # depending if the contour is within the largest contour or not
                else:
                    inside = False
                    for point in contour['data']:
                        poly = contours[largestIndex]['data']
                        # Assume if one point is inside, all will be inside
                        if point_in_contour(point, poly):
                            inside = True
                            break
                    # only add covered volume if contour is not inside the largest
                    if not inside:
                        CV += CV_vol

        # Volume units are given in cm^3
        PITV /= 1000.0
        CV /= 1000.0
        TV = self.calculate_volume(sPlanes, grid_delta)
        CI = CV * CV / (TV * PITV)
        print('Conformity index: ', CI)
        return CI

    @staticmethod
    def calc_ci_vol(mask, doseplane, lowerlimit, grid_delta):

        # Multiply the structure mask by the dose plane to get the dose mask
        cv_mask = doseplane * mask

        # Calculate the volume for the contour for the given dose plane
        PITV_vol = np.sum(doseplane > lowerlimit) * (grid_delta[0] * grid_delta[1] * grid_delta[2])

        CV_vol = np.sum(cv_mask > lowerlimit) * (grid_delta[0] * grid_delta[1] * grid_delta[2])

        return PITV_vol, CV_vol

    @staticmethod
    def calculate_volume(sPlanes, grid_delta):
        """Calculates the volume for the given structure."""

        # sPlanes = self.structure['planes']

        ordered_keys = [z for z, sPlane in sPlanes.items()]
        ordered_keys.sort(key=float)

        # Store the total volume of the structure
        sVolume = 0
        n = 0
        # Iterate over each plane in the structure
        # for sPlane in sPlanes.values():
        for z in ordered_keys:
            sPlane = sPlanes[z]
            # calculate contour areas
            contours, largestIndex = calculate_contour_areas_numba(sPlane)
            # See if the rest of the contours are within the largest contour
            area = contours[largestIndex]['area']
            for i, contour in enumerate(contours):
                # Skip if this is the largest contour
                if not (i == largestIndex):
                    inside = False
                    for point in contour['data']:
                        poly = contours[largestIndex]['data']
                        if point_in_contour(point, poly):
                            inside = True
                            # Assume if one point is inside, all will be inside
                            break
                    # If the contour is inside, subtract it from the total area
                    if inside:
                        area = area - contour['area']
                    # Otherwise it is outside, so add it to the total area
                    else:
                        area = area + contour['area']

            # If the plane is the first or last slice
            # only add half of the volume, otherwise add the full slice thickness
            if (n == 0) or (n == len(sPlanes) - 1):
                sVolume = float(sVolume) + float(area) * float(grid_delta[2]) * 0.5
            else:
                sVolume = float(sVolume) + float(area) * float(grid_delta[2])
            # Increment the current plane number
            n += 1

        # Since DICOM uses millimeters, convert from mm^3 to cm^3
        volume = sVolume / 1000

        return volume


# TODO implement DVH calc only on scored structures ?
def get_dvh_upsampled(structure, dose, key, end_cap=False):
    """Get a calculated cumulative DVH along with the associated parameters."""

    struc_teste = Structure(structure, end_cap=end_cap)
    dhist, chist = struc_teste.calculate_dvh(dose, upsample=True)
    dvh_data = prepare_dvh_data(dhist, chist)
    dvh_data['key'] = key

    return dvh_data


def calc_dvhs_upsampled(name, rs_file, rd_file, out_file=False, end_cap=False):
    """
        Computes structures DVH using a RS-DICOM and RD-DICOM diles
    :param rs_file: path to RS dicom-file
    :param rd_file: path to RD dicom-file
    :return: dict - computed DVHs
    """
    rtss = ScoringDicomParser(filename=rs_file)
    rtdose = ScoringDicomParser(filename=rd_file)
    # Obtain the structures and DVHs from the DICOM data
    structures = rtss.GetStructures()
    res = Parallel(n_jobs=-1, verbose=11)(
        delayed(get_dvh_upsampled)(structure, rtdose, key, end_cap) for key, structure in structures.items())
    cdvh = {}
    for k in res:
        key = k['key']
        cdvh[structures[key]['name']] = k

    if out_file:
        out_obj = {'participant': name,
                   'DVH': cdvh}
        save(out_obj, out_file)

    return cdvh


if __name__ == '__main__':
    rs_file = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RS.1.2.246.352.71.4.584747638204.248648.20170123083029.dcm'
    rd_file = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RD.1.2.246.352.71.7.584747638204.1750110.20170123082607.dcm'
    rp = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/RP.1.2.246.352.71.5.584747638204.952069.20170122155706.dcm'
    #
    # #

    f_2017 = r'/home/victor/Dropbox/Plan_Competition_Project/competition_2017/All Required Files - 23 Jan2017/PlanIQ Criteria TPS PlanIQ matched str names - TXT Fromat - Last mod Jan23.txt'

    rs_dicom = ScoringDicomParser(filename=rs_file)
    rt_dose = ScoringDicomParser(filename=rd_file)
    structures = rs_dicom.GetStructures()
    ptv56 = structures[27]

    struc_teste = Structure(ptv56)
    lower = 5320.00

    ci = struc_teste.calc_conformation_index(rt_dose, lower)
    print(ci)


    # f_2017 = r'C:\Users\Victor\Dropbox\Plan_Competition_Project\competition_2017\All Required Files - 23 Jan2017\PlanIQ Criteria TPS PlanIQ matched str names - TXT Fromat - Last mod Jan23.txt'
    # constrains, scores, criteria = read_scoring_criteria(f_2017)

    # rs_file = r'C:\Users\Victor\Dropbox\Plan_Competition_Project\competition_2017\All Required Files - 23 Jan2017\RS.1.2.246.352.71.4.584747638204.248648.20170123083029.dcm'
    # rp = r'C:\Users\Victor\Dropbox\Plan_Competition_Project\competition_2017\All Required Files - 23 Jan2017\RP.1.2.246.352.71.5.584747638204.952069.20170122155706.dcm'
    # rd_file = r'C:\Users\Victor\Dropbox\Plan_Competition_Project\competition_2017\All Required Files - 23 Jan2017\RD.1.2.246.352.71.7.584747638204.1750110.20170123082607.dcm'

    # obj = Participant(rp, rs_file, rd_file)
    # obj.set_participant_data('Ahmad')
    # val = obj.eval_score(constrains_dict=constrains, scores_dict=scores)
