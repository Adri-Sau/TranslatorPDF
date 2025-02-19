import pytesseract, os, click, cv2 # opencv-python
from tqdm import tqdm
from pdf2image import convert_from_path 

class Translate:
    def __init__(self, filepath: str, p: bool) -> None:
        self.filepath = filepath.replace("\\", "/")
        self.filename = filepath.replace("\\", "/").split("/")[-1]

        self.tempfolder = "temp"

        self.preservetemp = p

        self.bounds = {}

        self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        self.process()

    def save_pages_as_images(self) -> None:
        click.echo(self.filepath)
        os.path.exists(self.tempfolder) or os.makedirs(self.tempfolder)
        convert_from_path(self.filepath, 500, fmt="jpeg", output_folder=self.tempfolder, output_file=self.filename.split(".")[0], thread_count=8)

    
    def delete_box(self, i: int, d: dict) -> dict:
        del d['level'][i]
        del d['page_num'][i]
        del d['block_num'][i]
        del d['par_num'][i]
        del d['line_num'][i]
        del d['word_num'][i]
        del d['left'][i]
        del d['top'][i]
        del d['width'][i]
        del d['height'][i]
        del d['conf'][i]
        del d['text'][i]
        return d

    def generate_bounds(self, image_path: str) -> dict:
        bounds = {}
        for image_filename in tqdm(os.listdir(image_path)):
            img = cv2.imread(image_path + image_filename)
            d = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

            n_boxes = len(d['text'])

            faulty_boxes = []

            for i in range(n_boxes-1, -1,-1):
                level = d['level'][i]
                if level != 2:
                    faulty_boxes.append(i)
                    continue
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                if (w*h < 3000) or w < 20 or h < 10:
                    faulty_boxes.append(i)
            # print(img.size) # (1654, 2339)

            cv2.imwrite(self.temp_folder + image_filename, img)

            for i in faulty_boxes:
                d = self.delete_box(i, d)

            bounds[image_filename] = d
            
        return bounds
    
    def fix_external_bounds(self, tuple: tuple, i: int, filename: str) -> None:
        (x, y, w, h) = tuple
        if x < 0:
            self.bounds[filename]['left'][i] = 0
        if y < 0:
            self.bounds[filename]['top'][i] = 0
        if x + w > 1654:
            self.bounds[filename]['width'][i] = 1654 - x
        if y + h > 2339:
            self.bounds[filename]['height'][i] = 2339 - y
    
    def fix_relative_bounds(self, tuple_i: tuple, tuple_j: tuple, i: int, j: int, filename: str) -> None:
        (x, y, w, h) = tuple_i
        (x2, y2, w2, h2) = tuple_j

        
        if y2 >= y + h and abs(y+h-y2) < 20:
            print(tuple_i, tuple_j)
            self.bounds[filename]['left'][i] = max(x, x2)
            self.bounds[filename]['top'][i] = y
            self.bounds[filename]['width'][i] = max(w, w2)
            self.bounds[filename]['height'][i] = h + abs(y2-y) + h2
            self.bounds = self.delete_box(j, self.bounds[filename])
    
    def fix_bounds(self) -> None:
        for filename in tqdm(self.bounds):
            for i in range(len(self.bounds[filename]['text'])):
                (x, y, w, h) = (self.bounds[filename]['left'][i], self.bounds[filename]['top'][i], self.bounds[filename]['width'][i], self.bounds[filename]['height'][i])
                self.fix_external_bounds((x, y, w, h), i, filename)
                for j in range(len(self.bounds[filename]['text'])):
                    if i == j:
                        continue
                    (x2, y2, w2, h2) = (self.bounds[filename]['left'][j], self.bounds[filename]['top'][j], self.bounds[filename]['width'][j], self.bounds[filename]['height'][j])
                    self.fix_relative_bounds((x, y, w, h), (x2, y2, w2, h2), i, j, filename)
    
    def visualize_bounds(self) -> None:
        for image_filename in tqdm(self.bounds):
            img = cv2.imread(self.temp_folder + image_filename)
            d = self.bounds[image_filename]
            n_boxes = len(d['text'])
            for i in range(n_boxes):
                (x, y, w, h) = (d['left'][i], d['top'][i], d['width'][i], d['height'][i])
                cv2.rectangle(img, (x, y), (x + w, y + h), (0,0,255), 1)

            cv2.imwrite(self.temp_folder + image_filename, img)

    def remove_temp_folder(self) -> None:
        for image_filename in tqdm(os.listdir(self.tempfolder)):
            os.remove(self.tempfolder + "/" + image_filename)
        os.rmdir(self.tempfolder)

    def process(self) -> None:
        if not self.filename.endswith(".pdf"):
            click.echo("Please provide a PDF file")
            return

        click.echo(f"Saving pages of {self.filename} as images")
        self.save_pages_as_images()

        # click.echo(f"Generating bounds for {self.filename}")
        # self.bounds = self.generate_bounds()

        # # print(self.bounds)

        # click.echo(f"Fixing bounds for {self.filename}")
        # self.fix_bounds()

        # click.echo(f"Visualizing bounds for {self.filename}")
        # self.visualize_bounds()

        if not self.preservetemp:
            self.remove_temp_folder()

        click.echo(f"Done processing {self.filename}")
        click.echo()
