# Copyright 2015 Yale University - Grablab
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Modified to work with Python 3 by Sebastian Castro, 2020
# Modified object list to download complete YCB objects by Hongzhuo Liang, 2020
# Modified to extract rgbd files into a folder by Hongzhuo Liang, 2021
import os
import json
# import urllib
import sys
from urllib.request import Request, urlopen

# Define an output folder
output_directory = os.path.join("models", "ycb")

# Define a list of objects to download from
# http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/
objects_to_download = "all"
# objects_to_download = ["001_chips_can",
#                        "002_master_chef_can",
#                        "003_cracker_box",
#                        "004_sugar_box"]

# You can edit this list to only download certain kinds of files.
# 'berkeley_rgbd' contains all of the depth maps and images from the Carmines.
# 'berkeley_rgb_highres' contains all of the high-res images from the Canon cameras.
# 'berkeley_processed' contains all of the segmented point clouds and textured meshes.
# 'google_16k' contains google meshes with 16k vertices.
# 'google_64k' contains google meshes with 64k vertices.
# 'google_512k' contains google meshes with 512k vertices.
# See the website for more details.
# ["berkeley_rgbd", "berkeley_rgb_highres", "berkeley_processed", "google_16k", "google_64k", "google_512k"]

if len(sys.argv) == 2 and sys.argv[1] == "rgbd_512":
    files_to_download = ["berkeley_rgbd", "google_512k"]
else:
    files_to_download = ["berkeley_processed", "google_16k", "google_512k"]

# Extract all files from the downloaded .tgz, and remove .tgz files.
# If false, will just download all .tgz files to output_directory
extract = True
base_url = "http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/data/"
objects_url = "https://ycb-benchmarks.s3.amazonaws.com/data/objects.json"
os.makedirs(output_directory + "/tmp", exist_ok=True)


def fetch_objects(url):
    """ Fetches the object information before download """
    response = urlopen(url)
    html = response.read()
    objects = json.loads(html)
    return objects["objects"]


def download_file(url, filename):
    """ Downloads files from a given URL """
    u = urlopen(url)
    f = open(filename, "wb")
    file_size = int(u.getheader("Content-Length"))
    print("Downloading: {} ({} MB)".format(filename, file_size / 1000000.0))

    file_size_dl = 0
    block_sz = 65536
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl / 1000000.0, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print(status, end="\r")
    f.close()


def tgz_url(obj, obj_type):
    """ Get the TGZ file URL for a particular object and dataset type """
    if obj_type in ["berkeley_rgbd", "berkeley_rgb_highres"]:
        return base_url + "berkeley/{object}/{object}_{type}.tgz".format(object=obj, type=obj_type)
    elif obj_type in ["berkeley_processed"]:
        return base_url + "berkeley/{object}/{object}_berkeley_meshes.tgz".format(object=obj, type=obj_type)
    else:
        return base_url + "google/{object}_{type}.tgz".format(object=obj, type=obj_type)


def extract_tgz(filename, output_dir):
    """ Extract a TGZ file """
    if "berkeley_rgbd" in filename:
        output_dir += "/tmp"
        tar_command = "tar -xzf {filename} -C {dir}".format(filename=filename, dir=output_dir)
    else:
        tar_command = "tar -xzf {filename} -C {dir}".format(filename=filename, dir=output_dir)
    os.system(tar_command)
    os.remove(filename)
    if "berkeley_rgbd" in filename:
        obj_name = filename[11:-18]
        os.system(f"mv {output_dir}/{obj_name} {output_dir}/rgbd")
        os.makedirs(f"{output_dir[:-4]}/{obj_name}", exist_ok=True)
        os.system(f"mv {output_dir}/rgbd {output_dir[:-4]}/{obj_name}")


def check_url(url):
    """ Check the validity of a URL """
    try:
        request = Request(url)
        request.get_method = lambda: "HEAD"
        urlopen(request)
        return True
    except:
        return False


def main():
    # Grab all the object information
    with open("objects.json", "r") as handle:
        objects = json.load(handle)["objects"]

    # Download each object for all objects and types specified
    for obj in objects:
        if objects_to_download == "all" or obj in objects_to_download:
            for file_type in files_to_download:
                url = tgz_url(obj, file_type)
                if not check_url(url):
                    continue
                filename = "{path}/{object}_{file_type}.tgz".format(
                    path=output_directory,
                    object=obj,
                    file_type=file_type)
                download_file(url, filename)
                if extract:
                    extract_tgz(filename, output_directory)


if __name__ == "__main__":
    main()

