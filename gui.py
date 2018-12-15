from tkinter import *
from tkinter import filedialog
from main import Cluster

import cv2 as cv
import PIL.Image
import PIL.ImageTk
import time

MAX_LENGTH = 740


class MainWindow:

    def __init__(self):
        self.window = Tk()
        self.window.title("Crystallize the Image")
        self.cluster = None
        self.out_image = None
        self.file_button = None
        self.file_name = None
        self.save_button = None
        self.save_name = None
        self.image = None
        self.image_lab = None

        self.canvas_left = None
        self.canvas_right = None
        self.show_height = None
        self.show_width = None

        self.bottom_frame = None
        self.choice_var = IntVar()
        self.choice_button = None
        self.k_value = IntVar()
        self.k_box = None
        self.k_label = None
        self.m_value = IntVar()
        self.m_box = None
        self.m_label = None
        self.cal_button = None

        self.k_text = StringVar()
        self.k_text.set("k: ")
        self.m_text = StringVar()
        self.m_text.set("m: ")

        self.saving_index = 0
        self.init_window()

    def init_window(self):
        self.file_button = Button(self.window, text="choose an image", command=self.choose_file)
        self.file_button.grid(row=1, column=1, pady=4, padx=4)
        self.save_button = Button(self.window, text="save the crystallized image", command=self.save_file)
        self.save_button.grid(row=1, column=2, pady=4, padx=4)

    def choose_file(self):
        self.file_name = filedialog.askopenfilename(initialdir="/", title="Select file",
                                                    filetypes=(("jpeg files", "*.jpg"),
                                                               ("png files", "*.png"), ("all files", "*.*")))
        self.image = cv.imread(self.file_name)
        if self.image is None:
            return

        # for processing (feed into the class Cluster)
        self.image_lab = cv.cvtColor(self.image, cv.COLOR_BGR2LAB)

        img = cv.cvtColor(self.image, cv.COLOR_BGR2RGB)
        self.show_height, self.show_width, no_channels = self.image.shape
        # resize the image
        if self.show_height > self.show_width:
            if self.show_height > MAX_LENGTH:
                ratio = self.show_height / MAX_LENGTH
                self.show_width = int(self.show_width / ratio)
                self.show_height = MAX_LENGTH
                img = cv.resize(img, (self.show_width, self.show_height), interpolation=cv.INTER_AREA)
        else:
            if self.show_width > MAX_LENGTH:
                ratio = self.show_width / MAX_LENGTH
                self.show_height = int(self.show_height / ratio)
                self.show_width = MAX_LENGTH
                img = cv.resize(img, (self.show_width, self.show_height), interpolation=cv.INTER_AREA)

        # get the right format for canvas
        photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img))

        if self.canvas_left is not None:
            self.canvas_left.destroy()
        self.canvas_left = Canvas(self.window, width=self.show_width, height=self.show_height)
        self.canvas_left.grid(row=2, column=1, pady=4, padx=4)
        self.canvas_left.create_image(0, 0, image=photo, anchor=NW)

        if self.canvas_right is not None:
            self.canvas_right.destroy()
        self.canvas_right = Canvas(self.window, width=self.show_width, height=self.show_height)
        self.canvas_right.grid(row=2, column=2, pady=4, padx=4)

        self.bottom_frame = Frame(self.window)
        self.bottom_frame.grid(row=3, column=1, columnspan=2, pady=4, padx=4)

        self.choice_button = Checkbutton(self.bottom_frame, text="Superpixel", variable=self.choice_var,
                                         onvalue=1, offvalue=0)
        self.choice_button.grid(row=1, column=1, pady=4, padx=4)
        self.k_label = Label(self.bottom_frame, textvariable=self.k_text)
        self.k_label.grid(row=1, column=2, pady=4, padx=4)
        self.k_value.set(1000)
        self.k_box = Spinbox(self.bottom_frame, from_=3, to_=80000, textvariable=self.k_value)
        self.k_box.grid(row=1, column=3, pady=4, padx=4)

        self.m_label = Label(self.bottom_frame, textvariable=self.m_text)
        self.m_label.grid(row=1, column=4, pady=4, padx=4)
        self.m_value.set(30)
        self.m_box = Spinbox(self.bottom_frame, from_=1, to_=1000, textvariable=self.m_value)
        self.m_box.grid(row=1, column=5, pady=4, padx=4)

        self.cal_button = Button(self.bottom_frame, text="Calculate", command=self.calculate)
        self.cal_button.grid(row=1, column=6, pady=4, padx=4)
        self.window.mainloop()

    def calculate(self):
        start = time.time()
        if self.cluster is not None:
            del self.cluster
            self.cluster = None
        self.cluster = Cluster(self.image_lab, int(self.k_value.get()), int(self.m_value.get()))
        times = 1
        if self.choice_var.get():
            times = 10
        for it in range(times):
            self.cluster.assign()
            self.out_image = self.cluster.output()
            print(it)
            name = "new_" + str(it) + ".jpg"
            cv.imwrite(name, self.out_image)
        end = time.time()
        duration = end - start
        # print("time used: " + str(duration)) # used for record
        self.display()

    def display(self):
        img = cv.cvtColor(self.out_image, cv.COLOR_BGR2RGB)
        img = cv.resize(img, (self.show_width, self.show_height), interpolation=cv.INTER_AREA)
        photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img))
        self.canvas_right.create_image(0, 0, image=photo, anchor=NW)
        self.window.mainloop()

    def save_file(self):
        if self.out_image is not None:
            name = "output" + str(self.saving_index) + ".jpg"
            self.saving_index += 1
            cv.imwrite(name, self.out_image)
            print("saved, the output file is " + name)
        else:
            print("there is no crystallized image")


if __name__ == '__main__':
    window = MainWindow()
    window.window.mainloop()
