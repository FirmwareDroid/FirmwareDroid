#############################################################
# Modified version of the ubi_reader
# (c) 2013 Jason Pruitt (jrspruitt@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################
import logging
import os
from scripts.utils.file_utils.file_util import create_directories


def extract_ubi_image(img_file_path, output_path):
    """
    Extracts an UBI image file to the given output path.
    :param img_file_path: str - path of the ubi image file.
    :param output_path: str - path of the output folder.
    :return bool - true if image was extracted, false if not.
    """
    isExtracted = False
    logging.info(f"Attempt to extract image with ubi reader: {img_file_path}")
    args = {"log": False,
            "verbose": False,
            "warn_only_block_read_errors": False,
            "ignore_block_header_errors": False,
            "uboot_fix": False,
            "start_offset": None,
            "guess_offset": None,
            "end_offset": None,
            "block_size": None,
            "image_type": None,
            "outpath": output_path}
    try:
        ubireader_extract_images(args, img_file_path)
        isExtracted = True
    except SystemExit as err:
        logging.error(f"UBI-Reader called SystemExit Code: {err}")
    except Exception as err:
        logging.error(err)
    logging.info(f"Ubi reader finished")
    return isExtracted


def ubireader_extract_images(args, img_file_path):
    """
    UBI Reader is a Python module and collection of scripts capable of extracting the contents of UBI and UBIFS images,
    along with analyzing these images to determine the parameter settings to recreate them using the mtd-utils tools.
    :param args: array - arguments for the ubi tool. See ubi_reader reference for more info.
    :param img_file_path: str - path of the image to extact
    """
    from ubireader import settings
    from ubireader.ubi import ubi
    from ubireader.ubi.defines import UBI_EC_HDR_MAGIC
    from ubireader.ubi_io import ubi_file
    from ubireader.utils import guess_filetype, guess_start_offset, guess_peb_size
    settings.logging_on = args["log"]
    settings.logging_on_verbose = args["verbose"]
    settings.warn_only_block_read_errors = args["warn_only_block_read_errors"]
    settings.ignore_block_header_errors = args["ignore_block_header_errors"]
    settings.uboot_fix = args["uboot_fix"]
    if args["start_offset"]:
        start_offset = args["start_offset"]
    elif args["guess_offset"]:
        start_offset = guess_start_offset(img_file_path, args["guess_offset"])
    else:
        start_offset = guess_start_offset(img_file_path)

    if args["end_offset"]:
        end_offset = args["end_offset"]
    else:
        end_offset = None

    filetype = guess_filetype(img_file_path, start_offset)
    if filetype != UBI_EC_HDR_MAGIC:
        raise ValueError(f"File does not look like UBI data: {img_file_path}")

    img_name = os.path.basename(img_file_path)
    if args["outpath"]:
        outpath = os.path.abspath(os.path.join(args["outpath"], img_name))
    else:
        outpath = os.path.join(settings.output_dir, img_name)

    if args["block_size"]:
        block_size = args["block_size"]
    else:
        block_size = guess_peb_size(img_file_path)

        if not block_size:
            raise ValueError(f"Block size could not be determined: {img_file_path}")

    if args["image_type"]:
        image_type = args["image_type"].upper()
    else:
        image_type = 'UBIFS'

    # Create file object.
    ufile_obj = ubi_file(img_file_path, block_size, start_offset, end_offset)

    # Create UBI object
    ubi_obj = ubi(ufile_obj)

    # Loop through found images in file.
    for image in ubi_obj.images:
        if image_type == 'UBI':
            # Create output path and open file.
            img_outpath = os.path.join(outpath, 'img-%s.ubi' % image.image_seq)
            create_directories(outpath)
            f = open(img_outpath, 'wb')

            # Loop through UBI image blocks
            for block in image.get_blocks(ubi_obj.blocks):
                if ubi_obj.blocks[block].is_valid:
                    # Write block (PEB) to file
                    f.write(ubi_obj.file.read_block(ubi_obj.blocks[block]))

        elif image_type == 'UBIFS':
            # Loop through image volumes
            for volume in image.volumes:
                # Create output path and open file.
                vol_outpath = os.path.join(outpath, 'img-%s_vol-%s.ubifs' % (image.image_seq, volume))
                create_directories(outpath)
                f = open(vol_outpath, 'wb')

                # Loop through and write volume block data (LEB) to file.
                for block in image.volumes[volume].reader(ubi_obj):
                    f.write(block)
