import cv2
import numpy as np
import random

def whiteBalance(img):
	randomPoolSize = 100
	selectionPoolSize = 20
	height, width, colors = img.shape #y, x, color
	randomPixels = map(lambda id: img[random.randint(0, height-1), random.randint(0, width-1)], range(0, randomPoolSize))
	randomPixels = map(lambda gbr: (int(gbr[2]), int(gbr[0]), int(gbr[1])), randomPixels)
	filtered = filter(lambda (r, g, b): r<255 and g<255 and b<255, randomPixels)
	sortedArr = sorted(filtered, key=lambda (r, g, b): r+g+b)
	brigthest = sortedArr[max(0, len(sortedArr)-selectionPoolSize):]
	(r, g, b) = reduce(lambda (r1, g1, b1), (r2, g2, b2): (r1+r2, g1+g2, b1+b2), brigthest, (0,0,0))
	(r, g, b) = (r/len(brigthest), g/len(brigthest), b/len(brigthest))
	average = (r+g+b)/3
	(dr, dg, db) = (r-average, g-average, b-average)
	print (dr, dg, db)
	# avert overflow of uint8 [0,255]
	img[:,:,:] *= (255-max(dr, dg, db))/255.0
	img[:,:,:] += max(dr, dg, db)
	img[:,:,0] -= dg
	img[:,:,1] -= db
	img[:,:,2] -= dr
	return img

# img is a raw color image. findEdges returns a binary image where white is edge.
def findEdges(img):
	kernel = np.ones((5,5), np.uint8)
	erosion = cv2.erode(img, kernel, iterations=1)
	dilation = cv2.dilate(img, kernel, iterations=1)
	difference = dilation - erosion
	grey = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
	(_, binarized) = cv2.threshold(grey, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
	return binarized

# img should be a binary image showing edges. findPaper returns a contour with
# 4 points that is the outline of the paper.
def findPaper(img):
	(contours, _) = cv2.findContours(img.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	contours = sorted(contours, key = cv2.contourArea, reverse = True)

	# loop over the contours
	for contour in contours:
		# approximate the contour
		perimeter = cv2.arcLength(contour, True)
		approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

		# if our approximated contour has four points, then we
		# can assume that we have found our paper
		if len(approx) == 4:
			return approx

# img should be a binary image showing edges. findPaper returns a contour with
# 4 points that is the outline of the paper.
def findPaper(img):
	(contours, _) = cv2.findContours(img.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
	contours = sorted(contours, key=lambda contour: cv2.arcLength(contour, True), reverse = True)

	# loop over the contours
	for contour in contours:
		# approximate the contour
		perimeter = cv2.arcLength(contour, True)
		approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

		# if our approximated contour has four points, then we
		# can assume that we have found our paper
		if len(approx) == 4:
			return approx


# img is the raw color image. paper is the contour with four-points that
# outlines the paper in img. extractPaper returns a color image that is
# 1100x850 (US Letter paper) of the perspective-corrected paper.
def extractPaper(img, paper):
	# Figure out the orientation.
	dist01 = np.linalg.norm(paper[0] - paper[1])
	dist03 = np.linalg.norm(paper[0] - paper[3])
	horizontal = dist01 > dist03
	paper = np.array([paper[0] if horizontal else paper[1], paper[1] if horizontal else paper[2], paper[2] if horizontal else paper[3], paper[3] if horizontal else paper[0]], np.float32)

	# us letter: 8.5 by 11
	source = np.array([[0,850], [1100,850], [1100,0], [0,0]], np.float32)
	transformMatrix = cv2.getPerspectiveTransform(paper, source)
	transformed = cv2.warpPerspective(img, transformMatrix, (1100, 850))
	return transformed
  

def withImage(img):
	imgCopy = img.copy()
	
	edges = findEdges(img)
	paper = findPaper(edges)
	extracted = extractPaper(img, paper)
	extractedCopy = extracted.copy()
	
	whiteBalancedImage = whiteBalance(extracted)
	hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
	
	# TODO: connect red component paths / find crossings
	#~ Threshold the HSV image, keep only the red pixels
	#Python: cv2.inRange(src, lowerb, upperb[, dst])  dst
	# For HSV, Hue range is [0,179], Saturation range is [0,255] and Value range is [0,255].
	lower_red_hue_range = cv2.inRange(hsv_image, (0, 190, 50), (20, 255, 255))
	upper_red_hue_range = cv2.inRange(hsv_image, (160, 190, 50), (179, 255, 255))
	red_hue_image = cv2.addWeighted(lower_red_hue_range, 1.0, upper_red_hue_range, 1.0, 0.0)
	
	return [imgCopy, extractedCopy, whiteBalancedImage]
