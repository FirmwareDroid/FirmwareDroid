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


class Metadata:
    def __init__(self, inode, itype, size, ctime, mtime, uid=0, gid=0, mode=0, xattr={}):
        self._attr = {
            'inode': inode,
            'type': itype,
            'size': size,
            'ctime': ctime,
            'mtime': mtime,
            'uid': uid,
            'gid': gid,
            'mode': mode
        }
        self._xattr = xattr

    def __str__(self):
        attr_s = []
        for key, value in self._attr.items():
            attr_s.append("{key}=\"{value}\"".format(
                key=key,
                value=value))
        for key, value in self._xattr.items():
            attr_s.append(
                key if value is None else "{key}=\"{value}\"".format(
                    key=key,
                    value=value.decode(
                        'unicode_escape').encode(
                        'unicode_escape').decode(
                        'ascii')))
        return " ".join(attr_s)
