import os
import md5util
import time

if __name__ == "__main__":
    from PyInstaller.__main__ import run

    key = md5util.Md5Util.get_data_md5({"key": 'www.one-in-cloud.com' + str(time.time())}, ["key"])

    opts = [
        '-F',
        '-w',
        # '-D',
        '--add-data=%s;%s' % (os.path.join('client','resource', 'images', '*.png'),os.path.join('client','resource', 'images')),
        '--add-data=%s;%s' % (os.path.join('client', 'resource', 'sounds', '*.wav'), os.path.join('client', 'resource', 'sounds')),
        '--name=%s' % '幸运飞艇-策略2',
        '--icon=xyft.ico',
        # '--key=%s' % key,
        '--clean',
        '-y',
        'strategy2_run.py'
    ]

    run(opts)