import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
from keras import Input, Model
from keras.src.layers import Conv2D, MaxPooling2D, UpSampling2D, concatenate
from keras.src.losses import binary_crossentropy
from keras.src.optimizers import Adam

# from keras.models import Model
# from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate
# from keras.optimizers import Adam
# from keras.callbacks import ModelCheckpoint
# from keras import backend as K
# from keras.metrics import binary_crossentropy
# import tensorflow as tf
# from tensorflow.keras.callbacks import ModelCheckpoint
# from tensorflow.keras.optimizers import Adam
# from tensorflow.keras.optimizers.schedules import ExponentialDecay

image_size = (512, 512)

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
    #model.summary()
    model.compile(optimizer=Adam(), loss=binary_crossentropy, metrics=['accuracy'])
    return model

class ImagePredictor:
    def __init__(self, model_path):
        # Load the model
        self.model = get_unet()
        self.model.load_weights(model_path)
        #self.model.summary()  # Display model structure
        self.image_size = (512, 512)  # Expected input size for the model

    def _load_and_preprocess_image(self, image_path):
        """Load an image, resize it, and normalize its pixels."""
        img = cv2.imread(image_path, cv2.IMREAD_COLOR)  # Load in color
        if img is None:
            raise ValueError(f"Image not found or unable to read image at path: {image_path}")
        img = cv2.resize(img, self.image_size, interpolation=cv2.INTER_AREA)
        img = img / 255.0  # Normalize pixel values to [0, 1]
        img = np.expand_dims(img, axis=0)  # Add batch dimension
        return img

    def predict_mask(self, image_path):
        """Predict and return the mask for a single image."""
        img = self._load_and_preprocess_image(image_path)
        pred = self.model.predict(img)
        pred_mask = (pred.squeeze() * 255).astype(np.uint8)  # Convert to uint8
        return pred_mask

    def predict_masks(self, image_paths):
        """Predict and return masks for a list of images."""
        masks = []
        for path in image_paths:
            mask = self.predict_mask(path)
            masks.append(mask)
        return masks
