# Utility for hiding partititons in GPT disks (for Python 3)
# USAGE: sudo python gpt_secret_partition /dev/sdb
# 
# Other GPT utilities https://github.com/DenisNovac/GPTUtils
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

import sys

from gpt_structures import GptHeader
from gpt_structures import GptPartition
from gpt_reader import GptReader
from partition_type import PartitionType



# hides partition from applications such as fdisk, gparted
# prevents them from mounting
# only gpt_reader knows where to look to find hidden partitions
def hide_partition( disk_path, primary_header, secondary_header, partition, hide ):

    # partitions entries are the same - we can use only one
    primary_block=partition.primary_block
    
    # guids are the same in both blocks
    guids=primary_block[0:32]
    
    # can not use custom guids. It must be ZEROES to be passed
    new_guids=None
    if hide:
        new_guids=bytes(bytearray(32))
    else:
        new_guids=primary_block[len(partition.primary_block)-32:len(partition.primary_block)]

    # creating block with guids at the end
    new_block=new_guids+primary_block[32:len(primary_block)-32]+guids
    
    # now we need to insert this block into partition table
    # this is relative offset inside a patritions table
    offset_in_table = partition.primary_offset-primary_header.partition_table_offset

    # need to create field with table to calculate checksum
    new_partition_table=primary_header.partition_table[0:offset_in_table]+new_block+primary_header.partition_table[offset_in_table+primary_header.entry_size:len(primary_header.partition_table)]
    new_partition_checksum=primary_header.calculate_partition_table_checksum(new_partition_table)
    
    # now create headers with previous checksum and calculate
    # new checksum with it
    new_primary_header=primary_header.gpt_header[0:0x58]+new_partition_checksum+primary_header.gpt_header[0x5C:primary_header.header_size]
    new_primary_checksum=primary_header.calculate_checksum(new_primary_header)

    new_secondary_header=secondary_header.gpt_header[0:0x58]+new_partition_checksum+secondary_header.gpt_header[0x5C:secondary_header.header_size]
    new_secondary_checksum=secondary_header.calculate_checksum(new_secondary_header)


    # now we need to insert new partition block in both tables
    # and new checksums in both headers
    # r+ mode allows to write inside of file
    disk = open(disk_path,"r+b")

    # seek primary header checksum
    disk.seek(primary_header.gpt_header_offset+0x10)
    disk.write(new_primary_checksum)
    disk.seek(0)

    # seek primary header partition table checksum
    disk.seek(primary_header.gpt_header_offset+0x58)
    disk.write(new_partition_checksum)
    disk.seek(0)

    # seek partition inside partition table
    disk.seek(primary_header.partition_table_offset+offset_in_table)
    disk.write(new_block)
    disk.seek(0)

    # seek secondary partition inside secondary partition table
    disk.seek(secondary_header.partition_table_offset+offset_in_table)
    disk.write(new_block)
    disk.seek(0)

    # seek secondary header checksum
    disk.seek(secondary_header.gpt_header_offset+0x10)
    disk.write(new_secondary_checksum)
    disk.seek(0)

    # seek secondary header partition table checksum
    disk.seek(secondary_header.gpt_header_offset+0x58)
    disk.write(new_partition_checksum)

    disk.close()



def main( args ):
    reader = None
    try:
        reader=GptReader(args[1],True)
    except IndexError:
        print("USAGE: sudo python3 gpt_secret_partition.py DISK_PATH(/dev/sdX)")
        exit(-1)
    if not reader.verify_gpt():
        print(args[1]+" is not a GPT disk")
        exit(-1)

    primary_header = reader.read_primary_gpt_header()
    secondary_header = reader.read_secondary_gpt_header()
    primary_header.print_info()
    secondary_header.print_info()

    reader.append_partitions_list( primary_header.partition_table, True )
    reader.append_partitions_list( secondary_header.partition_table, False)
    
    # interactive interface
    while True:
        print("\nDetected partitions: "+str(len(reader.PARTITIONS_LIST)))
        keys=list(reader.PARTITIONS_LIST.keys())
        number=1
        for k in keys:
            partition=reader.PARTITIONS_LIST.get(k)
            type=PartitionType.type(partition.guid)
            print(str(number)+": "+partition.unique_guid+" "+partition.guid+" "+type+" "+str(partition.is_secret))
            number=number+1

        # user choses partition to work with or exit
        choice=input("Choose partition (E for exit): ")
        if str(choice).upper()=='E':
            exit(0)
        choice=int(choice)
        partition=reader.PARTITIONS_LIST.get(keys[choice-1])
        print("Partition info: ")
        partition.info()

        # menu - hide or unhide partitions or exit
        choice=input("\nWhat to do: \n(H)Hide\n(U)Unhide\n(B)Back\n(E)Exit\n: ").upper()
        if choice=='B':
            continue
        if choice=='H':
            # if it is already hidden
            if partition.is_secret:
                print("\n\nERROR: YOU CAN NOT HIDE SECRET PARTITION")
                continue
            hide_partition(args[1],primary_header,secondary_header,partition,True)
        if choice=='U':
            # if it is already unhidden
            if not partition.is_secret:
                print("\n\nERROR: YOU CAN NOT UNHIDE NOT SECRET PARTITION")
                continue
            hide_partition(args[1],primary_header,secondary_header,partition,False)
        exit(0)



# need this if execution is not from import
if __name__ == "__main__":
    main(sys.argv)