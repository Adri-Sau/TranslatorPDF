import pytesseract, os, click, cv2, pandas # opencv-python
from tqdm import tqdm
from pdf2image import convert_from_path 

class Translate:
    def __init__(self, filepath: str, p: bool) -> None:
        self.filepath = filepath.replace("\\", "/")
        self.filename = filepath.replace("\\", "/").split("/")[-1]
        self.preservetemp = p

        self.first_page = 1
        self.last_page = 10

        self.tempfolder = "temp"
        self.boundsfile = "/bounds.pkl"

        self.regex = r'^[A-Za-z0-9\-]+([.,][A-Za-z0-9]+)*[.,]?$'
        self.config = r'-l eng+deu --oem 3 --psm 6'
        # psm 6 for toc
        # psm 4 for all
        self.char_whitelist = r'-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

        self.min_level = 2
        self.max_level = 4
        self.min_width = 10
        self.min_height = 10


        self.bounds = {}

        self.tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path

        self.process()

    def save_pages_as_images(self) -> None:
        os.path.exists(self.tempfolder) or os.makedirs(self.tempfolder)
        convert_from_path(self.filepath, 300, fmt="jpeg", output_folder=self.tempfolder, output_file=self.filename.split(".")[0], thread_count=8, first_page=self.first_page, last_page=self.last_page)

    def get_bounds(self) -> None:
        if os.path.exists(self.tempfolder + self.boundsfile):
            self.bounds = pandas.read_pickle(self.tempfolder + self.boundsfile)
            click.echo("Bounds loaded from file")
            return
        
        toc = True
        for image_filename in tqdm(os.listdir(self.tempfolder)):
            img = cv2.imread(self.tempfolder + "/" + image_filename)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

            if toc:
                word = pytesseract.image_to_string(img)
                word.strip()[0] if word.strip() else None
                if word and ("kapitel".lower() in word.lower()):
                    self.config = r'-l eng+deu --oem 3 --psm 4'
                    toc = False

            self.bounds[image_filename] = pytesseract.image_to_data(img, config=self.config, output_type=pytesseract.Output.DATAFRAME)

    def clean_bounds(self) -> None:
        for image_filename in tqdm(os.listdir(self.tempfolder)):
            if image_filename == self.boundsfile.strip("/"):
                continue
            df = self.bounds[image_filename]
            self.bounds[image_filename] = df[(df.width > self.min_width) & (df.height > self.min_height) & (df.level >= self.min_level) & (df.level <= self.max_level)].reset_index(drop=True)  
            
    def visualize_bounds(self) -> None:   
        for image_filename in tqdm(os.listdir(self.tempfolder)):
            if image_filename == self.boundsfile.strip("/"):
                continue
            img = cv2.imread(self.tempfolder + "/" + image_filename)
            df = self.bounds[image_filename]
            colors = [(0,0,255), (0,255,0), (255,0,0), (255,255,0), (255,0,255)]
            for l, x, y, w, h in zip(df.level, df.left, df.top, df.width, df.height):
                cv2.rectangle(img, (x, y), (x + w, y + h), colors[l-1], 5-l+1) #page bounding box
            cv2.imwrite(self.tempfolder + "/" + image_filename, img)
            
    def save_bounds(self) -> None:
        pandas.to_pickle(self.bounds, self.tempfolder + self.boundsfile)
            
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

        click.echo("Generating bounds")
        self.get_bounds()

        click.echo("Cleaning bounds")
        self.clean_bounds()

        click.echo("Visualizing bounds")
        self.visualize_bounds()

        click.echo(f"Saving bounds for {self.filename}")
        self.save_bounds()

        if not self.preservetemp:
            self.remove_temp_folder()

        click.echo("Done!")
