#!/usr/bin/env python3
"""仅恢复经过白名单、SHA-256 和路径检查的 Office PDF iOS 文本源码；拒绝覆盖。"""
import argparse
import hashlib
import json
import pathlib
import sys

FORMAT = 'office-pdf-ios-source-v1'
SOURCE_ROOT = 'native-kernels/lizhao-office-pdf-ios'
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_BYTES = 28 * 1024 * 1024
# 精确白名单，不能从上传的 manifest 扩大。无文档样本、证书、凭据或其他插件。
ALLOWED_PATHS = (
    'apply_offline_policy.py', 'build_kernel.py', 'build_compat.py', 'offline-policy.json', 'offline-policy.patch',
    'OFFLINE_POLICY.md', 'README.md',
    'include/module.modulemap', 'include/OfficePdfKernel.h', 'src/OfficePdfKernel.mm',
    'src/OfficePdfRegistration.cxx',
    'ci/office-pdf-ios.yml', 'ci/export_candidate.yml', 'ci/harness.yml', 'ci/README.md', 'ci/run.py', 'ci/test_run.py', 'ci/pkg_config.py',
    'ci/checkpoint.py', 'ci/test_checkpoint.py',
    'ci/inspect_link.py', 'ci/test_inspect_link.py', 'ci/inspect_run7.json',
    'ci/package_sources.py', 'ci/restore-source.py', 'ci/test_sources.py',
    'acceptance/KernelAbiAcceptance.swift', 'acceptance/build_harness.py',
    'acceptance/test_build_harness.py', 'acceptance/notices-source.json',
    'tests/input_fixtures.py', 'tests/input_main.swift', 'tests/input_README.md', 'tests/input_run.py',
    'tests/OfficePdfTaskGateTests.swift', 'tests/test_build_kernel.py', 'tests/test_offline_policy.py', 'tests/test_build_compat.py', 'tests/test_vcl_contract.py',
)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('JSON 字段重复：' + key)
        value[key] = item
    return value


def validate_manifest(raw):
    if len(raw) > MAX_MANIFEST_BYTES:
        raise ValueError('源码清单超过体积上限')
    value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != {'format', 'root', 'files'}:
        raise ValueError('源码清单结构无效')
    if value['format'] != FORMAT or value['root'] != SOURCE_ROOT or not isinstance(value['files'], list):
        raise ValueError('源码清单身份无效')
    files = {}
    identities = set()
    for item in value['files']:
        if not isinstance(item, dict) or set(item) != {'path', 'content', 'bytes', 'sha256'}:
            raise ValueError('源码文件字段无效')
        path = item['path']
        if not isinstance(path, str) or path not in ALLOWED_PATHS or '\\' in path or ':' in path or '\x00' in path:
            raise ValueError('非白名单或不安全路径')
        parts = pathlib.PurePosixPath(path)
        if parts.is_absolute() or any(part in ('', '.', '..') for part in parts.parts) or parts.as_posix() != path:
            raise ValueError('不安全相对路径')
        identity = path.casefold()
        if identity in identities:
            raise ValueError('源码路径重复：' + path)
        identities.add(identity)
        if not isinstance(item['content'], str) or type(item['bytes']) is not int:
            raise ValueError('源码内容或长度类型无效')
        content = item['content'].encode('utf-8')
        if len(content) > MAX_FILE_BYTES or len(content) != item['bytes']:
            raise ValueError('源码长度不一致：' + path)
        if item['sha256'] != hashlib.sha256(content).hexdigest():
            raise ValueError('源码 SHA-256 不一致：' + path)
        files[path] = content
    if set(files) != set(ALLOWED_PATHS):
        raise ValueError('源码白名单文件不完整')
    return files


def restore(manifest, destination):
    if manifest.is_symlink():
        raise ValueError('拒绝符号链接清单')
    if manifest.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError('源码清单超过体积上限')
    files = validate_manifest(manifest.read_bytes())
    # macOS 的 /var -> /private/var 属于工作根之前的系统别名。
    # 先固定真实工作根，再拒绝根内现有链接；不能把根内链接当系统别名放行。
    destination = destination.resolve(strict=True)
    if not destination.is_dir():
        raise ValueError('恢复目标工作目录必须已存在')
    native = destination / 'native-kernels'
    if native.is_symlink() or (native.exists() and not native.is_dir()):
        raise ValueError('native-kernels 目录不安全')
    target = destination / SOURCE_ROOT
    if target.exists() or target.is_symlink():
        raise ValueError('拒绝覆盖已有内核目录')
    native.mkdir(exist_ok=True)
    target.mkdir()  # 原子占有新目录；已有路径即失败，不覆盖并发创建者。
    for relative, content in sorted(files.items()):
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open('xb') as stream:
            stream.write(content)
    return {'root': SOURCE_ROOT, 'files': len(files), 'sha256Verified': True, 'overwritten': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=pathlib.Path, default=pathlib.Path('kernel-source.json'))
    parser.add_argument('--destination', type=pathlib.Path, default=pathlib.Path('.'))
    args = parser.parse_args()
    try:
        print(json.dumps(restore(args.manifest, args.destination), ensure_ascii=False))
    except (OSError, ValueError, UnicodeError) as error:
        parser.exit(1, '恢复失败：' + str(error) + '\n')


if __name__ == '__main__':
    main()
