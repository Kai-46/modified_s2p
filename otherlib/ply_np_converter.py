from .plyfile import PlyData, PlyElement
import numpy as np


def np2ply(vertex, out_ply, color=None, comments=None, text=False, text_fmt=None):
    if color is not None:
        data = np.hstack((vertex, color))
    else:
        data = vertex
    dim = data.shape[1]

    data = list(zip(*[data[:, i] for i in range(dim)]))
    if dim == 3:
        vertex = np.array(data, dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
    else:
        vertex = np.array(data, dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                                    ('red', 'uint8'), ('green', 'uint8'), ('blue', 'uint8')])

    el = PlyElement.describe(vertex, 'vertex')
    if text:
        if text_fmt is None:
            if color is None:
                text_fmt = ['%.18g', '%.18g', '%.18g']
            else:
                text_fmt = ['%.18g', '%.18g', '%.18g', '%i', '%i', '%i']

        if comments is None:
            PlyData([el], text=True, text_fmt=text_fmt).write(out_ply)
        else:
            PlyData([el], text=True, text_fmt=text_fmt, comments=comments).write(out_ply)
    else:
        if comments is None:
            PlyData([el], byte_order='<').write(out_ply)
        else:
            PlyData([el], byte_order='<', comments=comments).write(out_ply)


def ply2np(in_ply, return_comments=False, only_xyz=True):
    ply = PlyData.read(in_ply)
    comments = ply.comments

    vertex = ply['vertex'].data
    names = vertex.dtype.names

    data = []
    if 'x' in names:
        data.append(np.hstack((vertex['x'].reshape((-1, 1)),
                              vertex['y'].reshape((-1, 1)),
                              vertex['z'].reshape((-1, 1)))))
    if not only_xyz:
        if 'nx' in names:
            data.append(np.hstack((vertex['nx'].reshape((-1, 1)),
                                  vertex['ny'].reshape((-1, 1)),
                                  vertex['nz'].reshape((-1, 1)))))
        if 'red' in names:
            data.append(np.hstack((vertex['red'].reshape((-1, 1)),
                                  vertex['green'].reshape((-1, 1)),
                                  vertex['blue'].reshape((-1, 1)))))

    data = np.hstack(tuple(data))
    if return_comments:
        return data, comments
    else:
        return data


if __name__ == '__main__':
    data = np.random.randn(500, 9)

    np2ply(data, '/data2/tmp.ply')

    ply2np('/data2/tmp.ply')