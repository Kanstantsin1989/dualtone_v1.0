import sys
from tkinter import Tk, Menu, Frame, Button, Label, Canvas, StringVar, Spinbox, IntVar, colorchooser, Toplevel, Text
from tkinter.filedialog import askopenfilename, asksaveasfilename
import tkinter.messagebox as mb
import tkinter.ttk as ttk
import _tkinter
from idlelib.tooltip import Hovertip
import copy
from PIL import Image, ImageTk, ImageOps, ImageFilter, ImageEnhance
from PIL.Image import Resampling
import PIL
import os
import numpy as np
from copy import deepcopy
import keyboard
from threading import Thread
import webbrowser


def has_transparency(image):
    "Checks if opening image is transparent"

    if image.mode == 'RGBA':
        alpha_channel = image.split()[3]
        return any(alpha != 255 for alpha in alpha_channel.getdata())

    return False


def bicubic_interpolation(img, color1, color2):
    "Converts image to 2-colored gamma, there will be quality loss in jpg, jpeg, jfif, and webp files"

    img = np.array(img)
    mask = img.mean(axis=-1) / 255
    r1, g1, b1 = color1[0]
    r2, g2, b2 = color2[0]
    red = (1 - mask) * r1 + mask * r2
    green = (1 - mask) * g1 + mask * g2
    blue = (1 - mask) * b1 + mask * b2
    img[:, :, 0] = red
    img[:, :, 1] = green
    img[:, :, 2] = blue

    return Image.fromarray(img.astype('uint8'))


def RGB_filter(pil_object, array):
    "Adds sepia or red effects, no quality loss"

    img_array = np.array(pil_object)

    if img_array.shape[2] == 3:
        # RGB case
        converting_image = np.dot(img_array, array.T)
        converting_image = np.clip(converting_image, 0, 255).astype(np.uint8)
        return Image.fromarray(converting_image)
    elif img_array.shape[2] == 4:
        # RGBA case (consider alpha channel)
        alpha_channel = img_array[:, :, 3]
        converting_image = np.dot(img_array[:, :, :3], array.T)
        converting_image = np.clip(converting_image, 0, 255).astype(np.uint8)
        converting_image = np.dstack([converting_image, alpha_channel])
        return Image.fromarray(converting_image)
    else:
        raise ValueError("Unsupported number of color channels. Expected 3 (RGB) or 4 (RGBA).")


def invert_colors_rgba(pil_object):
    "Since default PIL library can't invert colors without loss of transparency, this function does it"

    img_array = np.array(pil_object)

    if img_array.shape[2] == 4:
        # RGBA case (consider alpha channel)
        alpha_channel = img_array[:, :, 3]
        rgb_channels = img_array[:, :, :3]

        inverted_rgb_channels = 255 - rgb_channels
        inverted_image = np.dstack([inverted_rgb_channels, alpha_channel])

        return Image.fromarray(inverted_image.astype(np.uint8))
    else:
        raise ValueError("Unsupported number of color channels. Expected 4 (RGBA).")


def RGB_filter_custom_color(pil_object, rgb_color):
    "Tints image with RGB color, there will be quality loss in jpg, jpeg, jfif, and webp files"

    img_array = np.array(pil_object)

    if len(rgb_color) == 3:  # RGB color
        scaling_factors = np.array(rgb_color) / 255.0
        alpha_channel = 1.0
    elif len(rgb_color) == 4:  # RGBA color
        scaling_factors = np.array(rgb_color[:3]) / 255.0
        alpha_channel = rgb_color[3] / 255.0
    else:
        raise ValueError("Color must be RGB or RGBA format")

    # Apply scaling factors to the RGB channels
    converted_image = img_array[:, :, :3] * scaling_factors
    converted_image = np.clip(converted_image, 0, 255).astype(np.uint8)

    # Apply scaling factor to the alpha channel (if present)
    if img_array.shape[2] == 4:
        alpha_channel_array = img_array[:, :, 3] * alpha_channel
        alpha_channel_array = np.clip(alpha_channel_array, 0, 255).astype(np.uint8)
        converted_image = np.dstack((converted_image, alpha_channel_array))

    return Image.fromarray(converted_image)


def linear_interpolation(pil_object, color1, color2):
    "Converts image to 2-colored gamma, there will be quality loss in jpg, jpeg, jfif, and webp files"

    img_array = np.asarray(pil_object)

    has_alpha = len(img_array.shape) == 3 and img_array.shape[2] == 4

    rgb_1 = np.array(color1[0])
    rgb_2 = np.array(color2[0])

    if has_alpha:
        alpha_channel = np.empty(img_array.shape[:2])

    t_values = np.clip(np.dot(img_array[:, :, :3] - rgb_1, rgb_2 - rgb_1) / np.dot(rgb_2 - rgb_1, rgb_2 - rgb_1), 0, 1)

    red = rgb_1[0] + t_values * (rgb_2[0] - rgb_1[0])
    green = rgb_1[1] + t_values * (rgb_2[1] - rgb_1[1])
    blue = rgb_1[2] + t_values * (rgb_2[2] - rgb_1[2])

    if has_alpha:
        alpha_channel[:] = img_array[:, :, 3]
        new_img_array = np.dstack([red, green, blue, alpha_channel]).astype(np.uint8)
    else:
        new_img_array = np.dstack([red, green, blue]).astype(np.uint8)

    if has_alpha:
        return Image.fromarray(new_img_array, 'RGBA')
    else:
        return Image.fromarray(new_img_array, 'RGB')


class BrightnessSpinbox(Spinbox):
    "Spinbox that lets enter only integers no longer than 3 digits"

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(width=4)
        self.configure(validate="key")
        self.configure(validatecommand=(self.register(self.validate_input), "%P"))

    def validate_input(self, new_value):
        try:
            if type(new_value) == int or new_value == '':
                return True
            elif ' ' in new_value:
                return False
            if len(new_value) > 3:
                return False
            _str = int(new_value)
            return True

        except:
            return False


class ContrastSpinbox(Spinbox):
    "Spinbox that lets enter only negative or positive integers, minus can be entered only as the 1st symbol"

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)

        self.configure(width=4)
        self.configure(validate="key")
        self.configure(validatecommand=(self.register(self.validate_input), "%P"))

    def validate_input(self, new_value):
        try:
            if new_value == "":
                return True
            if new_value in "-0123456789":
                return True
            elif ' ' in new_value:
                return False
            if new_value[0] == "-":
                if len(new_value) > 4:
                    return False
            else:
                if len(new_value) > 3:
                    return False
            _str = int(new_value)
            return True

        except:
            return False


class ColorFrame(Frame):
    "Widgets based on Frame intended for choosing colors by user, it's enough to set its parent and function in initUI"

    def __init__(self, parent, function, **kwargs):
        Frame.__init__(self, parent, **kwargs)
        self.configure(width=26)
        self.configure(height=26)
        self.configure(bd=1)
        self.configure(relief="sunken")
        self.bind("<Button-1>", function)


class ProgressbarFrame(Frame):
    """Little Frame with Progressbar working while a file is being opened if image resolution is 1920x1200 or more,
    needs main window name, parallel flow, and text"""

    def __init__(self, parent, parallel_flow, text, *args):
        Frame.__init__(self, parent, *args)
        self.configure(background="#2E3234")
        # accepts function for parallel working and text for window
        self.parallel_flow = parallel_flow
        self.text = text

        # adding tkinter widgets
        self.label = Label(self,
                           text=text,
                           font=("Helvetica", 13),
                           fg="white",
                           bg="#2E3234"
                           )
        self.label.pack(padx=20, pady=14)
        self.pb = ttk.Progressbar(self, mode="indeterminate")
        self.pb.start(interval=32)  # 32 is optimal value
        self.pb.pack(fill="x", padx=20)
        self.place(relx=0.5, rely=0.5, anchor="center", width=330, height=110)
        self.after(0, self.show_and_start)

    def show_and_start(self):

        # Starts given thread as second one"
        t = Thread(target=self.run_thread)
        t.start()

    def run_thread(self):

        # exception when user closes this app while image is being opened
        try:
            self.parallel_flow()
        except RuntimeError:
            sys.exit(0)

        # closes window
        self.after(0, self.close_window)

    def close_window(self):
        self.destroy()

class HyperlinkLabel(Label):
    "Hyperlink to open icons8.com and page with source code on GitHub"
    def __init__(self, master=None, text="", url="", **kwargs):
        super().__init__(master, text=text, cursor="hand2", fg="blue", **kwargs)
        self.url = url
        self.bind("<Button-1>", self.open_url)

    def open_url(self, event):
        webbrowser.open_new(self.url)


class DualTone:

    def __init__(self):

        # 100% default value for brightness and contrast
        self.default_spinbox_val = 100

        # np matrix for red color filter
        self.red = np.array([[1.6, 0, 0],
                             [0, 1, 0],
                             [0, 0, 1]])

        # np matrix for sepia filter
        self.sepia = np.array([[0.393, 0.769, 0.189],
                               [0.349, 0.686, 0.168],
                               [0.272, 0.534, 0.131]])

        # default color for overall tint RGB filter
        self.tint_color_tuple = ((255, 128, 255), '#ff80ff')

        # default colors for two-colored RGB filters
        self.rgb1_tuple = ((0, 0, 0), '#000000')
        self.rgb2_tuple = ((0, 255, 255), '#00ffff')

        # tuple of all color filters for RGB
        self.RGB_filters = ("None",
                            "Mirror",
                            "Black and White",
                            "Sepia", "Red",
                            "Overall Tint RGB Filter",
                            "2-Colored RGB (Bicubic)",
                            "2-Colored RGB (Linear)",
                            "Blur",
                            "Smooth",
                            "Sharpen",
                            "Detail",
                            "Edge Enhance",
                            "Emboss",
                            "Contour #1",
                            "Contour #2",
                            "Invert",
                            "Posterize 1 bit",
                            "Posterize 2 bit",
                            "Posterize 3 bit",
                            "Posterize 4 bit")

        # tuple of all color filters for RGBA
        self.RGBA_filters = ("None",
                             "Mirror",
                             "Sepia",
                             "Red",
                             "Overall Tint RGB Filter",
                             "2-Colored RGB (Bicubic)",
                             "2-Colored RGB (Linear)",
                             "Blur",
                             "Smooth",
                             "Sharpen",
                             "Detail",
                             "Edge Enhance",
                             "Invert")

        # UI initialization
        self.initUI()

        self.root.mainloop()


    def initUI(self):
        # standard Tkinter window
        self.root = Tk()
        self.root.title('DualTone v.1.0')

        # avoids error with "zoomed" state on Linux
        try:
            self.root.state("zoomed")
        except _tkinter.TclError:
            self.root.geometry("1400x700+0+0")
        self.root.minsize(1200, 700)
        self.root.iconbitmap("icons/app_icon.ico")

        # Toolbar for all functions
        self.toolbar = Frame(self.root, relief="groove", bd=2)
        self.toolbar.pack(side="top", fill="x")

        # image for icons
        open_icon = ImageTk.PhotoImage(Image.open("icons/icons8-image-64.png").resize((30, 30), Resampling.LANCZOS))
        save_icon = ImageTk.PhotoImage(Image.open("icons/icons8-save-60.png").resize((28, 28), Resampling.LANCZOS))
        cmyk_icon = ImageTk.PhotoImage(Image.open("icons/icons8-cmyk-48.png").resize((30, 30), Resampling.LANCZOS))
        info_icon = ImageTk.PhotoImage(Image.open("icons/icons8-info-60.png").resize((30, 30), Resampling.LANCZOS))
        switch_icon = ImageTk.PhotoImage(Image.open("icons/icons8-sorting-arrows-20.png"))

        # 'Open image' button
        self.open_file_button = Button(self.toolbar,
                                       image=open_icon,
                                       command=self.checkBeforeOpen,
                                       bd=0)
        self.open_file_button.image = open_icon
        self.open_file_button.pack(side="left", padx=4, pady=2)
        Hovertip(self.open_file_button, " Open Image (Ctrl+O) ")

        # 'Save' button
        self.save_file_button = Button(self.toolbar,
                                       image=save_icon,
                                       command=self.saveFile,
                                       state="disabled",
                                       bd=0)
        self.save_file_button.image = save_icon
        self.save_file_button.pack(side="left",  pady=2)
        Hovertip(self.save_file_button, " Save file (Ctrl+S) ")

        # "CMYK" button
        self.cmyk_button = Button(self.toolbar,
                                  image=cmyk_icon,
                                  command=self.saveCMYK,
                                  state="disabled",
                                  bd=0)
        self.cmyk_button.image = cmyk_icon
        self.cmyk_button.pack(side="left", pady=1, padx=3)
        Hovertip(self.cmyk_button, " Convert image to CMYK color mode \n"
                                   " (Ctrl+Shift+S)")

        # 'Info' button
        self.info_button = Button(self.toolbar,
                                  image=info_icon,
                                  command=self.info,
                                  bd=0)
        self.info_button.image = info_icon
        self.info_button.pack(side="left", pady=2)
        Hovertip(self.info_button, " About Program (F1) ")

        # label for filters combobox
        self.lbl = Label(self.toolbar, text="Image filter:", font=("Helvetica", 12))
        self.lbl.pack(side="left", padx=6)

        # combobox to choose one of all color filters
        self.filters_combobox = ttk.Combobox(self.toolbar,
                                             values=self.RGB_filters,
                                             state="readonly",
                                             font=("Helvetica", 11),
                                             height=len(self.RGB_filters),
                                             width=17)
        Hovertip(self.filters_combobox, " Chose a filter to add to your picture. ")
        # combobox activates only after user opens picture
        self.filters_combobox.config(state="disabled")
        self.filters_combobox.pack(side="left")

        # no filter is set by default
        self.filters_combobox.current(0)
        self.filters_combobox.bind("<<ComboboxSelected>>", lambda event: self.applyFilter(self.filters_combobox.get()))

        # sets brightness and contrast vals by default 100% value
        self.bright_var = IntVar()
        self.bright_var.set(self.default_spinbox_val)
        self.contrast_var = IntVar()
        self.contrast_var.set(self.default_spinbox_val)

        # spinboxes to change brightness and contrast
        self.bright_lbl = Label(self.toolbar, text="Brightness, %:", font=("Helvetica", 12))
        self.bright_lbl.pack(side="left", padx=5)
        self.bright_spinbox = BrightnessSpinbox(self.toolbar,
                                                textvariable=self.bright_var,
                                                font=("Helvetica", 12),
                                                from_=0,
                                                to=280,
                                                increment=1,
                                                command=self.getBrightnessAndContrast,
                                                state="disabled")
        self.bright_spinbox.pack(side="left")
        self.bright_spinbox.bind("<Return>", self.brightnessFromKeyboard)
        Hovertip(self.bright_spinbox, " Enter percentage of brightness \n from 0 to 280.")

        self.contrast_lbl = Label(self.toolbar, text="Contrast, %:", font=("Helvetica", 12))
        self.contrast_lbl.pack(side="left", padx=5)

        self.contrast_spinbox = ContrastSpinbox(self.toolbar,
                                                textvariable=self.contrast_var,
                                                font=("Helvetica", 12),
                                                from_=-300,
                                                to=300,
                                                increment=1,
                                                command=self.getBrightnessAndContrast,
                                                state="disabled")
        self.contrast_spinbox.pack(side="left")
        self.contrast_spinbox.bind("<Return>", self.contrastFromKeyboard)
        Hovertip(self.contrast_spinbox, " Enter percentage of contrast \n from -300 to 300.")

        # Color for "Overall Tint RGB Filter"
        self.rgb_tint_lbl = Label(self.toolbar, text="Overall Tint RGB Filter:", font=("Helvetica", 12))
        self.rgb_tint_lbl.pack(side="left", padx=5)
        self.rgb_tint_color_frame = ColorFrame(self.toolbar,
                                               function=self.setTintRGB,
                                               bg=self.tint_color_tuple[1])
        self.rgb_tint_color_frame.pack(side="left", pady=2)
        Hovertip(self.rgb_tint_color_frame, ' Click here to set RGB color \n for "Overall Tint RGB Filter". ')

        # two colors for 2-Colored RGB filters and button to switch them
        self.rgb_2clrs_lbl = Label(self.toolbar, text="2-Colored RGB Filters:", font=("Helvetica", 12))
        self.rgb_2clrs_lbl.pack(side="left", padx=5)
        self.rgb1_frame = ColorFrame(self.toolbar,
                                     function=self.setFirstRGB,
                                     bg=self.rgb1_tuple[1])
        self.rgb1_frame.pack(side="left", pady=2)
        Hovertip(self.rgb1_frame, ' Click here to set 1st RGB color \n for 2-Colored RGB filters".')

        self.switch_colors_button = Button(self.toolbar,
                                           image=switch_icon,
                                           width=20,
                                           height=20,
                                           bd=0,
                                           command=self.switcher)
        self.switch_colors_button.image = switch_icon
        self.switch_colors_button.pack(side="left", padx=5)
        Hovertip(self.switch_colors_button, " Switch two RGB colors (Changes gamma \n"
                                            " only in Bicubic Interpolation mode).")

        self.rgb2_frame = ColorFrame(self.toolbar,
                                     function=self.setSecondRGB,
                                     bg=self.rgb2_tuple[1])
        self.rgb2_frame.pack(side="left", pady=2)
        Hovertip(self.rgb2_frame, ' Click here to set 2nd RGB color \n for 2-Colored RGB filters".')

        self.canv = Canvas(self.root,
                           bg="#ffff7e",
                           highlightthickness=0,
                           relief="groove")
        self.canv.pack(side="top", fill="both", expand=True)
        self.canv.bind("<Button-3>", self.showMenu)
        self.canv.bind("<Configure>", self.onResize)

        # Statusbar:
        self.statusbar = Label(self.canv,
                               relief="groove",
                               bd=2,
                               text='No file open',
                               anchor='w')
        self.statusbar.pack(side="bottom", fill="both")

        # checks if file was changed and suggests save it if yes
        self.root.protocol("WM_DELETE_WINDOW", self.saveBeforeClose)

        # hot keys working in any language, not only in English unlike tkinter "bind" method
        keyboard.add_hotkey('ctrl+o', self.checkBeforeOpen)
        keyboard.add_hotkey('ctrl+s', self.saveFile)
        keyboard.add_hotkey('ctrl+shift+s', self.saveCMYK)

        # binding with default tkinter method
        self.root.bind("<F1>", self.info)

        # Menu bound on Mouse 2 button
        self.menu_var = StringVar()
        self.menu_var.set("None")
        self.menu = Menu(self.toolbar, tearoff=False)
        self.menu.add_command(label="Open Image (Ctrl+O)", command=self.checkBeforeOpen)
        self.menu.add_command(label="Save Image (Ctrl+S)", command=self.saveFile, state="disabled")
        self.menu.add_command(label="Convert to CMYK (Ctrl+Shift+S)", command=self.saveCMYK, state="disabled")
        self.menu.add_separator()

        # radiobuttons to duplicate filters combobox
        for f in self.RGB_filters:
            self.menu.add_radiobutton(label=f,
                                      command=lambda f=f: self.filterFromMenu(f),
                                      variable=self.menu_var,
                                      state="disabled")
        self.menu.add_separator()
        self.menu.add_command(label="About Program (F1)", command=self.info)
        self.menu.add_separator()
        self.menu.add_command(label="Exit (Alt+F4)", command=self.saveBeforeClose)


    def brightnessFromKeyboard(self, *args):
        """Lets user enter brightness value from keyboard, sets 100% if he or she enters wrong value"""

        try:  # handles all exceptions if users enters something wrong or presses Enter having not entered value
            a = self.bright_spinbox.get()
            # sets default value 100 if user enters number more than 280
            if int(a) not in range(0, 281):
                self.bright_var.set(int(self.default_spinbox_val))
                self.getBrightnessAndContrast()
            # sets value entered by user
            else:
                self.bright_var.set(int(a))
                self.getBrightnessAndContrast()
        except:
            self.bright_var.set(int(self.default_spinbox_val))
            self.getBrightnessAndContrast()


    def contrastFromKeyboard(self, *args):
        '''The same thing as "brightnessFromKeyboard" method'''

        try:
            a = self.contrast_spinbox.get()
            if int(a) not in range(-300, 301):
                self.contrast_var.set(self.default_spinbox_val)
                self.getBrightnessAndContrast()
            else:
                self.contrast_var.set(int(a))
                self.getBrightnessAndContrast()
        except:
            self.contrast_var.set(self.default_spinbox_val)
            self.getBrightnessAndContrast()


    def checkBeforeOpen(self, *args):
        """Checks first if any filter is applied and/or brightness and contrast aren't equal 100.
        If nothing is changed, program just opens another picture. If current picture is
        changed, it suggests save new file with mb.askyesnocancel method. """

        # gets filter and values of brightness and contrast
        filter = self.filters_combobox.get()
        brightness = self.bright_spinbox.get()
        contrast = self.contrast_spinbox.get()

        try:
            # unreachable code: if there's no displayed image, raises AttributeError and won't print line below
            if not self.displayed_image:
                print("This line will never be printed:)")

            # won't ask to save file if nothing is changed, suggests open another picture
            elif filter == "None" and int(brightness) == 100 and int(contrast) == 100:
                self.openFile()

            # asks if user wants to save file if something is changed
            else:
                question = mb.askyesnocancel("Warning", "The image has been changed.\n"
                                                      "Would you like to save your image?")

                # if users click "Yes"
                if question is True:
                    self.saveFile()
                    self.openFile()

                # if user clicks "No"
                elif question is False:
                    self.openFile()

                # if user clicks "Cancel", just closes question window
                else:
                    pass

        # continues to open file if there's no displayed image
        except AttributeError:
            self.openFile()


    def openFile(self):
        "Continues to open file"

        ftypes = [
            ("All files", "*"),
            ("JPG files", "*.jpg"),
            ("JPEG files", "*.jpeg"),
            ("PNG files", "*.png"),
            ("BMP files", "*.bmp"),
            ("JFIF files", "*.jfif"),
            ("TIFF files", "*.tif"),
            ("TIFF files", "*.tiff"),
            ("ICO files", "*.ico"),
            ("WebP files", "*.webp"),
            ("PPM files", "*.ppm"),
            ("PGM files", "*.pgm"),
            ("PBM files", "*.pbm"),
            ("PCX files", "*.pcx"),
            ("TGA files", "*.tga"),
        ]

        # gets list of extensions of supported files in order to prevent program to try to open unsupported ones
        extensions = []

        # uses for cycle, gets slice of 2nd element of each nested tuple: extension without asterix
        for i in ftypes[1:]:
            i = i[1][1:]
            extensions.append(i)

        # converts "extensions" list into a tuple: ('.jpg', '.jpeg', '.png', '.bmp', '.jfif', '.tif', '.tiff', '.ico',
        # '.webp', '.ppm', '.pgm', '.pbm', '.pcx', '.tga')
        extensions = tuple(extensions)

        # gets filename
        filename = askopenfilename(filetypes=ftypes, title="Open File")

        # won't do anything if user doesn't change file
        if filename == '':
            return
        # checks file extension, if it's supported, image will be open
        elif filename.lower().endswith(extensions):
            self.filename = filename
        # also checks file extension, if it isn't supported, image won't be open and this method will be stopped
        else:
            if filename.lower().endswith(".gif"):
                # informs that GIF images aren't supported
                mb.showerror("Error", "GIF files aren't supported!")
                return
            else:
                mb.showerror("Error", "Can't open this file!")
                return

        self.displayImage()

    def displayImage(self, progress_message="Displaying your image..."):
        "Begins to display image"

        # Exception that won't try to open damaged image
        try:
            self.original_image = Image.open(self.filename)
        except PIL.UnidentifiedImageError:
            mb.showerror("Error", "Can't open this file. Perhaps\n"
                                  "this file is damaged")
            return

        # won't open image with any another error
        except:
            mb.showerror("Error", "Can't open this file!")
            return

        def displaying_flow():
            "Internal function to open file as 2nd thread while progressbar is displayed"

            self.original_clr_mode = copy.deepcopy(self.original_image.mode)

            # if opening image has P or RGBX color modes, it will be converted to RGBA
            if self.original_image.mode == "P" or "RGBX":
                self.original_image = self.original_image.convert("RGBA")

            # activates only filters available for RGBA
            if has_transparency(self.original_image):
                self.filters_combobox.configure(values=self.RGBA_filters)
                for e in self.RGB_filters:
                    if e in self.RGBA_filters:
                        self.menu.entryconfig(e, state="active")
                    else:
                        self.menu.entryconfig(e, state="disabled")

            # activates all filters for RGB
            elif not has_transparency(self.original_image):
                if self.original_image.mode != "RGB":
                    self.original_image = self.original_image.convert("RGB")
                self.filters_combobox.configure(values=self.RGB_filters)
                for e in self.RGB_filters:
                    self.menu.entryconfig(e, state="active")

            # gets reserve copy of image for next operations, with it file can be saved even if it's deleted from PC
            self.reserve_copy = deepcopy(self.original_image)

            # converts reserve copy to numpy array for optimization
            a = np.asarray(self.reserve_copy)
            self.reserve_copy = Image.fromarray(a)

            # shows file info in statusbar
            self.configStatusbar()
            # sets default brightness and contrast values
            self.menu_var.set("None")
            self.filters_combobox.set("None")
            self.bright_var.set(self.default_spinbox_val)
            self.contrast_var.set(self.default_spinbox_val)

            # activates all disabled widgets
            self.save_file_button.config(state="active")
            self.cmyk_button.config(state="active")
            self.filters_combobox.config(state="active")
            self.menu.entryconfig("Save Image (Ctrl+S)", state="active")
            self.menu.entryconfig("Convert to CMYK (Ctrl+Shift+S)", state="active")
            self.contrast_spinbox.config(state="normal")
            self.bright_spinbox.config(state="normal")

            # continues displaying by fitting image to window size
            self.resizeToFit()

        # doesn't show progressbar picture resolution is less than 1920x1200
        if self.original_image.width <= 1920 and self.original_image.height < 1200:
            displaying_flow()
        else:    # shows progressbar if picture resolution is more than 1920x1200
            ProgressbarFrame(self.root, displaying_flow, progress_message)


    def resizeToFit(self):
        "Resizes images so that they will fit to window size if they are larger than window size"

        # Get the canvas width and height
        self.viewer_w = self.canv.winfo_width()
        self.viewer_h = self.canv.winfo_height() - self.statusbar.winfo_height()

        try:    # handles NameError and AttributeError if image isn't open
            original_w, original_h = self.original_image.width, self.original_image.height
            # fits image to window size if its weight or height are more than window ones
            if original_w <= self.viewer_w and original_h <= self.viewer_h:
                self.displayed_image = self.original_image
            else:
                ratio = min(self.viewer_w / original_w, self.viewer_h / original_h)

                self.displayed_image = self.original_image.resize((int(original_w * ratio), int(original_h * ratio)),
                                                                  Resampling.LANCZOS)

            # copy is needed for changing brightness and contrast, they won't work properly without this copy
            self.displayed_image_copy = copy.deepcopy(self.displayed_image)
            self.getBrightnessAndContrast()

        except (NameError, AttributeError):
            pass


    def getBrightnessAndContrast(self):
        "Gets brightness and contrast values from spinboxes, also this method is binded to spinboxes for optimization"

        # sets brightness; user enters its percentage, program converts it to float values
        brightness_rate = int(self.bright_spinbox.get()) * 0.01
        brightness_enhancer = ImageEnhance.Brightness(self.displayed_image_copy)   # won't work without copy
        self.displayed_image = brightness_enhancer.enhance(brightness_rate)

        # sets contrast; user enters its percentage, program converts it to float values
        contrast_rate = int(self.contrast_spinbox.get()) * 0.01
        contrast_enhancer = ImageEnhance.Contrast(self.displayed_image)
        self.displayed_image = contrast_enhancer.enhance(contrast_rate)


        # eventually displays image in canvas with its filter and rightness and contrast values
        self.displayed_image_2 = ImageTk.PhotoImage(self.displayed_image)

        self.canv.create_image(self.viewer_w // 2,
                                self.viewer_h // 2,
                                image=self.displayed_image_2,
                                anchor="center",
                                tag="image")


    def applyFilter(self, filter):
        "Applies a filter to image"

        def apply_filter_flow():
            if filter == "None":
                self.original_image = self.reserve_copy

            elif filter == "Black and White":
                self.original_image = ImageOps.grayscale(self.reserve_copy)

            elif filter == "Sepia":
                self.original_image = RGB_filter(self.reserve_copy, self.sepia)

            elif filter == "Red":
                self.original_image = RGB_filter(self.reserve_copy, self.red)

            elif filter == "Overall Tint RGB Filter":
                self.original_image = RGB_filter_custom_color(self.reserve_copy, self.tint_color_tuple[0])

            elif filter == "2-Colored RGB (Bicubic)":
                self.original_image = bicubic_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)

            elif filter == "2-Colored RGB (Linear)":
                self.original_image = linear_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)
                # informing user that two similar colors mustn't be set
                if self.rgb1_tuple == self.rgb2_tuple:
                    mb.showinfo("Info", "You will get completely black image\n"
                                        "if you set two absolutely similar RGB\n"
                                        "colors with Linear interpolation filter!\n")

            elif filter == "Emboss":
                self.original_image = self.reserve_copy.filter(ImageFilter.EMBOSS)

            elif filter == "Blur":
                self.original_image = self.reserve_copy.filter(ImageFilter.BLUR)

            elif filter == "Sharpen":
                self.original_image = self.reserve_copy.filter(ImageFilter.SHARPEN)

            elif filter == "Smooth":
                self.original_image = self.reserve_copy.filter(ImageFilter.SMOOTH)

            elif filter == "Mirror":
                self.original_image = ImageOps.mirror(self.reserve_copy)

            elif filter == "Invert":
                if not has_transparency(self.original_image):
                    self.original_image = ImageOps.invert(self.reserve_copy)
                if has_transparency(self.original_image):
                    self.original_image = invert_colors_rgba(self.reserve_copy)

            elif filter == "Detail":
                self.original_image = self.reserve_copy.filter(ImageFilter.DETAIL)

            elif filter == "Edge Enhance":
                self.original_image = self.reserve_copy.filter(ImageFilter.EDGE_ENHANCE)

            elif filter == "Contour #1":
                self.original_image = self.reserve_copy.filter(ImageFilter.CONTOUR)

            elif filter == "Contour #2":
                self.original_image = self.reserve_copy.convert("L").filter(ImageFilter.FIND_EDGES)

            elif filter == "Posterize 1 bit":
                self.original_image = ImageOps.posterize(self.reserve_copy, 1)

            elif filter == "Posterize 2 bit":
                self.original_image = ImageOps.posterize(self.reserve_copy, 2)

            elif filter == "Posterize 3 bit":
                self.original_image = ImageOps.posterize(self.reserve_copy, 3)

            elif filter == "Posterize 4 bit":
                self.original_image = ImageOps.posterize(self.reserve_copy, 4)

            # fits image to window size
            self.resizeToFit()


        def watch_cursor(root, parallel_flow):
            root.config(cursor="watch")  # changing cursor to "watch" while filter is being applied

            # creates and starts 2nd flow
            thread = Thread(target=parallel_flow)
            thread.start()

            # Checking is the 2nd flow was stopped
            def check_thread():
                if thread.is_alive():
                    root.after(0, check_thread)   # with 0 it's more comfortable for user's eyes
                else:
                    root.config(cursor="")  # returns cursor to default arrow

            root.after(0, check_thread)

        watch_cursor(self.root, apply_filter_flow)

        # duplicates setting of filter in menu
        self.menu_var.set(filter)


    # functionality for tint RGB filter
    def setTintRGB(self, *args):
        "Sets overall tint RGB filter"

        # gets copy of self.tint_color_tuple for a case if user clicks 'Cancel'
        rgb_copy = copy.deepcopy(self.tint_color_tuple)
        self.tint_color_tuple = colorchooser.askcolor()
        # returns value of previous color if user clicked "Cancel"
        if self.tint_color_tuple == (None, None):
            self.tint_color_tuple = rgb_copy
        # sets selected color as color of frame with second element of tuple
        self.rgb_tint_color_frame.configure(bg=self.tint_color_tuple[1])
        # applies the same filter with new (if user sets it) or old color (if user clicks "Cancel")
        if self.filters_combobox.get() == "Overall Tint RGB Filter":
            self.original_image = RGB_filter_custom_color(self.reserve_copy, self.tint_color_tuple[0])
            self.applyFilter(filter="Overall Tint RGB Filter")


    # functionality for 2-colored RGB filters
    def setFirstRGB(self, *args):
        "Sets first color with tkinter colorchooser.askcolor()"
        try:
            # gets current color for a case if user clicks 'Cancel'
            rgb_copy = copy.deepcopy(self.rgb1_tuple)
            self.rgb1_tuple = colorchooser.askcolor()
            # saves current color if user clicks "Cancel"
            if self.rgb1_tuple == (None, None):
                self.rgb1_tuple = rgb_copy
            # sets selected color as color of frame with second element of tuple
            self.rgb1_frame.configure(bg=self.rgb1_tuple[1])
            # applies selected or current color for 2-colored RGB filters
            if self.filters_combobox.get() == "2-Colored RGB (Bicubic)":
                self.original_image = bicubic_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)
                self.applyFilter(filter="2-Colored RGB (Bicubic)")

            elif self.filters_combobox.get() == "2-Colored RGB (Linear)":
                self.original_image = linear_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)
                self.applyFilter(filter="2-Colored RGB (Linear)")

        except TypeError:
            pass

    def setSecondRGB(self, *args):
        "Sets second color with tkinter colorchooser.askcolor(), the same as setFirstRGB method"
        try:
            rgb_copy = copy.deepcopy(self.rgb2_tuple)
            self.rgb2_tuple = colorchooser.askcolor()
            # saves current color if user clicks "Cancel"
            if self.rgb2_tuple == (None, None):
                self.rgb2_tuple = rgb_copy
            self.rgb2_frame.configure(bg=self.rgb2_tuple[1])

            if self.filters_combobox.get() == "2-Colored RGB (Bicubic)":
                self.original_image = bicubic_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)
                self.applyFilter(filter="2-Colored RGB (Bicubic)")

            elif self.filters_combobox.get() == "2-Colored RGB (Linear)":
                self.original_image = linear_interpolation(self.reserve_copy, self.rgb1_tuple, self.rgb2_tuple)
                self.applyFilter(filter="2-Colored RGB (Linear)")

        except TypeError:
            pass


    def switcher(self):
        "Switches two RGB colors (only for bicubic interpolation)"
        # gets copies of self.rgb1_tuple and self.rgb2_tuple to switch them
        color1 = copy.deepcopy(self.rgb1_tuple)
        color2 = copy.deepcopy(self.rgb2_tuple)
        # changes places of two tuples
        self.rgb1_tuple = color2
        self.rgb1_frame.configure(bg=self.rgb1_tuple[1])
        self.rgb2_tuple = color1
        self.rgb2_frame.configure(bg=self.rgb2_tuple[1])
        # applies filters with switched colors for bicubic interpolation, won't change picture in linear interpolation
        if self.filters_combobox.get() == "2-Colored RGB (Bicubic)":
            self.applyFilter(self.filters_combobox.get())


    def filterFromMenu(self, value):
        "Duplicates filters combobox, sets the same value both for combobox and menu"
        self.menu_var.set(value)
        self.filters_combobox.set(value)
        self.applyFilter(value)


    def saveFile(self, *args):
        "Saves file applying color filter and changes of brightness and contrast"

        # handles with AttributeError if user presses Ctrl+S and there's no image: just nothing happens.
        # Otherwise, all hotkey scripts will be broken
        try:
            if not self.original_image:
                print("This unreachable code prevents to break CTRL+S script")
        except AttributeError:
            return

        # checks if image is transparent and suggests two different extensions lists for each case
        if not has_transparency(self.original_image):
            ftypes = [
                # file formats with no or minimal loss of quality:
                ("PNG files (Best Quality)", "*.png"),
                ("BMP files (Best Quality)", "*.bmp"),
                ("TIF files (Best Quality)", "*.tif"),
                ("TIFF files (Best Quality)", "*.tiff"),
                ("PPM files (Best Quality)", "*.ppm"),
                ("PGM files (Best Quality)", "*.pgm"),
                ("PBM files (Best Quality)", "*.pbm"),
                ("PCX files (Best Quality)", "*.pcx"),
                ("TGA files (Best Quality)", "*.tga"),
                # ICO files won't be larger than 256x256
                ("ICO files (Max size 256x256)", "*.ico"),
                # file formats witch can be with serious loss of quality with RGB filters
                ("JPG files (Lower Quality)", "*.jpg"),
                ("JPEG files (Lower Quality)", "*.jpeg"),
                ("JFIF files (Lower Quality)", "*.jfif"),
                ("WebP files (Lower Quality)", "*.webp"),
            ]

        elif has_transparency(self.original_image):
            ftypes = [
                ("PNG files", "*.png"),
                ("WebP files", "*.webp"),
                ("ICO files", "*.ico")
            ]

        # gets saving file name
        new_image_name = asksaveasfilename(filetypes=ftypes, title="Save New File", defaultextension="")
        if not new_image_name:
            return

        def saving_flow():
            "Flow that is being executed along with progressbar"
            new_image = self.reserve_copy

            # applies filter, brightness and contrast
            filter = self.filters_combobox.get()

            if filter == "Black and White":
                new_image = ImageOps.grayscale(new_image)

            elif filter == "Sepia":
                new_image = RGB_filter(new_image, self.sepia)

            elif filter == "Red":
                new_image = RGB_filter(new_image, self.red)

            elif filter == "Overall Tint RGB Filter":
                new_image = RGB_filter_custom_color(new_image, self.tint_color_tuple[0])

            elif filter == "2-Colored RGB (Bicubic)":
                new_image = bicubic_interpolation(new_image, self.rgb1_tuple, self.rgb2_tuple)

            elif filter == "2-Colored RGB (Linear)":
                new_image = linear_interpolation(new_image, self.rgb1_tuple, self.rgb2_tuple)

            elif filter == "Emboss":
                new_image = new_image.filter(ImageFilter.EMBOSS)

            elif filter == "Blur":
                new_image = new_image.filter(ImageFilter.BLUR)

            elif filter == "Sharpen":
                new_image = new_image.filter(ImageFilter.SHARPEN)

            elif filter == "Smooth":
                new_image = new_image.filter(ImageFilter.SMOOTH)

            elif filter == "Mirror":
                new_image = ImageOps.mirror(new_image)

            elif filter == "Invert":
                if not has_transparency(self.original_image):
                    new_image = ImageOps.invert(new_image)
                if has_transparency(self.original_image):
                    new_image = invert_colors_rgba(new_image)

            elif filter == "Detail":
                new_image = new_image.filter(ImageFilter.DETAIL)

            elif filter == "Edge Enhance":
                new_image = new_image.filter(ImageFilter.EDGE_ENHANCE)

            elif filter == "Contour #2":
                new_image = new_image.convert("L").filter(ImageFilter.FIND_EDGES)

            elif filter == "Contour #1":
                new_image = new_image.filter(ImageFilter.CONTOUR)

            elif filter == "Posterize 1 bit":
                new_image = ImageOps.posterize(new_image, 1)

            elif filter == "Posterize 2 bit":
                new_image = ImageOps.posterize(new_image, 2)

            elif filter == "Posterize 3 bit":
                new_image = ImageOps.posterize(new_image, 3)

            elif filter == "Posterize 4 bit":
                new_image = ImageOps.posterize(new_image, 4)

            brightness_rate = int(self.bright_spinbox.get()) * 0.01
            contrast_rate = int(self.contrast_spinbox.get()) * 0.01

            if float(brightness_rate) != int(1):
                brightness_enhancer = ImageEnhance.Brightness(new_image)
                new_image = brightness_enhancer.enhance(float(brightness_rate))

            if float(contrast_rate) != int(1):
                contrast_enhancer = ImageEnhance.Contrast(new_image)
                new_image = contrast_enhancer.enhance(float(contrast_rate))

            if self.original_clr_mode == "P" and has_transparency(self.original_image):
                # saves transparent ico-files in RGBA mode
                if new_image_name.lower().endswith(".ico"):
                    pass
                # returns P mode if it was original mode of transparent image
                else:
                    new_image = new_image.convert("P")

            # exception for a case if user can't save image in a chosen folder
            try:
                new_image.save(new_image_name)
            except:
                mb.showerror("Error!", "Can't save image in this folder!")
                return

            # sets default settings
            self.filters_combobox.set("None")
            self.menu_var.set("None")
            self.bright_var.set(self.default_spinbox_val)
            self.contrast_var.set(self.default_spinbox_val)

            # opens and displays new image with its new filter, brightness, and contrast. These lines of code are
            # taken from displayImage method to being executed while Progressbar Window is shown for better user's
            # experience
            self.filename = new_image_name
            self.original_image = Image.open(self.filename)

            self.original_clr_mode = copy.deepcopy(self.original_image.mode)

            # if opening image has "P" color mode, it will be converted to RGBA
            if self.original_image.mode == "P" or "RGBX":
                self.original_image = self.original_image.convert("RGBA")

            # activates only filters available for RGBA
            if has_transparency(self.original_image):
                self.filters_combobox.configure(values=self.RGBA_filters)
                for e in self.RGB_filters:
                    if e in self.RGBA_filters:
                        self.menu.entryconfig(e, state="active")
                    else:
                        self.menu.entryconfig(e, state="disabled")

            # activates all filters for RGB
            elif not has_transparency(self.original_image):
                if self.original_image.mode != "RGB":
                    self.original_image = self.original_image.convert("RGB")
                self.filters_combobox.configure(values=self.RGB_filters)
                for e in self.RGB_filters:
                    self.menu.entryconfig(e, state="active")

            # gets reserve copy of image for next operations, with it file can be saved even if it's deleted from PC
            self.reserve_copy = deepcopy(self.original_image)

            # converts reserve copy to numpy array for optimization
            a = np.asarray(self.reserve_copy)
            self.reserve_copy = Image.fromarray(a)

            # sets default brightness and contrast values
            self.menu_var.set("None")
            self.filters_combobox.set("None")
            self.bright_var.set(self.default_spinbox_val)
            self.contrast_var.set(self.default_spinbox_val)

            # continues displaying by fitting image to window size
            self.resizeToFit()
            self.configStatusbar()

        ProgressbarFrame(self.root, saving_flow, "Saving your file, please wait...")


    def saveCMYK(self, *args):
        "Saves file applying color filter and changes of brightness and contrast"

        # handles with AttributeError if user presses Ctrl+Shift+S and there's no image: just nothing happens.
        # Otherwise, all hotkey scripts will be broken
        try:
            if not self.original_image:
                print("Another unreachable code intended to prevent to break Ctrl+Shift+S hot keys script")
        except AttributeError:
            return

        if has_transparency(self.original_image):
            warning = mb.askyesno("Warning", "If you save your image as CMYK,\n"
                                             "its transparency will be lost.\n"
                                             "Do you want to proceed?")
            # cancels converting to CMYK if user clicks No, otherwise picture will be saved without transparency
            if warning == False:
                return

        ftypes = [
            # file formats that support CMYK:
            ("JPG files", "*.jpg"),
            ("JPEG files", "*.jpeg"),
            ("TIF files", "*.tif"),
            ("TIFF files", "*.tiff"),
            ("JFIF files", "*.jfif"),
        ]

        new_image_name = asksaveasfilename(filetypes=ftypes, title="Save as CMYK", defaultextension="")
        if not new_image_name:
            return

        def CMYK_flow():
            "Flow that is being executed along with Progressbar"

            filter = self.filters_combobox.get()

            new_image = self.reserve_copy

            if filter == "Black and White":
                new_image = ImageOps.grayscale(new_image)

            elif filter == "Sepia":
                new_image = RGB_filter(new_image, self.sepia)

            elif filter == "Red":
                new_image = RGB_filter(new_image, self.red)

            elif filter == "Overall Tint RGB Filter":
                new_image = RGB_filter_custom_color(new_image, self.tint_color_tuple[0])

            elif filter == "2-Colored RGB (Bicubic)":
                new_image = bicubic_interpolation(new_image, self.rgb1_tuple, self.rgb2_tuple)

            elif filter == "2-Colored RGB (Linear)":
                new_image = linear_interpolation(new_image, self.rgb1_tuple, self.rgb2_tuple)

            elif filter == "Emboss":
                new_image = new_image.filter(ImageFilter.EMBOSS)

            elif filter == "Blur":
                new_image = new_image.filter(ImageFilter.BLUR)

            elif filter == "Sharpen":
                new_image = new_image.filter(ImageFilter.SHARPEN)

            elif filter == "Smooth":
                new_image = new_image.filter(ImageFilter.SMOOTH)

            elif filter == "Mirror":
                new_image = ImageOps.mirror(new_image)

            elif filter == "Invert":
                new_image = ImageOps.invert(new_image)

            elif filter == "Detail":
                new_image = new_image.filter(ImageFilter.DETAIL)

            elif filter == "Edge Enhance":
                new_image = new_image.filter(ImageFilter.EDGE_ENHANCE)

            elif filter == "Contour #2":
                new_image = new_image.convert("L").filter(ImageFilter.FIND_EDGES)

            elif filter == "Contour #1":
                new_image = new_image.filter(ImageFilter.CONTOUR)

            elif filter == "Posterize 1 bit":
                new_image = ImageOps.posterize(new_image, 1)

            elif filter == "Posterize 2 bit":
                new_image = ImageOps.posterize(new_image, 2)

            elif filter == "Posterize 3 bit":
                new_image = ImageOps.posterize(new_image, 3)

            elif filter == "Posterize 4 bit":
                new_image = ImageOps.posterize(new_image, 4)

            brightness_rate = int(self.bright_spinbox.get()) * 0.01
            contrast_rate = int(self.contrast_spinbox.get()) * 0.01

            if float(brightness_rate) != int(1):
                brightness_enhancer = ImageEnhance.Brightness(new_image)
                new_image = brightness_enhancer.enhance(float(brightness_rate))

            if float(contrast_rate) != int(1):
                contrast_enhancer = ImageEnhance.Contrast(new_image)
                new_image = contrast_enhancer.enhance(float(contrast_rate))

            # exception if user can't save image in directory he or she chose
            try:
                # converts RGB to CMYK and saves
                new_image.convert("CMYK").save(new_image_name)
            except:
                mb.showerror("Error!", "Can't save image in this folder!")
                return

            # sets default settings
            self.filters_combobox.set("None")
            self.menu_var.set("None")
            self.bright_var.set(self.default_spinbox_val)
            self.contrast_var.set(self.default_spinbox_val)

            # Opens and displays new image with its new filter, brightness, and contrast. These lines of code are
            # taken from displayImage method to being executed while Progressbar Window is shown
            self.filename = new_image_name
            self.original_image = Image.open(self.filename)
            self.original_clr_mode = copy.deepcopy(self.original_image.mode)

            # converts CMYK to RGB so that user could apply anothef filter again
            self.original_image = self.original_image.convert("RGB")

                # activates all filters for RGB
            self.filters_combobox.configure(values=self.RGB_filters)
            for e in self.RGB_filters:
                self.menu.entryconfig(e, state="active")

            # gets reserve copy of image for next operations, with it file can be saved even if it's deleted from PC
            self.reserve_copy = deepcopy(self.original_image)

            # converts reserve copy to numpy array for optimization
            a = np.asarray(self.reserve_copy)
            self.reserve_copy = Image.fromarray(a)

            # sets default brightness and contrast values
            self.menu_var.set("None")
            self.filters_combobox.set("None")
            self.bright_var.set(self.default_spinbox_val)
            self.contrast_var.set(self.default_spinbox_val)

            # continues displaying by fitting image to window size
            self.resizeToFit()
            self.configStatusbar()

        ProgressbarFrame(self.root, CMYK_flow, "Converting to CMYK...")


    def saveBeforeClose(self):
        """Checks if image is changed when user closes program.
        exit(0) must be imported from sys, otherwise the app won't be closed by close button
        after it's converted into exe file for Windows"""

        try:
            # closes program if nothing was changed
            filter = self.filters_combobox.get()
            brightness_rate, contrast_rate = self.bright_spinbox.get(), self.contrast_spinbox.get()
            if filter == "None" and int(brightness_rate) == 100 and int(contrast_rate) == 100:
                sys.exit(0)
            # asks if user wants to save changed picture
            else:
                question = mb.askyesnocancel("Warning", "Would you like to save your image?")
                # saves file and closes program
                if question is True:
                    self.saveFile()
                    sys.exit(0)
                # doesn't save file and closes program
                elif question is False:
                    sys.exit(0)
                # doesn't do anything
                else:
                    pass
        # closes program if image isn't open not asking anything
        except ValueError:
            sys.exit(0)

    def configStatusbar(self):
        """Shows file path, its resolution and size"""

        self.original_size = os.stat(self.filename).st_size
        if self.original_size < 1024:
            self.original_size = str(f"{self.original_size} bytes")
        elif self.original_size in range(1024, 1048577):
            self.original_size = str(f"{round(self.original_size / 1024, 2)} kb")
        elif self.original_size >= 1048577:
            self.original_size = str(f"{round(self.original_size / 1048576, 2)} mb")
        elif self.original_size >= 1073741824:
            self.original_size = str(f"{round(self.original_size / 1073741824, 2)} Gb")

        self.statusbar.config(text=f"{self.filename}; "
                                   f"resolution: {self.original_image.width}x{self.original_image.height}, "
                                   f"image size: {self.original_size}, "
                                   f"original color mode: {self.original_clr_mode}")

    def showMenu(self, e):
        """Call of menu by clicking right mouse button"""
        self.menu.post(e.x_root, e.y_root)


    def onResize(self, event):
        """Determines the ratio of old width/height to new width/height"""

        self.canv.width = event.width
        self.canv.height = event.height
        self.canv.config(width=self.canv.width, height=self.canv.height)

        # Cancel the previous call, if there is one
        if hasattr(self, "_after_id"):
            self.canv.after_cancel(self._after_id)

        # planning image update after 200 milliseconds (or other suitable delay)
        self._after_id = self.canv.after(200, self.resizeToFit)


    def info(self, *args):

        root = Toplevel()
        root.title("About Program")
        root.geometry("900x780+0+0")
        root.resizable(False, False)

        text_frame = Frame(root, bg="white")
        text_frame.pack(side='left', fill="both", expand=True)

        icon = ImageTk.PhotoImage(Image.open("icons/app_icon.ico").resize((128, 128), Resampling.LANCZOS))
        label_1 = Label(text_frame, image=icon)
        label_1.pack(side='top', pady=20)

        label_2 = Label(text_frame, text="DualTone v.1.0", font=("Helvetica", 18, "bold"), bg="white")
        label_2.pack(side='top')

        label_3 = Label(text_frame, text="Copyright 2023 Kanstantsin Mironau", font="Helvetica 11", bg="white")
        label_3.pack(side='top')

        label_4 = HyperlinkLabel(text_frame,
                                 text="Icons by Icons8",
                                 url="https://icons8.com",
                                 font="Helvetica 11",
                                 bg="white")
        label_4.pack(side='top')

        label_5 = HyperlinkLabel(text_frame,
                                 text="Source code and User's guide are available on GitHub",
                                 url="https://github.com/Kanstantsin1989/dualtone_v1.0",
                                 font="Helvetica 11",
                                 bg="white")
        label_5.pack(side='top')

        license = "\nThis application is distributed under the MIT license\n" \
                       "\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software " \
                       "and associated documentation files (the “Software”), to deal in the Software without " \
                       "restriction, including without limitation the rights to use, copy, modify, merge, publish, " \
                       "distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the " \
                       "Software is furnished to do so, subject to the following conditions:\n" \
                       "\nThe above copyright notice and this permission notice shall be included in all copies or " \
                       "substantial portions of the Software.\n" \
                       "\nTHE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING " \
                       "BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND " \
                       "NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, " \
                       "DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, " \
                       "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.\n" \
                       "\nE-mail to contact the author: 7524440@gmail.com\n"

        license_text = Text(text_frame, font="Helvetica 12", foreground="black", wrap="word", bd=0)
        license_text.pack(side="top", fill="both", expand=True, padx=15, pady=15)
        license_text.insert("end", license)

        donations = '''
If you like this app, you can donate the author:

Bitcoin: bc1qchcz4nmcsa7v5xz7pwngwkk2jcqya3r5qmdx7r
Etherum: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B
Polygon: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B
Polkadot: 16Pf7GjVpgb8nfMujFExkaWtCu5NyeR6oksC7AKkTtPvfuUw
BNB Smart Chain: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B
Rootstock: 0xbEBC82f17Efdf78839364974f64c9c8665da5b7b
Optimism: 0xBEBc82F17eFdf78839364974f64C9c8665da5B7B
Paypal: 7524440@gmail.com
Payoneer: 7524440@gmail.com
'''

        license_text.insert("end", donations)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=license_text.yview)
        license_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")
        root.mainloop()


if __name__ == '__main__':
    DualTone()