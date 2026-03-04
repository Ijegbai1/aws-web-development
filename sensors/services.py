import numpy as np
from collections import deque

def contact_area_pct(frame_32x32, lower_threshold=200):
    arr = np.array(frame_32x32, dtype=np.int32)
    total = arr.size
    above = int((arr > lower_threshold).sum())
    return (above / total) * 100.0

def peak_pressure_index(frame_32x32, min_region_pixels=10, lower_threshold=200):
    """
    Peak Pressure Index: max pressure in any connected region (4-neighbour)
    where region pixels are above lower_threshold AND region size >= min_region_pixels.
    If no region qualifies, return max of whole frame (or 0).
    """
    arr = np.array(frame_32x32, dtype=np.int32)
    mask = arr > lower_threshold
    h, w = mask.shape

    visited = np.zeros_like(mask, dtype=bool)
    best_peak = 0

    def neighbors(r, c):
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < h and 0 <= nc < w:
                yield nr, nc

    for r in range(h):
        for c in range(w):
            if mask[r, c] and not visited[r, c]:
                q = deque([(r, c)])
                visited[r, c] = True
                coords = []
                local_peak = int(arr[r, c])

                while q:
                    cr, cc = q.popleft()
                    coords.append((cr, cc))
                    local_peak = max(local_peak, int(arr[cr, cc]))
                    for nr, nc in neighbors(cr, cc):
                        if mask[nr, nc] and not visited[nr, nc]:
                            visited[nr, nc] = True
                            q.append((nr, nc))

                if len(coords) >= min_region_pixels:
                    best_peak = max(best_peak, local_peak)

    if best_peak == 0:
        best_peak = int(arr.max())
    return best_peak

def high_pressure(frame_32x32, high_threshold=2000, hotspot_pixels=10):
    """
    True if at least hotspot_pixels are above high_threshold.
    """
    arr = np.array(frame_32x32, dtype=np.int32)
    return int((arr > high_threshold).sum()) >= hotspot_pixels
