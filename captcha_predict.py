import config as cfg
from keras.models import model_from_json
from keras.models import Sequential
import numpy as np

class captcha_recognize:
    def __init__(self):
        self.model = self.load_model()
        self.digit = 6
        
    def one_hot_reverse(self,onehot):
        return self.lable[np.where(onehot==1)[0][0]]
    
    def load_model(self):
        self.model = model_from_json(open(cfg.PATH_CNN_MODEL).read())
        self.model.load_weights(cfg.PATH_CNN_WEIGHTS)
        
    def preprocess(self, img_orig):
        new_width = img_orig.shape[1]//self.digit
        img_orig = img_orig[:, :new_width*self.digit, :]
        imgs = img_orig.reshape(img_orig.shape[0], self.digit, new_width, img_orig.shape[2])
        imgs = np.array([imgs[:, idx, :, :] for idx in range(self.digit)])
        return imgs / 255

    def captcha_predict(self,X):
        if type(self.model)!= Sequential:
            self.load_model()
        ans = self.model.predict(X)
        captcha = ''
        for i in ans:
            captcha += str(i.argmax())
        return captcha

captcha_rec = captcha_recognize()