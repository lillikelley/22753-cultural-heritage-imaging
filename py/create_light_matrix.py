import cv2 as cv
import numpy as np

# Example light directions
light_directions = np.array([
    [0.6, 0.8, 1.0],
    [0.8, 0.6, 1.0],
    [0.6, -0.8, 1.0],
    [-0.8, 0.6, 1.0]
])

# Save to LightMatrix.yml
fs = cv.FileStorage('LightMatrix.yml', cv.FILE_STORAGE_WRITE)
fs.write("Lights", light_directions)
fs.release()
