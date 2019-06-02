# Program for searching partitions in GPT-disks.
# 
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

import sys

LBA_SIZE=512
GPT_ENTRY_SIZE=128
DISK_SECTORS=0

# dictionary with detected partitions:
# {partition unique guid:partition object}
PARTITIONS_LIST=dict()

# verifying gpt through signatures and Protective MBR partition
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
    
    partition_table = [ ]
    print("\nMBR Partition table: ")
    for i in range(0,4):
        partition_table.append(protective_mbr[0x01BE+16*i:0x01BE+16*i+16])
        print(partition_table[i].hex())
    
    if partition_table[0].hex()=="0"*32:
        print("There is no first partition.")
        exit(-1)

    for i in range(1,4):
        if not partition_table[i].hex()=="0"*32:
            print("There is some MBR partition except first one. This is not a GPT disk.")
            exit(-1)
    
    guid_first_partition=partition_table[0]
    guid_first_partition_sectors=int.from_bytes(guid_first_partition[0x0C:0x0C+4],"little")+1
    
    print("\nDisk size in sectors (if not - you are not running a GPT disk): "+str(guid_first_partition_sectors))
    gpt_signature=guid_first_partition[0x04:0x04+1]
    print("Signature of first MBR partition: "+gpt_signature.hex())
    if not gpt_signature.hex() == "ee":
        print("Signature is not 0xEE. This is not a GPT disk.")
        exit(-1)
    
    print("GPT disk found on "+disk_path+".\n")
    DISK_SECTORS=guid_first_partition_sectors

# there is two gpt tables on disk - at the beginning and end

def read_primary_gpt_entries( disk_path ):
    file = open(disk_path,"rb")
    # jump to LBA 1
    file.seek(LBA_SIZE) 
    gpt_header = file.read(LBA_SIZE)
    # read LBA 2-33
    gpt_partition_table = file.read(LBA_SIZE*32)
    file.close()
    print("GPT header: ")
    print(gpt_header.hex())

    get_partitions_list(gpt_partition_table, True)
        

def read_secondary_gpt_entries( disk_path ):
    file = open(disk_path,"rb")
    # jump to LBA -1
    file.seek(DISK_SECTORS*512-LBA_SIZE)
    secondary_gpt_header = file.read(LBA_SIZE)
    print("\nSecondary GPT header: ")
    print(secondary_gpt_header.hex())
    # jump to LBA -33, read LBA -33-(-2)
    file.seek(DISK_SECTORS*512-LBA_SIZE*33)
    secondary_gpt_partition_table=file.read(LBA_SIZE*32)
    file.close()

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

        guid_string="-".join(guid)
        unique_guid=entry[16:32].hex()
    
        if not unique_guid == "0"*32:
            partition=None
            known_partition = PARTITIONS_LIST.get(unique_guid)
            if not known_partition:
                partition=GPTPartition()
                partition.guid=guid_string
                partition.unique_guid=unique_guid
                PARTITIONS_LIST.update({unique_guid:partition})
            if known_partition:
                partition=known_partition
            if is_primary:
                partition.primary_block=entry
                partition.primary_offset=offset
            if not is_primary:
                partition.secondary_block=entry
                partition.secondary_offset=offset

        number=number+1
        offset=offset+GPT_ENTRY_SIZE

# structure for saving detected GPT partitions
class GPTPartition(object):
    guid=None
    unique_guid=None
    primary_block=None
    secondary_block=None
    primary_offset=None
    secondary_offset=None

    def __init__(self):
        pass

    def info(self):
        
        print("\n-------------"+self.guid+" : "+self.unique_guid+"-------------")
        print("\n"+str(self.primary_offset)+":")
        print(self.primary_block.hex())

        print("\n"+str(self.secondary_offset)+":")
        print(self.secondary_block.hex())



def main( args ):
    try:
        verify_gpt(args[1])
        read_primary_gpt_entries(args[1])
        read_secondary_gpt_entries(args[1])
    except IndexError:
        print("USAGE: python3 GPTreader.py DISK_PATH(/dev/sdX)")
        exit(-1)
    
    for k in PARTITIONS_LIST.keys():
        partition=PARTITIONS_LIST.get(k)
        partition.info()

    print(len(PARTITIONS_LIST))
        


main( sys.argv )