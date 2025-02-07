from pyplanscoring.core.geometry import get_dose_grid_3d, get_contour_roi_grid, calculate_contour_areas


def test_dose_max_3d_location(dose_3d, rd_dcm):
    location = dose_3d.dose_max_location
    assert len(location) == 3
    # check value inside grid range
    grid = rd_dcm.get_grid_3d()

    for i in range(len(location)):
        assert grid[i].min() <= location[i] <= grid[i].max()


def test_image_resolution(dose_3d):
    # test dose image resolution x,y,z
    assert dose_3d.x_res == 2.5
    assert dose_3d.y_res == 2.5
    assert dose_3d.z_res == 3.0


def test_xyx_size(dose_3d, rd_dcm):
    grid = rd_dcm.get_grid_3d()
    assert dose_3d.x_size == len(grid[0])
    assert dose_3d.y_size == len(grid[1])
    assert dose_3d.z_size == len(grid[2])


def test_get_z_dose_plane(dose_3d, rd_dcm, body, plot_flag):
    grid = rd_dcm.get_grid_3d()
    zi = '100.50'
    grid_delta = (0.2, 0.2, 3)
    # test get z at position 0 mm and no lookup table
    dose_0 = dose_3d.get_z_dose_plane(float(zi))

    # test_high resolution xy grid
    dose_grid_points, up_dose_lut, spacing = get_dose_grid_3d(grid, delta_mm=grid_delta)
    dose_1 = dose_3d.get_z_dose_plane(float(zi), up_dose_lut)

    # plot brain dose contour at using rasterisation window
    brain_slices = list(body['planes'].keys())
    brain_slices.sort(key=float)

    slice_i = body['planes'][zi]
    contours, largest_index = calculate_contour_areas(slice_i)
    # contour
    contour_points = contours[0]['data']
    contour_dose_grid, ctr_dose_lut = get_contour_roi_grid(contour_points, delta_mm=grid_delta, fac=1)
    dose_2 = dose_3d.get_z_dose_plane(float(zi), ctr_dose_lut)
    if plot_flag:
        import matplotlib.pyplot as plt
        plt.imshow(dose_0, interpolation='none')
        plt.title("Dose at axis z: {} mm - grid resolution: 2.5 mm x 2.5 mm".format(zi))
        plt.figure()
        plt.imshow(dose_1, interpolation='none')
        plt.title("Dose at axis z: {} mm - grid resolution: 0.1 mm x 0.1 mm".format(zi))
        plt.figure()
        plt.imshow(dose_2, interpolation='none')
        plt.title("Windowed Dose at axis z: {} mm - grid resolution: 0.1 mm x 0.1 mm".format(zi))
        plt.show()


def test_get_dose_to_point(dose_3d):
    # test dose max location
    dose_max = dose_3d.dose_max_3d
    location = dose_3d.dose_max_location
    d_teste = dose_3d.get_dose_to_point(location)
    assert d_teste == dose_max


def test_sum_dose_3d():
    # TODO add this validation test
    # # path to 4 dicom files
    # # path to 4 dicom files
    # rd_file1 = '/home/victor/Dropbox/Plan_Competition_Project/tests/tests_data/left_chest_wall/RD.1.2.246.352.71.7.584747638204.1901407.20180402142345.dcm'
    # rd_file2 = '/home/victor/Dropbox/Plan_Competition_Project/tests/tests_data/left_chest_wall/RD.1.2.246.352.71.7.584747638204.1901882.20180404145404.dcm'
    # rd_file3 = '/home/victor/Dropbox/Plan_Competition_Project/tests/tests_data/left_chest_wall/RD.1.2.246.352.71.7.584747638204.1901887.20180404145404.dcm'
    # rd_file4 = '/home/victor/Dropbox/Plan_Competition_Project/tests/tests_data/left_chest_wall/RD.1.2.246.352.71.7.584747638204.1901890.20180402152703.dcm'
    #
    # rd_files = [rd_file1, rd_file2, rd_file3, rd_file4]
    # doses_3d = [PyDicomParser(filename=rd_file).get_dose_3d() for rd_file in rd_files]
    # dose_matrix_shapes_mm = np.array([d.xyz_size for d in doses_3d])
    # max_grid_idx = dose_matrix_shapes_mm.argmax(axis=0)
    # # getting sum grid
    # x_sum = doses_3d[max_grid_idx[0]].grid[0]
    # y_sum = doses_3d[max_grid_idx[1]].grid[1]
    # z_sum = doses_3d[max_grid_idx[2]].grid[2]
    #
    # grid_sum = (x_sum, y_sum, z_sum)
    #
    # # getting interpolated matrixes on grid_sum
    # tmp_dose3d = [d.get_interpolated_3d_matrix(grid_sum) for d in doses_3d]
    # plan_sum_arr = sum(tmp_dose3d)
    #
    # acc = DoseAccumulation(doses_3d)
    # plan_sum = acc.get_plan_sum()
    # np.testing.assert_array_almost_equal(plan_sum_arr, plan_sum.values)
    pass
