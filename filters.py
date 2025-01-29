import cv2
import numpy as np

def apply_sobel(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    sobel = cv2.sqrt(sobelx**2 + sobely**2)
    sobel = cv2.convertScaleAbs(sobel)
    return cv2.cvtColor(sobel, cv2.COLOR_GRAY2BGR)

def apply_gaussian(frame):
    return cv2.GaussianBlur(frame, (15, 15), 0)

def apply_salt_pepper(frame):
    row, col, ch = frame.shape
    s_vs_p = 0.0001
    amount = s_vs_p

    # Sal
    num_salt = int(np.ceil(amount * frame.size * 0.5))
    coords_salt = [np.random.randint(0, i - 1, num_salt) for i in frame.shape]
    frame[coords_salt[0], coords_salt[1], :] = 255

    # Pimenta
    num_pepper = int(np.ceil(amount * frame.size * 0.5))
    coords_pepper = [np.random.randint(0, i - 1, num_pepper) for i in frame.shape]
    frame[coords_pepper[0], coords_pepper[1], :] = 0

    return frame

def apply_gray(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
