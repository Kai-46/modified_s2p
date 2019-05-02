import numpy as np
import numpy_groupies as npg


# points: each row is (xx, yy, zz)
# xoff: ul_e
# yoff: ul_n
# xsize: width
# ysize: height
def proj_to_grid(points, xoff, yoff, xresolution, yresolution, xsize, ysize):
    # first create a place holder
    group_idx = np.arange(xsize * ysize).astype(dtype=np.int)
    group_val = np.empty(xsize * ysize)
    group_val.fill(np.nan)

    row = np.floor((yoff - points[:, 1]) / xresolution).astype(dtype=np.int)
    col = np.floor((points[:, 0] - xoff) / yresolution).astype(dtype=np.int)
    points_group_idx = row * xsize + col
    points_val = points[:, 2]

    # remove points that lie out of the dsm boundary
    mask = np.logical_and(points_group_idx >=0, points_group_idx < xsize * ysize)
    points_group_idx = points_group_idx[mask]
    points_val = points_val[mask]

    group_idx = np.concatenate((group_idx, points_group_idx))
    group_val = np.concatenate((group_val, points_val))

    dsm = npg.aggregate(group_idx, group_val, func='nanmax', fill_value=np.nan)
    dsm = dsm.reshape((ysize, xsize))

    # try to fill very small holes
    dsm_new = dsm.copy()
    nan_places = np.argwhere(np.isnan(dsm_new))
    for i in range(nan_places.shape[0]):
        row = nan_places[i, 0]
        col = nan_places[i, 1]
        neighbors = []
        for j in range(row-1, row+2):
            for k in range(col-1, col+2):
                if j >= 0 and j < dsm_new.shape[0] and k >=0 and k < dsm_new.shape[1]:
                    val = dsm_new[j, k]
                    if not np.isnan(val):
                        neighbors.append(val)

        if neighbors:
            dsm[row, col] = np.median(neighbors)

    return dsm


if __name__ == '__main__':
    pass
