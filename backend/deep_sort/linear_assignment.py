import numpy as np
from scipy.optimize import linear_sum_assignment


def linear_assignment(cost_matrix, threshold):
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int)
    
    indices = linear_sum_assignment(cost_matrix)
    indices = np.array(indices).T
    
    return indices


def iou_distance(tracks, detections):
    if len(tracks) == 0 or len(detections) == 0:
        return np.zeros((len(tracks), len(detections)))
    
    cost_matrix = np.zeros((len(tracks), len(detections)))
    for i, track in enumerate(tracks):
        for j, det in enumerate(detections):
            cost_matrix[i, j] = 1.0 - iou(track.to_tlbr(), det.to_tlbr())
    
    return cost_matrix


def iou(bbox1, bbox2):
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    
    union_area = area1 + area2 - inter_area
    
    if union_area == 0:
        return 0
    
    return inter_area / union_area


def min_cost_distance(tracks, detections, track_indices=None, detection_indices=None):
    if track_indices is None:
        track_indices = list(range(len(tracks)))
    if detection_indices is None:
        detection_indices = list(range(len(detections)))
    
    cost_matrix = np.zeros((len(track_indices), len(detection_indices)))
    for row, track_idx in enumerate(track_indices):
        for col, det_idx in enumerate(detection_indices):
            cost_matrix[row, col] = 1.0 - iou(
                tracks[track_idx].to_tlbr(),
                detections[det_idx].to_tlbr()
            )
    
    return cost_matrix
