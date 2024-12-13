import cv2
import numpy as np

# Load the image
image_path = 'path/to/your/image.jpg'
image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
if image is None: # Check if image is loaded successfully
    print(f"Error: Unable to load image {image_path}")

# Apply GaussianBlur to reduce noise and improve contour detection
blurred = cv2.GaussianBlur(image, (5, 5), 0)

# Apply a binary threshold to the image
_, binary = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

# Create an empty mask
mask = np.zeros_like(image)

# Draw the largest contour on the mask
if contours:
    cv2.drawContours(mask, contours, 0, 255, -1)  # -1 fills the contour

# Save the mask
mask_path = 'path/to/save/mask.bmp'
cv2.imwrite(mask_path, mask)

# Display the mask
cv2.imshow('Binary Mask', mask)
cv2.waitKey(0)
cv2.destroyAllWindows()

print(f"Mask created and saved as {mask_path}")
