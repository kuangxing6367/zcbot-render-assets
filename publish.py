# -*- coding: utf-8 -*-
"""把主仓打好的 assets.zip 发布到本仓库的 Release。

做什么
------
1. **发布前自查**：解压读 manifest.json，逐文件比对 sha256 与 size。
   坏包在本地就该拦下来，而不是等用户下了 9MB 才发现对不上。
2. 用 tag 标记发布：默认 `assets-v<manifest.version>`。
3. tag 已存在时覆盖同名 asset（`--clobber`），让 `releases/latest/download/assets.zip`
   这个固定链接永远指向最新资源，消费方不需要改配置。

用法
----
    python publish.py                          # 自动找 ../zgric_onebot11_35xLe/dist/assets.zip
    python publish.py --from path/to/assets.zip
    python publish.py --tag assets-v1.21.0     # 手动指定 tag
    python publish.py --dry-run                # 只做自查，不联网
    python publish.py --notes notes.md         # 指定 release 说明文件

为什么用 gh 而不是裸 HTTP
------------------------
上传走 GitHub 的 uploads host，需要 token 与分块；`gh release upload` 已经处理好了。
脚本只管调用与结果校验，不自己拼请求。
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = 'kuangxing6367/zcbot-render-assets'
DEFAULT_FROM = os.path.join(os.path.dirname(HERE), 'zgric_onebot11_35xLe',
                            'dist', 'assets.zip')

# 包内必须有、且不能为空的东西
REQUIRED = ('manifest.json',)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(262144), b''):
            h.update(chunk)
    return h.hexdigest()


def find_gh():
    for cand in (shutil.which('gh'),
                 r'C:\Program Files\GitHub CLI\gh.exe',
                 '/usr/bin/gh', '/usr/local/bin/gh'):
        if cand and os.path.isfile(cand):
            return cand
    return None


def verify(zip_path):
    """解压前自查：结构、manifest 完整性、每文件 sha256。返回 (manifest, files)。"""
    if not os.path.isfile(zip_path):
        raise SystemExit('找不到资源包: {}'.format(zip_path))

    zf = zipfile.ZipFile(zip_path)
    names = set(zf.namelist())
    for req in REQUIRED:
        if req not in names:
            raise SystemExit('资源包缺少 {}，拒绝发布'.format(req))

    try:
        manifest = json.loads(zf.read('manifest.json').decode('utf-8'))
    except Exception as e:
        raise SystemExit('manifest.json 解析失败: {}'.format(e))

    mfiles = manifest.get('files') or {}
    if not mfiles:
        raise SystemExit('manifest.json 里没有任何文件记录，拒绝发布')

    problems = []
    for arc, meta in sorted(mfiles.items()):
        if arc not in names:
            problems.append('manifest 声明了 {} 但包里没有'.format(arc))
            continue
        data = zf.read(arc)
        got = hashlib.sha256(data).hexdigest()
        if got != meta.get('sha256'):
            problems.append('{} sha256 不符：manifest={} 实际={}'.format(
                arc, meta.get('sha256'), got))
        if len(data) != meta.get('size'):
            problems.append('{} 大小不符：manifest={} 实际={}'.format(
                arc, meta.get('size'), len(data)))

    # 包里多出来的文件也要报——通常是打包脚本漏写 manifest
    extra = names - set(mfiles) - {'manifest.json'}
    for arc in sorted(extra):
        if not arc.endswith('/'):
            problems.append('包里有 {} 但 manifest 未记录'.format(arc))

    if problems:
        print('自查失败，共 {} 个问题:'.format(len(problems)))
        for p in problems:
            print('  - ' + p)
        raise SystemExit(4)

    print('自查通过: {} 个文件'.format(len(mfiles)))
    return manifest, mfiles


def write_sha_file(zip_path):
    digest = sha256_of(zip_path)
    out = zip_path + '.sha256'
    with open(out, 'w', encoding='utf-8') as f:
        f.write('{}  assets.zip\n'.format(digest))
    print('sha256: {}'.format(digest))
    return out


def run(cmd, dry):
    print('$ ' + ' '.join(cmd))
    if dry:
        return 0
    return subprocess.call(cmd)


def release_exists(gh, tag):
    r = subprocess.run([gh, 'release', 'view', tag, '--repo', REPO],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description='发布 assets.zip 到 zcbot-render-assets')
    ap.add_argument('--from', dest='src', default=DEFAULT_FROM,
                    help='assets.zip 路径（默认主仓 dist/assets.zip）')
    ap.add_argument('--tag', default=None, help='Release tag（默认 assets-v<version>）')
    ap.add_argument('--notes', default=None, help='Release 说明 markdown 文件')
    ap.add_argument('--dry-run', action='store_true', help='只自查，不联网')
    ap.add_argument('--skip-verify', action='store_true',
                    help='跳过自查（不建议，除非确定包是好的）')
    args = ap.parse_args(argv)

    src = os.path.abspath(args.src)
    print('资源包: {}  ({:.2f}MB)'.format(src, os.path.getsize(src) / 1048576.0)
          if os.path.isfile(src) else '资源包: {}  (不存在)'.format(src))

    manifest = {}
    if not args.skip_verify:
        manifest, _ = verify(src)

    version = manifest.get('version') or '0.0.0'
    tag = args.tag or 'assets-v{}'.format(version)
    print('tag: {}  (manifest version {})'.format(tag, version))

    sha_file = write_sha_file(src)

    gh = find_gh()
    if not gh:
        raise SystemExit('找不到 gh CLI，请先安装并完成 gh auth login')
    if args.dry_run:
        print('\n--dry-run：自查完成，未执行上传')
        return 0

    notes = args.notes
    if not notes:
        # 无说明文件时给一段最小可用的默认说明
        notes = os.path.join(HERE, '.release_notes.generated.md')
        with open(notes, 'w', encoding='utf-8') as f:
            f.write('zcbot image_renderer 运行时资源包。\n\n'
                    '- 对应框架版本: {}\n'
                    '- 内容: 字体子集 4 个 + 7 个平台原生扩展\n'
                    '- 结构与局限见仓库 README\n'.format(version))

    if release_exists(gh, tag):
        print('Release {} 已存在，覆盖上传'.format(tag))
        rc = run([gh, 'release', 'upload', tag, '--repo', REPO,
                  '--clobber', src, sha_file], args.dry_run)
    else:
        rc = run([gh, 'release', 'create', tag, '--repo', REPO,
                  '--title', 'assets {}'.format(version),
                  '--notes-file', notes, src, sha_file], args.dry_run)

    if rc != 0:
        raise SystemExit('上传失败（gh 退出码 {}）'.format(rc))

    print('\n完成: https://github.com/{}/releases/tag/{}'.format(REPO, tag))
    print('固定下载地址: https://github.com/{}/releases/latest/download/assets.zip'
          .format(REPO))
    return 0


if __name__ == '__main__':
    sys.exit(main())
