import os
from matplotlib.image import imread
import numpy as np
import time
import tensorflow as tf
from skimage.transform import resize


def predict_image(image):
    model_dir = 'D:\\Python\\deep_learning\\FINAL_TF2_FILES\\TF_2_Notebooks_and_Data\\04-CNNs\\trash_classification_inceptionv3.keras'
    model = tf.keras.models.load_model(model_dir)

    img = resize(image, (224, 224, 3))
    img = np.expand_dims(img, axis=0) 

    prediction = model.predict(img)[0]

    class_labels = [
        'batlua',
        'book',
        'cans',
        'cardboard',
        'daulocthuocla',
        'glass trash',
        'khautrang',
        'milk_carton',
        'nylon',
        'paper',
        'pen',
        'pin',
        'plastic_bottle',
        'thietbidientu'
    ]

    predicted_index = np.argmax(prediction)
    predicted_label = class_labels[predicted_index]
    confidence = float(prediction[predicted_index])

    return predicted_label, confidence

def continous_prediction(file_path):

    file_name = os.path.basename(file_path)
    file_extension = os.path.splitext(file_name)[1].lower()

    accepted_image_formats = [".jpg", ".jpeg", ".png"]
    known_files = []

    if file_extension not in accepted_image_formats:
        print("Unsupported file format. Please use .jpg, .jpeg, or .png.")
        return
    
    if file_name in known_files:
        print("File already processed.")
        return

    known_files.append(file_name)

    image = imread(file_path)

    predictions, confidence = predict_image(image)

    print("Image:", file_name)
    return predictions, confidence

        

