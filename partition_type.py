# Enumeration for  GPT disks utility (for Python 3)
# 
# Other GPT utilities https://github.com/DenisNovac/GPTUtils
# Documentation https://en.wikipedia.org/wiki/GUID_Partition_Table

from enum import Enum


class PartitionType(Enum):
    MBR="024DEE41-33E7-11D3-9D69-0008C781F39F"
    EFI="C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
    BIOS_boot_partition="21686148-6449-6E6F-744E-656564454649"
    # Microsoft types:
    Microsoft_reserved_partition="E3C9E316-0B5C-4DB8-817D-F92DF00215AE"
    Microsoft_basic_data_partition="EBD0A0A2-B9E5-4433-87C0-68B6B72699C7"
    Microsoft_Logical_Disk_Manager_metadata_partition="5808C8AA-7E8F-42E0-85D2-E1E90434CFB3"
    Microsoft_Logical_Disk_Manager_data_partition="AF9B60A0-1431-4F62-BC68-3311714A69AD"
    Windows_Recovery_Environment="DE94BBA4-06D1-4D40-A16A-BFD50179D6AC"
    Microsoft_Storage_Spaces_partition="E75CAF8F-F680-4CEE-AFA3-B001E56EFC2D"
    # Linux types
    Linux_filesystem_data="0FC63DAF-8483-4772-8E79-3D69D8477DE4"
    Linux_RAID_partition="A19D880F-05FC-4D3B-A006-743F0F84911E"
    Linux_Root_partition_x86="44479540-F297-41B2-9AF7-D131D5F0458A"
    Linux_Root_partition_x86_64="4F68BCE3-E8CD-4DB1-96E7-FBCAF984B709"
    Linux_Root_partition_ARM_x32="69DAD710-2CE4-4E3C-B16C-21A1D49ABED3"
    Linux_Root_partition_ARM_x64="B921B045-1DF0-41C3-AF44-4C6F280D3FAE"
    Linux_Swap_partition="0657FD6D-A4AB-43C4-84E5-0933C84B4F4F"
    Linux_Logical_Volume_Manager_partition="E6D6D379-F507-44C2-A23C-238F2A3DF928"
    Linux_home_partition="933AC7E1-2EB4-4F13-B844-0E14E2AEF915"
    Linux_server_data_partition="3B8F8425-20E0-4F3B-907F-1A25A76F98E8"
    Linux_Plain_dm_crypt_partition="7FFEC5C9-2D00-49B7-8941-3EA10A5586B7"
    Linux_LUKS_partition="CA7D7CCB-63ED-4C53-861C-1742536059CC"
    Reserved="8DA63339-0007-60C0-C436-083AC8230908"

    # returns string representation of partition type
    @staticmethod
    def type( partition_guid ):
        for e in PartitionType:
            if e.value == partition_guid:
                # only output type, not class name
                return str(e).split("PartitionType.",1)[1]
        return "Unknown"