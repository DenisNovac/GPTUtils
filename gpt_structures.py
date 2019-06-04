# Structures for searching partitions in GPT disks (for Python 3)
# USAGE: see gpt_reader.py
# 
# Other GPT utilities https://github.com/DenisNovac/GPTUtils
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

import zlib



# structure for saving detected GPT partitions
class GptPartition( object ):
    guid=None
    unique_guid=None
    primary_block=None
    secondary_block=None
    primary_offset=None
    secondary_offset=None

    is_secret=False

    # initiates correctly through GptReader.append_partitions_list()
    # def __init__( self ):
        # pass

    def info( self ):
        print("\n-------------"+self.unique_guid+" : "+self.guid+"-------------")
        print("\n"+str(self.primary_offset)+":")
        print(self.primary_block.hex())
        print("\n"+str(self.secondary_offset)+":")
        print(self.secondary_block.hex())



# structure for work with gpt headers
class GptHeader( object ):
    gpt_header=None
    header_size=None
    entry_size=None
    checksum=None
    current_lba=None
    backup_lba=None
    entries_number=None
    entries_checksum=None

    gpt_header_offset=None
    partition_table=None
    partition_table_offset=None

    def __init__( self, gpt_header, gpt_header_offset, partition_table, partition_table_offset ):
        self.gpt_header=gpt_header
        self.header_size=int.from_bytes(gpt_header[0x0C:0x0C+4],"little")
        self.entry_size=int.from_bytes(gpt_header[0x54:0x54+4],"little")
        self.checksum=self.gpt_header[0x10:0x10+4]
        self.current_lba=int.from_bytes(gpt_header[0x18:0x18+8],"little")
        self.backup_lba=int.from_bytes(gpt_header[0x20:0x20+8],"little")
        self.entries_number=int.from_bytes(gpt_header[0x50:0x50+4],"little")
        self.entries_checksum=self.gpt_header[0x58:0x58+4]

        self.gpt_header_offset=gpt_header_offset
        self.partition_table=partition_table
        self.partition_table_offset=partition_table_offset
        pass

    def calculate_checksum( self, gpt_header ):
        header_size=int.from_bytes(gpt_header[0x0C:0x0C+4],"little")
        # creation of gpt_header with zeroed checksum field
        gpt_header_zero_cs=[ ]
        gpt_header_zero_cs.append(gpt_header[0:0x10])
        gpt_header_zero_cs.append(bytes(bytearray(4)))
        gpt_header_zero_cs.append(gpt_header[0x14:header_size])
        gpt_header_zero_cs=b''.join(gpt_header_zero_cs)
        # checksum in big-endian
        checksum=zlib.crc32(gpt_header_zero_cs)
        # checksum in little-endian bytes
        checksum=checksum.to_bytes((checksum.bit_length()+7)//8,"little")
        return checksum

    # partition table CRC32/zlib checksum
    def calculate_partition_table_checksum( self, partition_table ):
        # partition table checksum in big-endian
        checksum=zlib.crc32(partition_table)
        # patition table checksum in little-endian bytes
        checksum=checksum.to_bytes((checksum.bit_length()+7)//8,"little")
        # return in bytes
        return checksum

    def print_info( self ):
        print("\n\nGPT header ("+str(self.gpt_header_offset)+"): ")
        print(self.gpt_header.hex())
        print("Header size: "+str(self.header_size))
        print("Checksum: "+self.checksum.hex())
        print("Current LBA: "+str(self.current_lba))
        print("Backup LBA: "+str(self.backup_lba))
        print("Entries number: "+str(self.entries_number))
        print("Entry size: "+str(self.entry_size))
        print("Partition table offset: "+str(self.partition_table_offset))
        print("Partition table checksum: "+self.entries_checksum.hex())

        print("\nCalculated header checksum: "+self.calculate_checksum(self.gpt_header).hex())
        print("Calculated partition table checksum: "+
            self.calculate_partition_table_checksum(self.partition_table).hex())

    
