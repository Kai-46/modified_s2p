# test the affine approximation error of rpc

from s2plib.rpc_model import RPCModel
import numpy as np
# import random


def check_approx(ul_x, ul_y, w, h, rpc_model):
    # number of grid points along each axis
    # x: lat, y: lon, z: elev
    x_num = 20
    y_num = 20
    z_num = 1000
    x_axis_points = np.linspace(ul_x, ul_x + h, x_num)
    y_axis_points = np.linspace(ul_y, ul_y + w, y_num)
    z_axis_points = np.linspace(-1, 1, z_num)

    point_cnt = x_num * y_num * z_num
    grid_points = np.zeros([point_cnt, 3])
    row_points = np.zeros([point_cnt, 1])
    col_points = np.zeros([point_cnt, 1])

    for x in range(x_num):
        for y in range(y_num):
            for z in range(z_num):
                idx = x * y_num * z_num + y * z_num + z
                grid_points[idx, :] = [x_axis_points[x], y_axis_points[y], z_axis_points[z]]
                (col, row) = rpc_model.inverse_estimate_norm(x_axis_points[x], y_axis_points[y], z_axis_points[z])
                row_points[idx] = row
                col_points[idx] = col

    A = np.hstack((grid_points, np.ones([point_cnt, 1])))
    row_result = np.linalg.lstsq(A, row_points, rcond=None)
    row_coeff = row_result[0]
    # row_res = np.sqrt(row_result[1] / point_cnt)

    col_result = np.linalg.lstsq(A, col_points, rcond=None)
    col_coeff = col_result[0]
    # col_res = np.sqrt(col_result[1] / point_cnt)

    # l2_res = np.sqrt((row_result[1] + col_result[1]) / point_cnt)

    # compute maximum residuals
    all_row_res = A.dot(row_coeff) - row_points
    all_col_res = A.dot(col_coeff) - col_points
    row_max_res = np.linalg.norm(all_row_res, ord=np.inf)
    col_max_res = np.linalg.norm(all_col_res, ord=np.inf)
    # max_res = np.linalg.norm(np.sqrt(all_row_res ** 2 + all_col_res ** 2), ord=np.inf)

    # print('row_coeff: {}'.format(row_coeff))
    # print('col_coeff: {}'.format(col_coeff))
    # print('row_res: {}, col_res: {}, l2_res: {}'.format(row_res, col_res, l2_res))
    # print('row_max_res: {}, col_max_res: {}, max_res: {}'.format(row_max_res, col_max_res, max_res))

    # print('row_scale: {}, col_scale: {}'.format(rpc_model.linScale, rpc_model.colScale))
    # print('row_max_error: {}, col_max_error: {}'.format(rpc_model.linScale * row_max_res, rpc_model.colScale * col_max_res))
    row_max_error = rpc_model.linScale * row_max_res
    col_max_error = rpc_model.colScale * col_max_res

    # check the accuracy of the inverse affine model
    esti_grid_points = np.zeros([point_cnt, 3])
    A = np.hstack((row_coeff[0:2], col_coeff[0:2])).T
    for i in range(point_cnt):
        (x, y, z) = grid_points[i, :]
        row = row_points[i]
        col = col_points[i]
        b = np.array([row - row_coeff[2] * z - row_coeff[3],
                      col - col_coeff[2] * z - col_coeff[3]])
        tmp = np.linalg.lstsq(A, b, rcond=None)
        (x1, y1) = tmp[0]
        esti_grid_points[i, :] = [x1, y1, z]

    # res = np.sqrt(np.sum((esti_grid_points - grid_points) ** 2) / point_cnt)
    # print('res: {}'.format(res))
    # print('lon_scale: {}, lat_scale: {}'.format(rpc_model.lonScale, rpc_model.latScale))
    x_max_res = np.linalg.norm(esti_grid_points[:, 0] - grid_points[:, 0], ord=np.inf)
    y_max_res = np.linalg.norm(esti_grid_points[:, 1] - grid_points[:, 1], ord=np.inf)
    # print('lon_max_error: {}, lat_max_error: {}'.format(x_max_res * rpc_model.lonScale, y_max_res * rpc_model.latScale))

    lon_max_error = y_max_res * rpc_model.lonScale
    lat_max_error = x_max_res * rpc_model.latScale

    return row_max_error, col_max_error, lon_max_error, lat_max_error


rpc_file = '/Users/kai/modified_s2p/14DEC14160402-P1BS-500648062060_01_P001.XML'
rpc_model = RPCModel(rpc_file)

row_tile_cnt = 40
col_tile_cnt = 40

w = 2.0 / col_tile_cnt
h = 2.0 / row_tile_cnt

approx_result = np.zeros([row_tile_cnt * col_tile_cnt, 4])
for i in range(row_tile_cnt):
    ul_x = -1 + i * h
    for j in range(col_tile_cnt):
        ul_y = -1 + j * w
        idx = i * col_tile_cnt + j
        approx_result[idx, :] = check_approx(ul_x, ul_y, w, h, rpc_model)
        print('iter: {}, ul: {}, {}, result: {}'.format(idx, ul_x, ul_y, approx_result[idx, :]))

print('mean: {}'.format(np.mean(approx_result, axis=0)))
