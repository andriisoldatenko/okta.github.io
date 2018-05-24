"""
This script transform jekyll blog posts in markdown to hugo specific
It's specific to Okta blog

Unfortunately all available tools doesn't work with images
https://gohugo.io/commands/hugo_import_jekyll/#hugo-import-jekyll

TODO:
- may be create PR for hugo-import-jekyll
"""

import argparse
import logging

import os

import re
from time import strptime, time, strftime

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

JEKYLL_BLOG_FILENAME = re.compile(r'(\d+-\d+-\d+)-(.+)\..*')

# {% img blog/ultimate-pwa-guide/hnpwa.png alt:"Hacker News PWA" width:"800" %}{: .center-image }
IMG_TAG = re.compile(r'(.*|.?){% img ([\w\d/\-.]+) (.*) %}(.*|.?)')
API_OPERATION_TAG = re.compile(r'{% api_operation (\w+) ([\w/*:.{}+$#?=]+) %}')
API_LIFECYCLE_TAG = re.compile(r'{% api_lifecycle (\w+) %}')
API_CORS = re.compile(r'{% api_cors %}')
RAW_TAG = re.compile(r'{% raw %}')
END_RAW_TAG = re.compile(r'{% endraw %}')

def process_line(line):
    m = re.search(IMG_TAG, line)
    center_img = ''
    if m.group(4) and m.group(4) == '{: .center-image }':
        center_img = ' class="center-image"'
    else:
        center_img = m.group(4)
    new_line = m.group(1) + '<img src="/img/' +  m.group(2) + \
               '" ' + m.group(3).replace(':', '=')
    if center_img == ' class="center-image"':
        new_line = new_line + center_img + '>'
    else:
        new_line = new_line + '>' + center_img
    return new_line

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", help="dir with jekyll blog posts",
                        default='_source/_posts/')
    parser.add_argument("--output", help="dir with hugo blog posts",
                        default='hugo/content/blog')
    args = parser.parse_args()
    if args.target:
        if not os.path.exists(args.target):
            log.error('Please use correct folder')
            raise SystemExit
        for file in os.listdir(args.target):
            if file.endswith(".md"):
                f = os.path.join(args.target, file)
                m = re.match(JEKYLL_BLOG_FILENAME, file)
                if m:
                    file_date = strptime(m.group(1), "%Y-%m-%d")
                    new_file = '{}.md'.format(m.group(2))
                else:
                    file_date = None
                    new_file = file
                new_file_path = os.path.join(args.output, new_file)
                with open(f) as orig, open(new_file_path, 'w') as new:
                    data = orig.read()
                    if file_date:
                        data = re.sub(
                            r'author: ([\w\-]+)',
                            r'author: \1\ndate: ' +
                            strftime('%Y-%m-%dT%H:%M:%SZ', file_date),
                            data)
                    data = re.sub(API_OPERATION_TAG, r'{{< api_operation \1 "\2" >}}', data)
                    data = re.sub(API_LIFECYCLE_TAG, r'{{< api_lifecycle \1 >}}', data)
                    data = re.sub(API_CORS, r'{{< api_cors >}}', data)
                    data = re.sub(RAW_TAG, r'', data)
                    data = re.sub(END_RAW_TAG, r'', data)
                    new_lines = []
                    for line in data.splitlines():
                        if '{% img' in line:
                            img_count = line.count('{% img')
                            new_line = line
                            for _ in range(img_count):
                                new_line = process_line(new_line)
                            new_lines.append(new_line)
                        else:
                            new_lines.append(line)
                    new.write('\n'.join(new_lines))

if __name__ == '__main__':
    main()
