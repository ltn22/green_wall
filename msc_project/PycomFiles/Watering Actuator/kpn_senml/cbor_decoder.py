# _  __  ____    _   _ 
# | |/ / |  _ \  | \ | |
# | ' /  | |_) | |  \| |
# | . \  |  __/  | |\  |
# |_|\_\ |_|     |_| \_|
# 
# (c) 2018 KPN
# License: MIT license.
# Author: Jan Bogaerts
# 
# decode cbor

import uio
import ustruct as struct

class CBORDecodeError(Exception):
    """Raised when an error occurs deserializing a CBOR datastream."""

break_marker = object()

class CBORSimpleValue(object):
    """
    Represents a CBOR "simple value".
    :param int value: the value (0-255)
    """

    __slots__ = 'value'

    def __init__(self, value):
        if value < 0 or value > 255:
            raise TypeError('simple value too big')
        self.value = value

    def __eq__(self, other):
        if isinstance(other, CBORSimpleValue):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        return NotImplemented

    def __repr__(self):
        return 'CBORSimpleValue({self.value})'.format(self=self)

def decode_uint(decoder, subtype, allow_indefinite=False):
    # Major tag 0
    if subtype < 24:
        return subtype
    elif subtype == 24:
        return struct.unpack('>B', decoder.read(1))[0]
    elif subtype == 25:
        return struct.unpack('>H', decoder.read(2))[0]
    elif subtype == 26:
        return struct.unpack('>L', decoder.read(4))[0]
    elif subtype == 27:
        return struct.unpack('>Q', decoder.read(8))[0]
    elif subtype == 31 and allow_indefinite:
        return None
    else:
        raise CBORDecodeError('unknown unsigned integer subtype 0x%x' % subtype)

def decode_negint(decoder, subtype):
    # Major tag 1
    uint = decode_uint(decoder, subtype)
    return -uint - 1

def decode_bytestring(decoder, subtype):
    # Major tag 2
    length = decode_uint(decoder, subtype, allow_indefinite=True)
    if length is None:
        # Indefinite length
        buf = bytearray()
        while True:
            initial_byte = decoder.read(1)[0]
            if initial_byte == 255:
                return buf
            else:
                length = decode_uint(decoder, initial_byte & 31)
                value = decoder.read(length)
                buf.extend(value)
    else:
        return decoder.read(length)

def decode_string(decoder, subtype):
    # Major tag 3
    return decode_bytestring(decoder, subtype).decode('utf-8')

def decode_array(decoder, subtype):
    # Major tag 4
    items = []
    length = decode_uint(decoder, subtype, allow_indefinite=True)
    if length is None:
        # Indefinite length
        while True:
            value = decoder.decode()
            if value is break_marker:
                break
            else:
                items.append(value)
    else:
        for _ in range(length):
            item = decoder.decode()
            items.append(item)
    return items


def decode_map(decoder, subtype):
    # Major tag 5
    dictionary = {}
    length = decode_uint(decoder, subtype, allow_indefinite=True)
    if length is None:
        # Indefinite length
        while True:
            key = decoder.decode()
            if key is break_marker:
                break
            else:
                value = decoder.decode()
                dictionary[key] = value
    else:
        for _ in range(length):
            key = decoder.decode()
            value = decoder.decode()
            dictionary[key] = value

    return dictionary


def decode_special(decoder, subtype):
    # Simple value
    if subtype < 20:
        return CBORSimpleValue(subtype)

    # Major tag 7
    return special_decoders[subtype](decoder)

def decode_simple_value(decoder):
    return CBORSimpleValue(struct.unpack('>B', decoder.read(1))[0])

def decode_float16(decoder):
    payload = decoder.read(2)
    return unpack_float16(payload)


def decode_float32(decoder):
    return struct.unpack('>f', decoder.read(4))[0]


def decode_float64(decoder):
    return struct.unpack('>d', decoder.read(8))[0]    

major_decoders = {
    0: decode_uint,
    1: decode_negint,
    2: decode_bytestring,
    3: decode_string,
    4: decode_array,
    5: decode_map,
    7: decode_special
}

special_decoders = {
    20: lambda self: False,
    21: lambda self: True,
    22: lambda self: None,
    23: lambda self: undefined,
    24: decode_simple_value,
    25: decode_float16,
    26: decode_float32,
    27: decode_float64,
    31: lambda self: break_marker
}


class CBORDecoder(object):
    """
    Deserializes a CBOR encoded byte stream.
    """

    __slots__ = ('fp')

    def __init__(self, fp):
        self.fp = fp

    def read(self, amount):
        """
        Read bytes from the data stream.
        :param int amount: the number of bytes to read
        """
        data = self.fp.read(amount)
        if len(data) < amount:
            raise CBORDecodeError('premature end of stream (expected to read {} bytes, got {} '
                                  'instead)'.format(amount, len(data)))

        return data

    def decode(self):
        """
        Decode the next value from the stream.
        :raises CBORDecodeError: if there is any problem decoding the stream
        """
        try:
            initial_byte = self.fp.read(1)[0]
            major_type = initial_byte >> 5
            subtype = initial_byte & 31
        except Exception as e:
            raise CBORDecodeError('error reading major type at index {}: {}'
                                  .format(self.fp.tell(), e))

        decoder = major_decoders[major_type]
        try:
            return decoder(self, subtype)
        except CBORDecodeError:
            raise
        except Exception as e:
            raise CBORDecodeError('error decoding value {}'.format(e))          # tell doesn't work on micropython at the moment


def loads(payload, **kwargs):
    """
    Deserialize an object from a bytestring.
    :param bytes payload: the bytestring to serialize
    :param kwargs: keyword arguments passed to :class:`~.CBORDecoder`
    :return: the deserialized object
    """
    fp = uio.BytesIO(payload)
    return CBORDecoder(fp, **kwargs).decode()


def load(fp, **kwargs):
    """
    Deserialize an object from an open file.
    :param fp: the input file (any file-like object)
    :param kwargs: keyword arguments passed to :class:`~.CBORDecoder`
    :return: the deserialized object
    """
    return CBORDecoder(fp, **kwargs).decode()