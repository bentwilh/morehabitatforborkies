import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
from keras.models import Model
from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras import backend as K
from keras.metrics import binary_crossentropy
import tensorflow as tf
from tensorflow.keras.callbacks import ModelCheckpoint
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.optimizers.schedules import ExponentialDecay

# Settings
inDir = './model_train/Unet-forest/'
image_folder = os.path.join(inDir, 'train')
val_folder = os.path.join(inDir, 'val')
predictions_dir = os.path.join(inDir, 'predictions')
image_size = (512, 512)

def load_image(path):
    img = cv2.imread(path)  # Remove the grayscale flag
    img = img / 255.0  # Normalize the RGB values
    return img  # No need to expand dimensions

def load_mask(image_path):
    label_path = image_path.replace('tiles', 'masks_tiles').replace('.tif', '.png')
    mask = cv2.imread(label_path, cv2.IMREAD_GRAYSCALE)
    mask = mask / 255.0
    return np.expand_dims(mask, axis=-1)

def get_data(folder):
    x, y = [], []
    images = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.tif')]
    for img_path in images:
        img = load_image(img_path)
        mask = load_mask(img_path)
        x.append(img)
        y.append(mask)
    return np.array(x), np.array(y)

def get_unet():
    inputs = Input((image_size[0], image_size[1], 3))  # Change channel from 1 to 3
    c1 = Conv2D(16, (3, 3), activation='relu', padding='same')(inputs)
    p1 = MaxPooling2D((2, 2))(c1)
    c2 = Conv2D(32, (3, 3), activation='relu', padding='same')(p1)
    p2 = MaxPooling2D((2, 2))(c2)
    c3 = Conv2D(64, (3, 3), activation='relu', padding='same')(p2)
    p3 = MaxPooling2D((2, 2))(c3)
    u4 = UpSampling2D((2, 2))(c3)
    m4 = concatenate([u4, c2])
    c4 = Conv2D(32, (3, 3), activation='relu', padding='same')(m4)
    u5 = UpSampling2D((2, 2))(c4)
    m5 = concatenate([u5, c1])
    c5 = Conv2D(16, (3, 3), activation='relu', padding='same')(m5)
    outputs = Conv2D(1, (1, 1), activation='sigmoid')(c5)
    model = Model(inputs=inputs, outputs=outputs)
    model.summary()
    model.compile(optimizer=Adam(), loss=binary_crossentropy, metrics=['accuracy'])
    return model


def save_predictions(model, images, filenames):
    predictions = model.predict(images)
    print(f"Saving {len(predictions)} predictions")
    for pred, fname in zip(predictions, filenames):
        pred_image = (pred.squeeze() * 255).astype(np.uint8)
        pred_path = os.path.join(predictions_dir, f'{os.path.splitext(fname)[0]}_pred.png')
        success = cv2.imwrite(pred_path, pred_image)
        if not success:
            print(f"Failed to write {pred_path}")
        else:
            print(f"Saved prediction to {pred_path}")

def load_model_weights(model, weights_path):
    model.load_weights(weights_path)

def validate_model(model, val_folder):
    x_val, y_val = get_data(val_folder)
    results = model.evaluate(x_val, y_val, verbose=1)
    print("Validation loss:", results[0])
    print("Validation accuracy:", results[1])

def train_model():
    x, y = get_data(image_folder)
    if len(x) == 0:
        print("No data to train on.")
        return None
    initial_learning_rate = 0.01
    lr_schedule = ExponentialDecay(initial_learning_rate, decay_steps=1, decay_rate=0.8, staircase=True)
    optimizer = Adam(learning_rate=lr_schedule)
    model = get_unet()
    model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy'])
    model.fit(x, y, batch_size=8, epochs=50 verbose=1)
    model.save_weights('unet_rgb_full.weights.h5')

    return model

if __name__ == '__main__':
    model = train_model()
    #model = get_unet()
    #load_model_weights(model, 'unet_rgb_full.weights.h5')
    if model:
        image_filenames = [f for f in os.listdir(image_folder) if f.endswith('.tif')]
        images = np.array([load_image(os.path.join(image_folder, f)) for f in image_filenames if load_image(os.path.join(image_folder, f)) is not None])
        if images.size > 0:
            save_predictions(model, images, image_filenames)
        else:
            print("No images were loaded for prediction.")
        validate_model(model, val_folder)
