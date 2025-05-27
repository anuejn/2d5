import tempfile, urllib.request
import numpy as np
import cv2

i = 0
while True:
    i += 1
    with tempfile.NamedTemporaryFile() as f:
        urllib.request.urlretrieve("http://192.168.0.251:8080", f.name)
        data = np.fromfile(f.name, dtype=np.uint8)

    a = data.reshape((-1, 8))[:, 3]

    width = 1144 // 2
    image = a[:len(a)//width*width].reshape((-1, width))
    print(image.shape)
    cv2.imshow("live", 255 - image)
    cv2.imwrite(f"test{i}.png", 255 - image)
    key = cv2.waitKey(10)
    print("frame")
