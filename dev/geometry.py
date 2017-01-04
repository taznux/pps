#
# routine for performing the "point in polygon" inclusion test

# Copyright 2001, softSurfer (www.softsurfer.com)
# This code may be freely used and modified for any purpose
# providing that this copyright notice is included with it.
# SoftSurfer makes no warranty for this code, and cannot be held
# liable for any real or imagined damage resulting from its use.
# Users of this code must verify correctness for their application.

# translated to Python by Maciej Kalisiak <mac@dgp.toronto.edu>
# Numba compilations by Victor Alves <victorgabr@gmail.com>
#   a Point is represented as a tuple: (x,y)

# ===================================================================

# is_left(): tests if a point is Left|On|Right of an infinite line.

#   Input: three points P0, P1, and P2
#   Return: >0 for P2 left of the line through P0 and P1
#           =0 for P2 on the line
#           <0 for P2 right of the line
#   See: the January 2001 Algorithm "Area of 2D and 3D Triangles and Polygons"


import numba as nb
import numpy as np

# ===================================================================

# cn_PnPoly(): crossing number test for a point in a polygon
#     Input:  P = a point,
#             V[] = vertex points of a polygon
#     Return: 0 = outside, 1 = inside
# This code is patterned after [Franklin, 2000]
from numba import njit
from scipy.ndimage import zoom
from shapely.geometry import Polygon


def cn_PnPoly(P, V):
    cn = 0  # the crossing number counter

    # repeat the first vertex at end
    V = tuple(V[:]) + (V[0],)

    # loop through all edges of the polygon
    for i in range(len(V) - 1):  # edge from V[i] to V[i+1]
        if ((V[i][1] <= P[1] and V[i + 1][1] > P[1])  # an upward crossing
            or (V[i][1] > P[1] and V[i + 1][1] <= P[1])):  # a downward crossing
            # compute the actual edge-ray intersect x-coordinate
            vt = (P[1] - V[i][1]) / float(V[i + 1][1] - V[i][1])
            if P[0] < V[i][0] + vt * (V[i + 1][0] - V[i][0]):  # P[0] < intersect
                cn += 1  # a valid crossing of y=P[1] right of P[0]

    return cn % 2  # 0 if even (out), and 1 if odd (in)


# ===================================================================

# wn_PnPoly(): winding number test for a point in a polygon
#     Input:  P = a point,
#             V[] = vertex points of a polygon
#     Return: wn = the winding number (=0 only if P is outside V[])

def wn_PnPoly1(P, V):
    wn = 0  # the winding number counter

    # repeat the first vertex at end
    V = tuple(V[:]) + (V[0],)

    # loop through all edges of the polygon
    for i in range(len(V) - 1):  # edge from V[i] to V[i+1]
        if V[i][1] <= P[1]:  # start y <= P[1]
            if V[i + 1][1] > P[1]:  # an upward crossing
                if is_left(V[i], V[i + 1], P) > 0:  # P left of edge
                    wn += 1  # have a valid up intersect
        else:  # start y > P[1] (no test needed)
            if V[i + 1][1] <= P[1]:  # a downward crossing
                if is_left(V[i], V[i + 1], P) < 0:  # P right of edge
                    wn -= 1  # have a valid down intersect
    return wn


@nb.njit(nb.double(nb.double[:], nb.double[:], nb.double[:]))
def is_left(p0, p1, p2):
    """

       is_left(): tests if a point is Left|On|Right of an infinite line.
    Input:  three points P0, P1, and P2
    Return: >0 for P2 left of the line through P0 and P1
            =0 for P2  on the line
            <0 for P2  right of the line
        See: Algorithm 1 "Area of Triangles and Polygons"
        http://geomalgorithms.com/a03-_inclusion.html

    :param p0: point [x,y] array
    :param p1: point [x,y] array
    :param p2: point [x,y] array
    :return:
    """
    v = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1])
    return v


def cn_PnPoly1(P, V, n):
    """
        cn_PnPoly(): crossing number test for a point in a polygon
             Input:   P = a point,
                       V[] = vertex points of a polygon V[n+1] with V[n]=V[0]
              Return:  0 = outside, 1 = inside
         This code is patterned after [Franklin, 2000]
    :param P:
    :param V:
    :param n:
    :return:
    """
    cn = 0  # the  crossing number counter

    # // loop through all edges of the polygon
    for i in range(n):  # edge from V[i]  to V[i+1]
        if (((V[i][1] <= P[1]) and (V[i + 1][1] > P[1]))  ## an upward crossing
            or ((V[i][1] > P[1]) and (V[i + 1][1] <= P[1]))):  # a downward crossing
            # // compute  the actual edge-ray intersect x-coordinate
            vt = (P[1] - V[i][1]) / (V[i + 1][1] - V[i][1])

            if P[0] < V[i][0] + vt * (V[i + 1][0] - V[i][0]):  # P[0] < intersect
                cn += 1  # a valid crossing of y=P[1] right of P[0]

    return cn % 2 == 0  # 0 if even (out), and 1 if  odd (in)


@nb.njit(nb.int64(nb.double[:], nb.double[:, :]))
def wn_PnPoly(P, polygon):
    wn = 0  # the  winding number counter
    # repeat the first vertex at end
    V = np.zeros((polygon.shape[0] + 1, polygon.shape[1]))
    V[:-1] = polygon
    V[-1] = polygon[0]
    n = len(V)
    # // loop through all edges of the polygon
    for i in range(n - 1):  # edge from V[i] to  V[i+1]
        if V[i][1] <= P[1]:  # start y <= P[1]
            if V[i + 1][1] > P[1]:  # an upward crossing
                if is_left(V[i], V[i + 1], P) > 0:  # P left of  edge
                    wn += 1  # // have  a valid up intersect

        else:  # start y > P[1] (no test needed)
            if V[i + 1][1] <= P[1]:  # a downward crossing
                if is_left(V[i], V[i + 1], P) < 0:  # P right of  edge
                    wn -= 1  # have  a valid down intersect
    return wn


@nb.njit(nb.boolean[:](nb.boolean[:], nb.double[:, :], nb.double[:, :]))
def wn_contains_points(out, poly, points):
    """
        Winding number test for a list of point in a polygon
        Numba implementation 8 - 10 x times faster than matplotlib Path.contains_points()
    :param out: output boolean array
    :param poly: polygon (list of points/vertex)
    :param points: list of points to check inside polygon
    :return: Boolean array
        adapted from c++ code at:
        http://geomalgorithms.com/a03-_inclusion.html

    """
    n = len(points)

    for i in range(n):
        point = points[i]
        wn = 0  # the  winding number counter
        N = len(poly)
        # // loop through all edges of the polygon
        for k in range(N - 1):  # edge from V[i] to  V[i+1]

            if poly[k][1] <= point[1]:  # start y <= P[1]
                if poly[k + 1][1] > point[1]:  # an upward crossing
                    is_left_value = is_left(poly[k], poly[k + 1], point)
                    if is_left_value >= 0:  # P left of  edge
                        wn += 1  # // have  a valid up intersect

            else:  # start y > P[1] (no test needed)
                if poly[k + 1][1] <= point[1]:  # a downward crossing
                    is_left_value = is_left(poly[k], poly[k + 1], point)
                    if is_left_value <= 0:  # P right of  edge
                        wn -= 1  # have  a valid down intersect

            out[i] = wn

    return out


@nb.njit(nb.boolean(nb.double, nb.double, nb.double[:, :]))
def point_inside_polygon(x, y, poly):
    n = len(poly)
    # determine if a point is inside a given polygon or not
    # Polygon is a list of (x,y) pairs.
    p1x = 0.0
    p1y = 0.0
    p2x = 0.0
    p2y = 0.0
    xinters = 0.0
    plx = 0.0
    ply = 0.0
    idx = 0
    inside = False

    # p1x, p1y = poly[0]
    p1x = poly[0][0]
    p1y = poly[0][1]

    for i in range(n + 1):
        idx = i % n
        p2x = poly[idx][0]
        p2y = poly[idx][1]
        # p2x, p2y = poly[idx]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside

        p1x = p2x
        p1y = p2y
        # p1x, p1y = p2x, p2y

    return inside


@nb.njit(nb.boolean[:](nb.boolean[:], nb.double[:, :], nb.double[:, :]))
def contains_points(out, poly, points):
    n = len(points)
    for i in range(n):
        point = points[i]
        tmp = point_inside_polygon(point[0], point[1], poly)
        out[i] = tmp
    return out


@nb.njit(nb.boolean[:](nb.boolean[:], nb.double[:, :], nb.double[:, :]))
def numba_contains_points(out, poly, points):
    n = len(points)
    p1x = 0.0
    p1y = 0.0
    p2x = 0.0
    p2y = 0.0
    xinters = 0.0
    plx = 0.0
    ply = 0.0
    idx = 0
    inside = False
    x = 0
    y = 0
    N = len(poly)

    for i in range(n):
        point = points[i]
        x = point[0]
        y = point[1]
        # tmp = point_inside_polygon(point[0], point[1], poly)
        inside = False

        # determine if a point is inside a given polygon or not
        # Polygon is a list of (x,y) pairs.
        p1x = poly[0][0]
        p1y = poly[0][1]
        for j in range(N + 1):
            idx = j % N
            p2x = poly[idx][0]
            p2y = poly[idx][1]
            # p2x, p2y = poly[idx]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside

            p1x = p2x
            p1y = p2y

        out[i] = inside

    return out


def get_contour_mask_numba(doselut, dosegrid_points, poly):
    """Get the mask for the contour with respect to the dose plane."""

    n = len(dosegrid_points)
    out = np.zeros(n, dtype=bool)
    grid = numba_contains_points(out, poly, dosegrid_points)
    grid = grid.reshape((len(doselut[1]), len(doselut[0])))

    return grid


def get_contour_mask_wn(doselut, dosegrid_points, poly):
    """
        Get the mask for the contour with respect to the dose plane.
    :param doselut: Dicom 3D dose LUT (x,y)
    :param dosegrid_points: dosegrid_points
    :param poly: contour
    :return: contour mask on grid
    """

    n = len(dosegrid_points)
    out = np.zeros(n, dtype=bool)
    # preparing data to wn test
    # repeat the first vertex at end
    poly_wn = np.zeros((poly.shape[0] + 1, poly.shape[1]))
    poly_wn[:-1] = poly
    poly_wn[-1] = poly[0]

    grid = wn_contains_points(out, poly_wn, dosegrid_points)
    grid = grid.reshape((len(doselut[1]), len(doselut[0])))

    return grid


def poly_area(x, y):
    """
         Calculate the area based on the Surveyor's formula
    :param x: x-coordinate
    :param y: y-coordinate
    :return: polygon area-
    """
    return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def centroid_for_polygon(x, y):
    """
        http://en.wikipedia.org/wiki/Centroid#Centroid_of_polygon
    :param x: x-axis coordinates
    :param y: y-axis coordinates
    :return: centroid of polygonF
    """
    area = poly_area(x, y)
    imax = len(x) - 1

    result_x = 0
    result_y = 0
    for i in range(0, imax):
        result_x += (x[i] + x[i + 1]) * ((x[i] * y[i + 1]) - (x[i + 1] * y[i]))
        result_y += (y[i] + y[i + 1]) * ((x[i] * y[i + 1]) - (x[i + 1] * y[i]))

    result_x += (x[imax] + x[0]) * ((x[imax] * y[0]) - (x[0] * y[imax]))
    result_y += (y[imax] + y[0]) * ((x[imax] * y[0]) - (x[0] * y[imax]))
    result_x /= (area * 6.0)
    result_y /= (area * 6.0)

    return result_x, result_y


@nb.njit(nb.boolean(nb.double[:, :], nb.double[:, :]))
def check_contour_inside(contour, largest):
    inside = False
    for i in range(len(contour)):
        point = contour[i]
        p = wn_PnPoly(point, largest)
        if p:
            inside = True
            # Assume if one point is inside, all will be inside
            break
    return inside


if __name__ == '__main__':
    pass


def get_structure_planes(struc):
    sPlanes = struc['planes']

    ## INTERPOLATE PLANES IN Z AXIS
    # Iterate over each plane in the structure
    zval = [z for z, sPlane in sPlanes.items()]
    zval.sort(key=float)

    structure_planes = []
    for z in zval:
        plane_i = sPlanes[z]
        structure_planes.append(np.array(plane_i[0]['contourData']))

    cap_delta = struc['thickness'] / 2
    start_cap = structure_planes[0].copy()
    start_cap[:, 2] = start_cap[:, 2] - cap_delta
    #
    end_cap = structure_planes[-1].copy()
    end_cap[:, 2] = end_cap[:, 2] + cap_delta
    #
    # # extending end caps to original plans
    #
    # structure_planes[0] = start_cap
    # structure_planes[-1] = end_cap
    #
    res = [start_cap] + structure_planes + [end_cap]
    # res = structure_planes
    return res


def k_nearest_neighbors(k, feature_train, features_query):
    """

    :param k: kn neighbors
    :param feature_train: reference 1D array grid
    :param features_query: query grid
    :return: lower and upper neighbors
    """
    ec_dist = abs(feature_train - features_query)

    if k == 1:
        neighbors = ec_dist.argmin()
    else:
        neighbors = np.argsort(ec_dist)[:k]

    return neighbors


def expand_roi(roi_contours, delta):
    """
        Expand ROI contours by delta in X, Y and Z axis.


    :param roi_contours: list of each plane's x,y,z points
    :param delta: delta isotropic expansion
    :return: expanded ROI
    """

    start_cap = roi_contours[0].copy()
    start_cap[:, 2] = start_cap[:, 2] - delta

    end_cap = roi_contours[-1].copy()
    end_cap[:, 2] = end_cap[:, 2] + delta

    # extending end caps to original plans

    roi_contours[0] = start_cap
    roi_contours[-1] = end_cap
    # contour_tmp = [start_cap] + roi_contours + [end_cap]

    contour_tmp = roi_contours
    res = []
    for plane in contour_tmp:
        ctr = Polygon(plane)
        dilated = ctr.buffer(delta)
        dilated_xy = np.array(dilated.exterior.coords)
        zaxis = np.ones((len(dilated_xy), 1)) * plane[0, 2]
        tmp = np.concatenate([dilated_xy, zaxis], axis=1)
        res.append(tmp)

    return res


def calculate_planes_contour_areas(planes):
    """Calculate the area of each contour for the given plane.
       Additionally calculate and return the largest contour index."""
    # Calculate the area for each contour in the current plane
    contours = []
    largest = 0
    largestIndex = 0
    for c, contour in enumerate(planes):
        x = contour[:, 0]
        y = contour[:, 1]
        z = contour[0, 2]

        # Calculate the area based on the Surveyor's formula
        cArea = calc_area(x, y)

        # Remove the z coordinate from the xyz point tuple
        # data = list(map(lambda x: x[0:2], contour[:, :2]))

        # Add the contour area and points to the list of contours
        contours.append({'area': cArea, 'data': contour[:, :2], 'z': z})
        # Determine which contour is the largest
        if cArea > largest:
            largest = cArea
            largestIndex = c

    return contours, largestIndex


def InterpolateDosePlanes(uplane, lplane, fz):
    """Interpolates a dose plane between two bounding planes at the given relative location."""

    # uplane and lplane are the upper and lower dose plane, between which the new dose plane
    #   will be interpolated.
    # fz is the fractional distance from the bottom to the top, where the new plane is located.
    #   E.g. if fz = 1, the plane is at the upper plane, fz = 0, it is at the lower plane.

    # A simple linear interpolation
    doseplane = fz * uplane + (1.0 - fz) * lplane

    return doseplane


def interpolate_plane(ub, lb, location, ubpoints, lbpoints):
    """Interpolates a plane between two bounding planes at the given location."""

    # If the number of points in the upper bound is higher, use it as the starting bound
    # otherwise switch the upper and lower bounds
    # if not (len(ubpoints) >= len(lbpoints)):
    #     lbCopy = lb
    #     lb = ub
    #     ub = lbCopy

    plane = []
    # Determine the closest point in the lower bound from each point in the upper bound
    for u, up in enumerate(ubpoints):
        dist = 100000  # Arbitrary large number
        # Determine the distance from each point in the upper bound to each point in the lower bound
        for l, lp in enumerate(lbpoints):
            newDist = np.sqrt((up[0] - lp[0]) ** 2 + (up[1] - lp[1]) ** 2 + (ub - lb) ** 2)
            # If the distance is smaller, then linearly interpolate the point
            if newDist < dist:
                dist = newDist
                x = lp[0] + (location - lb) * (up[0] - lp[0]) / (ub - lb)
                y = lp[1] + (location - lb) * (up[1] - lp[1]) / (ub - lb)
        if not (dist == 100000):
            plane.append([x, y, location])

    return np.squeeze(plane)


@nb.njit
def interpolate_plane_numba(ub, lb, location, ubpoints, lbpoints):
    """Interpolates a plane between two bounding planes at the given location."""

    # If the number of points in the upper bound is higher, use it as the starting bound
    # otherwise switch the upper and lower bounds
    # if not (len(ubpoints) >= len(lbpoints)):
    #     lbCopy = lb
    #     lb = ub
    #     ub = lbCopy
    tmp = np.zeros(3)
    plane = np.zeros((len(ubpoints), 3))
    # Determine the closest point in the lower bound from each point in the upper bound
    # for u, up in enumerate(ubpoints):
    for u in range(len(ubpoints)):
        up = ubpoints[u]
        dist = 10000000  # Arbitrary large number
        # Determine the distance from each point in the upper bound to each point in the lower bound
        for l in range(len(lbpoints)):
            lp = lbpoints[l]
            newDist = np.sqrt((up[0] - lp[0]) ** 2 + (up[1] - lp[1]) ** 2 + (ub - lb) ** 2)
            # If the distance is smaller, then linearly interpolate the point
            if newDist < dist:
                dist = newDist
                x = lp[0] + (location - lb) * (up[0] - lp[0]) / (ub - lb)
                y = lp[1] + (location - lb) * (up[1] - lp[1]) / (ub - lb)
                tmp[0] = x
                tmp[1] = y
                tmp[2] = location
        if not (dist == 10000000):
            plane[u] = tmp

    return plane


def interp_structure_planes(structure_dict, n_planes=5, verbose=False):
    """
        Interpolates all structures planes inserting interpolated planes centered exactly between
    the original dose plane locations (sorted by z)

    :param structure_dict: RS structure dict object
    :param n_planes: Number of planes to be inserted
    :return: list containing
    """

    # TODO IMPLEMENT ROI SUPERSAMPLING IN X Y Z

    sPlanes = structure_dict['planes']
    dz = structure_dict['thickness'] / 2

    ## INTERPOLATE PLANES IN Z AXIS
    # Iterate over each plane in the structure
    zval = [z for z, sPlane in sPlanes.items()]
    zval.sort(key=float)

    structure_planes = []
    for z in zval:
        plane_i = sPlanes[z]
        structure_planes.append(np.array(plane_i[0]['contourData']))

    # extending a start-end cap slice
    # extending end cap slice by 1/2 CT slice thickness
    start_cap = structure_planes[0].copy()
    start_cap[:, 2] = start_cap[:, 2] - dz

    # extending end cap slice by 1/2 CT slice thickness
    end_cap = structure_planes[-1].copy()
    end_cap[:, 2] = end_cap[:, 2] + dz

    # extending end caps to original plans
    # structure_planes = [start_cap] + structure_planes + [end_cap]
    structure_planes[0] = start_cap
    structure_planes[-1] = end_cap

    # TODO to estimate number of interpolated planes to reach ~ 30000 voxels

    result = []
    result += [structure_planes[0]]
    for i in range(len(structure_planes) - 1):
        ub = structure_planes[i + 1][0][2]
        lb = structure_planes[i][0][2]
        loc = np.linspace(lb, ub, num=n_planes + 2)
        loc = loc[1:-1]
        ubpoints = structure_planes[i + 1]
        lbpoints = structure_planes[i]
        interp_planes = []
        if verbose:
            print('bounds', lb, ub)
            print('interpolated planes: ', loc)

        if not (len(ubpoints) >= len(lbpoints)):
            # if upper bounds does not have more points, swap planes to interpolate
            lbCopy = lb
            lb = ub
            ub = lbCopy
            ubpoints = structure_planes[i]
            lbpoints = structure_planes[i + 1]

        for l in loc:
            pi = interpolate_plane_numba(ub, lb, l, ubpoints, lbpoints)
            interp_planes.append(pi)
        result += interp_planes + [ubpoints]

    # adding last slice to result
    result += [structure_planes[-1]]
    # return planes sorted by z-axis position

    return sorted(result, key=lambda p: p[0][2])


def get_dose_grid(dose_lut):
    # Generate a 2d mesh grid to create a polygon mask in dose coordinates
    # Code taken from Stack Overflow Answer from Joe Kington:
    # http://stackoverflow.com/questions/3654289/scipy-create-2d-polygon-mask/3655582
    # Create vertex coordinates for each grid cell
    x_lut = dose_lut[0]  # zoom(dose_lut[0], super_sampling_fator)
    y_lut = dose_lut[1]  # , super_sampling_fator)

    x, y = np.meshgrid(x_lut, y_lut)
    x, y = x.flatten(), y.flatten()
    dose_grid_points = np.vstack((x, y)).T

    return dose_grid_points


def get_axis_grid(delta_mm, grid_axis):
    """
        Returns the up sampled axis by given resolution in mm

    :param delta_mm: desired resolution
    :param grid_axis: x,y,x axis from LUT
    :return: up sampled axis and delta grid
    """
    fc = (delta_mm + abs(grid_axis[-1] - grid_axis[0])) / (delta_mm * len(grid_axis))
    n_grid = int(round(len(grid_axis) * fc))

    up_sampled_axis, dt = np.linspace(grid_axis[0], grid_axis[-1], n_grid, retstep=True)

    return up_sampled_axis, dt


def get_dose_grid_3d(grid_3d, delta_mm=(2, 2, 2)):
    # Generate a 3d mesh grid to create a polygon mask in dose coordinates
    # adapted from Stack Overflow Answer from Joe Kington:
    # http://stackoverflow.com/questions/3654289/scipy-create-2d-polygon-mask/3655582
    # Create vertex coordinates for each grid cell
    xi = grid_3d[0]
    yi = grid_3d[1]
    zi = grid_3d[2]

    # x_lut = np.linspace(xi[0], xi[-1], len(xi) * super_sampling_fator)
    # y_lut = np.linspace(yi[0], yi[-1], len(yi) * super_sampling_fator)
    # z_lut = np.linspace(zi[0], zi[-1], len(zi) * super_sampling_fator)

    x_lut, x_delta = get_axis_grid(delta_mm[0], xi)
    y_lut, y_delta = get_axis_grid(delta_mm[1], yi)
    z_lut, z_delta = get_axis_grid(delta_mm[2], zi)

    xg, yg = np.meshgrid(x_lut, y_lut)
    xf, yf = xg.flatten(), yg.flatten()
    dose_grid_points = np.vstack((xf, yf)).T

    up_dose_lut = [x_lut, y_lut, z_lut]

    spacing = [x_delta, x_delta, z_delta]

    return dose_grid_points, up_dose_lut, spacing


def get_z_planes(struc_planes, ordered_z, z_interp_positions):
    result = []
    for zi in z_interp_positions:
        if zi not in ordered_z:
            # get grid knn
            kn = k_nearest_neighbors(2, ordered_z, zi)
            # define upper and lower bounds
            if kn[1] < kn[0]:
                l_idx = kn[1]
                u_idx = l_idx + 1
                if u_idx >= len(struc_planes):
                    u_idx = -1
                    l_idx = kn[0]
            else:
                l_idx = kn[0]
                u_idx = kn[1]

            # get upper and lower z values and contour points
            ub = struc_planes[u_idx][0][2]
            lb = struc_planes[l_idx][0][2]
            ub_points = struc_planes[u_idx]
            lb_points = struc_planes[l_idx]

            if not (len(ub_points) >= len(lb_points)):
                # if upper bounds does not have more points, swap planes to interpolate
                lbCopy = lb
                lb = ub
                ub = lbCopy
                ub_points = struc_planes[l_idx]
                lb_points = struc_planes[u_idx]

            interp_plane = interpolate_plane_numba(ub, lb, zi, ub_points, lb_points)
            result += [interp_plane]

        else:
            ec_dist = abs(ordered_z - zi)
            neighbor = ec_dist.argmin()
            result += [struc_planes[neighbor]]

    return result


@nb.njit(nb.double(nb.double[:], nb.double[:]))
def calc_area(x, y):
    cArea = 0
    # Calculate the area based on the Surveyor's formula
    for i in range(0, len(x) - 1):
        cArea = cArea + x[i] * y[i + 1] - x[i + 1] * y[i]
    cArea = abs(cArea / 2.0)

    return cArea
