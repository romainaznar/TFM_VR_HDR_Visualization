import os

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"

import cv2
import numpy as np
import glob

def extract_luminance_sat_from_exr(exr_path):
    img = cv2.imread(exr_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None

    if len(img.shape) == 3 and img.shape[2] >= 3:
        bgr = img[:, :, :3].astype(np.float64)

        b = bgr[:, :, 0]
        g = bgr[:, :, 1]
        r = bgr[:, :, 2]

        gray = 0.2126 * r + 0.7152 * g + 0.0722 * b
    else:
        gray = img.astype(np.float64)

    gray_flipped = np.flipud(gray)
    sat_flipped = np.cumsum(np.cumsum(gray_flipped, axis=0), axis=1)
    sat = np.flipud(sat_flipped)
    
    return sat

current_dir = os.getcwd()

anchor_files = glob.glob(os.path.join(current_dir, "*_left.exr"))
suffixes = ['_left', '_right', '_bottom', '_top', '_front', '_back']

for anchor_path in anchor_files:
    base_path = anchor_path.rsplit('_left.exr', 1)[0]
    prefix_name = os.path.basename(base_path)
    
    sat_list = []
    
    for suffix in suffixes:
        file_path = f"{base_path}{suffix}.exr"

        sat_table = extract_luminance_sat_from_exr(file_path)
        sat_list.append(sat_table)
        
    horizontal_atlas = np.hstack(sat_list)
    atlas_32 = horizontal_atlas.astype(np.float32)
    
    output_path = f"{base_path}_sat_atlas.exr"
    cv2.imwrite(output_path, atlas_32)