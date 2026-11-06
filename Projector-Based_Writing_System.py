import cv2
import numpy as np
import time 


#events = [i for i in dir(cv2) if 'EVENT' in i]
#print( events )

idx = []

def calibrate(event,x,y,flags,param):
	if event == cv2.EVENT_LBUTTONDOWN: # Handle a left mouse click during calibration.
		global idx
	idx.append((x,y))

# Open the webcam.
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

#frame_h, frame_w, _ = frame.shape()
#print(frame_h)
#print(frame_w)

cal = np.ones((1080,1920, 3), np.uint8) * 255
cal = cv2.rectangle(cal, (1,1), (1920 - 2, 1080 - 2), (0,0,255), 10)

# Show the calibration image in full-screen mode.
cv2.namedWindow("Kalibration", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Kalibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.imshow("Kalibration", cal)
ret, frame = cap.read()
#frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
frame_copy = frame

if cv2.waitKey(0) == ord('q'):
	ret, frame = cap.read()
	cv2.destroyAllWindows()
	cv2.namedWindow("Frame", cv2.WINDOW_NORMAL)
	cv2.setWindowProperty("Frame", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
	cv2.setMouseCallback('Frame',calibrate)
	#cv2.putText(frame, text='Bereits angeklickte Ecken' + str(len(idx)), org=(50, 50), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6, color=(0, 0, 255),thickness=1)
	cv2.imshow("Frame", frame)
	time.sleep(0.1)

if cv2.waitKey(0) == ord('q'):
	# Sort the selected corner points.
	abstand = []
	x = []
	abstand.append(idx[0][0] * idx[0][1])
	abstand.append(idx[1][0] * idx[1][1])
	abstand.append(idx[2][0] * idx[2][1])
	abstand.append(idx[3][0] * idx[3][1])
	idx_final = [[],[],[],[]]
	idx_final[0] = idx[abstand.index(min(abstand))]
	idx_final[1] = idx[abstand.index(max(abstand))]
	idx.remove(idx_final[0])
	idx.remove(idx_final[1])
	x.append(idx[0][0])
	x.append(idx[1][0])
	idx_final[2] = idx[x.index(min(x))]
	idx.remove(idx_final[2])
	idx_final[3] = idx[0]

	print(idx_final)
	pts_src = np.float32([idx_final[0],idx_final[1],idx_final[2],idx_final[3]])
	pts_dst = np.float32([[0,0],[1920 - 1,1080 - 1],[0,1080 - 1],[1920 - 1,0]])
	h = cv2.getPerspectiveTransform(pts_src, pts_dst)

drawing = np.zeros((1080 - 1, 1920 - 1), np.uint16)
drawing_b = np.zeros((1080 - 1, 1920 - 1), np.uint16)
drawing_g = np.zeros((1080 - 1, 1920 - 1), np.uint16)
zero = np.zeros((1080 - 1, 1920 - 1), np.uint8)
drawing_bgr = np.zeros((1080 - 1,1920 - 1, 3), np.uint8)
color = "green"
cv2.namedWindow("Drawing", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("Drawing", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)



with open('Zeiten.txt', 'w') as f:

	while True: 

		time_begin = time.time_ns()
		ret, frame = cap.read()
		f.write('Bildaufnahmezeit: ' + str((time.time_ns() - time_begin) / 1000000) + ' ms\n')
		if ret: 
			time_warp = time.time_ns()
			frame_scaled = cv2.warpPerspective(frame, h, (drawing.shape[1],drawing.shape[0]))
			f.write('Warptime: ' + str((time.time_ns() - time_warp) / 1000000) + ' ms\n')
			# A red Plexiglass filter and grayscale conversion work well here.
			frame_gray = cv2.cvtColor(frame_scaled, cv2.COLOR_BGR2GRAY)
			#print(np.max(frame_gray))
			rot = frame_gray[:,:] > 180			# The threshold may need adjustment for ambient light.
			rot = rot * 255 # Scale the binary mask to 8-bit intensity.
			rot = rot.astype(np.uint8)	# Convert to 8-bit pixels.

			# Calculate the X and Y center of the detected light pixels.
			coordinates = np.column_stack(np.where(rot == 255))
			mean_y = np.mean(coordinates[:, 0])		# Y coordinate in the image.
			mean_x = np.mean(coordinates[:, 1])		# X coordinate in the image.

			# Choose an action based on the detected point's position.
			if mean_x > 1800:	# In the menu area.
				if mean_y > 2*(1080/3):		# Green drawing color.
					color = "green"
				elif mean_y > (1080/3):		# Blue drawing color.
					color = "blue"
				elif mean_y > (1080/6):		# Eraser.
					color = "clear"
				else:	# Clear the entire drawing.
					drawing_bgr = np.zeros((1080 - 1,1920 - 1, 3), np.uint8)
					drawing_b = np.zeros((1080 - 1, 1920 - 1), np.uint16)
					drawing_g = np.zeros((1080 - 1, 1920 - 1), np.uint16)

			else:	# In the drawing area.
				if color == "green":
					drawing_g = drawing_g.astype(np.uint16)
					drawing_g = rot + drawing_g		# Add detected pixels to the drawing.
					drawing_g = np.where(drawing_g >= 254, 255, 0)	# Keep drawing pixels binary.
					drawing_g = drawing_g.astype(np.uint8)	# Convert to 8-bit pixels.
				elif color == "blue":
					drawing_b = drawing_b.astype(np.uint16)
					drawing_b = rot + drawing_b		# Add detected pixels to the drawing.
					drawing_b = np.where(drawing_b >= 254, 255, 0)	# Keep drawing pixels binary.
					drawing_b = drawing_b.astype(np.uint8)	# Convert to 8-bit pixels.
				elif color == "clear":
					# Erase a circular area around the detected point.
					if mean_y > 0 and mean_x > 0:
						drawing_b = cv2.circle(drawing_b, (int(mean_x),int(mean_y)),40,0,-1)
						drawing_g = cv2.circle(drawing_g, (int(mean_x),int(mean_y)),40,0,-1)

			drawing_bgr[:,:,0] = drawing_b
			drawing_bgr[:,:,1] = drawing_g
			drawing_bgr[:,:,2] = zero

			drawing_bgr = cv2.rectangle(drawing_bgr, (1800,1), (1920 - 2, int(1080/6)), (255,255,0), -1)
			drawing_bgr = cv2.rectangle(drawing_bgr, (1800,int(1080/6)), (1920 - 2, int(1080/3)), (150,255,0), -1)
			drawing_bgr = cv2.rectangle(drawing_bgr, (1800,int(1080/3)), (1920 - 2, int(2*1080/3)), (255,0,0), -1)
			drawing_bgr = cv2.rectangle(drawing_bgr, (1800,int(2*1080/3)), (1920 - 2, 1080 - 2), (0,255,0), -1)
			drawing_bgr = cv2.rectangle(drawing_bgr, (1,1), (1920 - 2, 1080 - 2), (0,255,0), 10)

			cv2.imshow("Drawing", drawing_bgr)

		else:
			print("Error: cannot access the webcam.")
		if cv2.waitKey(1) == ord('q'):
			break

		FPS = 1/((time.time_ns() - time_begin) / 1000000000)
		f.write("FPS: " + str(FPS) + '\n')
		f.write("Gesamtdauer Schleife: " + str((time.time_ns() - time_begin) / 1000000) + " ms\n")

#cv2.imwrite('Menu.png', drawing_bgr)
cap.release()
cv2.destroyAllWindows()