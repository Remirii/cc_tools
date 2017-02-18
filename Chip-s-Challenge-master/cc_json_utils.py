import json
import cc_data
import cc_dat_utils

CC_DAT_HEADER_CODE = b'\xAC\xAA\x02\x00'
RLE_CODE_INT = 255

READ_ADDRESS = 0

def make_level_from_json(parsed_json, givenLevel):
	level = cc_data.CCLevel()
	level.level_number = parsed_json["levels"][givenLevel]["level number"]
	level.time = parsed_json["levels"][givenLevel]["time"]
	level.num_chips = parsed_json["levels"][givenLevel]["chip number"]
    # Note: Map Detail is not used and is expected to always be 1
	map_detail = 1
	level.upper_layer = parsed_json["levels"][givenLevel]["upper layer"]
	level.lower_layer = parsed_json["levels"][givenLevel]["lower layer"]
	level.optional_fields = make_optional_fields_from_json(parsed_json, givenLevel)
	return level

def make_cc_data_from_json(json_file):
    """Reads a DAT file and constructs a CCDataFile object out of it
    This code assumes a valid DAT file and does not error check for invalid data
    Args:
        dat_file (string) : the filename of the DAT file to read in
    Returns:
        A CCDataFile object constructed with the data from the given file
    """
    data = cc_data.CCDataFile()
    json_data = open(json_file).read()
    parsed_json = json.loads(json_data)
    num_levels = len(parsed_json["levels"])
    for i in range(num_levels):
    	level = make_level_from_json(parsed_json, i)
    	data.levels.append(level)
    return data

def make_optional_fields_from_json(parsed_json, givenLevel):
	fields = []
	total_optional_fields = len(parsed_json["levels"][givenLevel]["optional fields"][0])
	count = 0
	while count < len(parsed_json["levels"][givenLevel]["optional fields"]):
		if parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 3:
			fields.append(cc_data.CCMapTitleField(parsed_json["levels"][givenLevel]["optional fields"][count]["title"]))
		elif parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 4:
			traps = []
			trap_count = len(parsed_json["levels"][givenLevel]["optional fields"][count]["traps"])
			for t in range(trap_count):
				bx = parsed_json["levels"][givenLevel]["optional fields"][count]["traps"][t]["bx"]
				by = parsed_json["levels"][givenLevel]["optional fields"][count]["traps"][t]["by"]
				tx = parsed_json["levels"][givenLevel]["optional fields"][count]["traps"][t]["tx"]
				ty = parsed_json["levels"][givenLevel]["optional fields"][count]["traps"][t]["ty"]
				traps.append(cc_data.CCTrapControl(bx, by, tx, ty))
			fields.append(cc_data.CCTrapControlsField(traps))
		elif parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 5:
			machines = []
			machine_count = len(parsed_json["levels"][givenLevel]["optional fields"][count]["cloning machines"])
			for t in range(trap_count):
				bx = parsed_json["levels"][givenLevel]["optional fields"][count]["cloning machines"][t]["bx"]
				by = parsed_json["levels"][givenLevel]["optional fields"][count]["cloning machines"][t]["by"]
				tx = parsed_json["levels"][givenLevel]["optional fields"][count]["cloning machines"][t]["tx"]
				ty = parsed_json["levels"][givenLevel]["optional fields"][count]["cloning machines"][t]["ty"]
				machines.append(cc_data.CCCloningMachineControl(bx, by, tx, ty))
			fields.append(cc_data.CCCloningMachineControlsField(machines))
		elif parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 6:
 			fields.append(cc_data.CCEncodedPasswordField(parsed_json["levels"][givenLevel]["optional fields"][count]["password"]))
		elif parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 7:
			fields.append(cc_data.CCMapHintField(parsed_json["levels"][givenLevel]["optional fields"][count]["hint"]))
		elif parsed_json["levels"][givenLevel]["optional fields"][count]["field type"] == 10:
			monster_count = len(parsed_json["levels"][givenLevel]["optional fields"][count]["monsters"])
			monsters = []
			for m in range(monster_count):
				x = parsed_json["levels"][givenLevel]["optional fields"][count]["monsters"][m]["x"]
				y = parsed_json["levels"][givenLevel]["optional fields"][count]["monsters"][m]["y"]
				monsters.append(cc_data.CCCoordinate(x,y))
				fields.append(cc_data.CCMonsterMovementField(monsters))
		count += 1
	return fields

def write_cc_data_to_dat(cc_dat, dat_file):
    """Writes the given CC dat in binary form to the file
    Args:
        cc_dat (CCData): the cc data to write
        dat_file (string): the filename of the output file
    """
    with open(dat_file, 'wb') as writer: # Note: DAT files are opened in binary mode
        # Basic DAT file format is: DAT header, total number of levels, level 1, level 2, etc.
        writer.write(CC_DAT_HEADER_CODE)
        writer.write(cc_dat.level_count.to_bytes(2, cc_data.BYTE_ORDER))
        for level in cc_dat.levels:
            write_level_to_dat(level, writer)

def calculate_option_field_byte_size(field):
    """Returns the size of a given field if converted to binary form
    Note: The total byte count of field entry is the type (1 byte) + size (1 byte) and size of the data in byte form
    Args:
        field (CCField)
    """
    byte_data = field.byte_data
    return len(byte_data) + 2


def calculate_total_optional_field_byte_size(optional_fields):
    """Returns the total size of all the given optional fields if converted to binary form
    Note: The total byte count of field entry is the type (1 byte) + size (1 byte) and size of the data in byte form
    Args:
        optional_fields (list of CCFields)
    """
    optional_fields_size = 0
    for field in optional_fields:
        optional_fields_size += calculate_option_field_byte_size(field)
    return optional_fields_size


def calculate_level_byte_size(level):
    """Returns the total size of the given level if converted to binary form
    The total byte count of level entry is:
    size (2) + level number (2) + time (2) + chip count (2) +
    map detail (2) + layer1 size (2) + number of bytes in layer1 + layer2 size (2) + number of bytes in layer2 +
    size of optional fields
    Args:
        level (CCLevel)
    """
    optional_fields_size = calculate_total_optional_field_byte_size(level.optional_fields)
    upper_layer_size = len(level.upper_layer)
    lower_layer_size = len(level.lower_layer)
    return 14 + upper_layer_size + lower_layer_size + optional_fields_size


def write_field_to_dat(field, writer):
    """Writes the given field in binary form to the given writer
    Args:
        field (CCField): the field to write
        writer (BufferedWriter): the active writer in binary write mode
    """
    byte_data = field.byte_data
    writer.write(field.type_val.to_bytes(1, cc_data.BYTE_ORDER))
    writer.write(len(byte_data).to_bytes(1, cc_data.BYTE_ORDER))
    writer.write(byte_data)


def write_layer_to_dat(layer, writer):
    """Writes the given layer in binary form to the given writer
    Note: while the DAT file format supports run length encoding, this function does not implement it
    Args:
        layer (list of ints): the layer to write
        writer (BufferedWriter): the active writer in binary write mode
    """
    byte_size = len(layer)
    writer.write(byte_size.to_bytes(2, cc_data.BYTE_ORDER))
    for val in layer:
        if type(val) is int:
            byte_val = val.to_bytes(1, cc_data.BYTE_ORDER)
        else:
            byte_val = val
        writer.write(byte_val)


def write_level_to_dat(level, writer):
    """Writes the given level in binary form to the given writer
    Args:
        level (CCLevel): the level to write
        writer (BufferedWriter): the active writer in binary write mode
    """
    level_bytes = calculate_level_byte_size(level)
    writer.write(level_bytes.to_bytes(2, cc_data.BYTE_ORDER))
    writer.write(level.level_number.to_bytes(2, cc_data.BYTE_ORDER))
    writer.write(level.time.to_bytes(2, cc_data.BYTE_ORDER))
    writer.write(level.num_chips.to_bytes(2, cc_data.BYTE_ORDER))
    writer.write(b'\x01\x00')  # Write the "map detail" which is always a 2 byte number set to 1
    write_layer_to_dat(level.upper_layer, writer)
    write_layer_to_dat(level.lower_layer, writer)
    total_field_byte_size = calculate_total_optional_field_byte_size(level.optional_fields)
    writer.write(total_field_byte_size.to_bytes(2, cc_data.BYTE_ORDER))
    for field in level.optional_fields:
        write_field_to_dat(field, writer)



write_cc_data_to_dat(make_cc_data_from_json("data/test_level1.json"), "test_level1.dat")

""" if field_type == cc_data.CCMapTitleField.TYPE:
                 return cc_data.CCMapTitleField(get_string_from_bytes(field_bytes))
             elif field_type == cc_data.CCTrapControlsField.TYPE:
                 trap_count = int(len(field_bytes) / 10)
                 traps = []
                 for t_index in range(trap_count):
                     i = t_index * 10
                     bx = int.from_bytes(field_bytes[i:(i + 2)], byteorder=cc_data.BYTE_ORDER)
                     by = int.from_bytes(field_bytes[i + 2:(i + 4)], byteorder=cc_data.BYTE_ORDER)
                     tx = int.from_bytes(field_bytes[i + 4:(i + 6)], byteorder=cc_data.BYTE_ORDER)
                     ty = int.from_bytes(field_bytes[i + 6:(i + 8)], byteorder=cc_data.BYTE_ORDER)
                     traps.append(cc_data.CCTrapControl(bx, by, tx, ty))
                 return cc_data.CCTrapControlsField(traps)
             elif field_type == cc_data.CCCloningMachineControlsField.TYPE:
                 machine_count = int(len(field_bytes) / 8)
                 machines = []
                 for m_index in range(machine_count):
                     i = m_index * 8
                     bx = int.from_bytes(field_bytes[i:(i + 2)], byteorder=cc_data.BYTE_ORDER)
                     by = int.from_bytes(field_bytes[i + 2:(i + 4)], byteorder=cc_data.BYTE_ORDER)
                     tx = int.from_bytes(field_bytes[i + 4:(i + 6)], byteorder=cc_data.BYTE_ORDER)
                     ty = int.from_bytes(field_bytes[i + 6:(i + 8)], byteorder=cc_data.BYTE_ORDER)
                     machines.append(cc_data.CCCloningMachineControl(bx, by, tx, ty))
                 return cc_data.CCCloningMachineControlsField(machines)
             elif field_type == cc_data.CCEncodedPasswordField.TYPE:
                 # passwords are encoded as a list of ints
                 password = []
                 # A bytes object behaves as a list of integers
                 # password data is terminated with a zero, iterate to one short of the end of the array
                 for b in field_bytes[0:(len(field_bytes)-1)]:
                     password.append(b)
                 return cc_data.CCEncodedPasswordField(password)
             elif field_type == cc_data.CCMapHintField.TYPE:
                 return cc_data.CCMapHintField(get_string_from_bytes(field_bytes))
             elif field_type == cc_data.CCPasswordField.TYPE:
                 return cc_data.CCPasswordField(get_string_from_bytes(field_bytes))
             elif field_type == cc_data.CCMonsterMovementField.TYPE:
                 monster_count = int(len(field_bytes) / 2)
                 monsters = []
                 for m_index in range(monster_count):
                     i = m_index * 2
                     x = int.from_bytes(field_bytes[i:(i + 1)], byteorder=cc_data.BYTE_ORDER)
                     y = int.from_bytes(field_bytes[i + 1:(i + 2)], byteorder=cc_data.BYTE_ORDER)
                     monsters.append(cc_data.CCCoordinate(x, y))
                 return cc_data.CCMonsterMovementField(monsters)
             else:
                 if __debug__:
                     raise AssertionError("Unsupported field type: " + str(field_type))
                 return cc_data.CCField(field_type, field_bytes)"""