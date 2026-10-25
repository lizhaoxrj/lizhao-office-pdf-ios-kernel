#!/usr/bin/env python3
"""只增量恢复独立六项尺寸诊断源码；不覆盖旧内核和已有目标。"""
import argparse
import hashlib
import json
import os
import pathlib
import stat

FORMAT = 'office-pdf-ios-size-sources-v1'
SOURCE_ROOT = 'native-kernels/lizhao-office-pdf-ios'
MAX_FILE_BYTES = 128 * 1024
MAX_TOTAL_BYTES = 512 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024
ALLOWED_PATHS = (
    'size_validation/restore_source.py', 'size_validation/package_sources.py',
    'size_validation/test_sources.py', 'size_validation/size_probe.py',
    'size_validation/test_size_probe.py', 'ci/size_probe.yml',
)


def stat_identity(value):
    """同 fd、前后路径都比较完整七字段；不把 atime 当内容变化。"""
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _plain(value, directory=False):
    if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
        raise ValueError('拒绝符号链接或 Windows 重解析点')
    if directory:
        if not stat.S_ISDIR(value.st_mode):
            raise ValueError('祖先必须是普通目录')
    elif not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise ValueError('文件必须是无硬链接的普通独立文件')


def absolute(path):
    path = pathlib.Path(path)
    if '..' in path.parts:
        raise ValueError('拒绝包含父路径跳转的工作路径')
    return pathlib.Path(os.path.abspath(path))


def checked_directories(path):
    """从文件系统根逐级 lstat；不 resolve 后丢掉根或祖先链接证据。"""
    path = absolute(path)
    result = []
    for item in reversed((path, *path.parents)):
        value = item.lstat()
        _plain(value, directory=True)
        result.append((item, stat_identity(value)))
    return result


def verify_directories(snapshot):
    for path, expected in snapshot:
        value = path.lstat()
        _plain(value, directory=True)
        # 共享临时根可能由其他任务新增普通文件；目录只固定实体/类型，
        # 文件内容的大小和纳秒时间仍执行完整七字段核验。
        if stat_identity(value)[:3] != expected[:3]:
            raise ValueError('读取期间祖先目录身份发生变化：' + str(path))


def read_stable(path, limit):
    path = absolute(path)
    ancestors = checked_directories(path.parent)
    before = path.lstat()
    _plain(before)
    if before.st_size > limit:
        raise ValueError('文件超过读取上限：' + str(path))
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0) | getattr(os, 'O_BINARY', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        _plain(opened)
        expected = stat_identity(before)
        if stat_identity(opened) != expected:
            raise ValueError('打开的文件与预检身份不同')
        chunks, count = [], 0
        while True:
            block = os.read(fd, min(65536, limit + 1 - count))
            if not block:
                break
            chunks.append(block)
            count += len(block)
            if count > limit:
                raise ValueError('读取期间文件超过上限')
        after = os.fstat(fd)
        final = path.lstat()
        _plain(final)
        if stat_identity(after) != expected or stat_identity(final) != expected or count != before.st_size:
            raise ValueError('读取期间文件七字段身份发生变化')
        verify_directories(ancestors)
        return b''.join(chunks)
    finally:
        os.close(fd)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('JSON 字段重复：' + key)
        result[key] = value
    return result


def validate_manifest(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('清单类型错误或超过 1MiB 上限')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != {'format', 'root', 'files'}:
        raise ValueError('清单必须只有 format、root、files')
    if value['format'] != FORMAT or value['root'] != SOURCE_ROOT or not isinstance(value['files'], list):
        raise ValueError('独立尺寸源码清单身份无效')
    files, identities, total = {}, set(), 0
    for item in value['files']:
        if not isinstance(item, dict) or set(item) != {'path', 'content', 'bytes', 'sha256'}:
            raise ValueError('文件字段不完整或含额外字段')
        relative = item['path']
        if not isinstance(relative, str) or relative not in ALLOWED_PATHS:
            raise ValueError('非精确六项白名单或非 canonical 路径')
        canonical = pathlib.PurePosixPath(relative)
        if canonical.as_posix() != relative or canonical.is_absolute() or any(p in ('', '.', '..') for p in canonical.parts):
            raise ValueError('路径不是规范相对路径')
        if relative.casefold() in identities:
            raise ValueError('重复路径或路径别名')
        identities.add(relative.casefold())
        if not isinstance(item['content'], str) or type(item['bytes']) is not int:
            raise ValueError('内容或字节数类型错误')
        content = item['content'].encode('utf-8')
        total += len(content)
        if len(content) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES or len(content) != item['bytes']:
            raise ValueError('单文件/总字节上限或实际大小不符')
        digest = item['sha256']
        if not isinstance(digest, str) or digest != hashlib.sha256(content).hexdigest():
            raise ValueError('实际 SHA-256 不符')
        files[relative] = content
    if set(files) != set(ALLOWED_PATHS):
        raise ValueError('必须精确包含六项来源')
    return files


def require_absent(path):
    """lstat 包括悬空链接；所有目标预检完成后才能开始写入。"""
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ValueError('拒绝覆盖已存在的目标：' + str(path))


def exclusive_directory(path):
    path = absolute(path)
    snapshot = checked_directories(path.parent)
    require_absent(path)
    # macOS 使用 dir_fd 固定直接父目录，Windows 以每次前后路径身份核验兜底。
    if os.mkdir in os.supports_dir_fd:
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
        try:
            if stat_identity(os.fstat(fd)) != snapshot[-1][1]:
                raise ValueError('建目录前父目录身份改变')
            verify_directories(snapshot)
            os.mkdir(path.name, dir_fd=fd)
            if (os.fstat(fd).st_dev, os.fstat(fd).st_ino) != snapshot[-1][1][:2]:
                raise ValueError('建目录期间父目录身份改变')
        finally:
            os.close(fd)
    else:
        verify_directories(snapshot)
        path.mkdir()
    checked_directories(path)
    for ancestor, identity in snapshot:
        current = ancestor.lstat()
        _plain(current, directory=True)
        if (current.st_dev, current.st_ino, current.st_mode) != identity[:3]:
            raise ValueError('建目录期间祖先身份改变')


def write_exclusive(path, content):
    path = absolute(path)
    snapshot = checked_directories(path.parent)
    require_absent(path)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0)
    parent_fd = None
    try:
        if os.open in os.supports_dir_fd:
            parent_fd = os.open(path.parent, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0))
            if stat_identity(os.fstat(parent_fd)) != snapshot[-1][1]:
                raise ValueError('写入前父目录身份改变')
            verify_directories(snapshot)
            fd = os.open(path.name, flags, 0o600, dir_fd=parent_fd)
        else:
            verify_directories(snapshot)
            fd = os.open(path, flags, 0o600)
        try:
            before = os.fstat(fd)
            _plain(before)
            if before.st_size != 0 or stat_identity(path.lstat()) != stat_identity(before):
                raise ValueError('独占创建文件身份异常')
            position = 0
            while position < len(content):
                written = os.write(fd, content[position:])
                if written <= 0:
                    raise OSError('文件写入未前进')
                position += written
            os.fsync(fd)
            after = os.fstat(fd)
            _plain(after)
            if stat_identity(after)[:4] != stat_identity(before)[:4] or after.st_size != len(content):
                raise ValueError('写入后文件身份或大小异常')
            os.lseek(fd, 0, os.SEEK_SET)
            readback = bytearray()
            while len(readback) <= len(content):
                block = os.read(fd, min(65536, len(content) + 1 - len(readback)))
                if not block:
                    break
                readback.extend(block)
            final = path.lstat()
            _plain(final)
            if bytes(readback) != content or stat_identity(os.fstat(fd)) != stat_identity(after) or stat_identity(final) != stat_identity(after):
                raise ValueError('同 fd 回读或最终路径七字段身份不符')
            # 自身新增文件会改变直接父目录时间/大小，祖先仍须保持同一目录实体。
            for ancestor, identity in snapshot:
                current = ancestor.lstat()
                _plain(current, directory=True)
                if (current.st_dev, current.st_ino, current.st_mode) != identity[:3]:
                    raise ValueError('写入期间祖先目录身份改变')
        finally:
            os.close(fd)
    finally:
        if parent_fd is not None:
            os.close(parent_fd)


def restore(manifest, destination):
    files = validate_manifest(read_stable(manifest, MAX_MANIFEST_BYTES))
    destination = absolute(destination)
    checked_directories(destination)
    target = destination / SOURCE_ROOT
    # 旧恢复器已恢复的根及 ci 可以存在；绝不要求删除或重建旧39项。
    checked_directories(target / 'ci')
    require_absent(target / 'size_validation')
    for relative in ALLOWED_PATHS:
        require_absent(target / relative)
    # 此前所有清单与所有目标均已预检；从此仅独占创建新的路径。
    exclusive_directory(target / 'size_validation')
    for relative, content in sorted(files.items()):
        write_exclusive(target / relative, content)
    for relative, content in files.items():
        if read_stable(target / relative, MAX_FILE_BYTES) != content:
            raise ValueError('返回成功前整批恢复源码回读不符：' + relative)
    return {'format': FORMAT, 'root': SOURCE_ROOT, 'files': len(files),
            'sha256Verified': True, 'overwritten': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=pathlib.Path, default=pathlib.Path('size-probe-source.json'))
    parser.add_argument('--destination', type=pathlib.Path, default=pathlib.Path('.'))
    args = parser.parse_args()
    try:
        print(json.dumps(restore(args.manifest, args.destination), ensure_ascii=False))
    except (OSError, ValueError, UnicodeError) as error:
        parser.exit(1, '独立尺寸源码恢复失败：' + str(error) + '\n')


if __name__ == '__main__':
    main()
