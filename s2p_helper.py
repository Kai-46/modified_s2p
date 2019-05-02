# use my approximate camera model to perform triangulation instead of using the RPC model

# python port of c/disp2ply.c

import numpy as np

# triangulate a match given the 3*4 projection matrices
def triangulate(proj_mat_ref, proj_mat_sec, pref, psec):
    # formulate a linear equation
    row1 = proj_mat_ref[0:1, :] - pref[0] * proj_mat_ref[2:3, :]
    row2 = proj_mat_ref[1:2, :] - pref[1] * proj_mat_ref[2:3, :]
    row3 = proj_mat_sec[0:1, :] - psec[0] * proj_mat_sec[2:3, :]
    row4 = proj_mat_sec[1:2, :] - psec[1] * proj_mat_sec[2:3, :]

    tmp = np.vstack((row1, row2, row3, row4))
    A = tmp[:, 0:3]
    b = -tmp[:, 3]
    x = np.linalg.lstsq(A, b, rcond=-1)[0]

    return x

# read projection matrices of our approximate camera
# ref: '18DEC15WV031000015DEC18140533-P1BS-500515572050_01_P001_________AAE_0AAAAABPABJ0.NTF'
#      '/data2/kz298/mvs3dm_result/Explorer/images/0037_WV03_15DEC18_40533-P1BS-500515572050_01_P001.png'
# sec: '18DEC15WV031000015DEC18140522-P1BS-500515572020_01_P001_________AAE_0AAAAABPABJ0.NTF'
#      '/data2/kz298/mvs3dm_result/Explorer/images/0036_WV03_15DEC18_40522-P1BS-500515572020_01_P001.png'

import json

camera_dict_file = '/data2/kz298/mvs3dm_result/Explorer/colmap/sfm_perspective/init_ba_camera_dict.json'
geo_grid_file = '/data2/kz298/mvs3dm_result/Explorer/geo_grid.json'
view_ref = '0031_WV03_15OCT22_40432-P1BS-500497282010_01_P001.png'
view_sec = '0032_WV03_15OCT23_41928-P1BS-500497285030_01_P001.png'
with open(camera_dict_file) as fp:
    camera_dict = json.load(fp)

from pyquaternion import Quaternion

def parse_params(params):
    size = params[0:2]
    fx = params[2]
    fy = params[3]
    cx = params[4]
    cy = params[5]
    s = params[6]

    qvec = params[7:11]
    tvec = params[11:14]

    K = np.array([[fx, s, cx],
                  [0., fy, cy],
                  [0., 0., 1.]])
    R = Quaternion(qvec[0], qvec[1], qvec[2], qvec[3]).rotation_matrix
    t = np.array(tvec).reshape((3, 1))
    P = np.dot(K, np.hstack((R, t)))

    return P

proj_mat_ref = parse_params(camera_dict[view_ref])
proj_mat_sec = parse_params(camera_dict[view_sec])

ul_col_ref = 13743
ul_row_ref = 15691
ul_col_sec = 14576
ul_row_sec = 13392

tile_dir = '/bigdata/kz298/s2p_phoenix_results_new/explorer/pair_24/tiles/row_0015713_height_1041/col_0013760_width_1081'
import os
# read rectifying homography
href = np.loadtxt(os.path.join(tile_dir, 'pair_1/H_ref.txt'))
hsec = np.loadtxt(os.path.join(tile_dir, 'pair_1/H_sec.txt'))

href_inv = np.linalg.inv(href)
hsec_inv = np.linalg.inv(hsec)

from otherlib.dsm_util import read_tif_without_header
# read disparity map
disparity = read_tif_without_header(os.path.join(tile_dir, 'pair_1/rectified_disp.tif'))
w = disparity.shape[1]
h = disparity.shape[0]

import imageio
# read mask size
mask = read_tif_without_header(os.path.join(tile_dir, 'pair_1/rectified_mask.png'))
ww = mask.shape[1]
hh = mask.shape[0]

assert (ww == w and hh == h)

# read color image
color_image = imageio.imread(os.path.join(tile_dir, 'rectified_ref.png'))

# read tile bounding box
with open(os.path.join(tile_dir, 'config.json')) as fp:
    config = json.load(fp)
roi = config['roi']
col_m = roi['x']
col_M = col_m + roi['w']
row_m = roi['y']
row_M = row_m + roi['h']

all_points = []
cnt = 0
for row in range(h):
    for col in range(w):
        if mask[row, col] < 1.0:
            continue

        # compute coordinates of pix in the full reference image
        tmp = np.dot(href_inv, np.array([col, row, 1.0]).reshape((3, 1)))
        tmp = tmp.reshape((3, ))
        p = [tmp[0]/tmp[2], tmp[1]/tmp[2]]

        # check that it lies in the image domain bounding box
        if (round(p[0]) < col_m or round(p[0]) > col_M or
            round(p[1]) < row_m or round(p[1]) > row_M):
            continue

        # compute the enu coordinates of the 3D point
        dx = disparity[row, col]
        tmp = np.dot(hsec_inv, np.array([col + dx, row, 1.0]).reshape((3, 1)))
        tmp = tmp.reshape((3, ))
        q = [tmp[0]/tmp[2], tmp[1]/tmp[2]]

        # note that it needs to mapped to local pixel coordinates
        # in order to apply the approximate camera model
        p = [p[0]-ul_col_ref, p[1]-ul_row_ref]
        q = [q[0]-ul_col_sec, q[1]-ul_row_sec]

        # triangulate points
        x = triangulate(proj_mat_ref, proj_mat_sec, p, q)

        # colorize point
        gray = color_image[row, col]

        cnt += 1
        print('triangulated {} points'.format(cnt))
        all_points.append(x.tolist() + [gray, gray, gray])

all_points = np.array(all_points)

# save to file
np.save(os.path.join(tile_dir, 'my_point_cloud.npy'), all_points)
from otherlib.ply_np_converter import np2ply
np2ply(all_points[:, 0:3], os.path.join(tile_dir, 'my_point_cloud.ply'), all_points[:, 3:6])

# convert to utm
from otherlib.latlonalt_enu_converter import enu_to_latlonalt
with open(geo_grid_file) as fp:
    geo_grid = json.load(fp)
lat0 = geo_grid['observer_lat']
lon0 = geo_grid['observer_lon']
alt0 = geo_grid['observer_alt']

xx = all_points[:, 0:1]
yy = all_points[:, 1:2]
zz = all_points[:, 2:3]
xx, yy, zz = enu_to_latlonalt(xx, yy, zz, lat0, lon0, alt0)

from otherlib.latlon_utm_converter import latlon_to_eastnorh
xx, yy = latlon_to_eastnorh(xx, yy)

np.save(os.path.join(tile_dir, 'my_point_cloud_utm.npy'), np.hstack((xx, yy, zz, all_points[:, 3:6])))
np2ply(np.hstack((xx, yy, zz)), os.path.join(tile_dir, 'my_point_cloud_utm.ply'),
       all_points[:, 3:6], comments=['projection: UTM 21S',])


from otherlib.dsm_util import read_dsm_tif, write_dsm_tif
dsm, meta = read_dsm_tif(os.path.join(tile_dir, 'dsm.tif'))
np.save(os.path.join(tile_dir, 'dsm.npy'), dsm)

from otherlib.proj_to_grid import proj_to_grid
print('meta: {}'.format(meta))
# meta['ul_northing'] = 6182707.000   # manually align
dsm = proj_to_grid(np.hstack((xx, yy, zz)), meta['ul_easting'], meta['ul_northing'],
                   meta['east_resolution'], meta['north_resolution'], meta['img_width'], meta['img_height'])
np.save(os.path.join(tile_dir, 'my_dsm.npy'), dsm)
write_dsm_tif(dsm, meta, os.path.join(tile_dir, 'my_dsm.tif'))