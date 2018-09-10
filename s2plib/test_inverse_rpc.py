from s2plib.rpc_model import RPCModel
import random

rpc_file = '/home/kai/satellite_project/dataset/core3d/PAN/jacksonville/14DEC14160402-P1BS-500648062060_01_P001/14DEC14160402-P1BS-500648062060_01_P001.XML'

rpc_model = RPCModel(rpc_file)

test_iter = 500000
total_iter = 0
max_dev_X = -100000
max_dev_Y = -100000
max_dev_Z = -100000
for i in range(test_iter):
    x = random.uniform(-1, 1)
    y = random.uniform(-1, 1)
    z = random.uniform(-1, 1)

    X = rpc_model.lonScale * x + rpc_model.lonOff
    Y = rpc_model.latScale * y + rpc_model.latOff
    Z = rpc_model.altScale * z + rpc_model.altOff

    (C, R, Z) = rpc_model.inverse_estimate(X, Y, Z)
    (X1, Y1, Z1, n) = rpc_model.direct_estimate(C, R, Z)

    total_iter += n

    if abs(X1[0] - X) > max_dev_X:
        max_dev_X = abs(X1[0] - X)

    if abs(Y1[0] - Y) > max_dev_Y:
        max_dev_Y = abs(Y1[0] - Y)

    if abs(Z1 - Z) > max_dev_Z:
        max_dev_Z = abs(Z1 - Z)

    print('iter: {}, avg. iter: {}'.format(i + 1, float(total_iter) / (i + 1)))

print('max dev: {},{},{}'.format(max_dev_X, max_dev_Y, max_dev_Z))
