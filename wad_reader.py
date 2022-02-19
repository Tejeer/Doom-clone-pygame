import data_types
import bytes_reader

from enum import Enum, auto


class LUMPS(Enum):

    THINGS = auto()
    LINEDEFS = auto()
    SIDEDEFS = auto()
    VERTEXES = auto()
    SEGS = auto()
    SSECTORS = auto()
    NODES = auto()
    SECTORS = auto()
    REJECT = auto()
    BLOCKMAP = auto()
    COUNT = auto()


class LUMPS_SIZE(Enum):
    VERTEXES = 4
    LINEDEFS = 14
    THINGS = 10
    SSECTORS = 4
    NODES = 28
    SEGS = 12
    SIDEDEFS = 30
    SECTORS = 26


class LINDEF_FLAGS(Enum):
    BLOCKING = 0
    BLOCKMONSTERS = 1
    TWOSIDED = 2
    DONTPEGTOP = 4
    DONTPEGBOTTOM = 8
    SECRET = 16
    SOUNDBLOCK = 32
    DONTDRAW = 64
    DRAW = 128


# DATA_NAME: [DATA_CONSTRUCTOR_FUNC, DATA_CONSTRUCTOR_FUNC_PARAMETERS]
DATA_CONSTRUCTORS_AND_PATTERN = {
        LUMPS.THINGS: [data_types.Thing, 'INT16 INT16 UINT16 UINT16 UINT16'],
        LUMPS.LINEDEFS: [data_types.LineDef, 'UINT16 UINT16 UINT16 UINT16 UINT16 UINT16 UINT16'],
        LUMPS.VERTEXES: [data_types.Vertex, 'INT16 INT16'],
        LUMPS.SIDEDEFS: [data_types.SideDef, 'INT16 INT16 STR STR STR UINT16'],
        LUMPS.SECTORS: [data_types.Sector, 'INT16 INT16 STR STR UINT16 UINT16 UINT16'],
        LUMPS.SEGS: [data_types.Seg, 'UINT16 UINT16 UINT16 UINT16 UINT16 UINT16'],
        LUMPS.SSECTORS: [data_types.SubSector, 'UINT16 UINT16'],
        LUMPS.NODES: [data_types.Node, 'INT16 ' * 12 + 'UINT16 UINT16']
        }

# DATA_TYPE: [CONSTRUCTOR, BYTE_SIZE]
READER_FUNCS = {
        'INT16': [bytes_reader.read_int16, 2],
        'STR': [bytes_reader.read_string, 8],
        'UINT16': [bytes_reader.read_uint16, 2]
        }


class WadLoader:
    def __init__(self, path, Map):
        self.load_wad(path)
        self.map = Map

    def load_wad(self, path):
        try:
            self.file = open(path, 'rb')
            self.read_header(0)
            self.read_directories()
        except FileNotFoundError:
            raise FileNotFoundError

    def close_file(self):
        self.file.close()

    def read_header(self, offset):
        wad_type = bytes_reader.read_string(self.file, offset, 4)
        dir_count = bytes_reader.read_uint32(self.file, offset + 4)
        dir_offset = bytes_reader.read_uint32(self.file, offset + 8)
        self.header = data_types.Header(wad_type, dir_count, dir_offset)

    def readIndividualLumpData(self, offset, lump):
        parameters = []
        constructor_func, parameter_pattern = DATA_CONSTRUCTORS_AND_PATTERN[lump]
        for parameter_type in parameter_pattern.split(' '):
            try:
                reader_func, byte_size = READER_FUNCS[parameter_type]
            except KeyError as ke:
                raise KeyError(ke, lump.name)
            readed_parameter = reader_func(self.file, offset)
            parameters.append(readed_parameter)
            offset += byte_size

        try:
            newObj = constructor_func(*parameters)
        except TypeError as te:
            raise TypeError(te, lump.name)
        return newObj

    def read_directories(self):
        self.directories = []
        self.dir_dict = {}
        for i in range(self.header.dir_count):
            offset = self.header.dir_offset + 16 * i
            lump_offset = bytes_reader.read_uint32(self.file, offset)
            lump_size = bytes_reader.read_uint32(self.file, offset + 4)
            lump_name = bytes_reader.read_string(self.file, offset + 8)
            directory = data_types.Directory(lump_offset, lump_size, lump_name)
            self.directories.append(directory)
            self.dir_dict[lump_name] = len(self.directories) - 1

    def read_map_data(self, data):
        index = self.dir_dict.get(self.map.get_name)
        if not index:
            return False
        index += data.value  # data index
        if self.directories[index].lump_name != data.name:
            raise KeyError
        data_size = LUMPS_SIZE[data.name].value
        data_count = self.directories[index].lump_size // data_size
        for i in range(data_count):
            offset = self.directories[index].lump_offset + i * data_size
            returned_obj = self.readIndividualLumpData(offset, data)
            self.map.add_data(data.name, returned_obj)

    def read_map(self, Map):
        self.read_map_data(LUMPS.VERTEXES)
        self.read_map_data(LUMPS.LINEDEFS)
        self.read_map_data(LUMPS.THINGS)
        self.read_map_data(LUMPS.NODES)
        self.read_map_data(LUMPS.SSECTORS)
        self.read_map_data(LUMPS.SEGS)
        self.read_map_data(LUMPS.SIDEDEFS)
        self.read_map_data(LUMPS.SECTORS)
