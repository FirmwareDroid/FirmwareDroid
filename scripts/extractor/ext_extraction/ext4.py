"""
    ext4extract - Ext4 data extracting tool
    Copyright (C) 2017, HexEdit (IFProject)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from struct import unpack
from .structs import *
from .direntry import DirEntry
from .metadata import Metadata


class Ext4(object):
    def __init__(self, filename=None):
        self._ext4 = None
        self._superblock = None
        self._block_size = 1024
        self._backup_bgs = []

        if filename is not None:
            self.load(filename)

    def __str__(self):
        if self._superblock is None:
            return "Not loaded"
        else:
            volume_name = self._superblock.s_volume_name.decode('utf-8').rstrip('\0')
            mounted_at = self._superblock.s_last_mounted.decode('utf-8').rstrip('\0')
            if not mounted_at:
                mounted_at = "not mounted"
            return "Volume name: {}, last mounted at: {}".format(volume_name, mounted_at)

    @property
    def _has_sparse_super(self):
        return bool(self._superblock.s_feature_ro_compat & 0x1)

    @property
    def _has_sparse_super2(self):
        return bool(self._superblock.s_feature_compat & 0x200)

    def _read_group_descriptor(self, bg_num):
        gd_offset = (self._superblock.s_first_data_block + 1) * self._block_size \
                    + (bg_num * self._superblock.s_desc_size)
        self._ext4.seek(gd_offset)
        return make_group_descriptor(self._ext4.read(32))

    @staticmethod
    def _test_root(a, b):
        while True:
            if a < b:
                return False
            if a == b:
                return True
            if a % b != 0:
                return False
            a /= b

    def _bg_has_super(self, bg_num):
        if bg_num == 0:
            return True
        if self._has_sparse_super2:
            if bg_num in self._backup_bgs:
                return True
            return False
        if bg_num <= 1:
            return True
        if not self._has_sparse_super:
            return True
        if not bg_num & 1:
            return False
        if self._test_root(bg_num, 3):
            return True
        if self._test_root(bg_num, 5):
            return True
        if self._test_root(bg_num, 7):
            return True
        return False

    def _read_inode(self, inode_num):
        inode_bg_num = (inode_num - 1) // self._superblock.s_inodes_per_group
        bg_inode_idx = (inode_num - 1) % self._superblock.s_inodes_per_group
        group_desc = self._read_group_descriptor(inode_bg_num)
        table_start = (inode_bg_num * self._superblock.s_blocks_per_group) \
            + group_desc.bg_inode_table_lo
        if not self._bg_has_super(inode_bg_num):
            table_start -= 2
        inode_offset = (table_start * self._block_size) \
            + (bg_inode_idx * self._superblock.s_inode_size)
        self._ext4.seek(inode_offset)
        return make_inode(self._ext4.read(128))

    def _read_inode_extra(self, inode_num):
        inode = self._read_inode(inode_num)
        extra = self._ext4.read(self._superblock.s_inode_size - 128)
        return inode, extra

    def _read_extent(self, data, extent_block):
        hdr = make_extent_header(extent_block[:12])
        if hdr.eh_magic != 0xf30a:
            raise RuntimeError("Bad extent magic")

        for eex in range(0, hdr.eh_entries):
            raw_offset = 12 + (eex * 12)
            entry_raw = extent_block[raw_offset:raw_offset + 12]
            if hdr.eh_depth == 0:
                entry = make_extent_entry(entry_raw)
                _start = entry.ee_block * self._block_size
                _size = entry.ee_len * self._block_size
                self._ext4.seek(entry.ee_start_lo * self._block_size)
                data[_start:_start + _size] = self._ext4.read(_size)
            else:
                index = make_extent_index(entry_raw)
                self._ext4.seek(index.ei_leaf_lo * self._block_size)
                lower_block = self._ext4.read(self._block_size)
                self._read_extent(data, lower_block)

    def _read_data(self, inode):
        data = b''

        if inode.i_size_lo == 0:
            pass
        elif inode.i_flags & 0x10000000 or (inode.i_mode & 0xf000 == 0xa000 and inode.i_size_lo <= 60):
            data = inode.i_block
        elif inode.i_flags & 0x80000:
            data = bytearray(inode.i_size_lo)
            self._read_extent(data, inode.i_block)
        else:
            raise RuntimeError("Mapped Inodes are not supported")

        return data

    def load(self, filename):
        self._ext4 = open(filename, "rb")
        self._ext4.seek(1024)
        self._superblock = make_superblock(self._ext4.read(256))
        if self._superblock.s_magic != 0xef53:
            raise RuntimeError("Bad superblock magic")
        incompat = self._superblock.s_feature_incompat
        for f_id in [0x1, 0x4, 0x10, 0x80, 0x200, 0x1000, 0x4000, 0x10000]:
            if incompat & f_id:
                raise RuntimeError("Unsupported feature ({:#x})".format(f_id))
        self._block_size = 2 ** (10 + self._superblock.s_log_block_size)
        if self._has_sparse_super2:
            self._ext4.seek(0x64c)
            self._backup_bgs = list(unpack('<2I', self._ext4.read(8)))
        else:
            self._backup_bgs = []

    def read_dir(self, inode_num):
        inode = self._read_inode(inode_num)
        dir_raw = self._read_data(inode)
        dir_data = list()
        offset = 0
        while offset < len(dir_raw):
            entry_raw = dir_raw[offset:offset + 8]
            entry = DirEntry()
            if self._superblock.s_feature_incompat & 0x2:
                dir_entry = make_dir_entry_v2(entry_raw)
                if dir_entry.inode == 0:
                    break
                entry.type = dir_entry.file_type
            else:
                dir_entry = make_dir_entry(entry_raw)
                if dir_entry.inode == 0:
                    break
                entry_inode = self._read_inode(dir_entry.inode)
                inode_type = entry_inode.i_mode & 0xf000
                if inode_type == 0x1000:
                    entry.type = 5
                elif inode_type == 0x2000:
                    entry.type = 3
                elif inode_type == 0x4000:
                    entry.type = 2
                elif inode_type == 0x6000:
                    entry.type = 4
                elif inode_type == 0x8000:
                    entry.type = 1
                elif inode_type == 0xA000:
                    entry.type = 7
                elif inode_type == 0xC000:
                    entry.type = 6
            entry.inode = dir_entry.inode
            entry.name = dir_raw[offset + 8:offset + 8 + dir_entry.name_len].decode('utf-8')
            dir_data.append(entry)
            offset += dir_entry.rec_len
        return dir_data

    def read_file(self, inode_num):
        inode = self._read_inode(inode_num)
        return self._read_data(inode)[:inode.i_size_lo], inode.i_atime, inode.i_mtime

    def read_link(self, inode_num):
        inode = self._read_inode(inode_num)
        return self._read_data(inode)[:inode.i_size_lo].decode('utf-8')

    def read_xattr(self, inode, extra=None):
        xattr = {}

        if extra:
            extra_isize, = unpack('<I', extra[:4])
            extra_data = extra[extra_isize:]
            if extra_data:
                xattr_ihdr, = unpack('<I', extra_data[:4])
                if xattr_ihdr == 0xea020000:
                    xattr.update(self._parse_xattr(extra_data[4:]))

        if inode.i_file_acl_lo:
            self._ext4.seek(inode.i_file_acl_lo * self._block_size)
            hdr_raw = self._ext4.read(32)
            xattr_hdr = make_xattr_header(hdr_raw)
            if xattr_hdr.h_magic != 0xea020000:
                raise RuntimeError("Bad xattr magic")
            xattr_data = self._ext4.read((self._block_size * xattr_hdr.h_blocks) - 32)
            xattr.update(self._parse_xattr(hdr_raw + xattr_data, 32))

        return xattr

    def _parse_xattr(self, xattr_data, offset=0):
        xattr_prefix = [
            "",
            "user.",
            "system.posix_acl_access",
            "system.posix_acl_default",
            "trusted.",
            "security.",
            "system.",
            "system.richacl"
        ]
        xattr = {}

        while offset < len(xattr_data):
            entry = make_xattr_entry(xattr_data[offset:offset + 16])
            if (entry.e_name_len, entry.e_name_index) == (0, 0):
                break
            offset += 16

            name = xattr_data[offset:offset + entry.e_name_len].decode('ascii')
            offset += entry.e_name_len

            if entry.e_value_inum:
                value = self._read_data(self._read_inode(entry.e_value_inum))
            else:
                value = xattr_data[entry.e_value_offs:entry.e_value_offs + entry.e_value_size]
            if value == b'':
                value = None

            key = xattr_prefix[entry.e_name_index] + name
            xattr[key] = value

        return xattr

    def read_meta(self, inode_num):
        inode, extra = self._read_inode_extra(inode_num)
        return Metadata(
            inode=inode_num,
            itype=inode.i_mode >> 12 & 0xf,
            size=inode.i_size_lo,
            ctime=inode.i_ctime,
            mtime=inode.i_mtime,
            uid=inode.i_uid,
            gid=inode.i_gid,
            mode=inode.i_mode & 0xfff,
            xattr=self.read_xattr(inode, extra))

    @property
    def root(self):
        return self.read_dir(2)
