# @kai

# this is a module that provides a wrapper for a single imagery and all the imagery inside the dataset

from __future__ import print_function
import os
import glob
import xml.etree.ElementTree as ET
import json
from collections import OrderedDict
from datetime import datetime
import math
import numpy as np


class SatImg(object):
    def __init__(self, path):
        # check if path is absolute
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        if path[-1] != '/':
            path = path + '/'
        self.path = path
        # search for .NTF file
        files = glob.glob(os.path.join(self.path, '*.NTF'))
        if len(files) > 1:
            raise RuntimeError('multiple .NTF files are detected inside {}'.format(self.path))
        img_file = files[0]
        # search for .xml file
        files = glob.glob(os.path.join(self.path, '*.XML'))
        if len(files) > 1:
            raise RuntimeError('multiple .XML files are detected inside {}'.format(self.path))
        meta_file = files[0]

        # double check whether img_file and rpc_file have the same name
        if img_file[:-4] != meta_file[:-4]:
            raise RuntimeError('.NTF and .XML files differ in name inside {}; please double check'.format(self.path))

        self.img_file = os.path.join(self.path, img_file)
        self.meta_file = os.path.join(self.path, meta_file)
        self.key_meta = self.parse_meta()
        # json object
        self.js = OrderedDict([('path', self.path), ('img_file', self.img_file),
                               ('meta_file', self.meta_file), ('key_meta', self.key_meta)])

        self.js_str = json.dumps(self.js, indent=2)

    def parse_meta(self):
        tree = ET.parse(self.meta_file)
        tmp = tree.find('IMD/NUMROWS').text
        rows = int(tmp)
        tmp = tree.find('IMD/NUMCOLUMNS').text
        cols = int(tmp)
        tmp = tree.find('IMD/BITSPERPIXEL').text
        bits = int(tmp)

        bbx = []
        tmp = [tree.find('IMD/BAND_P/ULLON').text, tree.find('IMD/BAND_P/ULLAT').text]
        bbx.append(tuple([float(x) for x in tmp]))
        tmp = [tree.find('IMD/BAND_P/URLON').text, tree.find('IMD/BAND_P/URLAT').text]
        bbx.append(tuple([float(x) for x in tmp]))
        tmp = [tree.find('IMD/BAND_P/LRLON').text, tree.find('IMD/BAND_P/LRLAT').text]
        bbx.append(tuple([float(x) for x in tmp]))
        tmp = [tree.find('IMD/BAND_P/LLLON').text, tree.find('IMD/BAND_P/LLLAT').text]
        bbx.append(tuple([float(x) for x in tmp]))

        time = tree.find('IMD/IMAGE/TLCTIME').text
        time = time[:-1]  # discard the last 'Z' character

        tmp = tree.find('IMD/IMAGE/MEANPRODUCTGSD').text
        GSD = float(tmp)    # unit is meter

        tmp = tree.find('IMD/IMAGE/MEANSUNAZ').text
        sun_az = float(tmp)
        tmp = tree.find('IMD/IMAGE/MEANSUNEL').text
        sun_el = float(tmp)

        tmp = tree.find('IMD/IMAGE/MEANSATAZ').text
        sat_az = float(tmp)
        tmp = tree.find('IMD/IMAGE/MEANSATEL').text
        sat_el = float(tmp)

        tmp = tree.find('IMD/IMAGE/MEANOFFNADIRVIEWANGLE').text
        off_nadir = float(tmp)

        # size is width * height
        # horizontal coordinate: (elevation, azimuth)
        return {'size': (cols, rows), 'bits': bits,
                'bbx': bbx, 'time': time, 'GSD': GSD,
                'sun_posi': (sun_el, sun_az), 'sat_posi': (sat_el, sat_az),
                'off_nadir': off_nadir}

    def get_datetime(self):
        return datetime.strptime(self.key_meta['time'], '%Y-%m-%dT%H:%M:%S.%f')

    # relative path with respect to the site data folder
    def relative_path(self):
        idx = self.path[:-1].rfind('/') + 1
        return self.img_file[idx:], self.meta_file[idx:]


class SiteData(object):
    def __init__(self, path, roi_utm):
        if not os.path.abspath(path):
            path = os.path.abspath(path)
        self.path = path
        self.imgs = []
        for item in os.listdir(self.path):
            img_path = os.path.join(self.path, item)
            if os.path.isdir(img_path):
                self.imgs.append(SatImg(img_path))

        self.imgs.sort(key=lambda img: img.get_datetime())
        self.img_cnt = len(self.imgs)

        self.roi_utm = roi_utm

    def top_k_pairs(self, k, config_dir=None, out_dir=None, tmp_dir=None, template=None):
        subset_pairs = self.pair_selection()
        if len(subset_pairs) > k:
            subset_pairs = subset_pairs[:k]

        if None not in [config_dir, out_dir, tmp_dir, template]:
            if not os.path.exists(config_dir):
                os.mkdir(config_dir)
            if not os.path.exists(out_dir):
                os.mkdir(out_dir)
            if not os.path.exists(tmp_dir):
                os.mkdir(tmp_dir)

            with open(template) as fp:
                config = json.load(fp)
            config['roi_utm'] = self.roi_utm

            cnt = 1
            for (i, j) in subset_pairs:
                # choose the image closer to the nadir as the reference
                if self.imgs[i].key_meta['off_nadir'] > self.imgs[j].key_meta['off_nadir']:
                    tmp = i
                    i = j
                    j = tmp

                config['temporary_dir'] = os.path.join(tmp_dir, 'image_pair_{}'.format(cnt))
                config['out_dir'] = os.path.join(out_dir, 'image_pair_{}'.format(cnt))
                config['images'][0]['img'] = self.imgs[i].img_file
                config['images'][0]['rpc'] = self.imgs[i].meta_file
                config['images'][1]['img'] = self.imgs[j].img_file
                config['images'][1]['rpc'] = self.imgs[j].meta_file

                with open(os.path.join(config_dir, 'config_{}.json'.format(cnt)), 'w') as fp:
                    json.dump(config, fp, indent=2, sort_keys=True)
                cnt += 1

        return [(self.imgs[i], self.imgs[j]) for (i, j) in subset_pairs]

    def pair_selection(self):
        # select a subset
        off_nadir_thres = 40
        subset = [i for i in range(self.img_cnt) if self.imgs[i].key_meta['off_nadir'] < off_nadir_thres]
        subset_cnt = len(subset)
        all_pairs = [(i, j) for i in range(subset_cnt) for j in range(i+1, subset_cnt)]
        subset_pairs = [pair for pair in all_pairs if 5 < self.pair_angle(pair) < 45]
        # sort by time_diff
        subset_pairs.sort(key=self.pair_timediff)

        return subset_pairs

    def pair_timediff(self, pair):
        # ignore year; only consider month, day, hour, minute, second
        dt_0 = self.imgs[pair[0]].get_datetime()
        dt_1 = self.imgs[pair[1]].get_datetime()
        # set to be the same year
        if dt_0.year != dt_1.year:
            dt_0 = dt_0.replace(year=dt_1.year)
        return abs(dt_0 - dt_1)

    def pair_angle(self, pair):
        (i, j) = pair

        (sat_el_i, sat_az_i) = self.imgs[i].key_meta['sat_posi']
        (sat_el_j, sat_az_j) = self.imgs[j].key_meta['sat_posi']

        # covert to radians
        sat_el_i = math.radians(sat_el_i)
        sat_az_i = math.radians(sat_az_i)
        sat_el_j = math.radians(sat_el_j)
        sat_az_j = math.radians(sat_az_j)

        radius = 100.0
        dist_i = radius / math.cos(sat_el_i)
        dist_j = radius / math.cos(sat_el_j)
        az_ij = math.fabs(sat_az_i - sat_az_j)
        if az_ij > math.pi:
            az_ij = 2 * math.pi - az_ij
        ground_dist_ij = 2 * radius * math.sin(az_ij / 2)
        height_dist_ij = radius * math.fabs(math.tan(sat_el_i) - math.tan(sat_el_j))
        dist_ij = math.sqrt(height_dist_ij * height_dist_ij + ground_dist_ij * ground_dist_ij)

        # apply law of cosines
        tmp = (dist_i * dist_i + dist_j * dist_j - dist_ij * dist_ij) / (2 * dist_i * dist_j)
        angle = math.fabs(math.acos(tmp))
        angle = math.degrees(angle)

        return angle

    # generate a stats about dates of the imageries on this site
    def stats_date(self):
        date2cnt_dict = {}
        for img in self.imgs:
            date = img.get_datetime().date().isoformat()
            if date in date2cnt_dict:
                date2cnt_dict[date] += 1
            else:
                date2cnt_dict[date] = 1

        date2cnt_list = sorted(date2cnt_dict.items(), key=lambda t: t[0])
        return date2cnt_list

    def stats_nadir(self):
        off_nadir = [img.key_meta['off_nadir'] for img in self.imgs]
        return min(off_nadir), max(off_nadir), np.mean(off_nadir), np.median(off_nadir)


def test_on_local():
    img = SatImg('/home/kai/satellite_project/dataset/core3d/PAN/jacksonville/14DEC14160402-P1BS-500648062060_01_P001/')

    with open('/home/kai/satellite_project/dataset/core3d/roi_utm.json') as fp:
        js_roi = json.load(fp)
    roi_utm = js_roi['jacksonville']
    site_data = SiteData('/home/kai/satellite_project/dataset/core3d/PAN/jacksonville/', roi_utm)
    print('total number of images: {}'.format(site_data.img_cnt))
    print(site_data.stats_date())
    # inside container
    pairs = site_data.top_k_pairs(10)
    print(site_data.stats_nadir())
    print('test passed!')


def run_on_phoenix():
    site_name = 'jacksonville'
    path_to_roi = '/phoenix/S3/kz298/dataset/core3d/roi_utm.json'
    with open(path_to_roi) as fp:
        js_roi = json.load(fp)
    roi_utm = js_roi[site_name]
    site_data = SiteData('/phoenix/S3/kz298/dataset/core3d/PAN/{}'.format(site_name), roi_utm)
    config_dir = '/phoenix/S3/kz298/result/configs/{}'.format(site_name)
    out_dir = '/phoenix/S3/kz298/result/output/{}'.format(site_name)
    tmp_dir = '/phoenix/S3/kz298/result/temp/{}'.format(site_name)
    template = '/phoenix/S3/kz298/template.json'

    site_data.top_k_pairs(10, config_dir, out_dir, tmp_dir, template)


if __name__ == '__main__':
    run_on_phoenix()
