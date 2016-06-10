import base64
import os
import StringIO
from PIL import Image

img_path = 'image_in/input.jpg'

img_size = os.path.getsize(img_path)

print 'Original image size: {:,} b'.format(img_size)

with open(img_path, 'r') as img:
    img_contents = img.read()

img_base64 = base64.b64encode(img_contents)
print 'Original image base64 size: {:,} b'.format(len(img_base64))

image = Image.open(img_path)
print 'Original image width/height: {}'.format(image.size)

size = 225, 225

re_sampling_filters = [
    {'name': 'BC', 'filter': Image.BICUBIC},
    {'name': 'BL', 'filter': Image.BILINEAR},
    {'name': 'LA', 'filter': Image.LANCZOS},
    {'name': 'NE', 'filter': Image.NEAREST}
]


def create_thumbnail_path(n, t):
    return img_path.replace('image_in/', 'thumbnail_out/').replace('.jpg', '.thumbnail.' + n + '.' + t + '.jpg')

if not os.path.exists('thumbnail_out'):
    os.makedirs('thumbnail_out')

for re_sampling_filter in re_sampling_filters:
    print ''
    name = re_sampling_filter['name']
    img_thumbnail = image.copy()
    img_thumbnail.thumbnail(size, re_sampling_filter['filter'])

    print 'thumbnail 1 {} width/height: {}'.format(name, img_thumbnail.size)

    img_thumbnail.save(create_thumbnail_path(name, '1'), 'JPEG')

    thumbnail_content = StringIO.StringIO()
    img_thumbnail.save(thumbnail_content, 'JPEG')
    thumbnail_base64 = base64.b64encode(thumbnail_content.getvalue())
    thumbnail_content.close()

    print 'base64 thumbnail {} size:    {:,} b'.format(name, len(thumbnail_base64))

    thumbnail_content = base64.b64decode(thumbnail_base64)

    with open(create_thumbnail_path(name, '2'), 'w') as imgFile:
        imgFile.write(thumbnail_content)

    print 'thumbnail 1 {} size:         {:,} b'.format(name, os.path.getsize(create_thumbnail_path(name, '1')))
    print 'thumbnail 2 {} size:         {:,} b'.format(name, os.path.getsize(create_thumbnail_path(name, '2')))

    Image.open(StringIO.StringIO(thumbnail_content)).save(create_thumbnail_path(name, '3'), 'JPEG')

