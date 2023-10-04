

# Based on https://fte.com/webhelpII/HSU/Content/Technical_Information/BT_Snoop_File_Format.htm


import struct


class BtSnoopFileHeader:
  DATALINK_TYPE_UNENCAPSULATED_HCI_H1 = 1001
  DATALINK_TYPE_HCI_UART_H4 = 1002
  DATALINK_TYPE_HCI_BSCP = 1003
  DATALINK_TYPE_HCI_SERIAL_H5 = 1004
  DATALINK_TYPE_RESERVED = range(0, DATALINK_TYPE_UNENCAPSULATED_HCI_H1)
  # Unassigned is not included, but it goes from 1005 to 4294967295.

  def __init__(self):
    self.identification_pattern = None
    self.version = None
    self.datalink_type = None

  def validate(self):
    error = None

    # The identification pattern field consists of 8 hexadecimal octets, 'btsnoop\0'.
    valid = self.identification_pattern == b"btsnoop\0"

    if not valid:
      error = f"Identification pattern validation failed: expected b'btsnoop\0', was {self.identification_pattern}"

    if valid:
      # There is only one version recognized by this parser for now.
      valid = self.version == 1

      if not valid:
        error = f"Version validation failed: expected 1, was {self.version}"

    if valid:
      # Don't restrict parsing to just HCI UART (H4) [1002].
      valid = self.datalink_type in [
        BtSnoopFileHeader.DATALINK_TYPE_UNENCAPSULATED_HCI_H1,
        BtSnoopFileHeader.DATALINK_TYPE_HCI_UART_H4,
        BtSnoopFileHeader.DATALINK_TYPE_HCI_BSCP,
        BtSnoopFileHeader.DATALINK_TYPE_HCI_SERIAL_H5
      ]

      if not valid:
        error = f"Datalink type not recognized: {self.datalink_type}"

    return error

  @staticmethod
  def read(binary_file_reader):
    bsfh = BtSnoopFileHeader()

    bsfh.identification_pattern = binary_file_reader.read(8)
    bsfh.version = struct.unpack(">I", binary_file_reader.read(4))[0]
    # It.. returns a tuple in 3.x? Yeaup: https://docs.python.org/3/library/struct.html#struct.unpack
    bsfh.datalink_type = struct.unpack(">I", binary_file_reader.read(4))[0]

    # Note: Regarding the comment from the forked repo:
    #
    #   assert datalinkType == 0x3EA, datalinkType # no idea
    #
    # With a reference to a C-based btsnoop decoder
    # (https://github.com/bertrandmartel/btsnoop-decoder/blob/master/src/btsnoopfileinfo.cpp#L66),
    #
    # #
    # # for (int i = 12;i<16;i++){
    # #   datalink_num+=((data[12] & 0xFF) << ((3-(i-12)))*8);
    # # }
    # #   datalink_num+=((data[12] & 0xFF) << ((3-(12-12)))*8);
    # #                                       ((3-(0)))*8
    # #                                       ((3-0))*8
    # #                                       ((3))*8
    # #   datalink_num+=((data[13] & 0xFF) << ((3-(13-12)))*8);
    # #                                       ((3-(1)))*8
    # #                                       ((3-1))*8
    # #                                       ((2))*8
    # #   datalink_num+=((data[14] & 0xFF) << ((3-(14-12)))*8);
    # #                                       ((3-(2)))*8
    # #                                       ((3-2))*8
    # #                                       ((1))*8
    # #   datalink_num+=((data[15] & 0xFF) << ((3-(15-12)))*8);
    # #                                       ((3-(3)))*8
    # #                                       ((3-3))*8
    # #                                       ((0))*8
    # # }
    # some testing, and a bit of virtual pen and paper:
    # 
    # data_link_bytes = bytearray([0x00, 0x00, 0x03, 0xEA])
    # data_link_number = 0

    # for i in range(len(data_link_bytes)):
    #   data_link_number += ((data_link_bytes[i] & 0xFF) << ((3 - i) * 8))

    # print(f"Data Link Number: {data_link_number}") -> Data Link Number: 1002
    # Which is the HCI UART (H4) data link type.

    # And then I saw the struct.unpack getting used, and then the bytes -> integer above
    # became quite trivial and unnecessary in the Land of Pythonia.
    # Still, nice to see how it works behind the scenes. ^_^

    return bsfh, bsfh.validate()


class BtSnoopFilePacketRecord:
  PACKET_FLAGS_DIRECTION_BIT = 0 # 0 = Sent; 1 = Received
  PACKET_FLAGS_COMMAND_BIT = 1   # 0 = Data; 1 = Command|Event
  PACKET_FLAGS_RESERVED_BITS = range(2, 32) # Should be 0.

  def __init__(self):
    self.original_length = None
    self.included_length = None
    self.packet_flags = None
    self.cumulative_drops = None
    self.timestamp_microseconds = None
    self.packet_data = None

  def validate(self):
    error = None

    # The included length might be less than the original length, if the packet as received was truncated.
    valid = self.included_length <= self.original_length

    if not valid:
      error = f"Failed packet record length validation: original length {self.orignal_length} smaller than included length {self.included_length}"

    if valid:
      # Ensure only the non-reserved bits are set.
      for bit in BtSnoopFilePacketRecord.PACKET_FLAGS_RESERVED_BITS:
        valid = (self.packet_flags & (2 << bit)) == 0

        if not valid:
          error = f"Failed packet flags reserved bits validation on bit {bit}"
          break

    # Note from format documentation indicates some implementations don't or can't count dropped packets,
    # so we'll exclude this from validation for now.

    # Well, the microseconds timestamp might also prove difficult to validate, as there might some implementations
    # that use the midnight of 2000 Jan 01 AD, meaning we can't ensure that the field _must_ be higher than 0.

    # Ensure that the length of the packet data is valid (included_length is used, in case of packet truncation).
    if valid:
      valid = len(self.packet_data) == self.included_length

      if not valid:
        error = f"Failed packet data length validation: packet data length {len(self.packet_data)} differs from included length {self.included_length}"

    return error

  @staticmethod
  def read(binary_file_reader):
    bsfpr, error = None, None

    raw_original_length = binary_file_reader.read(4)
    packet_record_available = len(raw_original_length) == 4

    if packet_record_available:
      bsfpr = BtSnoopFilePacketRecord()

      bsfpr.original_length = struct.unpack(">I", raw_original_length)[0]
      bsfpr.included_length = struct.unpack(">I", binary_file_reader.read(4))[0]
      bsfpr.packet_flags = struct.unpack(">I", binary_file_reader.read(4))[0]
      bsfpr.cumulative_drops = struct.unpack(">I", binary_file_reader.read(4))[0]
      bsfpr.timestamp_microseconds = struct.unpack(">q", binary_file_reader.read(8))[0]
      bsfpr.packet_data = binary_file_reader.read(bsfpr.included_length)
      error = bsfpr.validate()

    return bsfpr, error


class BtSnoopFile:
  def __init__(self):
    self.header = None
    self.packet_records = list()

  @staticmethod
  def read(path):
    bsf = BtSnoopFile()
    error = None

    with open(path, "rb") as file:
      bsf.header, error = BtSnoopFileHeader.read(file)

      packet_record_index = 0
      while not error:
        packet_record, error = BtSnoopFilePacketRecord.read(file)

        if not packet_record:
          break

        bsf.packet_records.append(packet_record)
        packet_record_index += 1

    return bsf, error

