from photostereo import photometry
import cv2 as cv
import time
import numpy as np
import os

IMAGES = 12
root_fold = "C:\Users\lilli\Documents\GitHub\22753-cultural-heritage-imaging\py\cultural_heritage_imaging\images\clip"
obj_name = "clip."
format = ".tiff"
light_manual = False

# Debugging: Check if the directory exists (absolute path)
print(f"Checking absolute path: {root_fold}")

if not os.path.exists(root_fold):
    print(f"Error: Directory {root_fold} does not exist.")
else:
    print(f"Absolute path {root_fold} exists.")
    print("Directory contents:", os.listdir(root_fold))

# Load input image array
image_array = []
for id in range(0, IMAGES):
    filename = os.path.join(root_fold, f"{obj_name}{id}{format}")
    print(f"Loading image: {filename}")
    im = cv.imread(filename, cv.IMREAD_GRAYSCALE)
    if im is not None:
        image_array.append(im)
    else:
        print(f"Warning: Image {filename} not found or cannot be read.")

myps = photometry(IMAGES, True)

if light_manual:
    # SETTING LIGHTS MANUALLY
    slants = [71.4281, 66.8673, 67.3586, 67.7405]
    tilts = [140.847, 47.2986, -42.1108, -132.558]
    slants = [42.9871, 49.5684, 45.9698, 43.4908]
    tilts = [-137.258, 140.542, 44.8952, -48.3291]

    myps.setlmfromts(tilts, slants)
    print(myps.settsfromlm())
else:
    # LOADING LIGHTS FROM FILE
    light_mat_path = os.path.join(root_fold, "LightMatrix.yml")
    print(f"Loading light matrix: {light_mat_path}")
    fs = cv.FileStorage(light_mat_path, cv.FILE_STORAGE_READ)
    if not fs.isOpened():
        print(f"Error: {light_mat_path} cannot be opened.")
    else:
        fn = fs.getNode("Lights")
        light_mat = fn.mat()
        myps.setlightmat(light_mat)
        fs.release()

# Load mask
mask_path = os.path.join(root_fold, "mask.bmp")
print(f"Loading mask: {mask_path}")
mask = cv.imread(mask_path, cv.IMREAD_GRAYSCALE)
if mask is None:
    print(f"Error: Mask {mask_path} cannot be read.")
    mask = np.ones_like(image_array[0], dtype=np.uint8)  # Default mask if not found

# Run photometry algorithm
tic = time.process_time()
try:
    normal_map = myps.runphotometry(image_array, np.asarray(mask, dtype=np.uint8))
    normal_map = cv.normalize(normal_map, None, 0, 255, cv.NORM_MINMAX, cv.CV_8UC3)
    albedo = myps.getalbedo()
    albedo = cv.normalize(albedo, None, 0, 255, cv.NORM_MINMAX, cv.CV_8UC1)
except TypeError as e:
    print(f"An error occurred: {e}")

toc = time.process_time()
print("Process duration: " + str(toc - tic))

# Save results
cv.imwrite('normal_map.png', normal_map)
cv.imwrite('albedo.png', albedo)

# Display results
cv.imshow("normal", normal_map)
cv.waitKey(0)
cv.destroyAllWindows()
