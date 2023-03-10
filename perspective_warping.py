# ======= imports
import numpy as np
import matplotlib.pyplot as plt
import cv2


# ======= helper functions
def plot_image(image, title=""):
    plt.figure(figsize=(10,10))
    plt.imshow(image)
    plt.title(title)
    plt.show()


def extract_keypoints_and_descriptors(image):
    feature_extractor = cv2.SIFT_create()
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return feature_extractor.detectAndCompute(gray_image, None)


def find_matches(desc1, desc2):
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(desc1, desc2, k=2)
    return np.asarray([m for m in matches if m[0].distance/m[1].distance < 1])[:, 0]


def find_homography(kp_from, kp_to, matches):
    good_kp_from = np.array([kp_from[m.trainIdx].pt for m in matches])
    good_kp_to = np.array([kp_to[m.queryIdx].pt for m in matches])
    return cv2.findHomography(good_kp_from, good_kp_to, cv2.RANSAC, 5.0), good_kp_from, good_kp_to


def warp_images(back, front, H):
    height, width = back.shape[:2]
    warped_front = cv2.warpPerspective(front, H, (width, height))
    back[warped_front > 0] = warped_front[warped_front > 0]
    return back
    

# ======= constants
ORIGINAL_VIDEO_PATH = r'Videos\original.mp4'
WARPED_VIDEO_PATH = r'Videos\warped.mp4'
TEMPLATE_IMAGE_PATH = r'Images\louvre.png'
ANOTHER_IMAGE_PATH = r'Images\dog.png'
OUTPUT_VIDEO_SHAPE = (1920, 1080)


if __name__ == '__main__':

    # ======= template image keypoint and descriptors
    template = cv2.imread(TEMPLATE_IMAGE_PATH)
    template_height, template_width = template.shape[:2]
    template_kp, template_desc = extract_keypoints_and_descriptors(template)

    # ======= video input, output and metadata
    capture = cv2.VideoCapture(ORIGINAL_VIDEO_PATH)

    fps = int(capture.get(cv2.CAP_PROP_FPS))
    frame_width  = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    num_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))    
    codec = cv2.VideoWriter_fourcc(*"mp4v")
    color = True
    plot_delay = 1000 // fps

    writer = cv2.VideoWriter(WARPED_VIDEO_PATH, codec, fps, OUTPUT_VIDEO_SHAPE, color)

    print(f'Processing {num_frames} frames of size {frame_width}x{frame_height}, {num_frames / fps:.2f} seconds, {fps} f/s')

    # ======= run on all frames
    for _ in range(num_frames):

        frame = capture.read()[1]
        frame = cv2.resize(frame, OUTPUT_VIDEO_SHAPE)

        # ======= find key points matches of frame and template
        # we saw this in the SIFT notebook
        frame_kp, frame_desc = extract_keypoints_and_descriptors(frame)
        good_matches = find_matches(frame_desc, template_desc)

        # ======= find homography
        # also in SIFT notebook
        (H, masked), _, _ = find_homography(template_kp, frame_kp, good_matches)

        # +++++++ do warping of another image on template image
        # we saw this in SIFT notebook
        another = cv2.imread(ANOTHER_IMAGE_PATH)
        another = cv2.resize(another, (template_width, template_height))
        warped = warp_images(frame, another, H)

        # ======= plot and save frame 
        writer.write(warped)

    # ======= end all
    capture.release()
    writer.release()
