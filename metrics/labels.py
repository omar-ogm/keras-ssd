import os
import shutil


class FileLabels:

    def __init__(self, path):
        self.f = None
        self.path = path

        if os.path.exists(self.path):
            shutil.rmtree(self.path)

    def create(self, filename):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.f = open(self.path + filename + ".txt", "w+")

    def append(self, class_name, confidence, x, y, w, h):

        if confidence:
            line = (class_name + ' ' +
                    str(confidence) + ' ' +
                    str(x) + ' ' +
                    str(y) + ' ' +
                    str(w) + ' ' +
                    str(h) + ' ' +
                    '\n')
        else:
            line = (class_name + ' ' +
                    str(x) + ' ' +
                    str(y) + ' ' +
                    str(w) + ' ' +
                    str(h) + ' ' +
                    '\n')

        self.f.write(line)

    def save(self):
        self.f.close()
