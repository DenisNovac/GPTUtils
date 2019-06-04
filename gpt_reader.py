# Program for searching partitions in GPT disks (for Python 3)
# USAGE: sudo python3 gpt_reader.py DISK_PATH(/dev/sdX)
# 
# Other GPT utilities https://github.com/DenisNovac/GPTUtils
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

import sys

from gpt_structures import GptHeader
from gpt_structures import GptPartition



# class for parsing data from gpt disks
class GptReader( object ):
    DISK_PATH=None
    LBA_SIZE=512
    # 128 bytes must be correct for most of the disks
    # Or it can be replaced with header.entry_size
    GPT_ENTRY_SIZE=128
    # size of the disk
    DISK_SECTORS=0
    # dictionary with detected partitions:
    # {partition unique guid:partition object}
    PARTITIONS_LIST=dict()

    # secret search will also search the end of partitions
    # for guids such as gpt_secret_partitions does for
    # hiding partitions
    SEARCH_SECRET=False

    def __init__( self, disk_path, search_secret ):
        self.SEARCH_SECRET=search_secret
        self.DISK_PATH=disk_path

    # verifying gpt through signatures and Protective MBR test
    def verify_gpt( self ):
        global DISK_SECTORS
        try:
            file = open(self.DISK_PATH,"rb")
            protective_mbr = file.read(self.LBA_SIZE)
            file.close()
        except FileNotFoundError:
            print("There is no "+self.DISK_PATH+" disk.")
            return False

        MBR_signature = protective_mbr[0x01FE:0x01FE+2]
        if MBR_signature.hex() == "55aa":
            print("MBR signature found.")
        else:
            print("MBR signature not found.")
            return False

        # reading Protective MBR
        partition_table = [ ]
        print("\nMBR Partition table: ")
        for i in range(0,4):
            partition_table.append(protective_mbr[0x01BE+16*i:0x01BE+16*i+16])
            print(partition_table[i].hex())
        # first partition must not be empty
        if partition_table[0].hex()=="0"*32:
            print("There is no first partition.")
            return False
        # all the other partititons must be empty
        for i in range(1,4):
            if not partition_table[i].hex()=="0"*32:
                print("There is some MBR partition except first one. This is not a GPT disk.")
                return False
        
        # the only record of protective mbr must ends at the end of disk
        guid_first_partition=partition_table[0]
        guid_first_partition_sectors=int.from_bytes(guid_first_partition[0x0C:0x0C+4],"little")+1
        print("\nDisk size in sectors (if not - you are not running a GPT disk): "+str(guid_first_partition_sectors))

        # the only record of protective mbr must have 0xEE signature
        gpt_signature=guid_first_partition[0x04:0x04+1]
        print("Signature of first MBR partition: "+gpt_signature.hex())
        if not gpt_signature.hex() == "ee":
            print("Signature is not 0xEE. This is not a GPT disk.")
            return False
        
        # verifying complete
        print("GPT disk found on "+self.DISK_PATH+".\n")
        DISK_SECTORS=guid_first_partition_sectors
        return True



    # there is two gpt tables on disk - at the beginning and end
    def read_primary_gpt_header( self ):
        file = open(self.DISK_PATH,"rb")
        # jump to LBA 1
        gpt_header_offset=self.LBA_SIZE
        file.seek(gpt_header_offset) 
        gpt_header = file.read(self.LBA_SIZE)
        # read LBA 2-33
        gpt_partition_table_offset=self.LBA_SIZE*2
        gpt_partition_table = file.read(self.LBA_SIZE*32)
        file.close()

        header=GptHeader(gpt_header, gpt_header_offset, 
                        gpt_partition_table, gpt_partition_table_offset)
        return header



    def read_secondary_gpt_header( self ):
        file = open(self.DISK_PATH,"rb")
        # jump to LBA -1
        secondary_gpt_header_offset=DISK_SECTORS*512-self.LBA_SIZE
        file.seek(secondary_gpt_header_offset)
        secondary_gpt_header = file.read(self.LBA_SIZE)
        # jump to LBA -33, read LBA -33-(-2)
        secondary_gpt_partition_table_offset=DISK_SECTORS*512-self.LBA_SIZE*33
        file.seek(secondary_gpt_partition_table_offset)
        secondary_gpt_partition_table=file.read(self.LBA_SIZE*32)
        file.close()


        header=GptHeader(secondary_gpt_header, 
                        secondary_gpt_header_offset, 
                        secondary_gpt_partition_table, 
                        secondary_gpt_partition_table_offset)
        return header



    # parse partition table into single entries, save to objects GPTPartition
    # and then save it in dictionary PARTITIONS_LIST as unique_guid:partition
    # is_primary variable needed to calculate offsets properly
    def append_partitions_list( self, raw_partition_table, is_primary ):
        # GUIDs of 128 partitions. One partition entry is 128 bytes.
        offset=None
        if is_primary:
            offset=self.LBA_SIZE*2
        else:
            offset=DISK_SECTORS*512-self.LBA_SIZE*33
        number=1
        for i in range(0,self.LBA_SIZE*32,self.GPT_ENTRY_SIZE):
            entry=raw_partition_table[i:i+self.GPT_ENTRY_SIZE]

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


            is_secret=False
            # search for gpt_secret_partition pertitions
            if unique_guid=="0"*32 and self.SEARCH_SECRET:
                secret_guid=entry[len(entry)-32:len(entry)-16]
                secret_unique_guid=entry[len(entry)-16:len(entry)]
                guid_first_part = secret_guid[0:8]

                guid_last_part = secret_guid[8:16]
                guid = []

                guid.append(guid_first_part[0:4][::-1].hex())
                guid.append(guid_first_part[4:6][::-1].hex())
                guid.append(guid_first_part[6:8][::-1].hex())

                guid.append(guid_last_part[0:2].hex())
                guid.append(guid_last_part[2:8].hex())

                guid_string="-".join(guid)
                unique_guid=secret_unique_guid.hex()
                if not unique_guid=="0"*32:
                    is_secret=True


            # if there is an actual partition
            if not unique_guid == "0"*32:
                partition=None
                # check if it is inside PARTITIONS_LIST
                known_partition = self.PARTITIONS_LIST.get(unique_guid)
                # if not - creating object
                if not known_partition:
                    partition=GptPartition()
                    partition.guid=guid_string.upper()
                    partition.unique_guid=unique_guid.upper()
                    self.PARTITIONS_LIST.update({unique_guid:partition})
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
                if is_secret:
                    partition.is_secret=True
            number=number+1
            offset=offset+self.GPT_ENTRY_SIZE
        


def main( args ):
    reader = None
    try:
        reader=GptReader(args[1],False)
    except IndexError:
        print("USAGE: sudo python3 gpt_reader.py DISK_PATH(/dev/sdX)")
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
    
    print("\n\nDetected partitions: "+str(len(reader.PARTITIONS_LIST)))
    for k in reader.PARTITIONS_LIST.keys():
        partition=reader.PARTITIONS_LIST.get(k)
        partition.info()
    return None
    
# need this if execution is not from import
if __name__ == "__main__":
    main(sys.argv)