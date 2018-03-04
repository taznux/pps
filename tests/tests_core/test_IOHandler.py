import os

from core.calculation import PyStructure, DVHCalculationMP
from core.io import IOHandler

from tests.conftest import DATA_DIR


def test_dvh_data(lens, body, brain, ptv70, spinal_cord, dose_3d):
    # calculating DVH
    grid_up = (0.2, 0.2, 0.2)
    structures_dicom = [lens, body, brain, ptv70, spinal_cord]
    structures_py = [PyStructure(s) for s in structures_dicom]
    grids = [grid_up, None, None, None, None]
    calc_mp = DVHCalculationMP(dose_3d, structures_py, grids, verbose=True)
    dvh_data = calc_mp.calculate_dvh_mp()

    obj = IOHandler(dvh_data)
    assert obj.dvh_data

    # saving dvh file
    file_path = os.path.join(DATA_DIR, "test_dvh.dvh")
    obj = IOHandler(dvh_data)
    obj.to_dvh_file(file_path)

    obj = IOHandler(dvh_data)
    f_dvh_dict = obj.read_dvh_file(file_path)
    assert f_dvh_dict == dvh_data

    file_path = os.path.join(DATA_DIR, "test_json_dvh.jdvh")
    obj = IOHandler(dvh_data)
    obj.to_json_file(file_path)

    obj = IOHandler(dvh_data)
    j_dvh_dict = obj.read_json_file(file_path)

    assert j_dvh_dict == dvh_data