# Program for searching partitions in GPT-disks (for Python 3)
# USAGE: sudo python3 gpt_reader.py DISK_PATH(/dev/sdX)
# 
# Other GPT utilities https://github.com/DenisNovac/GPTUtils
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

import sys

from gpt_structures import GptHeader
from gpt_structures import GptPartition

LBA_SIZE=512
# GPT_ENTRY_SIZE=128 # 128 must be correct for most of the disks
# Now it is calculated from header
GPT_ENTRY_SIZE=128
# size of the disk
DISK_SECTORS=0
# dictionary with detected partitions:
# {partition unique guid:partition object}
PARTITIONS_LIST=dict()



# verifying gpt through signatures and Protective MBR test
def verify_gpt( disk_path ):
    global DISK_SECTORS
    try:
        file = open(disk_path,"rb")
        protective_mbr = file.read(LBA_SIZE)
        file.close()
    except FileNotFoundError:
        print("There is no "+disk_path+" disk.")
        exit(-1)

    MBR_signature = protective_mbr[0x01FE:0x01FE+2]
    if MBR_signature.hex() == "55aa":
        print("MBR signature found.")
    else:
        print("MBR signature not found.")
        exit(-1)

    # reading Protective MBR
    partition_table = [ ]
    print("\nMBR Partition table: ")
    for i in range(0,4):
        partition_table.append(protective_mbr[0x01BE+16*i:0x01BE+16*i+16])
        print(partition_table[i].hex())
    # first partition must not be empty
    if partition_table[0].hex()=="0"*32:
        print("There is no first partition.")
        exit(-1)
    # all the other partititons must be empty
    for i in range(1,4):
        if not partition_table[i].hex()=="0"*32:
            print("There is some MBR partition except first one. This is not a GPT disk.")
            exit(-1)
    
    # the only record of protective mbr must ends at the end of disk
    guid_first_partition=partition_table[0]
    guid_first_partition_sectors=int.from_bytes(guid_first_partition[0x0C:0x0C+4],"little")+1
    print("\nDisk size in sectors (if not - you are not running a GPT disk): "+str(guid_first_partition_sectors))

    # the only record of protective mbr must have 0xEE signature
    gpt_signature=guid_first_partition[0x04:0x04+1]
    print("Signature of first MBR partition: "+gpt_signature.hex())
    if not gpt_signature.hex() == "ee":
        print("Signature is not 0xEE. This is not a GPT disk.")
        exit(-1)
    
    # verifying complete
    print("GPT disk found on "+disk_path+".\n")
    DISK_SECTORS=guid_first_partition_sectors



# there is two gpt tables on disk - at the beginning and end
def read_primary_gpt_entries( disk_path ):
    file = open(disk_path,"rb")
    # jump to LBA 1
    gpt_header_offset=LBA_SIZE
    file.seek(gpt_header_offset) 
    gpt_header = file.read(LBA_SIZE)
    # read LBA 2-33
    gpt_partition_table_offset=LBA_SIZE*2
    gpt_partition_table = file.read(LBA_SIZE*32)
    file.close()

    header=GptHeader(gpt_header, gpt_header_offset, 
                     gpt_partition_table, gpt_partition_table_offset)
    header.print_info()

    get_partitions_list(gpt_partition_table, True)



def read_secondary_gpt_entries( disk_path ):
    file = open(disk_path,"rb")
    # jump to LBA -1
    secondary_gpt_header_offset=DISK_SECTORS*512-LBA_SIZE
    file.seek(secondary_gpt_header_offset)
    secondary_gpt_header = file.read(LBA_SIZE)
    # jump to LBA -33, read LBA -33-(-2)
    secondary_gpt_partition_table_offset=DISK_SECTORS*512-LBA_SIZE*33
    file.seek(secondary_gpt_partition_table_offset)
    secondary_gpt_partition_table=file.read(LBA_SIZE*32)
    file.close()


    header=GptHeader(secondary_gpt_header, 
                    secondary_gpt_header_offset, 
                    secondary_gpt_partition_table, 
                    secondary_gpt_partition_table_offset)
    header.print_info()

    get_partitions_list(secondary_gpt_partition_table, False)



# parse partition table into single entries, save to objects GPTPartition
# and then save it in dictionary PARTITIONS_LIST as unique_guid:partition
# is_primary variable needed to calculate offsets properly
def get_partitions_list ( raw_partition_table, is_primary ):
    # GUIDs of 128 partitions. One partition entry is 128 bytes.
    offset=None
    if is_primary:
        offset=LBA_SIZE*2
    else:
        offset=DISK_SECTORS*512-LBA_SIZE*33
    number=1
    for i in range(0,LBA_SIZE*32,GPT_ENTRY_SIZE):
        entry=raw_partition_table[i:i+GPT_ENTRY_SIZE]

        # this field has mixed endian
        # first part in little-endian
        guid_first_part = entry[0:8]
        # second part in big_endian
        guid_last_part = entry[8:16]
        guid = []
        # reverse first_part
        guid.append(guid_first_part[0:4][::-1].hex())
        guid.append(guid_first_part[4:6][::-1].hex())
        guid.append(guid_first_part[6:8][::-1].hex())
        # don't reverse second part
        guid.append(guid_last_part[0:2].hex())
        guid.append(guid_last_part[2:8].hex())
        # join parts for standard style
        guid_string="-".join(guid)
        unique_guid=entry[16:32].hex()

        # if there is an actual partition
        if not unique_guid == "0"*32:
            partition=None
            # check if it is inside PARTITIONS_LIST
            known_partition = PARTITIONS_LIST.get(unique_guid)
            # if not - creating object
            if not known_partition:
                partition=GptPartition()
                partition.guid=guid_string
                partition.unique_guid=unique_guid
                PARTITIONS_LIST.update({unique_guid:partition})
            # if it is inside PARTITION_LIST - work with it
            if known_partition:
                partition=known_partition
            # update info about offsets and block
            if is_primary:
                partition.primary_block=entry
                partition.primary_offset=offset
            if not is_primary:
                partition.secondary_block=entry
                partition.secondary_offset=offset
        number=number+1
        offset=offset+GPT_ENTRY_SIZE



def main( args ):
    try:
        verify_gpt(args[1])
        read_primary_gpt_entries(args[1])
        read_secondary_gpt_entries(args[1])
    except IndexError:
        print("USAGE: sudo python3 gpt_reader.py DISK_PATH(/dev/sdX)")
        exit(-1)
    print("\n\nDetected partitions: "+str(len(PARTITIONS_LIST)))
    for k in PARTITIONS_LIST.keys():
        partition=PARTITIONS_LIST.get(k)
        partition.info()
    # return for other scripts in repo
    return PARTITIONS_LIST
    
# need this if execution is not from import
if __name__ == "__main__":
    main(sys.argv)