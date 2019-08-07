"""
! left handed coordinate, z-up, y-forward
! left to right rotation matrix multiply: v'=vR
! non-standard quaternion multiply
"""

import numpy as np


def normalize(x):
    return x / max(np.linalg.norm(x), 1e-12)


def dcm_from_axis(x_dir, y_dir, z_dir, order):
    assert order in ['yzx', 'yxz', 'xyz', 'xzy', 'zxy', 'zyx']

    axis = {'x': x_dir, 'y': y_dir, 'z': z_dir}
    name = ['x', 'y', 'z']    
    idx0 = name.index(order[0])
    idx1 = name.index(order[1])
    idx2 = name.index(order[2])

    axis[order[0]] = normalize(axis[order[0]])
    axis[order[1]] = normalize(np.cross(
        axis[name[(idx1 + 1) % 3]], axis[name[(idx1 + 2) % 3]]
    ))   
    axis[order[2]] = normalize(np.cross(
        axis[name[(idx2 + 1) % 3]], axis[name[(idx2 + 2) % 3]]
    ))

    dcm = np.asarray([axis['x'], axis['y'], axis['z']])

    return dcm


def dcm2quat(dcm):
    q = np.zeros([4])
    tr = np.trace(dcm)

    if tr > 0:
        sqtrp1 = np.sqrt(tr + 1.0)
        q[0] = 0.5 * sqtrp1
        q[1] = (dcm[1, 2] - dcm[2, 1]) / (2.0 * sqtrp1)
        q[2] = (dcm[2, 0] - dcm[0, 2]) / (2.0 * sqtrp1)
        q[3] = (dcm[0, 1] - dcm[1, 0]) / (2.0 * sqtrp1)
    else:
        d = np.diag(dcm)
        if d[1] > d[0] and d[1] > d[2]:
            sqdip1 = np.sqrt(d[1] - d[0] - d[2] + 1.0)
            q[2] = 0.5 * sqdip1

            if sqdip1 != 0:
                sqdip1 = 0.5 / sqdip1

            q[0] = (dcm[2, 0] - dcm[0, 2]) * sqdip1
            q[1] = (dcm[0, 1] + dcm[1, 0]) * sqdip1
            q[3] = (dcm[1, 2] + dcm[2, 1]) * sqdip1

        elif d[2] > d[0]:
            sqdip1 = np.sqrt(d[2] - d[0] - d[1] + 1.0)
            q[3] = 0.5 * sqdip1

            if sqdip1 != 0:
                sqdip1 = 0.5 / sqdip1

            q[0] = (dcm[0, 1] - dcm[1, 0]) * sqdip1
            q[1] = (dcm[2, 0] + dcm[0, 2]) * sqdip1
            q[2] = (dcm[1, 2] + dcm[2, 1]) * sqdip1

        else:
            sqdip1 = np.sqrt(d[0] - d[1] - d[2] + 1.0)
            q[1] = 0.5 * sqdip1

            if sqdip1 != 0:
                sqdip1 = 0.5 / sqdip1

            q[0] = (dcm[1, 2] - dcm[2, 1]) * sqdip1
            q[2] = (dcm[0, 1] + dcm[1, 0]) * sqdip1
            q[3] = (dcm[2, 0] + dcm[0, 2]) * sqdip1

    return q


def quat_dot(q0, q1):
    original_shape = q0.shape
    q0 = np.reshape(q0, [-1, 4])
    q1 = np.reshape(q1, [-1, 4])

    w0, x0, y0, z0 = q0[:, 0], q0[:, 1], q0[:, 2], q0[:, 3]
    w1, x1, y1, z1 = q1[:, 0], q1[:, 1], q1[:, 2], q1[:, 3]
    q_product = w0 * w1 + x1 * x1 + y0 * y1 + z0 * z1
    q_product = np.expand_dims(q_product, axis=1)
    q_product = np.tile(q_product, [1, 4])

    return np.reshape(q_product, original_shape)


def quat_inverse(q):
    original_shape = q.shape
    q = np.reshape(q, [-1, 4])

    q_conj = [q[:, 0], -q[:, 1], -q[:, 2], -q[:, 3]]
    q_conj = np.stack(q_conj, axis=1)
    q_inv = np.divide(q_conj, quat_dot(q_conj, q_conj))

    return np.reshape(q_inv, original_shape)


def quat_mul(q0, q1):
    original_shape = q0.shape
    q1 = np.reshape(q1, [-1, 4, 1])
    q0 = np.reshape(q0, [-1, 1, 4])
    terms = np.matmul(q1, q0)
    w = terms[:, 0, 0] - terms[:, 1, 1] - terms[:, 2, 2] - terms[:, 3, 3]
    x = terms[:, 0, 1] + terms[:, 1, 0] - terms[:, 2, 3] + terms[:, 3, 2]
    y = terms[:, 0, 2] + terms[:, 1, 3] + terms[:, 2, 0] - terms[:, 3, 1]
    z = terms[:, 0, 3] - terms[:, 1, 2] + terms[:, 2, 1] + terms[:, 3, 0]

    q_product = np.stack([w, x, y, z], axis=1)
    return np.reshape(q_product, original_shape)


def quat_divide(q, r):
    return quat_mul(quat_inverse(r), q)


def quat2euler(q, order='zxy', eps=1e-8):
    original_shape = list(q.shape)
    original_shape[-1] = 3
    q = np.reshape(q, [-1, 4])

    q0 = q[:, 0]
    q1 = q[:, 1]
    q2 = q[:, 2]
    q3 = q[:, 3]

    if order == 'zxy':
        x = np.arcsin(np.clip(2 * (q0 * q1 + q2 * q3), -1 + eps, 1 - eps))
        y = np.arctan2(2 * (q0 * q2 - q1 * q3), 1 - 2 * (q1 * q1 + q2 * q2))
        z = np.arctan2(2 * (q0 * q3 - q1 * q2), 1 - 2 * (q1 * q1 + q3 * q3))
        euler = np.stack([z, x, y], axis=1)
    else:
        raise ValueError('Not implemented')

    return np.reshape(euler, original_shape)