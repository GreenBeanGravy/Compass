import cv2
import numpy as np
import pyautogui
import ctypes
import time
from accessible_output2.outputs.auto import Auto

# Define the VK codes for the "H" and "ALT" keys
VK_H = 0x48
VK_ALT = 0x12

# Define the minimum white shape size and the region of interest
min_shape_size = 1500  # Adjust this value as needed
roi_start_orig = (621, 182)  # Top-left corner of the region of interest
roi_end_orig = (1342, 964)  # Bottom-right corner of the region of interest

# Store whether the 'ALT + H' key combination was previously down
alt_h_key_down = False

# Define accessible output
ao2 = Auto()

def get_compass_direction(vector):
    # Adjust for the different coordinate system
    adjusted_vector = np.array([vector[0], -vector[1]])

    # Calculate the angle in degrees from the vector to the positive x axis
    degree = np.degrees(np.arctan2(adjusted_vector[1], adjusted_vector[0]))

    # Normalize the degree to be within [0, 360)
    degree = (degree + 360) % 360

    compass_brackets = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    compass_labels = ['East', 'Northeast', 'North', 'Northwest', 'West', 'Southwest', 'South', 'Southeast']

    for i, val in enumerate(compass_brackets):
        if degree < val:
            return compass_labels[i]
    
    return 'East'

while True:
    # Check if the 'H' and 'ALT' keys are down
    h_key_current_state = bool(ctypes.windll.user32.GetAsyncKeyState(VK_H) & 0x8000)
    alt_key_current_state = bool(ctypes.windll.user32.GetAsyncKeyState(VK_ALT) & 0x8000)

    # If the 'ALT + H' key combination was just pressed
    if h_key_current_state and alt_key_current_state and not alt_h_key_down:
        # Take a screenshot
        screenshot = pyautogui.screenshot()

        # Convert the screenshot to a numpy array and resize it
        screenshot_np = np.array(screenshot)
        screenshot_np = cv2.resize(screenshot_np, None, fx=4, fy=4, interpolation=cv2.INTER_LINEAR)

        # Adjust the region of interest according to the new size
        roi_start = tuple(4 * np.array(roi_start_orig))
        roi_end = tuple(4 * np.array(roi_end_orig))

        # Crop the screenshot to the region of interest
        roi_color = screenshot_np[roi_start[1]:roi_end[1], roi_start[0]:roi_end[0]]

        # Convert the cropped screenshot to grayscale
        roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGR2GRAY)

        # Apply a binary threshold. All pixels with a value greater than 230 will be considered white.
        # You can adjust this value as needed.
        _, thresholded = cv2.threshold(roi_gray, 210, 255, cv2.THRESH_BINARY)

        # Find contours in the thresholded image. Each contour corresponds to a white shape in the original image.
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Calculate the area of the contour
            area = cv2.contourArea(contour)

            # If the area of the contour is greater than the minimum size, it's a match
            if area > min_shape_size:
                # Calculate the center of mass of the contour
                M = cv2.moments(contour)
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
                center_mass = (cX, cY)

                # Draw the contour and center of mass of the shape on the image
                cv2.drawContours(roi_color, [contour], -1, (0, 255, 0), 2)
                cv2.circle(roi_color, center_mass, 5, (255, 0, 0), -1)

                # Calculate the convex hull of the contour
                hull = cv2.convexHull(contour)

                if len(hull) > 2:
                    vertices = np.squeeze(hull)
                    distances = [np.linalg.norm(vertices[i] - center_mass) for i in range(len(vertices))]
                    farthest_vertex_index = np.argmax(distances)
                    farthest_vertex = vertices[farthest_vertex_index]
                    
                    # Draw the arrow pointing in the direction of the farthest vertex
                    cv2.arrowedLine(roi_color, tuple(np.int0(center_mass)), tuple(np.int0(farthest_vertex)), (0, 255, 0), 2)
                    
                    direction_vector = farthest_vertex - np.array(center_mass)
                    compass_direction = get_compass_direction(direction_vector)
                    ao2.speak(f"You are facing {compass_direction}")

                # Save the image
                cv2.imwrite(f'shape_{time.time()}.png', roi_color)

                break

    # Store the current state of the 'ALT + H' key combination for the next iteration
    alt_h_key_down = h_key_current_state and alt_key_current_state
