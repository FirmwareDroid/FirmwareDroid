import os
import logging

# PAC Header size calculation. Content of most values are unknown.
# 16bit int => 2byte * 24   = someField
# 32bit int => 4byte        = someInt
# 16bit int => 2byte * 256  = productName
# 16bit int => 2byte * 256  = firmwareName
# 32bit int => 4byte        = partitionCount
# 32bit int => 4byte        = partitionsListStart
# 32bit int => 4byte * 5    = someIntFields1
# 16bit int => 2byte * 50   = productName2
# 16bit int => 2byte * 6    = someIntFields2
# 16bit int => 2byte * 2    = someIntFields3
# Total Size PAC-Header     = 1220
from io import BytesIO


class PacHeader:
    """
    Header of the PAC file. Bytes have to be exact to match header.
    """
    def __init__(self,
                 someField,
                 someInt,
                 productName,
                 firmwareName,
                 partitionCount,
                 partitionsListStart,
                 someIntFields1,
                 productName2,
                 someIntFields2,
                 someIntFields3):
        self.someField = someField
        self.someInt = someInt
        self.productName = productName
        self.firmwareName = firmwareName
        self.partitionCount = partitionCount
        self.partitionsListStart = partitionsListStart
        self.someIntFields1 = someIntFields1
        self.productName2 = productName2
        self.someIntFields2 = someIntFields2
        self.someIntFields3 = someIntFields3


class PartitionHeader:
    """
    Header of the Partition. Bytes have to be exact to match header.
    """
    def __init__(self,
                 partition_header_length,
                 partitionName,
                 fileName,
                 partitionSize,
                 someFields1,
                 partitionAddrInPac,
                 someFields2):
        self.partition_header_length = partition_header_length
        self.partitionName = partitionName
        self.fileName = fileName
        self.partitionSize = partitionSize
        self.someFileds1 = someFields1
        self.partitionAddrInPac = partitionAddrInPac
        self.someFileds2 = someFields2


def unpack_pac(path):
    """
    Decompresses a *.pac file.
    :param path: str - path to the *.pac file.
    """
    if os.path.isfile(path) and path.lower().endswith(".pac"):
        try:
            pac_header = create_pac_header(path)
            partition_header_list = create_partition_headers(path, pac_header)
            create_partition_files(path, partition_header_list)
        except Exception as err:
            logging.error(str(err))


def create_pac_header(path):
    """
    Gets the PAC header from the file. The header contains the meta-data needed to extract the files.
    :param path: str - path to the *.pac file.
    :return: class'PacHeader'
    """
    with open(path, "rb") as poc_file:
        some_field = poc_file.read(48)
        some_int = int.from_bytes(poc_file.read(4), byteorder='little')
        # print("some_int: " + str(some_int))
        product_name = poc_file.read(512).decode("utf-8")
        # print("product_name: " + product_name)
        firmware_name = poc_file.read(512).decode("utf-8")
        # print("firmware_name: " + firmware_name)
        partition_count = int.from_bytes(poc_file.read(4), byteorder='little')
        # print("partition_count: " + str(partition_count))
        partitions_list_start = int.from_bytes(poc_file.read(4), byteorder='little')
        # print("partitions_list_start: " + str(partitions_list_start))

        some_int_fields1 = poc_file.read(20)
        product_name2 = poc_file.read(100)
        some_int_fields2 = poc_file.read(12)
        some_int_fields3 = poc_file.read(4)

        return PacHeader(some_field,
                         some_int,
                         product_name,
                         firmware_name,
                         partition_count,
                         partitions_list_start,
                         some_int_fields1,
                         product_name2,
                         some_int_fields2,
                         some_int_fields3)


def create_partition_headers(path, pac_header):
    """
    Extracts the partition headers from the information found in the pac header.
    :param path: str - path to the *.pac file.
    :param pac_header: class: 'PacHeader' - pac header of the file.
    :return: list of class:'PartitionHeader'
    """
    with open(path, "rb") as poc_file:
        seek_position = pac_header.partitionsListStart
        partition_header_list = []
        for x in range(0, pac_header.partitionCount):
            # print("-----------------------------")
            poc_file.seek(seek_position, 0)
            partition_header_length = int.from_bytes(poc_file.read(4), byteorder='little')
            # print("partition_header_length: " + str(partition_header_length))
            if partition_header_length <= 0:
                raise ValueError("Partition length error!")
            partition_name = poc_file.read(512).decode("utf-8")
            # print("partition_name: " + str(partition_name))
            file_name = poc_file.read(1024).decode("utf-8")
            # print("file_name: " + str(file_name))
            partition_size = int.from_bytes(poc_file.read(4), byteorder='little', signed=False)
            # print("partition_size: " + str(partition_size))
            some_fields1 = poc_file.read(8)
            partition_addr_in_Pac = int.from_bytes(poc_file.read(4), byteorder='little', signed=False)
            # print("partition_addr_in_Pac: " + str(partition_addr_in_Pac))

            some_Fields2 = poc_file.read(12)
            partition_header_list.append(PartitionHeader(
                partition_header_length,
                partition_name,
                file_name,
                partition_size,
                some_fields1,
                partition_addr_in_Pac,
                some_Fields2)
            )
            poc_file.seek(seek_position, 0)
            seek_position += partition_header_length
            # print("seek_position at end of loop: " + str(seek_position))
    return partition_header_list


def create_partition_files(path, partition_header_list):
    """
    Extracts the partition files with the partition header information. Writes the extracted files to the disk.
    :param path: str - path to the *.pac file.
    :param partition_header_list: list of class'PartitionHeader'
    """
    with open(path, "rb") as poc_file:
        for partition_header in partition_header_list:
            # print("############################################")
            # print("Attempt to extract: " + partition_header.fileName)
            if partition_header.partitionSize <= 0:
                print("Skipped partition cause of zero length: ")
                continue
            try:
                # print("partition_size: " + str(partition_header.partitionSize))
                # print("partition_header.partitionAddrInPac: " + str(partition_header.partitionAddrInPac))
                poc_file.seek(partition_header.partitionAddrInPac, 0)

                partition_file_path = os.path.join(os.path.dirname(path), partition_header.fileName.replace('\x00', ""))
                # print("partition_file_path: " + str(partition_file_path))
                partition_file = open(partition_file_path, "wb")

                data_size_left = partition_header.partitionSize
                while data_size_left > 0:
                    copy_length = 256 if (data_size_left > 256) else data_size_left
                    data_size_left -= copy_length
                    chunk = poc_file.read(copy_length)
                    partition_file.write(chunk)
                partition_file.close()

                # partition_data = poc_file.read(partition_header.partitionSize)
                # if partition_data:
                #    partition_file.write(partition_data)

                # print("Extracted partition from poc: " + partition_header.fileName)
            except Exception as error:
                print("Error:" + str(error))


