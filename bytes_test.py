# install pdf2image, poppler-utils

from pdf2image import convert_from_bytes
from PIL import Image
import boto3, time, io
import textractcaller as tc
from trp import Document


# f = open("06 106656 WET 05 SA.pdf", "rb")
# infile = f.read()
# f.close()
# images = convert_from_bytes(infile)
# for idx, img in enumerate(images):
#     img_byte_arr = io.BytesIO()
#     img.save(img_byte_arr, format='png')
#     img_byte_arr = img_byte_arr.getvalue()
#     break
#     # img.save(f"{idx}.jpg", "jpeg")

s3 = boto3.resource('s3', region_name='us-east-1')
bucket = s3.Bucket('mercator-test')
obj = bucket.Object('pdfs/06 106656 WET 05 SA.pdf')
fs = obj.get()['Body'].read()
images = convert_from_bytes(fs)
for idx, img in enumerate(images):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='png')
    img_byte_arr = img_byte_arr.getvalue()
    break
textract = boto3.client('textract')
textract_json = tc.call_textract(
    input_document="s3://mercator-test/pdfs/06 106656 WET 05 SA.pdf",
    boto3_textract_client=textract
)

doc = Document(textract_json)
wordlist = []
for page in doc.pages:
    for line in page.lines:
        for word in line.words:
            wordlist.append(word.text)
words = " ".join(wordlist)
print(words)
if "The name of the amalgamated corporation is: (Set out in BLOCK CAPITAL LETTERS)" in words:
    print(True)
# response = textract.analyze_document(
#     Document={
#         'Bytes': img_byte_arr
#     },
#     FeatureTypes=["QUERIES"],
#     QueriesConfig={
#         "Queries": [{
#             "Text": "What is the address of the registered office?",
#             "Alias": "ADDRESS_REGISTERED_OFFICE"
#         }]
#     }

# )
# print(response)


# # images = [Image.open(x) for x in ['Test1.jpg', 'Test2.jpg', 'Test3.jpg']]
# widths, heights = zip(*(i.size for i in images))

# max_width = max(widths)
# total_height = sum(heights)

# new_im = Image.new('RGB', (max_width, total_height))

# y_offset = 0
# for im in images:
#   new_im.paste(im, (0, y_offset))
#   y_offset += im.size[1]

# new_im.save('test2.jpg', dpi=(300,300))


# image_1 = Image.open(r'0.jpg')
# image_2 = Image.open(r'1.jpg')
# image_3 = Image.open(r'2.jpg')


# im_1 = image_1.convert('RGB')
# im_2 = image_2.convert('RGB')
# im_3 = image_3.convert('RGB')


# image_list = [im_2, im_3]

# im_1.save(r'C:\Users\Ron\Desktop\Test\my_images.pdf', save_all=True, append_images=image_list)