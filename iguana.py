import cv2
import numpy as np
import os


def load_yolo():
    net = cv2.dnn.readNet("darknet/yolov3.weights", "darknet/cfg/yolov3.cfg")
    classes = []
    with open("darknet/data/coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layers_names = net.getLayerNames()
    # print(f"layers_names: {layers_names}")
    unconnected = net.getUnconnectedOutLayers()

    # output_layers = [layers_names[i[0] - 1]
    #                  for i in unconnected]
    output_layers = [layers_names[i - 1]
                     for i in unconnected]
    return net, classes, output_layers


def detect_objects(image, net, output_layers, classes, target):
    height, width, channels = image.shape
    blob = cv2.dnn.blobFromImage(image, scalefactor=0.00392, size=(
        416, 416), mean=(0, 0, 0), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    confidences = []
    class_ids = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            thing = classes[class_id]
            confidence = scores[class_id]
            # print(
            #     f"found {thing} ({confidence*100}%)") if confidence > 0.5 else None
            if confidence > 0.5 and classes[class_id] == target:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                confidences.append(float(confidence))
                class_ids.append(class_id)
    return confidences, class_ids


def main():
    net, classes, output_layers = load_yolo()

    input_folder = "/Users/ecohen/Documents/LR/Camera/1947-1979/"
    output_folder = f"{target} pictures"
    output_no_folder = f"{target} free pictures"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(output_no_folder):
        os.makedirs(output_no_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_folder, filename)
            image = cv2.imread(image_path)

            confidences, class_ids = detect_objects(
                image, net, output_layers, classes, target)

            if len(class_ids) > 0:
                print(
                    f"Found a {target} in '{filename}'. Saving to '{output_folder}'...")
                output_path = os.path.join(output_folder, filename)
                cv2.imwrite(output_path, image)
            else:
                print(
                    f"No {target} found in '{filename}'. Saving to '{output_no_folder}'...")
                output_path = os.path.join(output_no_folder, filename)
                cv2.imwrite(output_path, image)


target = "car"
if __name__ == "__main__":
    main()
